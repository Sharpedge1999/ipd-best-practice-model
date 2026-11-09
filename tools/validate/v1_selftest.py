#!/usr/bin/env python3
"""Seeded-fault self-test of the V1 spec checks (v1_spec.py): copies spec/ to a temp dir, injects one fault per
case, runs v1_spec.py on the copy and asserts that the expected rule fires on the expected element.

Read-only on the project. Usage: python -I tools/validate/v1_selftest.py [--work /tmp/v1_selftest_spec]
"""
import argparse
import copy
import glob
import json
import os
import shutil
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V1 = os.path.join(ROOT, "tools", "validate", "v1_spec.py")


def node(s, i):
    return next(n for n in s["nodes"] if n["id"] == i)


def flow(s, i):
    return next(f for f in s["flows"] if f["id"] == i)


# (name, model, mutate(spec), expected rule, expected element substring, expected severity)
CASES = [
    ("unknown src key", "L4-01", lambda s: node(s, "A1")["src"].append({"key": "NO-SUCH-KEY", "loc": "S1"}), "SRC-KEY", "A1", "MUST"),
    ("src loc not behind REQs", "L4-01", lambda s: node(s, "A1")["src"].__setitem__(0, dict(node(s, "A1")["src"][0], loc="A1-9.9.9")), "SRC-LOC", "A1", "MUST"),
    ("unknown REQ", "L4-01", lambda s: node(s, "A2")["req"].append("REQ-999"), "REQ-ID", "A2", "MUST"),
    ("duplicate id", "L4-01", lambda s: s["flows"].append(dict(flow(s, "F2"))), "ID-UNIQUE", "F2", "MUST"),
    ("dangling flow", "L4-01", lambda s: flow(s, "F2").__setitem__("to", "A99"), "REF", "F2", "MUST"),
    ("schema: task without req", "L4-01", lambda s: node(s, "A4").pop("req"), "SCHEMA", "", "MUST"),
    ("FLW-08 AND join closes XOR", "L4-01", lambda s: node(s, "G4").__setitem__("type", "and-join"), "FLW-08", "G4", "MUST"),
    ("FLW-03 implicit split", "L4-07", lambda s: s["flows"].append({"id": "F99", "from": "A2", "to": "A5"}), "FLW-03", "A2", "MUST"),
    ("FLW-04 OR branch without join", "L4-08", lambda s: (flow(s, "F15").__setitem__("to", "E2"), flow(s, "F16").__setitem__("to", "G4")), "FLW-04", "G", "MUST"),
    ("REACH unreachable", "L4-07", lambda s: (s["nodes"].append({"id": "A99", "type": "task", "label": "Review orphan task", "lane": "L_SPON",
                                                                "src": node(s, "A1")["src"], "req": node(s, "A1")["req"], "binding": node(s, "A1")["binding"],
                                                                "jurisdiction": node(s, "A1").get("jurisdiction", [])}),
                                              s["flows"].append({"id": "F99", "from": "A99", "to": "E1"})), "REACH", "A99", "MUST"),
    ("DEC-06 annotation missing", "L4-04", lambda s: s.__setitem__("rule_exceptions", [r for r in s["rule_exceptions"] if r["rule"] != "DEC-06"]), "FLW-04", "G1", "MUST"),
    ("LBL-01 action noun", "L4-04", lambda s: node(s, "A5").__setitem__("label", "Deviation categorisation"), "LBL-01", "A5", "MUST"),
    ("LBL-02 event as command", "L4-04", lambda s: node(s, "E1").__setitem__("label", "Classify deviation"), "LBL-02", "E1", "MUST"),
    ("LBL-03 split without ?", "L4-04", lambda s: node(s, "G2").__setitem__("label", "Important protocol deviation"), "LBL-03", "G2", "MUST"),
    ("LBL-03 unlabelled answer", "L4-04", lambda s: flow(s, "F7").pop("label"), "LBL-03", "F7", "MUST"),
    ("ROL-01 lane not a glossary role", "L4-02", lambda s: s["lanes"][1].__setitem__("name", "CRA team"), "ROL-01", "L_MON", "MUST"),
    ("ROL-02 message flow on gateway", "L4-02", lambda s: s["message_flows"][0].__setitem__("from", "G3"), "ROL-02", "M1", "MUST"),
    ("SCP-06 hand-off label changed", "L4-05", lambda s: next(m for m in s["message_flows"] if m["id"] == "M1").__setitem__("label", "Serious breach reported"), "SCP-06", "M4", "MUST"),
    ("SCP-06 outcome missing", "L4-06", lambda s: node(s, "E2").__setitem__("label", "Site closed"), "SCP-06", "A6", "MUST"),
    ("FLW-07 OR without default", "L4-08", lambda s: flow(s, "F14").pop("default"), "FLW-07", "G3", "SHOULD"),
    # round 3: OR default-flow flaw (OMG 10.6.3) - default flow onto work instead of straight to the OR join; default labelled unconditional
    ("FLW-07 OR default path carries work", "L4-08", lambda s: (flow(s, "F14").pop("default"), flow(s, "F12").__setitem__("default", True)), "FLW-07", "F12", "MUST"),
    ("FLW-07 OR default labelled unconditional", "L4-08", lambda s: flow(s, "F14").__setitem__("label", "Always"), "FLW-07", "F14", "MUST"),
    ("BINDING not strongest", "L4-01", lambda s: node(s, "A10").__setitem__("binding", "binding-ICH"), "BINDING", "A10", "MUST"),
    ("DRAFT flag lost", "L4-01", lambda s: node(s, "A13").pop("draft"), "DRAFT", "A13", "MUST"),
    ("VERIFY item dropped", "L4-01", lambda s: node(s, "A6").__setitem__("verify", []), "VERIFY", "A6", "MUST"),
    ("COVERAGE binding REQ removed", "L4-08", lambda s: node(s, "A4").__setitem__("req", [q for q in node(s, "A4")["req"] if q != "REQ-196"]), "COVERAGE", "REQ-196", "MUST"),
    ("FLW-01 palette", "L4-07", lambda s: node(s, "A2").__setitem__("type", "intermediate-catch-timer"), "FLW-01", "A2", "MUST"),
]


