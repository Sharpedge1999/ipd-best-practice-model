#!/usr/bin/env python3
"""B2 gate - runs spec2bpmn twice and checks the output independently of the layout code.

Usage:
    python -I tools/b2_gate.py --specs <dir> --out <file.bpmn> --models-out <dir>
        --log out/build_log.md --section "<name>" [--screens <dir>] [--no-render]

Checks (all on the written XML / DI, not on layout internals):
  G1 determinism     two consecutive runs, sha256 of every output file identical
  G2 moddle          bpmn-moddle import with the ipd extension: zero warnings; export and
                     re-import: object graph identical; ipd:trace identical (moddle level)
  G3 trace C14N      ipd:trace subtrees and documentation texts identical (canonical XML)
                     between the written file and the bpmn-moddle export
  G4 XSD             OMG BPMN 2.0 XSD (copy shipped with bpmn-moddle, sha256 logged)
  G5 DI complete     every participant, lane, flow node, sequence flow, message flow, data
                     reference, data association and group has exactly one DI element in the
                     diagram of its collaboration; no dangling DI; labels on named events,
                     gateways, data, flows
  G6 markers         isMarkerVisible="true" on every exclusive gateway shape
  G7 overlaps        no two flow node / data shapes overlap; labels overlap no shape or label;
                     nodes inside their lane; lanes / pools disjoint; groups do not cover
                     non-members; no edge passes through a non-endpoint shape or a foreign label;
                     edges orthogonal
                     edge end points dock on the outline of their source / target (no unrouted
                     edge); call activities >= 150 px wide and, in the bpmn-js render, >= 17 px
                     free between label text and shape bottom (W1 "Open L4" chip); LAY-02:
                     message flow ends on activities dock on the top or bottom edge, never a side;
                     bent message flows keep a straight first / last run of >= 20 px
  G8 clearance       >= 70 px free below every task, call activity, event, gateway (and data
                     element, message flow label) per the zone rule in build_log.md, inside
                     its lane / pool gap; activities with bottom message docks: 150 px zone aligned
                     away from the dock corridors; every zone in the report equals the rule zone
  smoke              bpmnlint recommended (V1 owns the full lint), headless render (bpmn-js)
The result is written between markers into --log; the rest of the log is kept.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from lxml import etree

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
XSD_DIR = ROOT / "vendor" / "node" / "node_modules" / "bpmn-moddle" / "resources" / "bpmn" / "xsd"
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "ipd": "urn:ipd-best-practice:trace:1.0",
}
BP = "{%s}" % NS["bpmn"]
FLOW_NODES = {"task", "callActivity", "startEvent", "endEvent", "intermediateCatchEvent",
              "intermediateThrowEvent", "exclusiveGateway", "parallelGateway", "inclusiveGateway"}
ACTIVITIES = {"task", "callActivity"}
EVENTS = {"startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent"}
GATEWAYS = {"exclusiveGateway", "parallelGateway", "inclusiveGateway"}
DATA_REFS = {"dataObjectReference", "dataStoreReference"}
EDGE_KINDS = {"sequenceFlow", "messageFlow", "dataInputAssociation", "dataOutputAssociation", "association"}

OVERLAY_W, OVERLAY_H = 150, 70
MSG_MIN_RUN = 20          # straight first / last run of a bent message flow
CALL_LABEL_FREE = 17      # W1 chip 15 px high + 2 px margin, below the call activity label text
ZONE_GAP_ACT, ZONE_GAP_LABEL, NO_LABEL_GAP = 6, 4, 8


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def local(el):
    return etree.QName(el).localname


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


# ------------------------------------------------------------------ geometry
def overlap(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def inside(a, outer, tol=0):
    return (a[0] >= outer[0] - tol and a[1] >= outer[1] - tol and a[0] + a[2] <= outer[0] + outer[2] + tol
            and a[1] + a[3] <= outer[1] + outer[3] + tol)


def seg_hits(p, q, r):
    x0, y0, x1, y1 = r[0], r[1], r[0] + r[2], r[1] + r[3]
    if p[1] == q[1]:
        a, b = sorted((p[0], q[0]))
        return y0 < p[1] < y1 and a < x1 and b > x0
    if p[0] == q[0]:
        a, b = sorted((p[1], q[1]))
        return x0 < p[0] < x1 and a < y1 and b > y0
    # diagonal: sample
    for k in range(1, 20):
        x = p[0] + (q[0] - p[0]) * k / 20.0
        y = p[1] + (q[1] - p[1]) * k / 20.0
        if x0 < x < x1 and y0 < y < y1:
            return True
    return False


def on_outline(p, r, tol=1):
    x, y = p
    x0, y0, x1, y1 = r[0], r[1], r[0] + r[2], r[1] + r[3]
    on_h = x0 - tol <= x <= x1 + tol and (abs(y - y0) <= tol or abs(y - y1) <= tol)
    on_v = y0 - tol <= y <= y1 + tol and (abs(x - x0) <= tol or abs(x - x1) <= tol)
    return on_h or on_v


def on_diamond(p, r, tol=1.5):
    cx, cy = r[0] + r[2] / 2.0, r[1] + r[3] / 2.0
    hw, hh = r[2] / 2.0, r[3] / 2.0
    d = abs(p[0] - cx) / hw + abs(p[1] - cy) / hh
    return abs(d - 1.0) * min(hw, hh) <= tol


def on_polyline(p, pts):
    for a, b in zip(pts, pts[1:]):
        if min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]):
            if a[0] == b[0] == p[0] or a[1] == b[1] == p[1]:
                return True
    return False


def docked(ref, p, shapes, edges, byid):
    """End point p of an edge lies on the outline of element ref."""
    el = byid.get(ref)
    if el is None:
        return False
    if local(el) == "sequenceFlow":
        return ref in edges and on_polyline(p, edges[ref])
    if ref not in shapes:
        return False
    r = shapes[ref][0]
    if local(el) in GATEWAYS:
        return on_diamond(p, r)
    if local(el) in EVENTS:
        cx, cy, rad = r[0] + r[2] / 2.0, r[1] + r[3] / 2.0, r[2] / 2.0
        return abs(((p[0] - cx) ** 2 + (p[1] - cy) ** 2) ** 0.5 - rad) <= 1.5
    return on_outline(p, r)


def bounds_of(el):
    b = el.find("dc:Bounds", NS)
    if b is None:
        return None
    return tuple(int(round(float(b.get(k)))) for k in ("x", "y", "width", "height"))


# ------------------------------------------------------------------ DI checks
def di_checks(xml_path, report_zones=None):
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    byid = {el.get("id"): el for el in root.iter() if isinstance(el.tag, str) and el.get("id")}
    errors, stats = [], {}
    diagrams = root.findall("bpmndi:BPMNDiagram", NS)
    collabs = root.findall("bpmn:collaboration", NS)
    plane_of = {}
    for dg in diagrams:
        pl = dg.find("bpmndi:BPMNPlane", NS)
        plane_of.setdefault(pl.get("bpmnElement"), []).append((dg, pl))
    per_diagram = []
    for c in collabs:
        cid = c.get("id")
        planes = plane_of.get(cid, [])
        if len(planes) != 1:
            errors.append(f"G5 {cid}: {len(planes)} diagrams reference this collaboration")
            continue
        dg, pl = planes[0]
        expected = {}     # id -> kind ('shape' | 'edge')
        lane_of, pool_of_node, members = {}, {}, {}
        node_kind = {}
        for part in c.findall("bpmn:participant", NS):
            expected[part.get("id")] = "shape"
            pref = part.get("processRef")
            if not pref:
                continue
            proc = byid.get(pref)
            if proc is None:
                errors.append(f"G5 {part.get('id')}: processRef {pref} missing")
                continue
            for lane in proc.iter(BP + "lane"):
                expected[lane.get("id")] = "shape"
                for ref in lane.findall("bpmn:flowNodeRef", NS):
                    lane_of[ref.text] = lane.get("id")
            for el in proc:
                k = local(el)
                if k in FLOW_NODES or k in DATA_REFS or k == "textAnnotation":
                    expected[el.get("id")] = "shape"
                    pool_of_node[el.get("id")] = part.get("id")
                    node_kind[el.get("id")] = k
                    for cv in el.findall("bpmn:categoryValueRef", NS):
                        members.setdefault(cv.text, set()).add(el.get("id"))
                    for a in el.findall("bpmn:dataInputAssociation", NS) + el.findall("bpmn:dataOutputAssociation", NS):
                        expected[a.get("id")] = "edge"
                elif k in ("sequenceFlow", "association"):
                    expected[el.get("id")] = "edge"
                elif k == "group":
                    expected[el.get("id")] = "shape"
        for mf in c.findall("bpmn:messageFlow", NS):
            expected[mf.get("id")] = "edge"
        groups = {}
        for g in c.findall("bpmn:group", NS):
            expected[g.get("id")] = "shape"
            groups[g.get("id")] = g.get("categoryValueRef")
        # DI elements
        di_count, shapes, edges, labels = {}, {}, {}, {}
        for d in pl:
            if not isinstance(d.tag, str):
                continue
            k = local(d)
            be = d.get("bpmnElement")
            di_count[be] = di_count.get(be, 0) + 1
            if be not in expected:
                errors.append(f"G5 {dg.get('id')}: DI {d.get('id')} references {be}, not an element of {cid}")
                continue
            want = expected[be]
            if (k == "BPMNShape") != (want == "shape"):
                errors.append(f"G5 {be}: DI kind {k} does not fit")
            if k == "BPMNShape":
                b = bounds_of(d)
                if b is None:
                    errors.append(f"G5 {be}: shape without bounds")
                    continue
                shapes[be] = (b, d)
            else:
                pts = [(int(round(float(w.get("x")))), int(round(float(w.get("y"))))) for w in d.findall("di:waypoint", NS)]
                if len(pts) < 2:
                    errors.append(f"G5 {be}: edge with {len(pts)} waypoints")
                edges[be] = pts
            lb = d.find("bpmndi:BPMNLabel", NS)
            if lb is not None:
                b = bounds_of(lb)
                if b is None:
                    errors.append(f"G5 {be}: BPMNLabel without bounds")
                else:
                    labels[be] = b
        missing = sorted(e for e in expected if di_count.get(e, 0) == 0)
        multi = sorted(e for e in expected if di_count.get(e, 0) > 1)
        for e in missing:
            errors.append(f"G5 {e}: no DI element")
        for e in multi:
            errors.append(f"G5 {e}: {di_count[e]} DI elements")
        # labels required on named events, gateways, data, flows
        for eid, kind in expected.items():
            el = byid.get(eid)
            if el is None:
                continue
            k = local(el)
            if el.get("name") and (k in EVENTS or k in GATEWAYS or k in DATA_REFS or k in ("sequenceFlow", "messageFlow")):
                if eid not in labels:
                    errors.append(f"G5 {eid}: named {k} without BPMNLabel bounds")
            if k in ("group",) and eid not in labels:
                errors.append(f"G5 {eid}: group without BPMNLabel bounds")
        # chip room (W1 "Open L4" tab right of the collapsed-marker): call activities >= 150 px wide
        for eid in expected:
            el = byid.get(eid)
            if el is not None and local(el) == "callActivity" and eid in shapes and shapes[eid][0][2] < 150:
                errors.append(f"G7 {eid}: call activity narrower than 150 px (no room for the Open L4 chip)")
        # G6 markers
        xor_total = xor_ok = 0
        for eid in expected:
            el = byid.get(eid)
            if el is not None and local(el) == "exclusiveGateway":
                xor_total += 1
                if eid in shapes and shapes[eid][1].get("isMarkerVisible") == "true":
                    xor_ok += 1
                else:
                    errors.append(f"G6 {eid}: isMarkerVisible missing")
        # G7 overlaps
        leaf = {e: shapes[e][0] for e in expected if e in node_kind and e in shapes}
        ov = 0
        ids = sorted(leaf)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                if overlap(leaf[a], leaf[b]):
                    ov += 1
                    errors.append(f"G7 shapes overlap: {a} / {b}")
        lab_ids = sorted(labels)
        for i, a in enumerate(lab_ids):
            for e in ids:
                if overlap(labels[a], leaf[e]):
                    ov += 1
                    errors.append(f"G7 label of {a} overlaps shape {e}")
            for b in lab_ids[i + 1:]:
                if overlap(labels[a], labels[b]):
                    ov += 1
                    errors.append(f"G7 labels overlap: {a} / {b}")
        parts = [p.get("id") for p in c.findall("bpmn:participant", NS)]
        for i, a in enumerate(parts):
            for b in parts[i + 1:]:
                if overlap(shapes[a][0], shapes[b][0]):
                    ov += 1
                    errors.append(f"G7 pools overlap: {a} / {b}")
        lanes_by_pool = {}
        for part in c.findall("bpmn:participant", NS):
            proc = byid.get(part.get("processRef") or "")
            if proc is None:
                continue
            ls = [l.get("id") for l in proc.iter(BP + "lane")]
            lanes_by_pool[part.get("id")] = ls
            for l in ls:
                if not inside(shapes[l][0], shapes[part.get("id")][0]):
                    errors.append(f"G7 lane {l} not inside pool")
            for i, a in enumerate(ls):
                for b in ls[i + 1:]:
                    if overlap(shapes[a][0], shapes[b][0]):
                        ov += 1
                        errors.append(f"G7 lanes overlap: {a} / {b}")
        container = {}
        for e in ids:
            cont = lane_of.get(e) or pool_of_node.get(e)
            if node_kind[e] in DATA_REFS or node_kind[e] == "textAnnotation":
                cont = pool_of_node.get(e)
            container[e] = cont
            if not inside(leaf[e], shapes[cont][0]):
                errors.append(f"G7 {e} not inside {cont}")
            if e in labels and not inside(labels[e], shapes[cont][0]):
                errors.append(f"G7 label of {e} not inside {cont}")
        # first associated element of data references and text annotations
        art_anchor = {}
        for eid in ids:
            if node_kind[eid] in DATA_REFS:
                for a in root.iter(BP + "dataOutputAssociation"):
                    if a.find("bpmn:targetRef", NS).text == eid:
                        art_anchor.setdefault(eid, a.getparent().get("id"))
                for a in root.iter(BP + "dataInputAssociation"):
                    if a.find("bpmn:sourceRef", NS).text == eid:
                        art_anchor.setdefault(eid, a.getparent().get("id"))
            elif node_kind[eid] == "textAnnotation":
                for a in root.iter(BP + "association"):
                    if a.get("targetRef") == eid:
                        ref = a.get("sourceRef")
                        el2 = byid.get(ref)
                        if el2 is not None and local(el2) == "sequenceFlow":
                            ref = el2.get("sourceRef")
                        art_anchor.setdefault(eid, ref)
        for gid, cv in groups.items():
            gb = shapes[gid][0]
            mem = members.get(cv, set())
            for e in ids:
                if e in mem or not overlap(gb, leaf[e]):
                    continue
                if (node_kind[e] in DATA_REFS or node_kind[e] == "textAnnotation") and art_anchor.get(e) in mem:
                    continue            # artifact attached to a member may sit inside the frame
                ov += 1
                errors.append(f"G7 group {gid} covers non-member {e}")
            for g2 in groups:
                if g2 > gid and overlap(gb, shapes[g2][0]):
                    errors.append(f"G7 groups overlap: {gid} / {g2}")
        # edges
        ends = {}
        for eid in edges:
            el = byid[eid]
            k = local(el)
            if k in ("dataInputAssociation", "dataOutputAssociation"):
                owner = el.getparent().get("id")
                if k == "dataInputAssociation":
                    ends[eid] = {el.find("bpmn:sourceRef", NS).text, owner}
                else:
                    ends[eid] = {owner, el.find("bpmn:targetRef", NS).text}
            else:
                ends[eid] = {el.get("sourceRef"), el.get("targetRef")}
        non_orth = through = through_label = 0
        segs_h, segs_v = [], []
        for eid, pts in edges.items():
            for p, q in zip(pts, pts[1:]):
                if p[0] != q[0] and p[1] != q[1]:
                    non_orth += 1
                    errors.append(f"G7 edge {eid}: diagonal segment {p}-{q}")
                (segs_h if p[1] == q[1] else segs_v).append((eid, p, q))
                for e in ids:
                    if e in ends[eid]:
                        continue
                    if seg_hits(p, q, leaf[e]):
                        through += 1
                        errors.append(f"G7 edge {eid} passes through {e}")
                for lid, lb in labels.items():
                    if lid == eid:
                        continue
                    if seg_hits(p, q, lb):
                        through_label += 1
                        errors.append(f"G7 edge {eid} passes through label of {lid}")
        # docking: first / last waypoint on the outline of the source / target (bounding box
        # side, or diamond edge for gateways; collapsed pools: pool border; association from
        # a sequence flow: a point of that flow) - catches unrouted (fallback) edges
        undocked = 0
        for eid, pts in edges.items():
            el = byid[eid]
            k = local(el)
            if k == "dataInputAssociation":
                src, tgt = el.find("bpmn:sourceRef", NS).text, el.getparent().get("id")
            elif k == "dataOutputAssociation":
                src, tgt = el.getparent().get("id"), el.find("bpmn:targetRef", NS).text
            else:
                src, tgt = el.get("sourceRef"), el.get("targetRef")
            for ref, p in ((src, pts[0]), (tgt, pts[-1])):
                if not docked(ref, p, shapes, edges, byid):
                    undocked += 1
                    errors.append(f"G7 edge {eid}: end point {p} not on the outline of {ref}")
        crossings = 0
        for (e1, p1, q1) in segs_h:
            xa, xb = sorted((p1[0], q1[0]))
            y = p1[1]
            for (e2, p2, q2) in segs_v:
                if e1 == e2:
                    continue
                ya, yb = sorted((p2[1], q2[1]))
                if xa < p2[0] < xb and ya < y < yb:
                    crossings += 1
        # LAY-02 docking: message flow ends on activities use the top or bottom edge (never a side)
        bottom_docks, side_docks, act_ends = {}, 0, 0
        for mf in c.findall("bpmn:messageFlow", NS):
            pts = edges.get(mf.get("id"))
            if not pts:
                continue
            for ref, p in ((mf.get("sourceRef"), pts[0]), (mf.get("targetRef"), pts[-1])):
                if node_kind.get(ref) not in ACTIVITIES:
                    continue
                act_ends += 1
                b = leaf[ref]
                if p[1] == b[1] + b[3] and b[0] < p[0] < b[0] + b[2]:
                    bottom_docks.setdefault(ref, []).append(p[0])
                elif not (p[1] == b[1] and b[0] < p[0] < b[0] + b[2]):
                    side_docks += 1
                    errors.append(f"G7 LAY-02 {mf.get('id')}: docks on a side edge of {ref} at {p} (use top / bottom)")
        # LAY-02: start circle and arrowhead of a message flow need a straight end run of >= 20 px
        for mf in c.findall("bpmn:messageFlow", NS):
            pts = edges.get(mf.get("id"))
            if pts and len(pts) > 2:
                runs = [abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(pts, pts[1:])]
                if min(runs[0], runs[-1]) < MSG_MIN_RUN:
                    errors.append(f"G7 LAY-02 {mf.get('id')}: end run {min(runs[0], runs[-1])} px (< {MSG_MIN_RUN})")
        # G8 clearance
        obstacles = []     # (rect, owner, what)
        for e in ids:
            obstacles.append((leaf[e], e, "shape"))
        for lid, lb in labels.items():
            obstacles.append((lb, lid, "label"))
        zones = []
        for e in ids:
            b = leaf[e]
            cx = b[0] + b[2] / 2.0
            zw = max(OVERLAY_W, b[2])
            if node_kind[e] == "textAnnotation":
                if byid[e].find(".//ipd:source", NS) is None:
                    continue                 # W1 overlays annotations only when they carry sources
                anchor = b[1] + b[3] + ZONE_GAP_ACT
            elif node_kind[e] in ACTIVITIES:
                anchor = b[1] + b[3] + ZONE_GAP_ACT
                if e in bottom_docks:
                    # bottom message docks: 150 px zone aligned away from the dock corridors
                    nl = sum(1 for x in bottom_docks[e] if x < cx)
                    nr = len(bottom_docks[e]) - nl
                    zw = OVERLAY_W
                    zones.append((e, (b[0] + nl * (b[2] - OVERLAY_W) // (nl + nr), anchor, zw), shapes[container[e]][0], True))
                    continue
            elif e in labels:
                anchor = labels[e][1] + labels[e][3] + ZONE_GAP_LABEL
            else:
                anchor = b[1] + b[3] + NO_LABEL_GAP
            zones.append((e, (cx - zw / 2.0, anchor, zw), shapes[container[e]][0], True))
        msg_ids = [mf.get("id") for mf in c.findall("bpmn:messageFlow", NS)]
        for m in msg_ids:
            if m in labels:
                lb = labels[m]
                zones.append((m, (lb[0], lb[1] + lb[3] + ZONE_GAP_LABEL, OVERLAY_W), None, False))
        if report_zones is not None:
            for zid, (zx, zy, zw), cont, is_node in zones:
                rz = report_zones.get(zid)
                if rz is None:
                    errors.append(f"G8 {zid}: no overlay zone in the report")
                elif abs(rz[0] - zx) > 1 or abs(rz[1] - zy) > 1 or rz[2] != zw or rz[3] != OVERLAY_H:
                    errors.append(f"G8 {zid}: report zone {rz} differs from the rule {[zx, zy, zw, OVERLAY_H]}")
        min_free, short = None, []
        pool_rects = [shapes[p][0] for p in parts]
        for zid, (zx, zy, zw), cont, is_node in zones:
            x0, x1 = zx, zx + zw
            limits = []
            if cont is not None:
                limits.append(cont[1] + cont[3])
                if x0 < cont[0] or x1 > cont[0] + cont[2]:
                    limits.append(zy)
            else:
                for pr in pool_rects:
                    if pr[0] < x1 and x0 < pr[0] + pr[2]:
                        if pr[1] >= zy:
                            limits.append(pr[1])
                        elif pr[1] + pr[3] > zy:
                            limits.append(zy)        # zone starts inside a pool: no gap
            for r, owner, what in obstacles:
                if owner == zid and what == "shape":
                    continue
                if r[0] < x1 and x0 < r[0] + r[2] and r[1] + r[3] > zy:
                    if owner == zid and what == "label" and r[1] + r[3] <= zy:
                        continue
                    limits.append(max(r[1], zy))
            for eid, p, q in segs_h:
                a, b2 = sorted((p[0], q[0]))
                if a < x1 and b2 > x0 and p[1] >= zy:
                    limits.append(p[1])
            for eid, p, q in segs_v:
                ya, yb = sorted((p[1], q[1]))
                if x0 < p[0] < x1 and yb > zy:
                    limits.append(max(ya, zy))
            free = min(limits) - zy if limits else 9999
            free = int(free)
            min_free = free if min_free is None else min(min_free, free)
            if free < OVERLAY_H:
                short.append(f"{zid}: {free} px")
                errors.append(f"G8 {zid}: only {free} px free below (need {OVERLAY_H})")
        allb = [shapes[p][0] for p in parts]
        per_diagram.append({
            "diagram": dg.get("id"),
            "size": f"{max(b[0] + b[2] for b in allb) + 20} x {max(b[1] + b[3] for b in allb) + 20}",
            "collaboration": cid,
            "semantic_elements_with_di": len(expected),
            "di_elements": sum(di_count.values()),
            "missing_di": len(missing),
            "duplicate_di": len(multi),
            "xor_gateways": xor_total,
            "xor_marker_visible": xor_ok,
            "overlaps": ov,
            "edges": len(edges),
            "edge_through_shape": through,
            "edge_through_label": through_label,
            "non_orthogonal_segments": non_orth,
            "edge_crossings": crossings,
            "undocked_edge_ends": undocked,
            "msg_activity_ends": act_ends,
            "msg_side_docks": side_docks,
            "msg_bottom_docks": sum(len(v) for v in bottom_docks.values()),
            "zones_checked": len(zones),
            "min_free_below_px": min_free,
            "zones_short": short,
        })
    stats["diagrams"] = per_diagram
    return errors, stats


def trace_c14n(orig, exported):
    """Compare ipd:trace subtrees and documentation texts (canonical XML)."""
    def collect(path):
        t = etree.parse(str(path))
        traces, docs = {}, {}
        for el in t.getroot().iter():
            if not isinstance(el.tag, str) or not el.get("id"):
                continue
            ext = el.find("bpmn:extensionElements", NS)
            if ext is not None:
                for tr in ext.findall("ipd:trace", NS):
                    traces.setdefault(el.get("id"), []).append(etree.tostring(tr, method="c14n"))
            ds = [d.text or "" for d in el.findall("bpmn:documentation", NS)]
            if ds:
                docs[el.get("id")] = ds
        return traces, docs
    t1, d1 = collect(orig)
    t2, d2 = collect(exported)
    diff_t = sorted(k for k in set(t1) | set(t2) if t1.get(k) != t2.get(k))
    diff_d = sorted(k for k in set(d1) | set(d2) if d1.get(k) != d2.get(k))
    return {"traces": len(t1), "traces_differing": diff_t, "documentation_elements": len(d1),
            "documentation_differing": diff_d}


def xsd_check(paths):
    schema = etree.XMLSchema(etree.parse(str(XSD_DIR / "BPMN20.xsd")))
    out = {}
    for p in paths:
        ok = schema.validate(etree.parse(str(p)))
        out[str(p)] = "valid" if ok else "; ".join(str(e) for e in list(schema.error_log)[:5])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--specs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--models-out", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--section", required=True)
    ap.add_argument("--screens", default=None)
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args(argv)
    out = Path(args.out)
    check_dir = out.parent / "check"
    check_dir.mkdir(parents=True, exist_ok=True)
    errors = []
    lines = []

    # G1 determinism
    conv = [sys.executable, "-I", str(TOOLS / "spec2bpmn.py"), "--specs", args.specs, "--out", args.out,
            "--models-out", args.models_out]
    hashes = []
    for k in range(2):
        rc, so, se = run(conv)
        if rc != 0:
            print(so + se)
            print("GATE FAIL: spec2bpmn failed")
            return 1
        rep = json.loads(out.with_suffix(".report.json").read_text(encoding="utf-8"))
        files = sorted(list(rep["outputs"]) + [str(out.with_suffix(".report.json"))])
        hashes.append({f: sha(f) for f in files})
    det_ok = hashes[0] == hashes[1]
    if not det_ok:
        errors.append("G1 outputs differ between two runs")
    report = rep
    bpmn_files = [args.out] + sorted(f for f in report["outputs"] if f != args.out)

    # G2 moddle + G3 C14N
    moddle = {}
    c14n = {}
    for f in bpmn_files:
        exp = check_dir / (Path(f).stem + ".moddle-export.bpmn")
        cmd = ["node", str(TOOLS / "moddle_check.mjs"), "--bpmn", f, "--export", str(exp)]
        if f == args.out:
            cmd.append("--lint")
        rc, so, se = run(cmd)
        try:
            res = json.loads(so)
        except ValueError:
            res = {"error": (so + se)[:500]}
        moddle[f] = res
        if rc != 0:
            errors.append(f"G2 moddle check failed for {f}")
        c14n[f] = trace_c14n(f, exp)
        if c14n[f]["traces_differing"] or c14n[f]["documentation_differing"]:
            errors.append(f"G3 trace/documentation differ after round trip in {f}")

    # G4 XSD
    xsd = xsd_check(bpmn_files)
    for f, v in xsd.items():
        if v != "valid":
            errors.append(f"G4 XSD: {f}: {v}")
    xsd_sha = {p.name: sha(p) for p in sorted(XSD_DIR.glob("*.xsd"))}

    # G5-G8
    report_zones = {}
    for m in report["models"]:
        report_zones.update(m.get("overlay_zones") or {})
    di_errors, di_stats = di_checks(args.out, report_zones)
    errors.extend(di_errors)
    per_model_di = {}
    for f in bpmn_files[1:]:
        e2, s2 = di_checks(f, report_zones)
        per_model_di[f] = len(e2)
        errors.extend(f"{Path(f).name}: {e}" for e in e2)

    # renders
    render = None
    if not args.no_render and args.screens:
        render = {}
        for zones in (False, True):
            cmd = ["node", str(TOOLS / "render_screens.mjs"), "--bpmn", args.out, "--out-dir", args.screens,
                   "--report", str(out.with_suffix(".report.json"))] + (["--zones"] if zones else [])
            rc, so, se = run(cmd)
            try:
                render["zones" if zones else "plain"] = json.loads(so)
            except ValueError:
                render["zones" if zones else "plain"] = {"error": (so + se)[:500]}
                errors.append("render failed")
        pl = render.get("plain", {})
        if pl.get("consoleErrors") or pl.get("importWarnings"):
            errors.append("render: console errors or import warnings")
        # call activities: rendered label text keeps >= CALL_LABEL_FREE px above the shape bottom
        for d in pl.get("diagrams", []):
            for cl in d.get("callLabels") or []:
                if cl.get("free") is None or cl["free"] < CALL_LABEL_FREE:
                    errors.append(f"G7 {cl['id']}: only {cl.get('free')} px free below the rendered label "
                                  f"(need {CALL_LABEL_FREE} for the Open L4 chip)")

    # ------------------------------------------------------------- log section
    L = lines.append
    L(f"### {args.section}")
    L("")
    L(f"Command: `python -I tools/spec2bpmn.py --specs {args.specs} --out {args.out} --models-out {args.models_out}`  ")
    L(f"Gate: `python -I tools/b2_gate.py --specs {args.specs} --out {args.out} --models-out {args.models_out} "
      f"--log {args.log} --section \"{args.section}\"" + (f" --screens {args.screens}" if args.screens else "") + "`")
    L("")
    L(f"Result: **{'PASS' if not errors else 'FAIL'}** ({len(errors)} error(s))")
    L("")
    L("Inputs: " + ", ".join(f"`{m['spec_file']}` ({m['model']}, sha256 `{m['spec_sha256'][:16]}...`)" for m in report["models"])
      + ("; skipped (not a spec): " + ", ".join(f"`{s}`" for s in report["skipped_files"]) if report["skipped_files"] else ""))
    L("")
    L("**G1 determinism** - two consecutive runs, sha256 per output file:")
    L("")
    L("| File | sha256 run 1 | run 2 identical |")
    L("|---|---|---|")
    for f in sorted(hashes[0]):
        L(f"| `{f}` | `{hashes[0][f]}` | {'yes' if hashes[0][f] == hashes[1].get(f) else 'NO'} |")
    L("")
    L("**G2 bpmn-moddle** (bpmn-moddle with `contracts/ipd_moddle.json`; export + re-import):")
    L("")
    L("| File | import warnings | re-import warnings | graph lossless | ipd:trace lossless | traces (moddle / XML) | ipd:source (moddle / XML) |")
    L("|---|---|---|---|---|---|---|")
    for f, r in moddle.items():
        if "error" in r:
            L(f"| `{f}` | ERROR | | | | | |")
            continue
        L(f"| `{f}` | {len(r['import_warnings'])} | {len(r['reimport_warnings'])} | {r['graph_lossless']} | "
          f"{r['trace_lossless']} | {r['trace_count']} / {r['trace_count_in_xml']} | {r['source_count']} / {r['source_count_in_xml']} |")
    L("")
    L("**G3 ipd:trace C14N** (canonical XML of every `ipd:trace` and all `bpmn:documentation` texts, written file vs bpmn-moddle export):")
    L("")
    for f, r in c14n.items():
        L(f"- `{f}`: {r['traces']} traces, {len(r['traces_differing'])} differing; "
          f"{r['documentation_elements']} documented elements, {len(r['documentation_differing'])} differing")
    L("")
    L("**G4 XSD** (OMG BPMN 2.0 XSD set from `vendor/node/node_modules/bpmn-moddle/resources/bpmn/xsd/`, origin "
      "github.com/bpmn-io/bpmn-moddle; sha256 " + ", ".join(f"{k} `{v[:12]}...`" for k, v in xsd_sha.items()) + "):")
    L("")
    for f, v in xsd.items():
        L(f"- `{f}`: {v}")
    L("")
    L("**G5-G8 DI, markers, overlaps, clearance** (combined file; per-model files re-checked: "
      + ", ".join(f"`{Path(f).name}` {n} errors" for f, n in per_model_di.items()) + "):")
    L("")
    call_free = {}
    if render is not None:
        for d in render.get("plain", {}).get("diagrams", []):
            vals = [c["free"] for c in d.get("callLabels") or [] if c.get("free") is not None]
            call_free[d["diagram"]] = (len(d.get("callLabels") or []), min(vals) if vals else None)
    L("| Diagram | size (px) | elements with DI | DI elements | missing | duplicate | XOR / marker visible | overlaps | edge through shape / label | diagonal segments | undocked edge ends | message flow ends on activities: side / bottom / all | edge crossings | zones checked | min free below (px) | call activities / min px below label (render) |")
    L("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for d in di_stats["diagrams"]:
        n, mn = call_free.get(d["diagram"], (None, None))
        cf = "not rendered" if n is None else (f"{n} / {mn}" if n else "0 / -")
        L(f"| `{d['diagram']}` | {d['size']} | {d['semantic_elements_with_di']} | {d['di_elements']} | {d['missing_di']} | {d['duplicate_di']} | "
          f"{d['xor_gateways']} / {d['xor_marker_visible']} | {d['overlaps']} | {d['edge_through_shape']} / {d['edge_through_label']} | "
          f"{d['non_orthogonal_segments']} | {d['undocked_edge_ends']} | {d['msg_side_docks']} / {d['msg_bottom_docks']} / {d['msg_activity_ends']} | {d['edge_crossings']} | {d['zones_checked']} | {d['min_free_below_px']} | {cf} |")
    L("")
    lint = moddle.get(args.out, {}).get("bpmnlint_recommended")
    L("**Smoke: bpmnlint recommended** (combined file; V1 owns the full lint): "
      + ("no findings" if lint == {} else ("; ".join(f"{k}: {len(v)}" for k, v in (lint or {}).items()) or "not run")))
    if lint:
        for k, v in lint.items():
            for item in v:
                L(f"  - {k}: {item}")
    L("")
    if render is not None:
        pl = render.get("plain", {})
        L("**Smoke: headless render** (bpmn-js NavigatedViewer, Chrome headless, offline): "
          f"{len(pl.get('diagrams', []))} diagrams, import warnings {len(pl.get('importWarnings', []) or [])}, "
          f"console errors {len(pl.get('consoleErrors', []) or [])}. PNGs: "
          + ", ".join(f"`{d['file']}`" for k in ("plain", "zones") for d in render.get(k, {}).get("diagrams", [])))
        L("")
    if report.get("warnings"):
        L("Converter warnings:")
        L("")
        for w in report["warnings"]:
            L(f"- {w}")
        L("")
    if report.get("notes"):
        for n in report["notes"]:
            L(f"Note: {n}")
        L("")
    if errors:
        L("Errors:")
        L("")
        for e in errors[:200]:
            L(f"- {e}")
        L("")
    section = "\n".join(lines)
    log = Path(args.log)
    begin = f"<!-- BEGIN GATE: {args.section} -->"
    end = f"<!-- END GATE: {args.section} -->"
    text = log.read_text(encoding="utf-8") if log.exists() else "# B2 build log\n\n"
    block = f"{begin}\n{section}\n{end}"
    if begin in text and end in text:
        pre = text.split(begin)[0]
        post = text.split(end, 1)[1]
        text = pre + block + post
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    log.write_text(text, encoding="utf-8")
    print(section)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
