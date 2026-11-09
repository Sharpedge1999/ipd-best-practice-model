#!/usr/bin/env python3
"""W1 viewer builder: one self-contained HTML page for the iPD BPMN 2.0 model.

Reads the converter output (.bpmn + .report.json), the source registry and -
when available - the merged findings and requirements of the synthesis step,
writes citations.json (trace data per element) and one HTML file with the
bpmn-js NavigatedViewer bundle, its CSS, the diagram-js-minimap bundle and CSS,
the BPMN XML, the moddle descriptor and citations.json inlined. No network
access at build time or in the page. REQ field 'modal' (must|should|may|
definition|example) is optional: an element whose REQs are all 'may' gets a
MAY chip; without the field the page shows no modal data.
Deterministic: no clock, no random values, stable ordering.

Usage:
  python -I tools/build_viewer.py --bpmn <file> --report <report.json>
         [--findings <yaml>] [--requirements <yaml>] --registry <yaml>
         --out <html> [--citations-out <json>] [--source-date YYYY-MM-DD]
         [--publish-dir <dir> [--publish-bpmn-name <file name>]]

--publish-dir writes a multi-file variant for a hosted page (with or without --out):
  index.html (template, all CSS inline; bpmn-js and diagram-js-minimap from jsDelivr with sha384 SRI
  computed from the pinned files in viewer/node_modules), boot.js (loader), app.js (same file as
  viewer/src/app.js), data/<model>.bpmn (copy of --bpmn) and data/citations.json (same content as the
  single-file build). No third-party code is copied into the publish variant.
  --publish-bpmn-name renames data/<model>.bpmn (e.g. ipd_best_practice.bpmn.xml for hosts that refuse .bpmn);
  the content stays byte-identical to --bpmn.

Missing --findings / --requirements files are not an error: the page then
shows the trace data from the .bpmn only (ipd:trace), and says so.
Exit codes: 0 ok (warnings allowed), 1 build error, 2 usage or I/O error.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: PyYAML is required", file=sys.stderr)
    sys.exit(2)

GENERATOR = "tools/build_viewer.py 1.1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BPMN_JS_VERSION = "18.31.1"
MINIMAP_VERSION = "5.6.0"   # diagram-js-minimap, pinned in viewer/package.json
# REQ modal (requirements.yaml field 'modal'); an element whose REQs are all 'may' gets the MAY chip
MODALS = ("must", "should", "may", "definition", "example")

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "ipd": "urn:ipd-best-practice:trace:1.0",
}
B = "{%s}" % NS["bpmn"]
IPD = "{%s}" % NS["ipd"]

TITLE = "Important protocol deviation (iPD) management - best-practice reference model (BPMN 2.0)"
STATUS = "Outside-in reference model derived from ICH, EU and US sources - not validated by process owners"

ACTIVITY_TAGS = {"task", "userTask", "serviceTask", "sendTask", "receiveTask", "manualTask",
                 "businessRuleTask", "scriptTask", "callActivity", "subProcess"}
EVENT_TAGS = {"startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent", "boundaryEvent"}
GATEWAY_TAGS = {"exclusiveGateway", "parallelGateway", "inclusiveGateway", "eventBasedGateway", "complexGateway"}
DATA_TAGS = {"dataObjectReference", "dataStoreReference"}
FLOW_NODE_TAGS = ACTIVITY_TAGS | EVENT_TAGS | GATEWAY_TAGS
# element kinds that get a source overlay on the canvas (zone below the element)
# (text annotations get an overlay only when they carry sources)
OVERLAY_TAGS = FLOW_NODE_TAGS | DATA_TAGS | {"messageFlow", "textAnnotation"}
# element kinds the filter bar highlights / dims and counts (annotations are notes, not steps)
FILTER_TAGS = FLOW_NODE_TAGS | DATA_TAGS | {"messageFlow"}
ARTIFACT_TAGS = {"textAnnotation", "association"}

BADGE = {"binding-law": "LAW", "binding-ICH": "ICH", "guidance": "GUIDANCE",
         "best-practice": "BP", "verify-binding": "VERIFY"}
BINDING_RANK = {"binding-law": 0, "binding-ICH": 1, "verify-binding": 2, "guidance": 3, "best-practice": 4}
BADGE_ORDER = ["LAW", "ICH", "GUIDANCE", "DRAFT", "BP", "VERIFY"]
JURISDICTIONS = ["ICH", "EU", "US"]

EVENT_DEFS = ["messageEventDefinition", "timerEventDefinition", "signalEventDefinition",
              "errorEventDefinition", "escalationEventDefinition", "conditionalEventDefinition",
              "terminateEventDefinition", "linkEventDefinition", "compensateEventDefinition"]


class BuildError(Exception):
    pass


# ----------------------------------------------------------------- helpers
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path):
    """Path relative to the project root (stable across machines), else basename."""
    ap = os.path.abspath(path)
    if ap.startswith(ROOT + os.sep):
        return os.path.relpath(ap, ROOT).replace(os.sep, "/")
    return os.path.basename(ap)


def text(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v).strip()


def as_list(v):
    if v is None or v == "":
        return []
    if isinstance(v, (list, tuple)):
        return [x for x in v if x is not None and x != ""]
    if isinstance(v, str):
        parts = re.split(r"[,\s]+", v.strip())
        return [p for p in parts if p]
    return [v]


def http_url(u):
    u = text(u)
    return u if re.match(r"^https?://\S+$", u) else ""


def norm_loc(loc):
    s = text(loc)
    s = re.sub(r"\s*\[verify[^\]]*\]\s*$", "", s)
    s = re.sub(r"\s+", "", s)
    return s.lower()


def local(tag):
    return tag.split("}", 1)[1] if "}" in tag else tag


def model_hash(model):
    h = model.lower()
    if not re.match(r"^[a-z0-9-]+$", h):
        raise BuildError("model id %r gives a non-ASCII hash name" % model)
    return h


def jdump_html(obj):
    """JSON for a <script type=application/json> block: '<' escaped, so no '</script' or '<!--'."""
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return s.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


# ----------------------------------------------------------------- inputs
def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_registry(path):
    data = load_yaml(path) or {}
    items = data.get("sources", []) if isinstance(data, dict) else data
    reg = {}
    for s in items or []:
        if not isinstance(s, dict) or not s.get("key"):
            continue
        reg[text(s["key"])] = {
            "key": text(s["key"]),
            "title": text(s.get("title")),
            "url": http_url(s.get("url")),
            "url_raw": text(s.get("url")),
            "url_status": text(s.get("url_status")),
            "binding_default": text(s.get("binding_default")),
            "jurisdiction": text(s.get("jurisdiction")),
            "draft": bool(s.get("draft", False)),
            "notes": text(s.get("notes")),
        }
    return reg


def load_findings(path, warnings):
    data = load_yaml(path)
    if isinstance(data, dict):
        for k in ("findings", "merged_findings", "items", "records"):
            if isinstance(data.get(k), list):
                data = data[k]
                break
        else:
            # mapping id -> record
            data = [dict(v, id=k) if isinstance(v, dict) and "id" not in v else v for k, v in data.items()]
    if not isinstance(data, list):
        raise BuildError("findings file %s: expected a list of findings" % path)
    out = {}
    for f in data:
        if not isinstance(f, dict) or not f.get("id"):
            continue
        fid = text(f["id"])
        if fid in out:
            warnings.append("findings: duplicate id %s (first kept)" % fid)
            continue
        out[fid] = {
            "id": fid,
            "src": text(f.get("src")),
            "doc": text(f.get("doc")),
            "url": http_url(f.get("url")),
            "loc": text(f.get("loc")),
            "loc_alt": text(f.get("loc_alt")),
            "page": text(f.get("page")),
            "paraphrase": text(f.get("paraphrase")),
            "quote": text(f.get("quote")),
            "modal": text(f.get("modal")),
            "binding": text(f.get("binding")),
            "binding_route": text(f.get("binding_route")),
            "draft": bool(f.get("draft", False)),
            "jurisdiction": text(f.get("jurisdiction")),
            "party": text(f.get("party")),
            "deadline": "" if text(f.get("deadline")).lower() == "none" else text(f.get("deadline")),
            "record": text(f.get("record")),
            "verify": [text(v) for v in as_list(f.get("verify")) if text(v)],
            "_retrieval": text(f.get("retrieval")),
        }
    return out


REQ_STATEMENT_KEYS = ("statement", "requirement", "text", "title", "summary", "description")
REQ_FINDING_KEYS = ("findings", "finding_ids", "finding", "basis", "evidence", "sources", "derived_from", "from")


def load_requirements(path, warnings):
    data = load_yaml(path)
    if isinstance(data, dict):
        for k in ("requirements", "reqs", "items", "records"):
            if isinstance(data.get(k), list):
                data = data[k]
                break
        else:
            data = [dict(v, id=k) if isinstance(v, dict) and "id" not in v else v for k, v in data.items()]
    if not isinstance(data, list):
        raise BuildError("requirements file %s: expected a list of requirements" % path)
    out = {}
    used = {"statement": set(), "findings": set()}
    for r in data:
        if not isinstance(r, dict):
            continue
        rid = text(r.get("id") or r.get("req"))
        if not rid:
            continue
        statement = ""
        for k in REQ_STATEMENT_KEYS:
            if text(r.get(k)):
                statement = text(r.get(k))
                used["statement"].add(k)
                break
        fids = []
        for k in REQ_FINDING_KEYS:
            v = r.get(k)
            if v:
                for x in as_list(v):
                    if isinstance(x, dict):
                        x = x.get("id") or x.get("finding")
                    x = text(x)
                    if re.match(r"^R\d-\d{3}$", x) and x not in fids:
                        fids.append(x)
                if fids:
                    used["findings"].add(k)
                    break
        party = r.get("party") if r.get("party") is not None else r.get("party_norm")
        if isinstance(party, (list, tuple)):
            party = ", ".join(text(p) for p in party)
        deadline = text(r.get("deadline"))
        modal = text(r.get("modal")).lower()
        if modal and modal not in MODALS:
            warnings.append("requirements: %s has modal %r (expected %s); shown as given"
                            % (rid, modal, "|".join(MODALS)))
        out[rid] = {
            "id": rid,
            "statement": statement,
            "binding": text(r.get("binding")),
            "draft": bool(r.get("draft", False)),
            "jurisdiction": [text(j) for j in as_list(r.get("jurisdiction"))],
            "deadline": "" if deadline.lower() == "none" else deadline,
            "record": text(r.get("record")),
            "party": text(party),
            "scope": text(r.get("scope") or r.get("status")),
            "reason": text(r.get("reason")),
            "binding_route": text(r.get("binding_route")),
            "trigger": text(r.get("trigger")),
            "action": text(r.get("action")),
            "recipient": text(r.get("recipient")),
            "verify": [text(v) for v in as_list(r.get("verify")) if text(v)],
            "modal": modal,
            "finding_ids": fids,
        }
    if out and not used["statement"]:
        warnings.append("requirements: no statement field found (looked for %s)" % ", ".join(REQ_STATEMENT_KEYS))
    if out and not used["findings"]:
        warnings.append("requirements: no finding id list found (looked for %s)" % ", ".join(REQ_FINDING_KEYS))
    return out


# ----------------------------------------------------------------- BPMN
def parse_trace(el):
    ext = el.find(B + "extensionElements")
    if ext is None:
        return None
    tr = ext.find(IPD + "trace")
    if tr is None:
        return None
    return {
        "binding": text(tr.get("binding")),
        "jurisdiction": text(tr.get("jurisdiction")).split(),
        "deadline": text(tr.get("deadline")),
        "draft": text(tr.get("draft")).lower() == "true",
        "record": text(tr.get("record")),
        "party": text(tr.get("party")),
        "interface": is_true(tr.get("interface")) or is_true(tr.get("{%s}interface" % NS["ipd"])),
        "sources": [{"key": text(s.get("key")), "loc": text(s.get("loc")), "page": text(s.get("page"))}
                    for s in tr.findall(IPD + "source")],
        "reqs": [text(r.get("id")) for r in tr.findall(IPD + "req") if text(r.get("id"))],
        "verify": [text(v.text) for v in tr.findall(IPD + "verify") if text(v.text)],
    }


def is_true(v):
    return text(v).lower() in ("true", "1", "yes")


def interface_marker(el):
    """Interface placeholder marker (decisions.md S0-18, pending): any ipd-namespace attribute 'interface'
    on the element or its ipd:trace, or an ipd:interface child in extensionElements."""
    if is_true(el.get("{%s}interface" % NS["ipd"])):
        return True
    ext = el.find(B + "extensionElements")
    if ext is not None:
        if ext.find(IPD + "interface") is not None:
            return True
        tr = ext.find(IPD + "trace")
        if tr is not None and (is_true(tr.get("interface")) or is_true(tr.get("{%s}interface" % NS["ipd"]))):
            return True
    return False


def parse_docs(el):
    docs = [d.text or "" for d in el.findall(B + "documentation")]
    return docs


def doc_fields(doc):
    """Parse 'Key: value' lines of the trace documentation (ipd_extension.md section 5)."""
    fields = []
    for line in (doc or "").splitlines():
        m = re.match(r"^([A-Za-z][A-Za-z ]*):\s?(.*)$", line)
        if m:
            fields.append([m.group(1).strip(), m.group(2).strip()])
        elif line.strip() and fields:
            fields[-1][1] += "\n" + line.strip()
    return fields


def event_kind(el):
    for d in EVENT_DEFS:
        if el.find(B + d) is not None:
            return d.replace("EventDefinition", "")
    return ""


def type_label(tag, el, participant_collapsed=False):
    ek = event_kind(el) if tag in EVENT_TAGS else ""
    ekl = {"message": "message", "timer": "timer", "signal": "signal", "error": "error",
           "escalation": "escalation", "conditional": "conditional", "terminate": "terminate",
           "link": "link", "compensate": "compensation"}.get(ek, ek)
    direction = text(el.get("gatewayDirection"))
    dir_txt = {"Diverging": "split", "Converging": "join"}.get(direction, "")
    if tag == "task":
        return "Task"
    if tag == "callActivity":
        return "Call activity"
    if tag == "subProcess":
        return "Sub-process"
    if tag.endswith("Task"):
        return tag[0].upper() + re.sub(r"([A-Z])", r" \1", tag[1:]).lower()
    if tag == "startEvent":
        return ("%s start event" % ekl.capitalize()) if ekl else "Start event"
    if tag == "endEvent":
        return ("%s end event" % ekl.capitalize()) if ekl else "End event"
    if tag == "intermediateCatchEvent":
        return "Intermediate %s catch event" % (ekl or "none")
    if tag == "intermediateThrowEvent":
        return "Intermediate %s throw event" % (ekl or "none")
    if tag == "boundaryEvent":
        return "Boundary %s event" % (ekl or "")
    gw = {"exclusiveGateway": ("Exclusive gateway", "XOR"), "parallelGateway": ("Parallel gateway", "AND"),
          "inclusiveGateway": ("Inclusive gateway", "OR"), "eventBasedGateway": ("Event-based gateway", ""),
          "complexGateway": ("Complex gateway", "")}
    if tag in gw:
        name, code = gw[tag]
        inner = " ".join(x for x in (code, dir_txt) if x)
        return name + (" (%s)" % inner if inner else "")
    if tag == "dataObjectReference":
        return "Data object"
    if tag == "dataStoreReference":
        return "Data store"
    if tag == "messageFlow":
        return "Message flow"
    if tag == "sequenceFlow":
        return "Sequence flow"
    if tag == "lane":
        return "Lane"
    if tag == "participant":
        return "Pool (collapsed)" if participant_collapsed else "Pool"
    if tag == "group":
        return "Group"
    if tag == "textAnnotation":
        return "Text annotation"
    if tag == "association":
        return "Association"
    return tag


def symbol_key(tag, el, collapsed=False):
    if tag in EVENT_TAGS:
        ek = event_kind(el)
        return tag + (":" + ek if ek else "")
    if tag == "participant":
        return "participant:collapsed" if collapsed else "participant"
    return tag


def parse_bpmn(path):
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        raise BuildError("BPMN file %s is not well-formed XML: %s" % (path, e))
    root = tree.getroot()
    if local(root.tag) != "definitions":
        raise BuildError("%s: root element is not bpmn:definitions" % path)

    elems = {}        # xml id -> raw record
    proc_of = {}      # flow element id -> process id
    lane_of = {}      # flow node id -> lane id
    proc_participant = {}  # process id -> participant id
    collab_of = {}    # participant / message flow / group id -> collaboration id
    collabs = {}      # collab id -> {name, docs, participants, message_flows, groups}
    processes = {}
    category_values = {}
    called = {}       # call activity id -> calledElement
    interfaces = set()  # call activities carrying the interface marker
    default_flows = set()

    def add(el, tag, **extra):
        eid = el.get("id")
        if not eid:
            return None
        rec = {"id": eid, "tag": tag, "name": text(el.get("name")), "trace": parse_trace(el),
               "docs": parse_docs(el), "el": el}
        rec.update(extra)
        elems[eid] = rec
        return rec

    for child in root:
        tag = local(child.tag)
        if tag == "category":
            for cv in child.findall(B + "categoryValue"):
                category_values[cv.get("id")] = text(cv.get("value"))
    for child in root:
        tag = local(child.tag)
        if tag == "collaboration":
            cid = child.get("id")
            c = {"id": cid, "name": text(child.get("name")), "docs": parse_docs(child),
                 "participants": [], "message_flows": [], "groups": []}
            for sub in child:
                st = local(sub.tag)
                if st == "participant":
                    rec = add(sub, "participant", process_ref=text(sub.get("processRef")))
                    c["participants"].append(sub.get("id"))
                    collab_of[sub.get("id")] = cid
                    if rec and rec["process_ref"]:
                        proc_participant[rec["process_ref"]] = sub.get("id")
                elif st == "messageFlow":
                    add(sub, "messageFlow", source=text(sub.get("sourceRef")), target=text(sub.get("targetRef")))
                    c["message_flows"].append(sub.get("id"))
                    collab_of[sub.get("id")] = cid
                elif st == "group":
                    add(sub, "group", category_value=text(sub.get("categoryValueRef")))
                    c["groups"].append(sub.get("id"))
                    collab_of[sub.get("id")] = cid
                elif st == "textAnnotation":
                    r = add(sub, "textAnnotation")
                    if r:
                        r["name"] = text(sub.findtext(B + "text"))
                    collab_of[sub.get("id")] = cid
                elif st == "association":
                    add(sub, "association", source=text(sub.get("sourceRef")), target=text(sub.get("targetRef")))
            collabs[cid] = c
        elif tag == "process":
            pid = child.get("id")
            processes[pid] = {"id": pid, "name": text(child.get("name"))}

            def walk_lanes(lane_set):
                for lane in lane_set.findall(B + "lane"):
                    add(lane, "lane", process=pid)
                    proc_of[lane.get("id")] = pid
                    for ref in lane.findall(B + "flowNodeRef"):
                        lane_of[text(ref.text)] = lane.get("id")
                    cls = lane.find(B + "childLaneSet")
                    if cls is not None:
                        walk_lanes(cls)

            for ls in child.findall(B + "laneSet"):
                walk_lanes(ls)
            for sub in child:
                st = local(sub.tag)
                if st == "textAnnotation":
                    r = add(sub, "textAnnotation", process=pid)
                    if r:
                        r["name"] = text(sub.findtext(B + "text"))
                    proc_of[sub.get("id")] = pid
                elif st == "association":
                    add(sub, "association", process=pid, source=text(sub.get("sourceRef")),
                        target=text(sub.get("targetRef")))
                if st in FLOW_NODE_TAGS or st in DATA_TAGS or st == "sequenceFlow":
                    extra = {"process": pid}
                    if st == "sequenceFlow":
                        extra.update(source=text(sub.get("sourceRef")), target=text(sub.get("targetRef")))
                    if st == "callActivity":
                        called[sub.get("id")] = text(sub.get("calledElement"))
                        if interface_marker(sub):
                            interfaces.add(sub.get("id"))
                    if sub.get("default"):
                        default_flows.add(sub.get("default"))
                    add(sub, st, **extra)
                    proc_of[sub.get("id")] = pid
                    # data associations (for the legend only)
                    if sub.find(B + "dataInputAssociation") is not None or \
                            sub.find(B + "dataOutputAssociation") is not None:
                        elems[sub.get("id")]["has_data_assoc"] = True

    # diagrams
    diagrams = []
    for d in root.findall("{%s}BPMNDiagram" % NS["bpmndi"]):
        plane = d.find("{%s}BPMNPlane" % NS["bpmndi"])
        if plane is None:
            continue
        shapes = {}
        for s in plane:
            st = local(s.tag)
            be = s.get("bpmnElement")
            if not be:
                continue
            if st == "BPMNShape":
                bd = s.find("{%s}Bounds" % NS["dc"])
                lbl = s.find("{%s}BPMNLabel/{%s}Bounds" % (NS["bpmndi"], NS["dc"]))
                shapes[be] = {
                    "bounds": [float(bd.get(k)) for k in ("x", "y", "width", "height")] if bd is not None else None,
                    "label": [float(lbl.get(k)) for k in ("x", "y", "width", "height")] if lbl is not None else None,
                    "expanded": text(s.get("isExpanded")),
                }
            elif st == "BPMNEdge":
                wps = [(float(w.get("x")), float(w.get("y"))) for w in s.findall("{%s}waypoint" % NS["di"])]
                lbl = s.find("{%s}BPMNLabel/{%s}Bounds" % (NS["bpmndi"], NS["dc"]))
                shapes[be] = {"waypoints": wps,
                              "label": [float(lbl.get(k)) for k in ("x", "y", "width", "height")] if lbl is not None else None}
        diagrams.append({"id": d.get("id"), "name": text(d.get("name")),
                         "plane_element": text(plane.get("bpmnElement")), "di": shapes})
    return {"elems": elems, "proc_of": proc_of, "lane_of": lane_of, "proc_participant": proc_participant,
            "collab_of": collab_of, "collabs": collabs, "processes": processes, "diagrams": diagrams,
            "category_values": category_values, "called": called, "default_flows": default_flows,
            "interfaces": interfaces}


# ----------------------------------------------------------------- verify triage
TRIAGE_CLASSES = ("open", "note", "general", "drop")
VERIFY_TAG = re.compile(r"\s*\[verify[^\]]*\]", re.I)


def load_verify_triage(path, warnings):
    """contracts/verify_triage.yaml: one entry per raw [verify] text -> class open | note | general | drop,
    a general wording for open and note, and the general statements (legend) for class general."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    general = {k: text((v or {}).get("wording")) for k, v in (data.get("general") or {}).items()}
    items = {}
    for it in data.get("items") or []:
        t, c = text(it.get("text")), text(it.get("class"))
        if not t or c not in TRIAGE_CLASSES:
            warnings.append("verify triage: entry with empty text or class %r skipped" % c)
            continue
        if c in ("open", "note") and not text(it.get("wording")):
            warnings.append("verify triage: %s entry without wording: %s" % (c, t[:60]))
        if c == "general" and text(it.get("general")) not in general:
            warnings.append("verify triage: unknown general statement %r for: %s" % (it.get("general"), t[:60]))
        items[t] = {"class": c, "wording": text(it.get("wording")), "general": text(it.get("general")),
                    "not_on": [text(x) for x in as_list(it.get("not_on")) if text(x)],
                    "not_on_note": text(it.get("not_on_note")),
                    "also_on": [text(x) for x in as_list(it.get("also_on")) if text(x)]}
    inline = []
    for it in data.get("inline") or []:
        if text(it.get("tag")) and text(it.get("action")) in ("strip", "replace", "keep"):
            inline.append({"tag": it["tag"], "fields": [text(f) for f in as_list(it.get("fields"))],
                           "action": text(it.get("action")), "note": text(it.get("note")),
                           "with": it.get("with") or ""})
        else:
            warnings.append("verify triage: inline rule without tag or action skipped")
    return {"general": general, "items": items, "inline": inline}