V1B = os.path.join(ROOT, "tools", "validate", "v1_bpmn.py")
XSD = os.path.join(ROOT, "vendor", "xsd_v1", "omg")


def _sub(old, new, count=1):
    def f(t):
        assert old in t, "seed anchor not found: %r" % old[:80]
        return t.replace(old, new, count)
    return f


def _drop_shape(xid):
    def f(t):
        import re as _re
        m = _re.search(r'\s*<bpmndi:BPMNShape id="%s_di"[^>]*>.*?</bpmndi:BPMNShape>' % xid, t, _re.S)
        assert m, xid
        return t[:m.start()] + t[m.end():]
    return f


# (name, file to mutate: "combined" or a model id, text mutation, expected rule, expected element substring)
BPMN_CASES = [
    ("XSD invalid element", "combined", _sub('<bpmn:sequenceFlow id="L4_04_F7"', '<bpmn:bogus id="L4_04_BOGUS"/><bpmn:sequenceFlow id="L4_04_F7"'), "XSD", "line"),
    ("not well-formed", "L4-04", _sub('<bpmn:sequenceFlow id="L4_04_F7"', '<bpmn:sequenceFlow id="L4_04_F7" <'), "XML-WF", "-"),
    ("DI shape missing", "combined", _drop_shape("L4_04_A5"), "DI", "L4_04_A5"),
    ("XOR marker hidden", "combined", _sub('id="L4_04_G1_di" bpmnElement="L4_04_G1" isMarkerVisible="true"', 'id="L4_04_G1_di" bpmnElement="L4_04_G1" isMarkerVisible="false"'), "LAY-04", "L4_04_G1"),
    ("colour attribute", "combined", _sub('id="L4_04_A5_di" bpmnElement="L4_04_A5"', 'id="L4_04_A5_di" bpmnElement="L4_04_A5" xmlns:bioc="http://bpmn.io/schema/bpmn/biocolor/1.0" bioc:fill="#ff0000"'), "LAY-04", "L4_04_A5"),
    ("trace binding changed", "combined", _sub('<ipd:trace binding="binding-ICH" jurisdiction="ICH"', '<ipd:trace binding="guidance" jurisdiction="ICH"'), "TRACE-XML", ""),
    ("doc text changed", "combined", _sub("Requirements: REQ-094, REQ-095", "Requirements: REQ-094"), "TRACE-DOC", "A3"),
    ("per-model export differs", "L4-04", _sub('name="Categorise deviation"', 'name="Categorise deviations"'), "EXPORT", ""),
    ("label changed in XML", "combined", _sub('name="Categorise deviation"', 'name="Categorise deviations"'), "FIDELITY", "A5"),
]


