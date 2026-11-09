#!/usr/bin/env python3
"""Write the ipd:trace of every element of a BPMN file as JSON (input for v1_render.mjs expectations).

Usage: python -I tools/validate/v1_expected_traces.py <file.bpmn> <out.json>
"""
import json
import sys

from lxml import etree

NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL", "ipd": "urn:ipd-best-practice:trace:1.0",
      "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI"}
root = etree.parse(sys.argv[1]).getroot()
out = {"traced": {}, "diagrams": []}
for tr in root.iter("{%s}trace" % NS["ipd"]):
    el = tr.getparent().getparent()
    out["traced"][el.get("id")] = dict(
        tag=etree.QName(el).localname,
        sources=[dict(key=s.get("key"), loc=s.get("loc"), page=s.get("page") or "") for s in tr.findall("ipd:source", NS)],
        reqs=[r.get("id") for r in tr.findall("ipd:req", NS)],
        verify=len(tr.findall("ipd:verify", NS)),
        binding=tr.get("binding") or "",
        draft=tr.get("draft") == "true")
for d in root.findall("bpmndi:BPMNDiagram", NS):
    out["diagrams"].append(dict(id=d.get("id"), collab=d.find("bpmndi:BPMNPlane", NS).get("bpmnElement")))
json.dump(out, open(sys.argv[2], "w"), indent=1)
print("%d traced elements, %d diagrams" % (len(out["traced"]), len(out["diagrams"])))