def apply_verify_triage(citations, triage, warnings):
    """Show VERIFY only for open points. Notes become plain notes, general points go to the legend, dropped points
    are not shown. The raw texts stay in the model, the requirements, the findings and the register (verify_raw).
    not_on: element or REQ ids that carry a text although it does not concern them; there it is not shown (a
    not_on_note may say why) and does not set the VERIFY badge. also_on: further elements an open point marks."""
    items, used_general, untriaged = triage["items"], set(), set()

    def excluded(t, ids):
        return any(i and i in t.get("not_on", []) for i in ids)

    def split(raw, *ids):
        opened, notes = [], []
        for v in raw:
            t = items.get(v)
            if t is not None and excluded(t, ids):
                if t.get("not_on_note") and t["not_on_note"] not in notes:
                    notes.append(t["not_on_note"])
                continue
            if t is None:
                untriaged.add(v)
                t = {"class": "open", "wording": VERIFY_TAG.sub("", v).strip(), "general": ""}
            if t["class"] == "open" and t["wording"] not in opened:
                opened.append(t["wording"])
            elif t["class"] == "note" and t["wording"] not in notes:
                notes.append(t["wording"])
            elif t["class"] == "general":
                used_general.add(t["general"])
        return opened, notes

    def blocked_for(*ids):
        return sorted(set(t["wording"] for t in items.values() if t["class"] == "open" and excluded(t, ids)))

    def inline_clean(val, field, notes=None):
        # inline [verify] fragments in displayed fields: strip or replace the ones the triage settled (rules in order)
        if not isinstance(val, str) or not val:
            return val
        for rule in triage.get("inline", []):
            if rule["action"] in ("strip", "replace") and field in rule["fields"] and rule["tag"] in val:
                val = re.sub(r"\s{2,}", " ", val.replace(rule["tag"], rule["with"] if rule["action"] == "replace" else "")).strip()
                if rule["note"] and notes is not None and rule["note"] not in notes:
                    notes.append(rule["note"])
        return val

    def triage_finding(f, *ids):
        if "verify_raw" not in f:
            f["verify_raw"] = f.get("verify", [])
            f["verify"], f["verify_notes"] = split(f["verify_raw"], *ids)
        f["binding_route"] = inline_clean(f.get("binding_route", ""), "binding_route")
        loc, page = inline_clean(f.get("loc", ""), "loc"), inline_clean(f.get("page", ""), "page")
        if loc != f.get("loc", ""):
            f["loc_shown"] = loc
        if page != f.get("page", ""):
            f["page_shown"] = page

    def loc_class(s):
        key = "SOURCE-LOC %s | %s | %s" % (s["key"], s["loc"], s.get("page", ""))
        t = items.get(key)
        if t is None:
            untriaged.add(key)
            return {"class": "open", "wording": "Section or page of this source not confirmed.", "general": ""}
        if t["class"] == "general":
            used_general.add(t["general"])
        return t

    before = sum(1 for r in citations["elements"].values() if "VERIFY" in r["badges"])
    for f in citations["findings"].values():
        triage_finding(f)
    for rec in citations["elements"].values():
        rec["verify_raw"] = rec["verify"]
        rec["verify"], rec["verify_notes"] = split(rec["verify_raw"], rec["id"])
        rec["verify_blocked"] = blocked_for(rec["id"])
        for rq in rec["reqs"]:
            rq["verify_raw"] = rq["verify"]
            rq["verify"], rq["verify_notes"] = split(rq["verify_raw"], rec["id"], rq["id"])
            rq["verify_blocked"] = blocked_for(rec["id"], rq["id"])
            for fld in ("binding_route", "recipient", "deadline", "record", "party", "trigger", "action"):
                rq[fld] = inline_clean(rq.get(fld, ""), fld, rq["verify_notes"])
            # the REQ carries copies of its findings: triage them in the context of this element and REQ
            fops = []
            for f in rq.get("findings", []):
                if isinstance(f, dict) and not f.get("missing"):
                    triage_finding(f, rec["id"], rq["id"])
                    fops += f.get("verify", [])
            # an open point of a requirement, or of a finding behind it, also marks the element (unless not_on)
            for w in rq["verify"] + fops:
                if w not in rec["verify"] and w not in rq["verify_blocked"]:
                    rec["verify"].append(w)
        rec["binding_routes"] = [inline_clean(r, "binding_route") for r in rec["binding_routes"]]
        for fld in ("deadline", "record", "party"):
            rec[fld] = inline_clean(rec.get(fld, ""), fld, rec["verify_notes"])
        for s in rec["sources"]:
            if "[verify" in s["loc"].lower() or "[verify" in (s.get("page") or "").lower():
                t = loc_class(s)
                if t["class"] == "open":
                    if t["wording"] and t["wording"] not in rec["verify"]:
                        rec["verify"].append(t["wording"])
                else:
                    s["loc_shown"] = VERIFY_TAG.sub("", inline_clean(s["loc"], "loc")).strip()
                    s["page_shown"] = VERIFY_TAG.sub("", inline_clean(s.get("page") or "", "page")).strip()
                    if t["class"] == "note" and t["wording"] and t["wording"] not in rec["verify_notes"]:
                        rec["verify_notes"].append(t["wording"])
    # also_on: an open point that belongs to further elements (e.g. a diagram-level model note)
    for t in items.values():
        if t["class"] == "open":
            for eid in t.get("also_on", []):
                rec = citations["elements"].get(eid)
                if rec is None:
                    warnings.append("verify triage: also_on element %s not found" % eid)
                elif t["wording"] not in rec["verify"]:
                    rec["verify"].append(t["wording"])
    for rec in citations["elements"].values():
        keep = bool(rec["verify"]) or rec["binding"] == "verify-binding"
        if keep and "VERIFY" not in rec["badges"]:
            rec["badges"] = sorted(rec["badges"] + ["VERIFY"], key=BADGE_ORDER.index)
        elif not keep and "VERIFY" in rec["badges"]:
            rec["badges"] = [b for b in rec["badges"] if b != "VERIFY"]
    for dg in citations["diagrams"]:
        md = []
        for kind, val in dg.get("model_doc") or []:
            if kind == "Open item" and "[verify" in val.lower():
                t = items.get(val)
                if t is None:
                    untriaged.add(val)
                    md.append([kind, val])
                elif t["class"] == "open":
                    md.append([kind, "[verify] " + t["wording"]])
                elif t["class"] == "note":
                    md.append(["Model note", t["wording"]])
                elif t["class"] == "general":
                    used_general.add(t["general"])
            else:
                md.append([kind, val])
        dg["model_doc"] = md
    leftover = sorted(set(m.group(0) for r in citations["elements"].values()
                          for v in [r.get("deadline", ""), r.get("record", ""), r.get("party", "")] + r["binding_routes"] +
                          [q.get(k, "") for q in r["reqs"] for k in ("binding_route", "recipient", "deadline", "record", "party")]
                          for m in re.finditer(r"\[verify[^\]]*\]", v or "", re.I)))
    for tag in leftover:
        if not any(rule["tag"].strip() in tag or tag in rule["tag"] for rule in triage.get("inline", []) if rule["action"] == "keep"):
            warnings.append("verify triage: inline fragment left in a displayed field: %s" % tag)
    after = sum(1 for r in citations["elements"].values() if "VERIFY" in r["badges"])
    for v in sorted(untriaged):
        warnings.append("verify triage: no entry, shown as VERIFY: %s" % v[:90])
    citations["meta"]["verify_general"] = {k: triage["general"][k] for k in sorted(used_general) if triage["general"].get(k)}
    citations["meta"]["counts"]["verify_elements"] = {"before_triage": before, "after_triage": after}
    citations["meta"]["counts"]["verify_untriaged"] = len(untriaged)