def bpmn_selftest(work):
    import glob as _g
    src_comb = os.path.join(ROOT, "out", "ipd_best_practice.bpmn")
    src_models = sorted(_g.glob(os.path.join(ROOT, "out", "models", "*.bpmn")))
    results = []
    baseline = None
    for name, target, mut, rule, elem in [("baseline", None, None, None, None)] + BPMN_CASES:
        d = os.path.join(work, "bpmn_" + name.replace(" ", "_").replace("-", "_"))
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(os.path.join(d, "models"))
        comb = os.path.join(d, "ipd_best_practice.bpmn")
        shutil.copy(src_comb, comb)
        for p in src_models:
            shutil.copy(p, os.path.join(d, "models"))
        if target:
            p = comb if target == "combined" else os.path.join(d, "models", target + ".bpmn")
            try:
                t = mut(open(p, encoding="utf-8").read())
            except AssertionError as e:
                results.append(dict(case=name, ok=False, detail="seed failed: %s" % e))
                continue
            open(p, "w", encoding="utf-8").write(t)
        out = os.path.join(d, "result.json")
        pr = subprocess.run([sys.executable, "-I", V1B, "--xsd-dir", XSD, "--out", out, "--combined", comb, "--models-dir", os.path.join(d, "models")],
                            capture_output=True, text=True)
        if pr.returncode != 0 or not os.path.exists(out):
            results.append(dict(case=name, ok=False, detail="crash: " + (pr.stderr or "")[-400:]))
            continue
        errs = json.load(open(out))["errors"]
        key = lambda e: (e["rule_id"], e["model"], str(e["element"]), e["message"])
        if baseline is None:
            baseline = {key(e) for e in errs}
            results.append(dict(case=name, ok=True, detail="%d errors (reference)" % len(errs)))
            continue
        new = [e for e in errs if key(e) not in baseline]
        hit = [e for e in new if e["rule_id"] == rule and elem in str(e["element"])]
        results.append(dict(case=name, ok=bool(hit), expected="%s %s" % (rule, elem),
                            detail=(hit[0]["message"][:160] if hit else "new errors: %s" % [(e["rule_id"], e["element"]) for e in new][:6])))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="/tmp/v1_selftest_spec")
    ap.add_argument("--bpmn-only", action="store_true")
    a = ap.parse_args()
    if a.bpmn_only:
        res = bpmn_selftest(a.work)
        for r in res:
            print("%-4s %-34s %s" % ("OK" if r["ok"] else "FAIL", r["case"], r["detail"]))
        n_ok = sum(1 for r in res if r["ok"])
        print("bpmn self-test: %d/%d cases detected" % (n_ok, len(res)))
        json.dump(res, open(os.path.join(a.work, "selftest_bpmn.json"), "w"), indent=1)
        return 0 if n_ok == len(res) else 1
    base = {}
    for f in glob.glob(os.path.join(ROOT, "spec", "L*.yaml")):
        s = yaml.safe_load(open(f, encoding="utf-8"))
        base[s["id"]] = s
    results = []
    # baseline: the unmodified copy must give the same error count as the real run
    for name, model, mut, rule, elem, sev in [("baseline", None, None, None, None, None)] + CASES:
        d = os.path.join(a.work, name.replace(" ", "_").replace("/", "_").replace("?", "q"))
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        for extra in ("notes.md", "coverage.md"):
            shutil.copy(os.path.join(ROOT, "spec", extra), d)
        for mid, s in base.items():
            s2 = copy.deepcopy(s)
            if mid == model:
                mut(s2)
            yaml.safe_dump(s2, open(os.path.join(d, mid + ".yaml"), "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
        out = os.path.join(d, "result.json")
        p = subprocess.run([sys.executable, "-I", V1, "--spec-dir", d, "--out", out], capture_output=True, text=True)
        if p.returncode != 0 or not os.path.exists(out):
            results.append(dict(case=name, ok=False, detail="crash: " + (p.stderr or "")[-400:]))
            continue
        errs = json.load(open(out))["errors"]
        if name == "baseline":
            baseline = {(e["rule_id"], e["model"], str(e["element"])) for e in errs}
            results.append(dict(case=name, ok=True, detail="%d errors (reference)" % len(errs)))
            continue
        new = [e for e in errs if (e["rule_id"], e["model"], str(e["element"])) not in baseline]
        hit = [e for e in new if e["rule_id"] == rule and elem in str(e["element"]) and e["severity"] == sev]
        results.append(dict(case=name, ok=bool(hit), expected="%s %s %s" % (rule, elem, sev),
                            detail=(hit[0]["message"][:160] if hit else "new errors: %s" % [(e["rule_id"], e["element"], e["severity"]) for e in new][:6])))
    n_ok = sum(1 for r in results if r["ok"])
    for r in results:
        print("%-4s %-34s %s" % ("OK" if r["ok"] else "FAIL", r["case"], r["detail"]))
    print("self-test: %d/%d cases detected" % (n_ok, len(results)))
    json.dump(results, open(os.path.join(a.work, "selftest.json"), "w"), indent=1)
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
