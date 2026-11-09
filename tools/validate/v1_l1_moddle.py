#!/usr/bin/env python3
"""V1 layer L1: run tools/validate/v1_moddle_lint.mjs (bpmn-moddle import with the ipd extension, round trip,
bpmnlint recommended) on all BPMN files and turn its output into error records.

Each bpmnlint hit is classified: a hit that is a modelling choice already justified in spec/notes.md (OR gateways,
FLW-02/FLW-07 with DEC-02 and a `justification` on the or-split) becomes a documented SHOULD; any other hit is a
real defect (MUST for bpmnlint category error, SHOULD for warn).

Usage: python -I tools/validate/v1_l1_moddle.py --out <json>
"""
import argparse
import glob
import json
import os
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    files = [os.path.join(ROOT, "out", "ipd_best_practice.bpmn")] + sorted(glob.glob(os.path.join(ROOT, "out", "models", "*.bpmn")))
    p = subprocess.run(["node", os.path.join(ROOT, "tools", "validate", "v1_moddle_lint.mjs")] + files, capture_output=True, text=True, cwd="/tmp")
    errors, passed = [], []

    def err(rule, model, el, msg, sev="MUST", status="open"):
        d = dict(rule_id=rule, layer="L1", model=model, element=el, message=msg, severity=sev, owner="B2", status=status)
        if d not in errors:
            errors.append(d)
    if p.returncode != 0:
        err("MODDLE", "-", "-", "v1_moddle_lint.mjs failed: %s" % p.stderr[-400:])
        json.dump(dict(errors=errors, passed=passed), open(a.out, "w"), indent=1)
        return 1
    d = json.loads(p.stdout)
    specs = {}
    for f in glob.glob(os.path.join(ROOT, "spec", "L*.yaml")):
        s = yaml.safe_load(open(f, encoding="utf-8"))
        specs[s["id"].replace("-", "_")] = s
    notes = open(os.path.join(ROOT, "spec", "notes.md"), encoding="utf-8").read()
    nrules = len(d["recommended_rules"])
    hits = {}
    for f, r in d["files"].items():
        lab = os.path.relpath(f, ROOT)
        if r.get("fatal"):
            err("MODDLE", lab, "-", "bpmn-moddle import failed: %s" % r["fatal"][:300])
            continue
        if r["import_warnings"]:
            for w in r["import_warnings"]:
                err("MODDLE", lab, "-", "bpmn-moddle import warning: %s" % w[:300])
        else:
            passed.append(dict(layer="L1", check="bpmn-moddle %s import with contracts/ipd_moddle.json: 0 warnings (%s)" % (d["versions"]["bpmn-moddle"], lab), count=r["xml_ids"]))
        rt_ok = (not r["reimport_warnings"] and r["roundtrip_traces"] == r["xml_traces"] == r["moddle_traces"]
                 and r["roundtrip_sources"] == r["xml_sources"] == r["moddle_sources"] and not r["roundtrip_missing_ids"])
        if rt_ok:
            passed.append(dict(layer="L1", check="lossless toXML/fromXML round trip: ipd:trace %d, ipd:source %d, ids kept (%s)"
                               % (r["xml_traces"], r["xml_sources"], lab), count=r["xml_traces"]))
        else:
            err("MODDLE", lab, "-", "round trip not lossless: traces xml/moddle/roundtrip %s/%s/%s, sources %s/%s/%s, missing ids %s, re-import warnings %s"
                % (r["xml_traces"], r["moddle_traces"], r["roundtrip_traces"], r["xml_sources"], r["moddle_sources"], r["roundtrip_sources"],
                   r["roundtrip_missing_ids"], r["reimport_warnings"][:3]))
        n_hits = 0
        for rule, reps in r["lint"].items():
            for x in reps:
                n_hits += 1
                xid = x["id"]
                model = xid.split("_")[0] if xid.startswith("L3_") else "_".join(xid.split("_")[:2])
                sid = xid[len(model) + 1:]
                s = specs.get(model)
                node = next((n for n in (s or {}).get("nodes", []) if n["id"] == sid), None)
                key = (rule, model, sid)
                hits.setdefault(key, []).append(lab)
                if len(hits[key]) > 1:
                    continue
                mname = model.replace("_", "-") if model != "L3" else "L3"
                if rule == "no-inclusive-gateway" and node and node["type"] in ("or-split", "or-join"):
                    split = node if node["type"] == "or-split" else None
                    justified = "FLW-02 / FLW-07" in notes and mname in notes.split("FLW-02 / FLW-07", 1)[1].split("\n", 1)[0]
                    if split is not None and not split.get("justification"):
                        justified = False
                    err("BPMNLINT", mname, sid, "bpmnlint %s (%s): %s - modelling choice: OR gateway for 'one or more' (FLW-07, DEC-02), "
                        "justified in notes.md section 8%s" % (rule, x["category"], x["message"], (" and by the or-split justification" if split else "")),
                        sev="SHOULD", status="documented-choice" if justified else "open")
                else:
                    err("BPMNLINT", mname, sid, "bpmnlint %s (%s): %s - real defect (not justified in notes.md)" % (rule, x["category"], x["message"]),
                        sev="MUST" if x["category"] == "error" else "SHOULD")
        passed.append(dict(layer="L1", check="bpmnlint %s recommended (%d rules) run (%s): %d hits, classified below" % (d["versions"]["bpmnlint"], nrules, lab, n_hits),
                           count=n_hits))
    json.dump(dict(errors=errors, passed=passed, versions=d["versions"], raw=d,
                   inputs=[os.path.relpath(f, ROOT) for f in files] + ["contracts/ipd_moddle.json"]), open(a.out, "w"), indent=1)
    print("v1_l1_moddle: %d error records, %d passed" % (len(errors), len(passed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