# ----------------------------------------------------------------- build
def strongest(bindings):
    bs = [b for b in bindings if b in BINDING_RANK]
    return sorted(bs, key=lambda b: BINDING_RANK[b])[0] if bs else ""


def badges_for(binding, draft, verify_items, sources):
    """Binding badge, then DRAFT whenever the element or one of its REQs is draft, then VERIFY."""
    out = []
    if binding:
        out.append(BADGE.get(binding, ""))
    if draft:
        out.append("DRAFT")
    has_verify = bool(verify_items) or binding == "verify-binding" or \
        any("[verify" in s["loc"] or "[verify" in s.get("page", "") for s in sources)
    if has_verify:
        out.append("VERIFY")
    out = [b for b in out if b]
    seen = []
    for b in out:
        if b not in seen:
            seen.append(b)
    return sorted(seen, key=BADGE_ORDER.index)


def split_routes(routes, registry):
    """REQ binding routes concatenate per-source routes ('E6R3: ...; EUCTR: ...'). Split them at '; <KEY>:'
    for registry keys only, and keep each segment once (spec order), so the panel lists one route per source."""
    keys = sorted(registry, key=len, reverse=True)
    if not keys:
        return routes
    pat = re.compile(r";\s+(?=(?:%s):\s)" % "|".join(re.escape(k) for k in keys))
    out = []
    for r in routes:
        for seg in pat.split(r):
            seg = seg.strip().rstrip(";").strip()
            if seg and seg not in out:
                out.append(seg)
    return out


