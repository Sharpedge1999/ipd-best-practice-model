#!/usr/bin/env python3
"""spec2bpmn - deterministic converter: iPD model specs (YAML, GEN-01) -> BPMN 2.0 XML + DI.

Usage:
    python -I tools/spec2bpmn.py --specs <dir> --out <file.bpmn> --models-out <dir>

Reads every *.yaml / *.yml file in --specs (not recursive) that is a model spec
(a mapping with level L3 or L4); anything else (e.g. findings samples) is
skipped and listed in the report. Runs tools/lint_spec.py on the specs first
and aborts on lint errors. Writes:

    <out>                      one bpmn:definitions with all models
    <out stem>.report.json     build report (inputs, counts, warnings, overlay zones)
    <models-out>/<model>.bpmn  one self-contained file per model

Contracts: contracts/decisions.md (B3 XML ids), contracts/ipd_extension.md
(ipd:trace + documentation), workflow_plan.md section 4. Layout: tools/layout.py.
Output is byte-identical for identical input (no timestamps, fixed ordering).

Exit codes: 0 ok, 1 lint or conversion error, 2 usage / I/O error.
"""

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml
from lxml import etree

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent

_spec = importlib.util.spec_from_file_location("ipd_layout", TOOLS / "layout.py")
layout = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(layout)

VERSION = "1.0"
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "ipd": "urn:ipd-best-practice:trace:1.0",
}
TARGET_NS = "urn:ipd-best-practice:model"

TYPE_TAG = {
    "task": "task",
    "call-activity": "callActivity",
    "start": "startEvent",
    "start-message": "startEvent",
    "start-timer": "startEvent",
    "end": "endEvent",
    "intermediate-catch-message": "intermediateCatchEvent",
    "intermediate-throw-message": "intermediateThrowEvent",
    "intermediate-catch-timer": "intermediateCatchEvent",
    "xor-split": "exclusiveGateway",
    "xor-join": "exclusiveGateway",
    "and-split": "parallelGateway",
    "and-join": "parallelGateway",
    "or-split": "inclusiveGateway",
    "or-join": "inclusiveGateway",
}
EVENT_DEF = {
    "start-message": "messageEventDefinition",
    "start-timer": "timerEventDefinition",
    "intermediate-catch-message": "messageEventDefinition",
    "intermediate-throw-message": "messageEventDefinition",
    "intermediate-catch-timer": "timerEventDefinition",
}
ACTIVITY = {"task", "call-activity"}
GATEWAY = set(layout.GATEWAY_TYPES)


class ConversionError(Exception):
    pass


def q(prefix, tag):
    return "{%s}%s" % (NS[prefix], tag)


def B(tag):
    return q("bpmn", tag)


def mp(model):
    return model.replace("-", "_")


def xid(model, sid):
    return f"{mp(model)}_{sid}"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------- trace
def _deadline(el):
    d = el.get("deadline")
    if not isinstance(d, str) or not d.strip() or d.strip().lower() == "none":
        return None
    return d


def _party(el):
    p = el.get("party")
    if isinstance(p, list):
        p = "; ".join(x for x in p if isinstance(x, str) and x.strip())
    return p if isinstance(p, str) and p.strip() else None


def _record(el):
    r = el.get("record")
    return r if isinstance(r, str) and r.strip() else None


def has_trace(el):
    """ipd_extension 1.1 section 4 (S0-17): any trace field present - src, req, binding,
    jurisdiction, deadline, draft, verify, record, party. draft: false and
    deadline: none count as absent."""
    return bool(el.get("src") or el.get("req") or el.get("binding") or el.get("jurisdiction")
                or _deadline(el) or el.get("draft") is True or el.get("verify")
                or _record(el) or _party(el))


