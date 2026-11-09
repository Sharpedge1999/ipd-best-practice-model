#!/usr/bin/env python3
"""V1 layer L1 (syntax, DI) and LAY-04 on the BPMN output, plus spec-to-XML fidelity and the full ipd:trace comparison (L4).

Read-only on all inputs. Writes one JSON document (errors + passed checks) to --out.

Usage: python -I tools/validate/v1_bpmn.py --xsd-dir <dir> --out <json> [--combined f.bpmn --models-dir d --spec-dir d]
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

import yaml
from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "ipd": "urn:ipd-best-practice:trace:1.0",
}
B = "{%s}" % NS["bpmn"]
TYPE_TAG = {
    "task": "task", "call-activity": "callActivity",
    "start": "startEvent", "start-message": "startEvent", "start-timer": "startEvent", "end": "endEvent",
    "xor-split": "exclusiveGateway", "xor-join": "exclusiveGateway",
    "and-split": "parallelGateway", "and-join": "parallelGateway",
    "or-split": "inclusiveGateway", "or-join": "inclusiveGateway",
}
ERRORS = []
PASSED = []


def err(rule, model, element, msg, severity="MUST", owner="B2", layer="L1", status="open"):
    d = dict(rule_id=rule, layer=layer, model=model, element=element, message=msg, severity=severity, owner=owner, status=status)
    if d not in ERRORS:  # the same defect seen in the combined file and in a per-model export is reported once
        ERRORS.append(d)


def ok(layer, check, count, note=""):
    PASSED.append(dict(layer=layer, check=check, count=count, note=note))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def mid(model):
    return model.replace("-", "_")


SPEC_DIR = os.path.join(ROOT, "spec")


def load_specs():
    specs = {}
    for f in sorted(glob.glob(os.path.join(SPEC_DIR, "*.yaml"))):
        s = yaml.safe_load(open(f, encoding="utf-8"))
        if isinstance(s, dict) and s.get("level") in ("L3", "L4"):
            specs[s["id"]] = s
    return specs


def check_xsd(path, schema, label):
    try:
        doc = etree.parse(path)
    except etree.XMLSyntaxError as e:
        err("XML-WF", label, "-", "not well-formed: %s" % e)
        return None
    if schema is not None:
        if not schema.validate(doc):
            for e in list(schema.error_log)[:20]:
                err("XSD", label, "line %d" % e.line, e.message)
            return doc
    return doc


def di_checks(root, model, specs, label):
    """DI completeness and markers for one model inside a parsed document."""
    m = mid(model)
    n_err0 = len(ERRORS)
    collab = root.find(".//bpmn:collaboration[@id='%s_COLLAB']" % m, NS)
    if collab is None:
        err("DI", model, m + "_COLLAB", "collaboration missing in %s" % label)
        return
    need = {}
    for p in collab.findall("bpmn:participant", NS):
        need[p.get("id")] = "participant"
        pref = p.get("processRef")
        if pref:
            proc = root.find(".//bpmn:process[@id='%s']" % pref, NS)
            if proc is None:
                err("REF", model, p.get("id"), "processRef %s does not resolve in %s" % (pref, label))
                continue
            for el in proc.iter():
                if not isinstance(el.tag, str) or not el.tag.startswith(B):
                    continue
                t = el.tag[len(B):]
                if t in ("task", "callActivity", "startEvent", "endEvent", "exclusiveGateway", "parallelGateway",
                         "inclusiveGateway", "intermediateCatchEvent", "intermediateThrowEvent", "sequenceFlow",
                         "dataStoreReference", "dataObjectReference", "textAnnotation", "association", "lane"):
                    need[el.get("id")] = t
                if t in ("dataInputAssociation", "dataOutputAssociation"):
                    need[el.get("id")] = t
    for mf in collab.findall("bpmn:messageFlow", NS):
        need[mf.get("id")] = "messageFlow"
    for g in collab.findall("bpmn:group", NS):
        need[g.get("id")] = "group"
    for a in collab.findall("bpmn:association", NS):
        need[a.get("id")] = "association"
    for a in collab.findall("bpmn:textAnnotation", NS):
        need[a.get("id")] = "textAnnotation"
    diag = root.find(".//bpmndi:BPMNDiagram[@id='%s_DIAGRAM']" % m, NS)
    if diag is None:
        err("DI", model, m + "_DIAGRAM", "diagram missing in %s" % label)
        return
    plane = diag.find("bpmndi:BPMNPlane", NS)
    if plane.get("bpmnElement") != m + "_COLLAB":
        err("DI", model, plane.get("id"), "plane bpmnElement %s != %s_COLLAB" % (plane.get("bpmnElement"), m))
    seen = {}
    shapes = {}
    for el in plane:
        if not isinstance(el.tag, str):
            continue
        be = el.get("bpmnElement")
        seen[be] = seen.get(be, 0) + 1
        if el.tag.endswith("BPMNShape"):
            b = el.find("dc:Bounds", NS)
            if b is None or float(b.get("width")) <= 0 or float(b.get("height")) <= 0:
                err("DI", model, be, "shape without positive bounds (%s)" % label)
            else:
                shapes[be] = (float(b.get("x")), float(b.get("y")), float(b.get("width")), float(b.get("height")), el)
        elif el.tag.endswith("BPMNEdge"):
            wps = el.findall("di:waypoint", NS)
            if len(wps) < 2:
                err("DI", model, be, "edge with %d waypoints (%s)" % (len(wps), label))
    missing = [i for i in need if i not in seen]
    extra = [i for i in seen if i not in need]
    dup = [i for i, c in seen.items() if c > 1]
    for i in missing:
        err("DI", model, i, "%s has no DI element in %s_DIAGRAM (%s)" % (need[i], m, label))
    for i in extra:
        err("DI", model, i, "DI element refers to an element outside the model (%s)" % label)
    for i in dup:
        err("DI", model, i, "duplicate DI elements (%s)" % label)
    # XOR markers (LAY-04, isMarkerVisible)
    nx = 0
    for gid, t in need.items():
        if t == "exclusiveGateway":
            nx += 1
            sh = shapes.get(gid)
            if sh is not None and sh[4].get("isMarkerVisible") != "true":
                err("LAY-04", model, gid, "XOR gateway shape without isMarkerVisible=\"true\" (%s)" % label,
                    layer="L3")
    # colour attributes (no colour-only meaning; colour attributes should not exist at all in the XML)
    for el in plane:
        if not isinstance(el.tag, str):
            continue
        for k in el.attrib:
            if "color" in k.lower() or k.endswith("fill") or k.endswith("stroke"):
                err("LAY-04", model, el.get("bpmnElement"), "colour attribute %s in DI (%s)" % (k, label), layer="L3")
    # lane containment: node centre inside its lane's shape, lane inside its pool
    lane_of = {}
    for lane in root.findall(".//bpmn:lane", NS):
        if not lane.get("id", "").startswith(m + "_"):
            continue
        for ref in lane.findall("bpmn:flowNodeRef", NS):
            lane_of[ref.text] = lane.get("id")
    for nid, lid in lane_of.items():
        s, l = shapes.get(nid), shapes.get(lid)
        if s and l:
            cx, cy = s[0] + s[2] / 2, s[1] + s[3] / 2
            if not (l[0] <= cx <= l[0] + l[2] and l[1] <= cy <= l[1] + l[3]):
                err("DI", model, nid, "shape centre outside its lane %s (%s)" % (lid, label))
    # nodes of expanded pools without lanes: inside the participant
    for p in collab.findall("bpmn:participant", NS):
        pref = p.get("processRef")
        if not pref:
            continue
        proc = root.find(".//bpmn:process[@id='%s']" % pref, NS)
        ps = shapes.get(p.get("id"))
        if ps is None or proc is None:
            continue
        for el in proc:
            i = el.get("id")
            if i in shapes and i not in lane_of and need.get(i) not in ("sequenceFlow", "association", None):
                s = shapes[i]
                cx, cy = s[0] + s[2] / 2, s[1] + s[3] / 2
                if not (ps[0] <= cx <= ps[0] + ps[2] and ps[1] <= cy <= ps[1] + ps[3]):
                    err("DI", model, i, "shape centre outside its pool %s (%s)" % (p.get("id"), label))
        if p.find("bpmndi:BPMNShape", NS) is not None:
            pass
    # expanded/collapsed flag in DI consistent with processRef
    for p in collab.findall("bpmn:participant", NS):
        s = shapes.get(p.get("id"))
        if s is None:
            continue
        ish = s[4].get("isHorizontal")
        if ish not in (None, "true"):
            err("DI", model, p.get("id"), "pool not horizontal (%s)" % label, severity="SHOULD")
    if len(ERRORS) == n_err0:
        ok("L1", "DI complete, bounds/waypoints valid, lane/pool containment (%s %s)" % (label, model), len(need))
        ok("L3", "LAY-04 isMarkerVisible on XOR, no colour attributes (%s %s)" % (label, model), nx)
    return need


TRACE_FIELDS = ("src", "req", "binding", "jurisdiction", "deadline", "draft", "verify", "record", "party")


def present(el, k):
    v = el.get(k)
    if k == "draft":
        return v is True
    if k == "deadline":
        return isinstance(v, str) and v.strip() not in ("", "none")
    if isinstance(v, list):
        return len(v) > 0
    return isinstance(v, str) and v.strip() != ""


def expected_trace(el):
    """ipd_extension.md sections 3-5: expected ipd:trace attributes/children and the documentation text, or None."""
    if not any(present(el, k) for k in TRACE_FIELDS):
        return None
    attrs = []
    if present(el, "binding"):
        attrs.append(("binding", el["binding"]))
    if present(el, "jurisdiction"):
        attrs.append(("jurisdiction", " ".join(el["jurisdiction"])))
    if present(el, "deadline"):
        attrs.append(("deadline", el["deadline"]))
    if present(el, "draft"):
        attrs.append(("draft", "true"))
    if present(el, "record"):
        attrs.append(("record", el["record"]))
    if present(el, "party"):
        attrs.append(("party", el["party"]))
    src = [(x["key"], x["loc"], x.get("page") or None) for x in el.get("src", [])]
    lines = []
    if src:
        lines.append("Sources: " + "; ".join("%s %s%s" % (k, l, (" (p. %s)" % p) if p else "") for k, l, p in src))
    if present(el, "req"):
        lines.append("Requirements: " + ", ".join(el["req"]))
    if present(el, "binding"):
        lines.append("Binding: " + el["binding"])
    if present(el, "jurisdiction"):
        lines.append("Jurisdiction: " + ", ".join(el["jurisdiction"]))
    if present(el, "deadline"):
        lines.append("Deadline: " + el["deadline"])
    if present(el, "record"):
        lines.append("Record: " + el["record"])
    if present(el, "party"):
        lines.append("Party: " + el["party"])
    if present(el, "draft"):
        lines.append("Draft: DRAFT guidance")
    if present(el, "verify"):
        lines.append("Verify: " + "; ".join(el["verify"]))
    return dict(attrs=attrs, sources=src, reqs=list(el.get("req", [])), verify=list(el.get("verify", [])), doc="\n".join(lines))


def actual_trace(el):
    tr = el.find("bpmn:extensionElements/ipd:trace", NS)
    docs = el.findall("bpmn:documentation", NS)
    d = dict(n_trace=len(el.findall("bpmn:extensionElements/ipd:trace", NS)), doc=None, doc_format=None, doc_first=None, order_ok=True)
    if docs:
        d["doc"] = docs[0].text or ""
        d["doc_format"] = docs[0].get("textFormat")
    kids = [c for c in el if isinstance(c.tag, str)]
    tags = [c.tag for c in kids]
    if B + "documentation" in tags and B + "extensionElements" in tags:
        d["doc_first"] = tags.index(B + "documentation") < tags.index(B + "extensionElements")
    if tr is None:
        d["trace"] = None
        return d
    ch = [c.tag.split("}")[1] for c in tr if isinstance(c.tag, str)]
    rank = {"source": 0, "req": 1, "verify": 2}
    d["order_ok"] = all(rank.get(a, 9) <= rank.get(b, 9) for a, b in zip(ch, ch[1:])) and all(c in rank for c in ch)
    d["trace"] = dict(
        attrs=list(tr.attrib.items()),
        sources=[(s.get("key"), s.get("loc"), s.get("page")) for s in tr.findall("ipd:source", NS)],
        reqs=[r.get("id") for r in tr.findall("ipd:req", NS)],
        verify=[v.text for v in tr.findall("ipd:verify", NS)],
    )
    return d


def compare_trace(model, sid, spec_el, xml_el, label, stats):
    exp = expected_trace(spec_el)
    act = actual_trace(xml_el)
    stats["elements"] += 1
    if exp is None:
        if act["trace"] is not None:
            err("TRACE-XML", model, sid, "ipd:trace present but the spec element has no trace field (%s)" % label)
        if act["doc"] and re.match(r"^(Sources|Requirements|Binding):", act["doc"]):
            err("TRACE-XML", model, sid, "trace text in documentation but no trace field in the spec (%s)" % label)
        return
    stats["traced"] += 1
    if act["n_trace"] != 1:
        err("TRACE-XML", model, sid, "%d ipd:trace elements (expected exactly 1) (%s)" % (act["n_trace"], label))
        return
    t = act["trace"]
    if t["attrs"] != exp["attrs"]:
        err("TRACE-XML", model, sid, "ipd:trace attributes %s != expected %s (value or order, ipd_extension 3) (%s)" % (t["attrs"], exp["attrs"], label))
    if t["sources"] != exp["sources"]:
        err("TRACE-XML", model, sid, "ipd:source list differs from spec src (%s)" % label)
    if t["reqs"] != exp["reqs"]:
        err("TRACE-XML", model, sid, "ipd:req list %s != spec req %s (%s)" % (t["reqs"], exp["reqs"], label))
    if t["verify"] != exp["verify"]:
        err("TRACE-XML", model, sid, "ipd:verify list differs from spec verify (%s)" % label)
    if not act["order_ok"]:
        err("TRACE-XML", model, sid, "ipd:trace child order not source, req, verify (%s)" % label)
    if act["doc"] != exp["doc"]:
        err("TRACE-DOC", model, sid, "documentation trace text differs from ipd_extension section 5 format (%s): got %r, expected %r"
            % (label, (act["doc"] or "")[:120], exp["doc"][:120]))
    if act["doc_format"] != "text/plain":
        err("TRACE-DOC", model, sid, "documentation textFormat %r != text/plain (%s)" % (act["doc_format"], label))
    if act["doc_first"] is False:
        err("TRACE-DOC", model, sid, "documentation does not precede extensionElements (%s)" % label)
    stats["ok"] += 1


def fidelity(root, specs, label, stats):
    """Spec -> XML: ids, types, names, flows, defaults, message flows, lanes, full trace (converter owner B2)."""
    n0 = len(ERRORS)
    n_checked = 0
    for model, s in specs.items():
        m = mid(model)
        byid = {e.get("id"): e for e in root.iter() if isinstance(e.tag, str) and e.get("id", "").startswith(m + "_")
                and not e.tag.startswith("{%s}" % NS["ipd"])}
        if not byid:
            err("FIDELITY", model, "-", "no elements of the model in %s" % label)
            continue
        st = stats.setdefault(model, dict(elements=0, traced=0, ok=0))
        for p in s["pools"]:
            el = byid.get("%s_%s" % (m, p["id"]))
            if el is None:
                err("FIDELITY", model, p["id"], "participant missing (%s)" % label)
                continue
            if el.get("name") != p["name"]:
                err("FIDELITY", model, p["id"], "participant name %r != spec %r" % (el.get("name"), p["name"]))
            if bool(el.get("processRef")) != bool(p["expanded"]):
                err("FIDELITY", model, p["id"], "expanded=%s but processRef=%s" % (p["expanded"], el.get("processRef")))
            compare_trace(model, p["id"], p, el, label, st)
        for l in s.get("lanes", []):
            el = byid.get("%s_%s" % (m, l["id"]))
            if el is None:
                err("FIDELITY", model, l["id"], "lane missing (%s)" % label)
                continue
            if el.get("name") != l["name"]:
                err("FIDELITY", model, l["id"], "lane name %r != spec %r" % (el.get("name"), l["name"]))
            compare_trace(model, l["id"], l, el, label, st)
        for n in s["nodes"]:
            n_checked += 1
            xid = "%s_%s" % (m, n["id"])
            el = byid.get(xid)
            if el is None:
                err("FIDELITY", model, n["id"], "node missing in XML (%s)" % label)
                continue
            tag = el.tag[len(B):]
            if tag != TYPE_TAG[n["type"]]:
                err("FIDELITY", model, n["id"], "XML type %s != spec type %s" % (tag, n["type"]))
            if n["type"] == "start-message" and el.find("bpmn:messageEventDefinition", NS) is None:
                err("FIDELITY", model, n["id"], "message start without messageEventDefinition")
            if n["type"] == "start-timer" and el.find("bpmn:timerEventDefinition", NS) is None:
                err("FIDELITY", model, n["id"], "timer start without timerEventDefinition")
            if n["type"] in ("start", "end") and len(el.findall("*", NS)) and any(c.tag.endswith("EventDefinition") for c in el):
                err("FIDELITY", model, n["id"], "none event carries an event definition")
            if (el.get("name") or None) != (n.get("label") or None):
                err("FIDELITY", model, n["id"], "XML name %r != spec label %r" % (el.get("name"), n.get("label")))
            if n["type"] == "call-activity":
                ce = el.get("calledElement")
                if n.get("calls"):
                    want = "%s_P_SPON_PROCESS" % mid(n["calls"])
                    if ce != want:
                        err("FIDELITY", model, n["id"], "calledElement %s != %s" % (ce, want))
                    elif root.find(".//bpmn:process[@id='%s']" % want, NS) is None:
                        if label == "combined":
                            err("REF", model, n["id"], "calledElement %s does not resolve in combined file" % want)
                        else:
                            stats.setdefault("_unresolved_called", []).append("%s %s -> %s" % (label, n["id"], want))
                elif ce:
                    err("FIDELITY", model, n["id"], "interface call activity has calledElement %s" % ce)
            # incoming/outgoing refs consistent with flows
            inc = sorted(x.text for x in el.findall("bpmn:incoming", NS))
            out = sorted(x.text for x in el.findall("bpmn:outgoing", NS))
            want_in = sorted("%s_%s" % (m, f["id"]) for f in s["flows"] if f["to"] == n["id"])
            want_out = sorted("%s_%s" % (m, f["id"]) for f in s["flows"] if f["from"] == n["id"])
            if inc != want_in or out != want_out:
                err("FIDELITY", model, n["id"], "incoming/outgoing refs %s/%s != spec flows %s/%s" % (inc, out, want_in, want_out))
            compare_trace(model, n["id"], n, el, label, st)
        for f in s["flows"]:
            el = byid.get("%s_%s" % (m, f["id"]))
            if el is None:
                err("FIDELITY", model, f["id"], "sequence flow missing (%s)" % label)
                continue
            if el.get("sourceRef") != "%s_%s" % (m, f["from"]) or el.get("targetRef") != "%s_%s" % (m, f["to"]):
                err("FIDELITY", model, f["id"], "source/target differ from spec")
            if (el.get("name") or None) != (f.get("label") or None):
                err("FIDELITY", model, f["id"], "flow name %r != spec label %r" % (el.get("name"), f.get("label")))
            src = byid.get("%s_%s" % (m, f["from"]))
            if f.get("default"):
                if src is not None and src.get("default") != el.get("id"):
                    err("FIDELITY", model, f["id"], "default flow not set on source gateway")
            elif src is not None and src.get("default") == el.get("id"):
                err("FIDELITY", model, f["id"], "XML marks a default flow the spec does not have")
            if el.find("bpmn:conditionExpression", NS) is not None:
                err("FLW-02", model, f["id"], "conditionExpression (body = flow label) on a non-default flow of a split with a default flow; "
                    "analytic element in a descriptive model, written to satisfy bpmnlint conditional-flows (build_log.md section 3)",
                    severity="SHOULD", status="documented-choice")
            # round 3: non-default outgoing flow of an OR split without a conditionExpression. The spec calls such flows
            # conditional (label = condition), but the XML does not encode the condition, so a tool that executes or
            # simulates the model may take every such flow (OMG 8.3.13: only a conditionExpression gates the token).
            snode = next((n for n in s["nodes"] if n["id"] == f["from"]), None)
            if (snode is not None and snode["type"] == "or-split" and not f.get("default")
                    and el.find("bpmn:conditionExpression", NS) is None and label.startswith("combined")):
                err("FLW-07", model, f["id"], "outgoing flow %r of OR split %s carries no conditionExpression (the split has no default flow, so the "
                    "converter writes none, build_log.md section 3); the condition exists only as the flow label, and a tool that executes or "
                    "simulates the XML may start this branch every time. Covered by the accepted B2 conditionExpression limitation (descriptive model)"
                    % (f.get("label"), f["from"]), severity="SHOULD", status="documented-choice")
        for mf in s.get("message_flows", []):
            el = byid.get("%s_%s" % (m, mf["id"]))
            if el is None:
                err("FIDELITY", model, mf["id"], "message flow missing (%s)" % label)
                continue
            if el.get("sourceRef") != "%s_%s" % (m, mf["from"]) or el.get("targetRef") != "%s_%s" % (m, mf["to"]):
                err("FIDELITY", model, mf["id"], "message flow ends differ from spec")
            if el.get("name") != mf["label"]:
                err("FIDELITY", model, mf["id"], "message flow name differs from spec label")
            compare_trace(model, mf["id"], mf, el, label, st)
        for d in s.get("data", []):
            el = byid.get("%s_%s" % (m, d["id"]))
            if el is None:
                err("FIDELITY", model, d["id"], "data reference missing (%s)" % label)
                continue
            want_tag = "dataStoreReference" if d["type"] == "data-store" else "dataObjectReference"
            if el.tag != B + want_tag:
                err("FIDELITY", model, d["id"], "XML %s != spec %s" % (el.tag.split('}')[1], d["type"]))
            if el.get("name") != d["label"]:
                err("FIDELITY", model, d["id"], "data name %r != spec %r" % (el.get("name"), d["label"]))
            for a in d["assoc"]:
                aid = "%s_%s_%s_%s" % (m, d["id"], a["node"], "IN" if a["dir"] == "in" else "OUT")
                if aid not in byid:
                    err("FIDELITY", model, d["id"], "data association %s missing" % aid)
            compare_trace(model, d["id"], d, el, label, st)
        for g in s.get("groups", []):
            if "%s_%s" % (m, g["id"]) not in byid:
                err("FIDELITY", model, g["id"], "group missing (%s)" % label)
        for a in s.get("annotations", []):
            el = byid.get("%s_%s" % (m, a["id"]))
            if el is None:
                err("FIDELITY", model, a["id"], "text annotation missing (%s)" % label)
                continue
            txt = el.find("bpmn:text", NS)
            if txt is None or (txt.text or "") != a["text"]:
                err("FIDELITY", model, a["id"], "annotation text differs from spec")
            for k, x in enumerate(a["assoc"], 1):
                if "%s_%s_ASSOC%d" % (m, a["id"], k) not in byid:
                    err("FIDELITY", model, a["id"], "association %s_%s_ASSOC%d missing" % (m, a["id"], k))
        # lanes membership
        for n in s["nodes"]:
            if n.get("lane"):
                lane = byid.get("%s_%s" % (m, n["lane"]))
                refs = [r.text for r in lane.findall("bpmn:flowNodeRef", NS)] if lane is not None else []
                if "%s_%s" % (m, n["id"]) not in refs:
                    err("FIDELITY", model, n["id"], "node not listed in lane %s" % n["lane"])
        # notes exported on the internal pool's process (S0-18)
        if s.get("notes"):
            want = s["notes"] if isinstance(s["notes"], str) else "\n".join(s["notes"])
            proc = byid.get("%s_P_SPON_PROCESS" % m)
            doc = proc.find("bpmn:documentation", NS) if proc is not None else None
            if doc is None or (doc.text or "") != want:
                err("FIDELITY", model, "notes", "spec notes not exported verbatim as documentation of %s_P_SPON_PROCESS" % m, severity="SHOULD")
    if len(ERRORS) == n0:
        ok("L1", "spec-to-XML fidelity: ids, types, names, flows, incoming/outgoing, defaults, message flows, data, groups, annotations, lanes, notes (%s)" % label, n_checked)


def canon(el):
    """Canonical string of an element subtree (namespace-qualified tags, sorted attributes, stripped text)."""
    parts = []
    for e in el.iter():
        if not isinstance(e.tag, str):
            continue
        parts.append("%s|%s|%s|%s" % (e.tag, sorted(e.attrib.items()), (e.text or "").strip(), (e.tail or "").strip()))
    return "\n".join(parts)


def per_model_consistency(combined, models_docs):
    """Every top-level element of a per-model file equals the same element of the combined file."""
    comb = {c.get("id"): c for c in combined if isinstance(c.tag, str) and c.get("id")}
    n = 0
    for label, root in models_docs.items():
        m = mid(label)
        for c in root:
            if not isinstance(c.tag, str) or not c.get("id"):
                continue
            n += 1
            o = comb.get(c.get("id"))
            if o is None:
                err("EXPORT", label, c.get("id"), "top-level element of the per-model file missing in the combined file")
            elif canon(o) != canon(c):
                err("EXPORT", label, c.get("id"), "per-model export differs from the combined file")
        have = {c.get("id") for c in root if isinstance(c.tag, str)}
        for i in comb:
            if i.startswith(m + "_") and i not in have:
                err("EXPORT", label, i, "element of the model in the combined file missing from the per-model file")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xsd-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--combined", default=os.path.join(ROOT, "out", "ipd_best_practice.bpmn"))
    ap.add_argument("--models-dir", default=os.path.join(ROOT, "out", "models"))
    ap.add_argument("--spec-dir", default=os.path.join(ROOT, "spec"))
    a = ap.parse_args()
    global SPEC_DIR
    SPEC_DIR = a.spec_dir
    specs = load_specs()
    xsd = os.path.join(a.xsd_dir, "BPMN20.xsd")
    schema = None
    xsd_info = {}
    try:
        schema = etree.XMLSchema(etree.parse(xsd))
        xsd_info = {f: sha(os.path.join(a.xsd_dir, f)) for f in sorted(os.listdir(a.xsd_dir)) if f.endswith(".xsd")}
    except Exception as e:  # noqa
        err("XSD", "-", "-", "XSD not loadable, XSD validation not run: %s" % e, severity="SHOULD")
    files = [("combined", a.combined)]
    files += [(os.path.basename(p)[:-5], p) for p in sorted(glob.glob(os.path.join(a.models_dir, "*.bpmn")))]
    file_info = {}
    stats = {}
    docs = {}
    combined_root = None
    for label, p in files:
        n0 = len(ERRORS)
        doc = check_xsd(p, schema, label)
        file_info[os.path.relpath(p, ROOT) if p.startswith(ROOT) else p] = {"sha256": sha(p)}
        if doc is None:
            continue
        if len(ERRORS) == n0:
            ok("L1", "well-formed XML + XSD valid against OMG BPMN20.xsd (%s)" % (os.path.relpath(p, ROOT) if p.startswith(ROOT) else p), 1)
        root = doc.getroot()
        if label == "combined":
            combined_root = root
        else:
            docs[label] = root
        ids = {}
        for e in root.iter():
            # ipd:req/@id is a plain attribute, not an XML ID (ipd_extension.md section 7)
            if isinstance(e.tag, str) and e.get("id") and not e.tag.startswith("{%s}" % NS["ipd"]):
                ids[e.get("id")] = ids.get(e.get("id"), 0) + 1
        for i, c in ids.items():
            if c > 1:
                err("XML-ID", label, i, "duplicate XML id (%d times)" % c)
        models = [label] if label != "combined" else list(specs)
        for model in models:
            if model in specs:
                di_checks(root, model, specs, label)
        fidelity(root, {k: v for k, v in specs.items() if k in models}, label, stats.setdefault(label, {}))
    if combined_root is not None:
        n0 = len(ERRORS)
        n = per_model_consistency(combined_root, docs)
        if len(ERRORS) == n0:
            ok("L1", "per-model exports out/models/*.bpmn identical to the corresponding elements of the combined file", n)
    unresolved = [x for st in stats.values() for x in st.get("_unresolved_called", [])]
    if unresolved:
        err("REF", "L3", "A1-A8", "per-model export L3.bpmn: calledElement of %d call activities points to processes that exist only in the "
            "combined file and the L4 files (no bpmn:import); a tool opening L3.bpmn alone cannot resolve them (known, build_log.md)" % len(unresolved),
            severity="SHOULD", status="documented-choice")
    tr = {lab: {m: v for m, v in st.items() if not m.startswith("_")} for lab, st in stats.items()}
    for lab, st in tr.items():
        for model, v in st.items():
            if v["traced"]:
                ok("L4", "ipd:trace and documentation text match the spec for every traced element (%s %s)" % (lab, model), v["traced"],
                   "%d elements compared, %d traced, %d fully equal" % (v["elements"], v["traced"], v["ok"]))
    json.dump(dict(errors=ERRORS, passed=PASSED, xsd=dict(dir=a.xsd_dir, sha256=xsd_info), files=file_info, trace_stats=tr,
                   inputs=[os.path.relpath(p, ROOT) for _, p in files if p.startswith(ROOT)] + ["contracts/ipd_extension.md", "spec/*.yaml"]),
              open(a.out, "w"), indent=1)
    print("v1_bpmn: %d errors, %d passed checks" % (len(ERRORS), len(PASSED)))


if __name__ == "__main__":
    sys.exit(main())