def finding_view(f):
    v = dict(f)
    v.pop("_retrieval", None)
    return v


def build(args):
    warnings = []
    for p in (args.bpmn, args.report, args.registry):
        if not os.path.isfile(p):
            print("ERROR: input not found: %s" % p, file=sys.stderr)
            sys.exit(2)

    bpmn_xml = open(args.bpmn, encoding="utf-8").read()
    model = parse_bpmn(args.bpmn)
    with open(args.report, encoding="utf-8") as f:
        report = json.load(f)
    registry = load_registry(args.registry)

    findings, requirements = {}, {}
    inputs = {
        "bpmn": {"file": rel(args.bpmn), "sha256": sha256_file(args.bpmn)},
        "report": {"file": rel(args.report), "sha256": sha256_file(args.report)},
        "registry": {"file": rel(args.registry), "sha256": sha256_file(args.registry)},
        "findings": None, "requirements": None,
    }
    if args.findings:
        if os.path.isfile(args.findings):
            findings = load_findings(args.findings, warnings)
            inputs["findings"] = {"file": rel(args.findings), "sha256": sha256_file(args.findings),
                                  "records": len(findings)}
        else:
            warnings.append("findings file not found (%s): trace data from the .bpmn only" % rel(args.findings))
    if args.requirements:
        if os.path.isfile(args.requirements):
            requirements = load_requirements(args.requirements, warnings)
            inputs["requirements"] = {"file": rel(args.requirements), "sha256": sha256_file(args.requirements),
                                      "records": len(requirements)}
        else:
            warnings.append("requirements file not found (%s): trace data from the .bpmn only"
                            % rel(args.requirements))

    # index findings by (src, loc)
    by_src_loc = {}
    for fid in sorted(findings):
        f = findings[fid]
        by_src_loc.setdefault((f["src"], norm_loc(f["loc"])), []).append(fid)

    elems = model["elems"]

    # report: model per diagram, overlay zones
    rep_models = {m.get("diagram"): m for m in report.get("models", []) if m.get("diagram")}
    diag_order = [m.get("diagram") for m in report.get("models", [])]

    # diagram membership
    diag_list = []
    for d in model["diagrams"]:
        rm = rep_models.get(d["id"], {})
        mid = rm.get("model")
        if not mid:
            m = re.match(r"^(.*)_DIAGRAM$", d["id"])
            mid = (m.group(1) if m else d["id"]).replace("_", "-")
            warnings.append("report has no model entry for diagram %s; model id %s derived from the id" % (d["id"], mid))
        collab = model["collabs"].get(d["plane_element"], {})
        diag_list.append({"d": d, "model": mid, "collab": collab, "zones": rm.get("overlay_zones", {}) or {},
                          "pool_order": rm.get("pool_order", [])})
    diag_list.sort(key=lambda x: (diag_order.index(x["d"]["id"]) if x["d"]["id"] in diag_order else 999,
                                  x["model"]))
    if not diag_list:
        raise BuildError("no BPMNDiagram in %s" % args.bpmn)

    # process -> diagram (via internal participants of the collaboration)
    proc_diagram = {}
    for dl in diag_list:
        for pid in dl["collab"].get("participants", []):
            pr = elems.get(pid, {}).get("process_ref")
            if pr:
                proc_diagram[pr] = dl["d"]["id"]

    diag_by_id = {dl["d"]["id"]: dl for dl in diag_list}

    def pool_name_of(eid):
        pid = model["proc_of"].get(eid)
        part = model["proc_participant"].get(pid)
        return elems[part]["name"] if part in elems else "", part

    def ref_name(ref):
        r = elems.get(ref)
        if not r:
            return ref
        return r["name"] or type_label(r["tag"], r["el"]) + " " + ref

    used_registry = set()
    used_findings = set()
    out_elements = {}
    symbols = set()
    diagrams_out = []

    for dl in diag_list:
        d = dl["d"]
        did, mid = d["id"], dl["model"]
        di = d["di"]
        ids_on = list(di.keys())
        records = []
        for eid in ids_on:
            r = elems.get(eid)
            if r is None:
                continue  # e.g. data associations, not separate citation records
            tag = r["tag"]
            collapsed = tag == "participant" and not r.get("process_ref")
            if tag in FLOW_NODE_TAGS or tag in DATA_TAGS or tag in ("participant", "lane", "group"):
                symbols.add(symbol_key(tag, r["el"], collapsed))
            if tag == "sequenceFlow":
                symbols.add("sequenceFlow")
                if eid in model["default_flows"]:
                    symbols.add("defaultFlow")
            if tag == "messageFlow":
                symbols.add("messageFlow")
            if r.get("has_data_assoc"):
                symbols.add("dataAssociation")
            tr = r["trace"]
            if tag == "sequenceFlow" and not tr:
                continue
            if tag == "association":
                symbols.add("association")
                continue
            if tag == "textAnnotation":
                symbols.add("textAnnotation")
            if tag in ("group", "textAnnotation") and not tr:
                continue
            trace = tr or {"binding": "", "jurisdiction": [], "deadline": "", "draft": False, "record": "",
                           "party": "", "interface": False, "sources": [], "reqs": [], "verify": []}
            docs = r["docs"]
            fields = doc_fields(docs[0]) if (tr and docs) else []
            extra_docs = docs[1:] if tr else docs
            record, party = trace["record"], trace["party"]
            for k, v in fields:
                if k == "Record" and not record:
                    record = v
                if k == "Party" and not party:
                    party = v
            label = r["name"]
            if tag == "group":
                label = model["category_values"].get(r.get("category_value"), label)
            lane_id = model["lane_of"].get(eid, "")
            pool_name, part_id = pool_name_of(eid)
            if tag == "participant":
                pool_name, part_id = r["name"], eid
            if tag == "lane":
                pool_name, part_id = pool_name_of(eid)
            performer = elems[lane_id]["name"] if lane_id in elems else pool_name

            # sources
            srcs = []
            seen_src = set()
            for s in trace["sources"]:
                k = (s["key"], s["loc"], s["page"])
                if k in seen_src:
                    continue
                seen_src.add(k)
                reg = registry.get(s["key"])
                if reg:
                    used_registry.add(s["key"])
                else:
                    warnings.append("%s: source key %s not in the registry" % (eid, s["key"]))
                fids = by_src_loc.get((s["key"], norm_loc(s["loc"])), [])
                srcs.append({
                    "key": s["key"], "loc": s["loc"], "page": s["page"],
                    "title": reg["title"] if reg else "",
                    "url": "", "url_status": reg["url_status"] if reg else "",
                    "binding_default": reg["binding_default"] if reg else "",
                    "in_registry": bool(reg),
                    "findings": list(fids),
                })

            # requirements
            reqs = []
            req_bindings = []
            routes = []
            for rid in trace["reqs"]:
                rq = requirements.get(rid)
                fl = []
                if rq:
                    for fid in rq["finding_ids"]:
                        f = findings.get(fid)
                        if f:
                            fl.append(finding_view(f))
                            used_findings.add(fid)
                        else:
                            fl.append({"id": fid, "missing": True})
                    req_bindings.append(rq["binding"])
                reqs.append({
                    "id": rid, "found": bool(rq),
                    "statement": rq["statement"] if rq else "",
                    "binding": rq["binding"] if rq else "",
                    "draft": rq["draft"] if rq else False,
                    "jurisdiction": rq["jurisdiction"] if rq else [],
                    "deadline": rq["deadline"] if rq else "",
                    "record": rq["record"] if rq else "",
                    "party": rq["party"] if rq else "",
                    "scope": rq["scope"] if rq else "",
                    "reason": rq["reason"] if rq else "",
                    "binding_route": rq["binding_route"] if rq else "",
                    "trigger": rq["trigger"] if rq else "",
                    "action": rq["action"] if rq else "",
                    "recipient": rq["recipient"] if rq else "",
                    "verify": rq["verify"] if rq else [],
                    "modal": rq["modal"] if rq else "",
                    "findings": fl,
                })
            # sources: URL from a linked finding (URL actually fetched), else registry URL
            req_fids = {f["id"] for rq in reqs for f in rq["findings"] if not f.get("missing")}
            for s in srcs:
                s["findings_match"] = "loc" if s["findings"] else ""
                if not s["findings"]:
                    # no finding at exactly this location: fall back to the findings with the same source key
                    # behind the element's requirements (the panel says that the location differs)
                    same_key = sorted(fid for fid in req_fids if findings.get(fid, {}).get("src") == s["key"])
                    if same_key:
                        s["findings"] = same_key
                        s["findings_match"] = "key"
                        warnings.append("%s: source %s %s matches no finding location; %d finding(s) with key %s "
                                        "behind its REQs shown instead" % (eid, s["key"], s["loc"], len(same_key), s["key"]))
                pref = [fid for fid in s["findings"] if fid in req_fids] or s["findings"]
                s["findings"] = pref + [fid for fid in s["findings"] if fid not in pref]
                url = ""
                for fid in pref:
                    if findings[fid]["url"]:
                        url = findings[fid]["url"]
                        break
                reg = registry.get(s["key"])
                s["url"] = url or (reg["url"] if reg else "")
                s["url_from"] = "finding" if url else ("registry" if s["url"] else "")
                used_findings.update(s["findings"])
            # binding route(s): REQ routes for the element binding, else routes of the findings behind it
            b = trace["binding"]
            for rq in reqs:
                if rq["binding_route"] and (not b or rq["binding"] == b) and rq["binding_route"] not in routes:
                    routes.append(rq["binding_route"])
            for rq in ([] if routes else reqs):
                for f in rq["findings"]:
                    if f.get("missing") or not f.get("binding_route"):
                        continue
                    if not b or f.get("binding") == b or rq["binding"] == b:
                        if f["binding_route"] not in routes:
                            routes.append(f["binding_route"])
            if not routes:
                for s in srcs:
                    for fid in s["findings"][:1]:
                        br = findings[fid]["binding_route"]
                        if br and br not in routes:
                            routes.append(br)
            routes = split_routes(routes, registry)
            if b and req_bindings and strongest(req_bindings) and strongest(req_bindings) != b:
                warnings.append("%s: element binding %s differs from strongest REQ binding %s"
                                % (eid, b, strongest(req_bindings)))

            req_draft = any(rq["draft"] for rq in reqs)
            # MAY chip: every linked REQ is known and has modal 'may' (no chip when the field is absent)
            may_only = bool(reqs) and all(rq["found"] and rq["modal"] == "may" for rq in reqs)
            badges = badges_for(trace["binding"], trace["draft"] or req_draft, trace["verify"], srcs)
            calls = None
            if tag == "callActivity":
                ce = model["called"].get(eid, "")
                tdid = proc_diagram.get(ce, "")
                if not ce or eid in model["interfaces"] or trace["interface"]:
                    # interface placeholder: neighbouring process outside this model (S0-18), no drill-down
                    calls = {"called_element": ce, "diagram": "", "model": "", "available": False, "interface": True}
                    symbols.add("callActivity:interface")
                elif tdid:
                    calls = {"called_element": ce, "diagram": tdid, "model": diag_by_id[tdid]["model"],
                             "available": True, "interface": False}
                else:
                    m = re.match(r"^(L\d+(?:_\d+)?)_", ce)
                    cm = m.group(1).replace("_", "-") if m else ""
                    calls = {"called_element": ce, "diagram": (m.group(1) + "_DIAGRAM") if m else "",
                             "model": cm, "available": False, "interface": False}
            mf = None
            if tag == "messageFlow":
                src_pool = pool_name_of(r["source"])[0] if r["source"] in model["proc_of"] else ref_name(r["source"])
                tgt_pool = pool_name_of(r["target"])[0] if r["target"] in model["proc_of"] else ref_name(r["target"])
                mf = {"source": r["source"], "target": r["target"],
                      "source_label": ref_name(r["source"]), "target_label": ref_name(r["target"]),
                      "source_pool": src_pool, "target_pool": tgt_pool}
                performer = "%s to %s" % (src_pool, tgt_pool)

            # DI geometry for ordering and the fallback overlay position
            g = di.get(eid, {})
            if g.get("bounds"):
                ox, oy = g["bounds"][0], g["bounds"][1]
            elif g.get("label"):
                ox, oy = g["label"][0], g["label"][1]
            elif g.get("waypoints"):
                ox, oy = min(p[0] for p in g["waypoints"]), min(p[1] for p in g["waypoints"])
            else:
                ox, oy = 0.0, 0.0
            zone = dl["zones"].get(eid)
            overlay = bool(srcs) and tag in OVERLAY_TAGS
            if overlay and not zone:
                warnings.append("%s: has sources but no overlay zone in the report; placed below the shape" % eid)

            verify_all = list(trace["verify"])
            hay = [label, eid, type_label(tag, r["el"], collapsed), performer, trace["deadline"], record, party]
            if calls and calls.get("interface"):
                hay.append("interface - outside this model")
            hay += ["%s %s %s %s" % (s["key"], s["loc"], s["page"], s["title"]) for s in srcs]
            for rq in reqs:
                hay += [rq["id"], rq["statement"], rq["party"], rq["record"]]
                for f in rq["findings"]:
                    if not f.get("missing"):
                        hay += [f["id"], f["paraphrase"], f["quote"], f["doc"], f["loc"]]
            for s in srcs:
                for fid in s["findings"]:
                    f = findings[fid]
                    hay += [f["id"], f["paraphrase"], f["quote"]]
            hay += verify_all
            seen_h, uniq_h = set(), []
            for h in hay:
                if h and h not in seen_h:
                    seen_h.add(h)
                    uniq_h.append(h)
            search = " | ".join(uniq_h).lower()

            rec = {
                "id": eid, "model": mid, "diagram": did, "type": "bpmn:" + tag[0].upper() + tag[1:],
                "type_label": type_label(tag, r["el"], collapsed), "label": label,
                "lane": elems[lane_id]["name"] if lane_id in elems else "", "pool": pool_name,
                "performer": performer,
                "binding": trace["binding"], "jurisdiction": trace["jurisdiction"], "deadline": trace["deadline"],
                "draft": trace["draft"], "req_draft": req_draft, "may_only": may_only,
                "record": record, "party": party,
                "verify": verify_all,
                "badges": badges, "sources": srcs, "reqs": reqs, "binding_routes": routes,
                "notes": [t.strip() for t in extra_docs if t and t.strip()],
                "calls": calls, "message_flow": mf,
                "filterable": tag in FILTER_TAGS, "overlay": overlay,
                "zone": zone if (overlay or (calls and calls.get("interface"))) else None,
                "panel_only": bool(srcs) and not overlay,
                "has_trace": bool(tr), "search": search, "_ord": (oy if tag in ("participant", "lane") else ox, oy),
                "_tag": tag,
            }
            records.append(rec)

        # stable order: left to right, then top to bottom; ties by id
        records.sort(key=lambda x: (x["_ord"][0], x["_ord"][1], x["id"]))
        for i, rec in enumerate(records):
            rec["order"] = i
        # parent call activity (L3 node calling this model's internal process)
        parent = None
        call_targets = []
        for rec in records:
            if rec["calls"]:
                call_targets.append({"element_id": rec["id"], "label": rec["label"], **rec["calls"]})
        diagrams_out.append({
            "id": did, "model": mid, "hash": model_hash(mid),
            "level": "L3" if mid.upper().startswith("L3") else ("L4" if mid.upper().startswith("L4") else ""),
            "name": d["name"], "title": dl["collab"].get("name", ""),
            "collaboration": d["plane_element"],
            "model_doc": doc_fields(dl["collab"].get("docs", [""])[0] if dl["collab"].get("docs") else ""),
            "pool_order": dl["pool_order"],
            "elements": [rec["id"] for rec in records],
            "filterable": [rec["id"] for rec in records if rec["filterable"]],
            "overlay_elements": [rec["id"] for rec in records if rec["overlay"]],
            "panel_only_elements": [rec["id"] for rec in records if rec["panel_only"]],
            "call_targets": call_targets,
            "parent": parent,
        })
        for rec in records:
            rec.pop("_ord")
            rec.pop("_tag")
            if rec["id"] in out_elements:
                warnings.append("element id %s appears in more than one diagram (last kept)" % rec["id"])
            out_elements[rec["id"]] = rec

    # parents: the call activity whose call target is this diagram
    for dg in diagrams_out:
        for ct in dg["call_targets"]:
            if ct["available"]:
                for child in diagrams_out:
                    if child["id"] == ct["diagram"] and child["parent"] is None:
                        child["parent"] = {"element_id": ct["element_id"], "label": ct["label"],
                                           "diagram": dg["id"], "model": dg["model"], "hash": dg["hash"]}
    hashes = [dg["hash"] for dg in diagrams_out]
    if len(set(hashes)) != len(hashes):
        raise BuildError("duplicate hash names: %s" % hashes)
    reserved = {"settings", "sidebar", "customize", "upgrade", "downloads"}
    for h in hashes:
        if h in reserved or h.startswith("comment-"):
            raise BuildError("hash name %s is reserved" % h)

    # findings referenced anywhere (once)
    findings_out = {fid: finding_view(findings[fid]) for fid in sorted(used_findings) if fid in findings}

    # source basis date: latest retrieval date of the findings used (else of all findings)
    dates = []
    pool = [findings[f] for f in used_findings if f in findings] or list(findings.values())
    for f in pool:
        dates += re.findall(r"\b(20\d\d-\d\d-\d\d)\b", f["_retrieval"])
    if args.source_date:
        basis = args.source_date
        basis_note = "source basis date given at build time"
    elif dates:
        basis = max(dates)
        basis_note = "latest retrieval date of the cited findings"
    elif findings:
        basis = "TBD"
        basis_note = "no retrieval date in the findings"
    else:
        basis = "TBD"
        basis_note = "findings not yet merged - retrieval dates unknown"

    # moddle-independent checks
    em, md = "\u2014", "\u00b7"
    n_em = sum(json.dumps(r, ensure_ascii=False).count(em) for r in out_elements.values())
    n_md = sum(json.dumps(r, ensure_ascii=False).count(md) for r in out_elements.values())
    if n_em or n_md:
        warnings.append("content contains %d em dash and %d middle dot characters (kept verbatim)" % (n_em, n_md))

    trace_only = not (inputs["findings"] and inputs["requirements"])
    modal_loaded = any(rq["modal"] for rq in requirements.values())
    basis_text = text(args.source_basis)
    meta = {
        "title": TITLE, "status": STATUS,
        "source_basis_date": basis, "source_basis_note": basis_note, "source_basis_text": basis_text,
        "trace_only": trace_only,
        "findings_loaded": bool(inputs["findings"]), "requirements_loaded": bool(inputs["requirements"]),
        "modal_loaded": modal_loaded,
        "inputs": inputs, "generator": GENERATOR,
        "converter": {"tool": text(report.get("tool")), "version": text(report.get("version")),
                      "warnings": report.get("warnings", [])},
        "symbols": sorted(symbols),
        "warnings": warnings,
        "counts": {
            "diagrams": len(diagrams_out),
            "elements": len(out_elements),
            "elements_with_sources": sum(1 for r in out_elements.values() if r["sources"]),
            "overlays": {dg["id"]: len(dg["overlay_elements"]) for dg in diagrams_out},
            "panel_only": {dg["id"]: len(dg["panel_only_elements"]) for dg in diagrams_out},
            "findings": len(findings_out), "requirements_loaded": len(requirements),
            "may_only": sum(1 for r in out_elements.values() if r["may_only"]),
        },
    }
    registry_out = {k: registry[k] for k in sorted(used_registry)}
    citations = {"schema": "ipd-viewer-citations/1.0", "meta": meta, "diagrams": diagrams_out,
                 "elements": out_elements, "findings": findings_out, "registry": registry_out}
    if args.verify_triage and os.path.isfile(args.verify_triage):
        inputs["verify_triage"] = {"file": rel(args.verify_triage), "sha256": sha256_file(args.verify_triage)}
        triage = load_verify_triage(args.verify_triage, warnings)
        inputs["verify_triage"]["records"] = len(triage["items"])
        apply_verify_triage(citations, triage, warnings)
    else:
        inputs["verify_triage"] = None
        meta["verify_general"] = {}
    return citations, bpmn_xml, warnings