def trace_text(el):
    lines = []
    if el.get("src"):
        parts = []
        for s in el["src"]:
            t = f"{s['key']} {s['loc']}"
            if s.get("page"):
                t += f" (p. {s['page']})"
            parts.append(t)
        lines.append("Sources: " + "; ".join(parts))
    if el.get("req"):
        lines.append("Requirements: " + ", ".join(el["req"]))
    if el.get("binding"):
        lines.append("Binding: " + el["binding"])
    if el.get("jurisdiction"):
        lines.append("Jurisdiction: " + ", ".join(el["jurisdiction"]))
    if _deadline(el):
        lines.append("Deadline: " + _deadline(el))
    if _record(el):
        lines.append("Record: " + _record(el))
    if _party(el):
        lines.append("Party: " + _party(el))
    if el.get("draft") is True:
        lines.append("Draft: DRAFT guidance")
    if el.get("verify"):
        lines.append("Verify: " + "; ".join(el["verify"]))
    return "\n".join(lines)


def add_trace(parent, el, extra_docs=()):
    """documentation (trace text first) + extensionElements/ipd:trace."""
    text = trace_text(el) if has_trace(el) else ""
    if text:
        d = etree.SubElement(parent, B("documentation"))
        d.set("textFormat", "text/plain")
        d.text = text
    for extra in extra_docs:
        d = etree.SubElement(parent, B("documentation"))
        d.set("textFormat", "text/plain")
        d.text = extra
    if not has_trace(el):
        return
    ext = etree.SubElement(parent, B("extensionElements"))
    tr = etree.SubElement(ext, q("ipd", "trace"))
    if el.get("binding"):
        tr.set("binding", el["binding"])
    if el.get("jurisdiction"):
        tr.set("jurisdiction", " ".join(el["jurisdiction"]))
    if _deadline(el):
        tr.set("deadline", _deadline(el))
    if el.get("draft") is True:
        tr.set("draft", "true")
    if _record(el):
        tr.set("record", _record(el))
    if _party(el):
        tr.set("party", _party(el))
    for s in el.get("src") or []:
        se = etree.SubElement(tr, q("ipd", "source"))
        se.set("key", s["key"])
        se.set("loc", s["loc"])
        if s.get("page"):
            se.set("page", s["page"])
    for r in el.get("req") or []:
        etree.SubElement(tr, q("ipd", "req")).set("id", r)
    for v in el.get("verify") or []:
        etree.SubElement(tr, q("ipd", "verify")).text = v


# --------------------------------------------------------------------- input
def discover(spec_dir):
    specs, skipped = [], []
    files = sorted([p for p in Path(spec_dir).iterdir() if p.is_file() and p.suffix in (".yaml", ".yml")],
                   key=lambda p: p.name)
    for p in files:
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConversionError(f"{p}: YAML does not parse: {exc}")
        if isinstance(data, dict) and data.get("level") in ("L3", "L4") and isinstance(data.get("id"), str):
            specs.append((p, data))
        else:
            skipped.append(p.name)
    return specs, skipped


def run_lint(specs):
    files = [str(p) for p, _ in specs]
    l3 = [str(p) for p, s in specs if s.get("level") == "L3"]
    cmd = [sys.executable, "-I", str(TOOLS / "lint_spec.py")] + files
    if len(l3) == 1:
        cmd += ["--parent", l3[0]]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


