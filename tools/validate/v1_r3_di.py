#!/usr/bin/env python3
"""V1 round 3: DI measurements on out/ipd_best_practice.bpmn for LAY-02 (review evidence, read-only).

1. Docking: for every message-flow end on an activity or event, which side of the shape the end waypoint touches
   (top/bottom = 90 degrees to the left-to-right main flow; left/right = side dock).
2. Parallel runs: message-flow segment parallel to a sequence-flow segment, gap < 10 px, overlap > 20 px.
3. Crossings: message flow x sequence flow segment crossings per diagram.
Usage: python -I tools/validate/v1_r3_di.py <file.bpmn> [--out x.json]
"""
import json
import sys
from collections import defaultdict

from lxml import etree

NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL", "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
      "dc": "http://www.omg.org/spec/DD/20100524/DC", "di": "http://www.omg.org/spec/DD/20100524/DI"}
NODE_TAGS = {"task", "callActivity", "startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent"}


def main():
    path = sys.argv[1]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    root = etree.parse(path).getroot()
    kind = {}
    for el in root.iter():
        if isinstance(el.tag, str) and el.get("id"):
            kind[el.get("id")] = etree.QName(el).localname
    mf_ends = {}
    for mf in root.iter("{%s}messageFlow" % NS["bpmn"]):
        mf_ends[mf.get("id")] = (mf.get("sourceRef"), mf.get("targetRef"))
    res = dict(docking=defaultdict(list), side_docks=[], parallel=[], crossings=defaultdict(int), n_ends=0)
    for d in root.findall("bpmndi:BPMNDiagram", NS):
        did = d.get("id")
        shapes, edges = {}, {}
        for s in d.iter("{%s}BPMNShape" % NS["bpmndi"]):
            b = s.find("dc:Bounds", NS)
            shapes[s.get("bpmnElement")] = tuple(float(b.get(k)) for k in ("x", "y", "width", "height"))
        for e in d.iter("{%s}BPMNEdge" % NS["bpmndi"]):
            edges[e.get("bpmnElement")] = [(float(w.get("x")), float(w.get("y"))) for w in e.findall("di:waypoint", NS)]
        for mid, (src, tgt) in mf_ends.items():
            if mid not in edges:
                continue
            wp = edges[mid]
            for end, ref in ((wp[0], src), (wp[-1], tgt)):
                if kind.get(ref) not in NODE_TAGS or ref not in shapes:
                    continue
                x, y, w, h = shapes[ref]
                ex, ey = end
                if kind[ref] in ("startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent"):
                    cx, cy = x + w / 2, y + h / 2
                    side = "top" if ey < cy - h / 4 else "bottom" if ey > cy + h / 4 else ("left" if ex < cx else "right")
                else:
                    dist = dict(top=abs(ey - y), bottom=abs(ey - (y + h)), left=abs(ex - x), right=abs(ex - (x + w)))
                    side = min(dist, key=dist.get)
                res["n_ends"] += 1
                res["docking"][side].append("%s %s@%s" % (did, mid, ref))
                if side in ("left", "right"):
                    res["side_docks"].append("%s %s end on %s (%s side)" % (did, mid, ref, side))
        seqs = {i: w for i, w in edges.items() if kind.get(i) == "sequenceFlow"}
        msgs = {i: w for i, w in edges.items() if kind.get(i) == "messageFlow"}

        def segs(w):
            return list(zip(w, w[1:]))
        for mi, mw in msgs.items():
            for si, sw in seqs.items():
                for (a, b) in segs(mw):
                    for (c, e) in segs(sw):
                        if abs(a[1] - b[1]) < 0.5 and abs(c[1] - e[1]) < 0.5:
                            ov = min(max(a[0], b[0]), max(c[0], e[0])) - max(min(a[0], b[0]), min(c[0], e[0]))
                            gap = abs(a[1] - c[1])
                            if ov > 20 and gap < 10:
                                res["parallel"].append("%s %s || %s horizontal, gap %.0f px over %.0f px" % (did, mi, si, gap, ov))
                        elif abs(a[0] - b[0]) < 0.5 and abs(c[0] - e[0]) < 0.5:
                            ov = min(max(a[1], b[1]), max(c[1], e[1])) - max(min(a[1], b[1]), min(c[1], e[1]))
                            gap = abs(a[0] - c[0])
                            if ov > 20 and gap < 10:
                                res["parallel"].append("%s %s || %s vertical, gap %.0f px over %.0f px" % (did, mi, si, gap, ov))
                        # proper crossing of a horizontal and a vertical segment
                        for (p, q), (r, s) in (((a, b), (c, e)), ((c, e), (a, b))):
                            if abs(p[1] - q[1]) < 0.5 and abs(r[0] - s[0]) < 0.5:
                                if min(p[0], q[0]) < r[0] < max(p[0], q[0]) and min(r[1], s[1]) < p[1] < max(r[1], s[1]):
                                    res["crossings"][did] += 1
    res["docking"] = {k: len(v) for k, v in res["docking"].items()}
    res["crossings"] = dict(res["crossings"])
    print(json.dumps(res, indent=1))
    if out:
        json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