# ----------------------------------------------------------------- page
def bundle_paths(args):
    cands = [args.bpmn_js_dir] if args.bpmn_js_dir else [
        os.path.join(ROOT, "viewer", "node_modules", "bpmn-js"),
        os.path.join(ROOT, "vendor", "node", "node_modules", "bpmn-js"),
    ]
    for c in cands:
        pj = os.path.join(c, "package.json")
        if os.path.isfile(pj):
            with open(pj, encoding="utf-8") as f:
                ver = json.load(f).get("version")
            if ver != BPMN_JS_VERSION:
                raise BuildError("bpmn-js %s at %s; %s required (viewer/package.json)" % (ver, c, BPMN_JS_VERSION))
            return c
    raise BuildError("bpmn-js not found; run npm ci in viewer/")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def minimap_paths():
    """diagram-js-minimap UMD bundle (global DiagramJSMinimap, dependencies bundled), CSS and licence."""
    for c in (os.path.join(ROOT, "viewer", "node_modules", "diagram-js-minimap"),
              os.path.join(ROOT, "vendor", "node", "node_modules", "diagram-js-minimap")):
        pj = os.path.join(c, "package.json")
        if os.path.isfile(pj):
            with open(pj, encoding="utf-8") as f:
                ver = json.load(f).get("version")
            if ver != MINIMAP_VERSION:
                raise BuildError("diagram-js-minimap %s at %s; %s required (viewer/package.json)"
                                 % (ver, c, MINIMAP_VERSION))
            return {"js": os.path.join(c, "dist", "diagram-minimap.umd.prod.js"),
                    "css": os.path.join(c, "assets", "diagram-js-minimap.css"),
                    "license": os.path.join(c, "LICENSE"), "dir": c}
    raise BuildError("diagram-js-minimap not found; run npm ci in viewer/")