# --------------------------------------------------------------------- model build
class ModelBuilder:
    def __init__(self, spec, lay, models, warnings):
        self.spec = spec
        self.m = spec["id"]
        self.lay = lay
        self.models = models
        self.warnings = warnings
        self.pools = {p["id"]: p for p in spec["pools"]}
        self.node_by = {n["id"]: n for n in spec["nodes"]}
        self.flows = spec.get("flows") or []
        self.node_pool = layout.node_pools(spec)
        self.incoming, self.outgoing = {}, {}
        for f in self.flows:
            self.outgoing.setdefault(f["from"], []).append(f)
            self.incoming.setdefault(f["to"], []).append(f)
        self.defaults = {f["from"]: f for f in self.flows if f.get("default") is True}
        self.group_of = {}
        for g in spec.get("groups") or []:
            for mbr in g["members"]:
                self.group_of.setdefault(mbr, []).append(g["id"])
        self.data_in, self.data_out = {}, {}
        for d in spec.get("data") or []:
            for a in d["assoc"]:
                (self.data_out if a["dir"] == "out" else self.data_in).setdefault(a["node"], []).append(d)
        self.counts = {}

    def X(self, sid):
        return xid(self.m, sid)

    def count(self, kind):
        self.counts[kind] = self.counts.get(kind, 0) + 1

    # ----------------------------------------------------------- semantic
    def root_elements(self):
        out = []
        for g in self.spec.get("groups") or []:
            cat = etree.Element(B("category"))
            cat.set("id", self.X(g["id"]) + "_CATEGORY")
            cv = etree.SubElement(cat, B("categoryValue"))
            cv.set("id", self.X(g["id"]) + "_VALUE")
            cv.set("value", g["label"])
            out.append(cat)
        for d in self.spec.get("data") or []:
            if d["type"] == "data-store":
                ds = etree.Element(B("dataStore"))
                ds.set("id", self.X(d["id"]) + "_STORE")
                ds.set("name", d["label"])
                out.append(ds)
        out.append(self.collaboration())
        for p in self.spec["pools"]:
            if p["expanded"]:
                out.append(self.process(p))
        return out

    def collaboration(self):
        spec = self.spec
        c = etree.Element(B("collaboration"))
        c.set("id", self.X("COLLAB"))
        c.set("name", spec["title"])
        info = [f"Model: {self.m}", f"Title: {spec['title']}"]
        if spec.get("parent"):
            info.append(f"Parent: {spec['parent']['model']} {spec['parent']['node']}")
        iface = spec.get("interface")
        if iface:
            info.append("Interface: start " + ", ".join(iface["start"]) + "; ends " + ", ".join(iface["ends"])
                        + ("; message flows " + ", ".join(iface["message_flows"]) if iface.get("message_flows") else ""))
        for r in spec.get("rule_exceptions") or []:
            info.append(f"Rule exception: {r['rule']} {r['element']} - {r['reason']}")
        for o in spec.get("open_items") or []:
            info.append(f"Open item: {o}")
        d = etree.SubElement(c, B("documentation"))
        d.set("textFormat", "text/plain")
        d.text = "\n".join(info)
        for p in spec["pools"]:
            part = etree.SubElement(c, B("participant"))
            part.set("id", self.X(p["id"]))
            part.set("name", p["name"])
            if p["expanded"]:
                part.set("processRef", self.X(p["id"]) + "_PROCESS")
            add_trace(part, p)
            self.count("participant")
        for mf in spec.get("message_flows") or []:
            e = etree.SubElement(c, B("messageFlow"))
            e.set("id", self.X(mf["id"]))
            e.set("name", mf["label"])
            e.set("sourceRef", self.X(mf["from"]))
            e.set("targetRef", self.X(mf["to"]))
            add_trace(e, mf)
            self.count("messageFlow")
        for g in spec.get("groups") or []:
            e = etree.SubElement(c, B("group"))
            e.set("id", self.X(g["id"]))
            e.set("categoryValueRef", self.X(g["id"]) + "_VALUE")
            self.count("group")
        return c

    def process(self, pool):
        spec = self.spec
        pid = pool["id"]
        pr = etree.Element(B("process"))
        pr.set("id", self.X(pid) + "_PROCESS")
        pr.set("name", pool["name"])
        pr.set("isExecutable", "false")
        notes = spec.get("notes")
        if pool["kind"] == "internal" and notes:
            d = etree.SubElement(pr, B("documentation"))
            d.set("textFormat", "text/plain")
            d.text = notes if isinstance(notes, str) else "\n".join(notes)
        lanes = [l for l in spec.get("lanes") or [] if l["pool"] == pid]
        nodes = [n for n in spec["nodes"] if self.node_pool[n["id"]] == pid]
        if lanes:
            ls = etree.SubElement(pr, B("laneSet"))
            ls.set("id", self.X(pid) + "_LANESET")
            for l in lanes:
                le = etree.SubElement(ls, B("lane"))
                le.set("id", self.X(l["id"]))
                le.set("name", l["name"])
                add_trace(le, l)
                for n in nodes:
                    if n.get("lane") == l["id"]:
                        etree.SubElement(le, B("flowNodeRef")).text = self.X(n["id"])
                self.count("lane")
        for n in nodes:
            pr.append(self.flow_node(n))
        for d in spec.get("data") or []:
            if self.node_pool[d["assoc"][0]["node"]] != pid:
                continue
            if d["type"] == "data-object":
                obj = etree.SubElement(pr, B("dataObject"))
                obj.set("id", self.X(d["id"]) + "_OBJECT")
                ref = etree.SubElement(pr, B("dataObjectReference"))
                ref.set("id", self.X(d["id"]))
                ref.set("name", d["label"])
                ref.set("dataObjectRef", self.X(d["id"]) + "_OBJECT")
                self.count("dataObjectReference")
            else:
                ref = etree.SubElement(pr, B("dataStoreReference"))
                ref.set("id", self.X(d["id"]))
                ref.set("name", d["label"])
                ref.set("dataStoreRef", self.X(d["id"]) + "_STORE")
                self.count("dataStoreReference")
            add_trace(ref, d)
        for f in self.flows:
            if self.node_pool[f["from"]] != pid:
                continue
            pr.append(self.sequence_flow(f))
        # data associations on events are written as bpmn:association artifacts
        for d in spec.get("data") or []:
            for a in d["assoc"]:
                n = self.node_by[a["node"]]
                if n["type"] in ACTIVITY or self.node_pool[n["id"]] != pid:
                    continue
                asc = etree.SubElement(pr, B("association"))
                asc.set("id", f"{self.X(d['id'])}_{n['id']}_{a['dir'].upper()}")
                if a["dir"] == "out":
                    asc.set("sourceRef", self.X(n["id"]))
                    asc.set("targetRef", self.X(d["id"]))
                else:
                    asc.set("sourceRef", self.X(d["id"]))
                    asc.set("targetRef", self.X(n["id"]))
                asc.set("associationDirection", "One")
                self.count("association")
                self.warnings.append(f"{self.m} {d['id']}-{n['id']}: data on a non-activity written as bpmn:association")
        for ta in spec.get("annotations") or []:
            if self.elem_pool(ta["assoc"][0]) != pid:
                continue
            e = etree.SubElement(pr, B("textAnnotation"))
            e.set("id", self.X(ta["id"]))
            add_trace(e, ta)
            etree.SubElement(e, B("text")).text = ta["text"]
            self.count("textAnnotation")
            for k, ref in enumerate(ta["assoc"], start=1):
                a = etree.SubElement(pr, B("association"))
                a.set("id", f"{self.X(ta['id'])}_ASSOC{k}")
                a.set("sourceRef", self.X(ref))
                a.set("targetRef", self.X(ta["id"]))
                a.set("associationDirection", "None")
                self.count("association")
        return pr

    def elem_pool(self, ref):
        if ref in self.node_pool:
            return self.node_pool[ref]
        for f in self.flows:
            if f["id"] == ref:
                return self.node_pool[f["from"]]
        return None

    def flow_node(self, n):
        t = n["type"]
        e = etree.Element(B(TYPE_TAG[t]))
        e.set("id", self.X(n["id"]))
        if n.get("label"):
            e.set("name", n["label"])
        if t in GATEWAY:
            e.set("gatewayDirection", "Diverging" if t.endswith("-split") else "Converging")
        if t == "call-activity" and n.get("calls") is None:
            pass        # S0-18: interface call activity (neighbouring process), no calledElement
        elif t == "call-activity":
            callee = n["calls"]
            target = self.models.get(callee)
            if target is not None:
                internal = [p["id"] for p in target["pools"] if p["kind"] == "internal"][0]
                e.set("calledElement", xid(callee, internal) + "_PROCESS")
            else:
                e.set("calledElement", xid(callee, "P_SPON") + "_PROCESS")
                self.warnings.append(f"{self.m} {n['id']}: called model {callee} not in the spec set; "
                                     f"calledElement set to {xid(callee, 'P_SPON')}_PROCESS by convention")
        dflt = self.defaults.get(n["id"])
        if dflt is not None:
            if t in ACTIVITY or t.startswith("xor") or t.startswith("or"):
                e.set("default", self.X(dflt["id"]))
            else:
                raise ConversionError(f"{self.m} {dflt['id']}: default flow from {n['id']} ({t}) is not "
                                      f"allowed in BPMN (only activities, XOR and OR gateways)")
        extra = []
        if n.get("justification"):
            extra.append("Justification: " + n["justification"])
        add_trace(e, n, extra)
        for gid in self.group_of.get(n["id"], []):
            etree.SubElement(e, B("categoryValueRef")).text = self.X(gid) + "_VALUE"
        for f in self.incoming.get(n["id"], []):
            etree.SubElement(e, B("incoming")).text = self.X(f["id"])
        for f in self.outgoing.get(n["id"], []):
            etree.SubElement(e, B("outgoing")).text = self.X(f["id"])
        if t in ACTIVITY:
            ins = self.data_in.get(n["id"], [])
            if ins:
                prop = etree.SubElement(e, B("property"))
                prop.set("id", self.X(n["id"]) + "_PROPERTY")
                prop.set("name", "__targetRef_placeholder")
            for d in ins:
                a = etree.SubElement(e, B("dataInputAssociation"))
                a.set("id", f"{self.X(d['id'])}_{n['id']}_IN")
                etree.SubElement(a, B("sourceRef")).text = self.X(d["id"])
                etree.SubElement(a, B("targetRef")).text = self.X(n["id"]) + "_PROPERTY"
                self.count("dataInputAssociation")
            for d in self.data_out.get(n["id"], []):
                a = etree.SubElement(e, B("dataOutputAssociation"))
                a.set("id", f"{self.X(d['id'])}_{n['id']}_OUT")
                etree.SubElement(a, B("targetRef")).text = self.X(d["id"])
                self.count("dataOutputAssociation")
        if t in EVENT_DEF:
            etree.SubElement(e, B(EVENT_DEF[t]))
        self.count(TYPE_TAG[t])
        return e

    def sequence_flow(self, f):
        e = etree.Element(B("sequenceFlow"))
        e.set("id", self.X(f["id"]))
        if f.get("label"):
            e.set("name", f["label"])
        e.set("sourceRef", self.X(f["from"]))
        e.set("targetRef", self.X(f["to"]))
        dflt = self.defaults.get(f["from"])
        if dflt is not None and dflt["id"] != f["id"]:
            # BPMN: with a default flow, the other outgoing flows are conditional
            # (bpmnlint conditional-flows). The condition is the flow label.
            ce = etree.SubElement(e, B("conditionExpression"))
            ce.set(q("xsi", "type"), "bpmn:tFormalExpression")
            ce.text = f.get("label") or ""
        self.count("sequenceFlow")
        return e

    # ----------------------------------------------------------- DI
    def diagram(self):
        lay = self.lay
        spec = self.spec
        dg = etree.Element(q("bpmndi", "BPMNDiagram"))
        dg.set("id", self.X("DIAGRAM"))
        dg.set("name", f"{self.m} - {spec['title']}")
        pl = etree.SubElement(dg, q("bpmndi", "BPMNPlane"))
        pl.set("id", self.X("PLANE"))
        pl.set("bpmnElement", self.X("COLLAB"))

        def shape(sid, rect, label=None, **attrs):
            s = etree.SubElement(pl, q("bpmndi", "BPMNShape"))
            s.set("id", self.X(sid) + "_di")
            s.set("bpmnElement", self.X(sid))
            for k, v in attrs.items():
                s.set(k, v)
            bounds(s, rect)
            if label is not None:
                lb = etree.SubElement(s, q("bpmndi", "BPMNLabel"))
                bounds(lb, label)

        def edge(eid, pts, label=None):
            e = etree.SubElement(pl, q("bpmndi", "BPMNEdge"))
            e.set("id", eid + "_di")
            e.set("bpmnElement", eid)
            for x, y in pts:
                w = etree.SubElement(e, q("di", "waypoint"))
                w.set("x", str(x))
                w.set("y", str(y))
            if label is not None:
                lb = etree.SubElement(e, q("bpmndi", "BPMNLabel"))
                bounds(lb, label)

        for pid in lay.pool_order:
            shape(pid, lay.shapes[pid], isHorizontal="true")
        for l in spec.get("lanes") or []:
            shape(l["id"], lay.shapes[l["id"]], isHorizontal="true")
        for n in spec["nodes"]:
            attrs = {}
            if n["type"].startswith("xor"):
                attrs["isMarkerVisible"] = "true"
            shape(n["id"], lay.shapes[n["id"]], lay.labels.get(n["id"]), **attrs)
        for d in spec.get("data") or []:
            shape(d["id"], lay.shapes[d["id"]], lay.labels.get(d["id"]))
        for g in spec.get("groups") or []:
            shape(g["id"], lay.shapes[g["id"]], lay.labels.get(g["id"]))
        for ta in spec.get("annotations") or []:
            shape(ta["id"], lay.shapes[ta["id"]])
        for f in self.flows:
            edge(self.X(f["id"]), lay.edges[f["id"]], lay.labels.get(f["id"]))
        for mf in spec.get("message_flows") or []:
            edge(self.X(mf["id"]), lay.edges[mf["id"]], lay.labels.get(mf["id"]))
        for d in spec.get("data") or []:
            for a in d["assoc"]:
                key = ("assoc", d["id"], a["node"], a["dir"])
                edge(f"{self.X(d['id'])}_{a['node']}_{a['dir'].upper()}", lay.edges[key])
        for ta in spec.get("annotations") or []:
            for k, ref in enumerate(ta["assoc"], start=1):
                edge(f"{self.X(ta['id'])}_ASSOC{k}", lay.edges[("annot", ta["id"], ref)])
        return dg