def minimap_js():
    """Minified UMD bundle with its MIT licence notice as a preserved comment (the bundle ships without one)."""
    mp = minimap_paths()
    lic = read(mp["license"]).strip()
    if "*/" in lic:
        raise BuildError("minimap licence text contains a comment terminator")
    return "/*! diagram-js-minimap v%s | bundled with min-dash, min-dom, tiny-svg\n%s\n*/\n%s" % (
        MINIMAP_VERSION, lic, read(mp["js"]).strip() + "\n")


def font_css(bjs):
    """bpmn-font icon CSS with the woff2 font as a data: URI (the shipped @font-face uses relative URLs)."""
    import base64
    fdir = os.path.join(bjs, "dist", "assets", "bpmn-font")
    css = read(os.path.join(fdir, "css", "bpmn.css"))
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@font-face\s*\{.*?\}", "", css, flags=re.S)
    css = css.replace('@charset "utf-8";', "")
    with open(os.path.join(fdir, "font", "bpmn.woff2"), "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    face = ("@font-face{font-family:'bpmn';src:url('data:font/woff2;base64,%s') format('woff2');"
            "font-weight:normal;font-style:normal}" % b64)
    return face + "\n" + css.strip() + "\n"


def check_inline(name, s, closing):
    if closing in s.lower():
        raise BuildError("%s contains %r and cannot be inlined" % (name, closing))


def write_page(args, citations, bpmn_xml):
    bjs = bundle_paths(args)
    dist = os.path.join(bjs, "dist")
    bundle = read(os.path.join(dist, "bpmn-navigated-viewer.production.min.js"))
    css_lib = read(os.path.join(dist, "assets", "diagram-js.css")) + "\n" + \
        read(os.path.join(dist, "assets", "bpmn-js.css")) + "\n" + font_css(bjs) + "\n" + \
        read(minimap_paths()["css"])
    mm_js = minimap_js()
    for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)", css_lib):
        if not m.group(1).startswith("data:") and not m.group(1).startswith("#"):
            raise BuildError("library CSS references a non-data URL: %s" % m.group(1)[:60])
    src_dir = os.path.join(ROOT, "viewer", "src")
    tpl = read(os.path.join(src_dir, "template.html"))
    app_css = read(os.path.join(src_dir, "app.css"))
    app_js = read(os.path.join(src_dir, "app.js"))
    moddle = json.load(open(args.moddle, encoding="utf-8"))
    check_inline("bpmn-js bundle", bundle, "</script")
    check_inline("minimap bundle", mm_js, "</script")
    check_inline("app.js", app_js, "</script")
    check_inline("CSS", css_lib + app_css, "</style")

    meta = citations["meta"]
    parts = {
        "{{IPD_TITLE}}": html_escape(meta["title"]),
        "{{IPD_STATUS}}": html_escape(meta["status"]),
        "{{IPD_LIB_CSS}}": css_lib,
        "{{IPD_APP_CSS}}": app_css,
        "{{IPD_BUNDLE}}": bundle,
        "{{IPD_MINIMAP_JS}}": mm_js,
        "{{IPD_DATA}}": jdump_html(page_data(citations)),
        "{{IPD_BPMN}}": jdump_html(bpmn_xml),
        "{{IPD_MODDLE}}": jdump_html(moddle),
        "{{IPD_APP_JS}}": app_js,
    }
    # single pass, so tokens inside inlined content are never re-substituted
    pattern = re.compile("|".join(re.escape(k) for k in parts))
    for k in parts:
        n = tpl.count(k)
        if n < 1 or (n != 1 and k not in ("{{IPD_TITLE}}", "{{IPD_STATUS}}")):
            raise BuildError("template token %s must occur exactly once (found %d)" % (k, n))
    html = pattern.sub(lambda m: parts[m.group(0)], tpl)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    return {"bundle_sha256": hashlib.sha256(bundle.encode("utf-8")).hexdigest(), "bpmn_js_dir": rel(bjs)}


def page_data(citations):
    """citations.json for embedding: REQ findings by id (the page resolves them from 'findings'),
    so a finding cited by many elements is embedded once. citations.json on disk stays denormalised."""
    data = json.loads(json.dumps(citations))
    for rec in data["elements"].values():
        for rq in rec["reqs"]:
            rq["findings"] = [f if f.get("missing") else f["id"] for f in rq["findings"]]
    data["page_compact"] = True
    return data


CDN_BASE = "https://cdn.jsdelivr.net/npm/"


def sri384(path):
    import base64
    with open(path, "rb") as f:
        return "sha384-" + base64.b64encode(hashlib.sha384(f.read()).digest()).decode("ascii")


def html_comment(s):
    if "--" in s:
        raise BuildError("licence text contains '--' and cannot go into an HTML comment")
    return "<!--\n%s\n-->" % s


def write_publish(args, citations, bpmn_xml):
    """Multi-file variant for hosting: own files plus two CDN scripts with SRI (see module docstring)."""
    out = os.path.abspath(args.publish_dir)
    bjs = bundle_paths(args)
    mp = minimap_paths()
    bundle_file = os.path.join(bjs, "dist", "bpmn-navigated-viewer.production.min.js")
    cdn = [
        (CDN_BASE + "bpmn-js@%s/dist/bpmn-navigated-viewer.production.min.js" % BPMN_JS_VERSION, bundle_file),
        (CDN_BASE + "diagram-js-minimap@%s/dist/diagram-minimap.umd.prod.js" % MINIMAP_VERSION, mp["js"]),
    ]
    dist = os.path.join(bjs, "dist")
    css_lib = read(os.path.join(dist, "assets", "diagram-js.css")) + "\n" + \
        read(os.path.join(dist, "assets", "bpmn-js.css")) + "\n" + font_css(bjs) + "\n" + read(mp["css"])
    src_dir = os.path.join(ROOT, "viewer", "src")
    tpl = read(os.path.join(src_dir, "template.html"))
    app_css = read(os.path.join(src_dir, "app.css"))
    check_inline("CSS", css_lib + app_css, "</style")
    moddle = json.load(open(args.moddle, encoding="utf-8"))
    bpmn_name = args.publish_bpmn_name or os.path.basename(args.bpmn)
    if not re.match(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$", bpmn_name):
        raise BuildError("model file name %r is not a plain relative file name" % bpmn_name)
    cfg = {"app": "app.js", "bpmn": "data/" + bpmn_name, "citations": "data/citations.json"}

    def script_tag(url, path):
        return '<script src="%s" integrity="%s" crossorigin="anonymous"></script>' % (url, sri384(path))

    # licence notices as in the single-file page: the bpmn-js header (first comment of its bundle) and the
    # MIT notice of diagram-js-minimap, here as HTML comments next to the CDN script tags
    head = read(bundle_file)[:400]
    m = re.match(r"/\*!\s*(.*?)\s*\*/", head, re.S)
    bjs_notice = (m.group(1) if m else "bpmn-js %s" % BPMN_JS_VERSION) + " (loaded from jsDelivr, licence header in the file)"
    mm_notice = "diagram-js-minimap v%s (loaded from jsDelivr), bundled with min-dash, min-dom, tiny-svg\n%s" % (
        MINIMAP_VERSION, read(mp["license"]).strip())
    blocks = {
        "IPD_DATA": "",
        "IPD_BPMN": "",
        "IPD_BUNDLE": html_comment(bjs_notice) + "\n" + script_tag(*cdn[0]),
        "IPD_MINIMAP_JS": html_comment(mm_notice) + "\n" + script_tag(*cdn[1]),
        "IPD_APP_JS": '<script id="ipd-publish" type="application/json">%s</script>\n<script src="boot.js"></script>'
                      % jdump_html(cfg),
    }
    for tok, rep_html in blocks.items():
        pat = re.compile(r"<script\b[^>]*>\s*\{\{%s\}\}\s*</script>\n?" % tok)
        if len(pat.findall(tpl)) != 1:
            raise BuildError("template block for %s must occur exactly once" % tok)
        tpl = pat.sub(lambda _m: rep_html + ("\n" if rep_html else ""), tpl)
    meta = citations["meta"]
    parts = {
        "{{IPD_TITLE}}": html_escape(meta["title"]),
        "{{IPD_STATUS}}": html_escape(meta["status"]),
        "{{IPD_LIB_CSS}}": css_lib,
        "{{IPD_APP_CSS}}": app_css,
        "{{IPD_MODDLE}}": jdump_html(moddle),
    }
    pattern = re.compile("|".join(re.escape(k) for k in parts))
    for k in parts:
        n = tpl.count(k)
        if n < 1 or (n != 1 and k not in ("{{IPD_TITLE}}", "{{IPD_STATUS}}")):
            raise BuildError("template token %s must occur exactly once (found %d)" % (k, n))
    html = pattern.sub(lambda mm: parts[mm.group(0)], tpl)
    if "{{IPD_" in html:
        raise BuildError("publish page has an unreplaced template token")
    os.makedirs(os.path.join(out, "data"), exist_ok=True)

    def wtext(rel_path, content):
        with open(os.path.join(out, rel_path), "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    wtext("index.html", html)
    wtext("app.js", read(os.path.join(src_dir, "app.js")))
    wtext("boot.js", read(os.path.join(src_dir, "boot.js")))
    with open(args.bpmn, "rb") as f, open(os.path.join(out, cfg["bpmn"]), "wb") as g:
        g.write(f.read())
    with open(os.path.join(out, cfg["citations"]), "w", encoding="utf-8", newline="\n") as f:
        json.dump(citations, f, ensure_ascii=False, sort_keys=True, indent=1)
        f.write("\n")
    files = ["index.html", "boot.js", "app.js", cfg["bpmn"], cfg["citations"]]
    return {"dir": out, "files": [(p, os.path.getsize(os.path.join(out, p)), sha256_file(os.path.join(out, p))) for p in files],
            "cdn": [(u, sri384(p)) for u, p in cdn]}


def html_escape(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the self-contained iPD BPMN viewer page")
    ap.add_argument("--bpmn", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--findings")
    ap.add_argument("--requirements")
    ap.add_argument("--registry", required=True)
    ap.add_argument("--out", help="single-file page (required unless --publish-dir is given)")
    ap.add_argument("--citations-out")
    ap.add_argument("--source-date", help="override the source basis date (YYYY-MM-DD)")
    ap.add_argument("--source-basis", help="header source-basis line, verbatim (replaces the derived date line)")
    ap.add_argument("--moddle", default=os.path.join(ROOT, "contracts", "ipd_moddle.json"))
    ap.add_argument("--bpmn-js-dir", help="bpmn-js package dir (default viewer/node_modules/bpmn-js)")
    ap.add_argument("--publish-dir", help="also (or only) write the multi-file hosted variant to this directory")
    ap.add_argument("--publish-bpmn-name", help="file name of the model under <publish-dir>/data/ (default: --bpmn file name)")
    ap.add_argument("--verify-triage", default=os.path.join(ROOT, "contracts", "verify_triage.yaml"),
                    help="triage of the [verify] texts (default contracts/verify_triage.yaml; skipped if absent)")
    args = ap.parse_args(argv)
    if args.publish_bpmn_name and not args.publish_dir:
        ap.error("--publish-bpmn-name needs --publish-dir")
    if not args.out and not args.publish_dir:
        ap.error("--out or --publish-dir is required")
    if args.source_date and not re.match(r"^\d{4}-\d{2}-\d{2}$", args.source_date):
        ap.error("--source-date must be YYYY-MM-DD")
    try:
        citations, bpmn_xml, warnings = build(args)
        info = write_page_and_citations(args, citations, bpmn_xml) if args.out else None
        pub = None
        if args.publish_dir:
            if not info:
                add_viewer_meta(args, citations)
            pub = write_publish(args, citations, bpmn_xml)
    except BuildError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 1
    except (OSError, yaml.YAMLError, json.JSONDecodeError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    m = citations["meta"]
    if info:
        print("viewer: %s (%d bytes, sha256 %s)" % (rel(args.out), info["html_size"], info["html_sha256"]))
        print("citations: %s (sha256 %s)" % (rel(info["citations"]), info["citations_sha256"]))
    if pub:
        for p, n, h in pub["files"]:
            print("publish: %s (%d bytes, sha256 %s)" % (rel(os.path.join(pub["dir"], p)), n, h))
        for u, h in pub["cdn"]:
            print("publish cdn: %s integrity %s" % (u, h))
    print("diagrams: %s" % ", ".join("%s (%d overlays, %d panel-only)" % (d["id"], len(d["overlay_elements"]),
                                                                        len(d["panel_only_elements"]))
                                     for d in citations["diagrams"]))
    print("mode: %s; source basis %s" % ("trace data from the .bpmn only" if m["trace_only"]
                                         else "findings + requirements merged", m["source_basis_date"]))
    for w in warnings:
        print("WARN %s" % w)
    return 0


def add_viewer_meta(args, citations):
    """Library versions and bundle hashes in meta (same values for the single-file and the publish variant)."""
    bjs = bundle_paths(args)
    bundle = read(os.path.join(bjs, "dist", "bpmn-navigated-viewer.production.min.js"))
    mm = read(minimap_paths()["js"])
    citations["meta"]["viewer"] = {"bpmn_js": BPMN_JS_VERSION, "bundle": "bpmn-navigated-viewer.production.min.js",
                                   "bundle_sha256": hashlib.sha256(bundle.encode("utf-8")).hexdigest(),
                                   "minimap": MINIMAP_VERSION, "minimap_bundle": "diagram-minimap.umd.prod.js",
                                   "minimap_bundle_sha256": hashlib.sha256(mm.encode("utf-8")).hexdigest()}


def write_page_and_citations(args, citations, bpmn_xml):
    cit_path = args.citations_out or os.path.join(os.path.dirname(os.path.abspath(args.out)), "citations.json")
    # bundle info goes into meta before both files are written (same content in both)
    add_viewer_meta(args, citations)
    write_page(args, citations, bpmn_xml)
    os.makedirs(os.path.dirname(os.path.abspath(cit_path)) or ".", exist_ok=True)
    with open(cit_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(citations, f, ensure_ascii=False, sort_keys=True, indent=1)
        f.write("\n")
    return {"html_size": os.path.getsize(args.out), "html_sha256": sha256_file(args.out),
            "citations": cit_path, "citations_sha256": sha256_file(cit_path)}


if __name__ == "__main__":
    sys.exit(main())