def bounds(parent, r):
    b = etree.SubElement(parent, q("dc", "Bounds"))
    b.set("x", str(r[0]))
    b.set("y", str(r[1]))
    b.set("width", str(r[2]))
    b.set("height", str(r[3]))


def definitions(parts):
    root = etree.Element(B("definitions"), nsmap=NS)
    root.set("id", "IPD_DEFINITIONS")
    root.set("targetNamespace", TARGET_NS)
    root.set("exporter", "ipd spec2bpmn")
    root.set("exporterVersion", VERSION)
    sem, dis = [], []
    for s, d in parts:
        sem.extend(s)
        dis.append(d)
    for e in sem + dis:
        root.append(e)
    return root


def serialize(root):
    body = etree.tostring(root, encoding="UTF-8", xml_declaration=False, pretty_print=True)
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + body


# --------------------------------------------------------------------- main
def model_sort_key(spec):
    return (0 if spec["id"] == "L3" else 1, spec["id"])


def convert(spec_dir, out_file, models_out):
    specs, skipped = discover(spec_dir)
    if not specs:
        raise ConversionError(f"no L3/L4 spec found in {spec_dir}")
    ids = [s["id"] for _, s in specs]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ConversionError(f"duplicate model ids: {', '.join(dup)}")
    rc, lint_out = run_lint(specs)
    if rc != 0:
        sys.stdout.write(lint_out)
        raise ConversionError("lint_spec reported errors; conversion aborted")
    specs.sort(key=lambda ps: model_sort_key(ps[1]))
    models = {s["id"]: s for _, s in specs}
    slots = layout.pool_slots([s for _, s in specs])
    warnings = []
    parts = {}
    report_models = []
    for path, spec in specs:
        lay = layout.layout_model(spec, slots)
        for w in lay.warnings:
            warnings.append(f"{spec['id']} layout: {w}")
        mb = ModelBuilder(spec, lay, models, warnings)
        sem = mb.root_elements()
        dg = mb.diagram()
        parts[spec["id"]] = (sem, dg)
        zones = {}
        for k, z in sorted(lay.zones.items()):
            zones[xid(spec["id"], k)] = list(z)
        report_models.append({
            "model": spec["id"],
            "spec_file": path.name,
            "spec_sha256": sha256_bytes(path.read_bytes()),
            "collaboration": xid(spec["id"], "COLLAB"),
            "diagram": xid(spec["id"], "DIAGRAM"),
            "plane": xid(spec["id"], "PLANE"),
            "pool_order": [xid(spec["id"], p) for p in lay.pool_order],
            "collapsed_pools": [xid(spec["id"], p["id"]) for p in spec["pools"] if not p["expanded"]],
            "processes": [xid(spec["id"], p["id"]) + "_PROCESS" for p in spec["pools"] if p["expanded"]],
            "counts": dict(sorted(mb.counts.items())),
            "overlay_zones": zones,
        })

    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    models_out = Path(models_out)
    models_out.mkdir(parents=True, exist_ok=True)

    def fresh(mid):
        # rebuild element trees per output file (lxml elements have one parent)
        sem, dg = parts[mid]
        return [etree.fromstring(etree.tostring(e)) for e in sem], etree.fromstring(etree.tostring(dg))

    written = {}
    combined = serialize(definitions([fresh(s["id"]) for _, s in specs]))
    out_file.write_bytes(combined)
    written[str(out_file)] = sha256_bytes(combined)
    for _, s in specs:
        data = serialize(definitions([fresh(s["id"])]))
        p = models_out / f"{s['id']}.bpmn"
        p.write_bytes(data)
        written[str(p)] = sha256_bytes(data)
    notes = []
    if "L3" in models:
        notes.append("Per-model files are self-contained (own collaboration, processes, diagram). "
                     "L3.bpmn keeps calledElement on its call activities, but the called L4 processes "
                     "are only in the combined file and in the L4 files.")
    report = {
        "tool": "spec2bpmn",
        "version": VERSION,
        "specs_dir": str(spec_dir),
        "skipped_files": skipped,
        "lint": "pass",
        "pool_slots": {k: list(v) for k, v in sorted(slots.items())},
        "models": report_models,
        "outputs": dict(sorted(written.items())),
        "warnings": warnings,
        "notes": notes,
    }
    rep_path = out_file.with_suffix(".report.json")
    rep_bytes = (json.dumps(report, indent=2, sort_keys=False, ensure_ascii=False) + "\n").encode("utf-8")
    rep_path.write_bytes(rep_bytes)
    return report, rep_path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Convert iPD model specs (YAML) to BPMN 2.0 XML with DI.")
    ap.add_argument("--specs", required=True, help="directory with L3/L4 spec YAML files")
    ap.add_argument("--out", required=True, help="combined .bpmn output file")
    ap.add_argument("--models-out", required=True, help="directory for one .bpmn per model")
    args = ap.parse_args(argv)
    if not Path(args.specs).is_dir():
        print(f"ERROR: specs directory not found: {args.specs}")
        return 2
    try:
        report, rep_path = convert(Path(args.specs), args.out, args.models_out)
    except ConversionError as exc:
        print(f"ERROR: {exc}")
        return 1
    except OSError as exc:
        print(f"ERROR: I/O: {exc}")
        return 2
    print(f"spec2bpmn {VERSION}: {len(report['models'])} model(s) from {args.specs}")
    for name in report["skipped_files"]:
        print(f"  skipped (not a spec): {name}")
    for path, digest in report["outputs"].items():
        print(f"  wrote {path}  sha256 {digest}")
    print(f"  report {rep_path}")
    for w in report["warnings"]:
        print(f"  WARN {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
