#!/usr/bin/env python3
"""W1 self-test model: a small, deterministic extension of the B2 fixture output for viewer tests.

NOT MODEL CONTENT. Reads out/fixture/ipd_fixture.bpmn + .report.json (unchanged) and writes
out/w1_selftest/w1_selftest.bpmn + .report.json with:
  - L3_A3 without calledElement: interface placeholder (decisions.md S0-18) -> no drill-down
  - L4_01_A1 (binding-ICH) also cites REQ-902 (draft guidance in requirements_test.yaml) -> ICH + DRAFT
  - L4_01_A4 (binding-ICH) with draft="true" on ipd:trace -> ICH + DRAFT in trace-only mode too
  - L4_01_A3 with ipd:trace record and party attributes (S0-17)
  - text annotations: L4_01_T1 (no sources, association to L4_01_G2), L4_01_T2 (with a source, own zone)
and out/w1_selftest/requirements_test.yaml (synthetic REQs for the merged code path) with the REQ field
modal: REQ-901 must, REQ-902 may, REQ-903 should, REQ-905 without modal (fallback). REQ-902 is the only
REQ of L3_A2 and L4_01_A2 -> MAY chip; L4_01_A1 (REQ-901 + REQ-902) is mixed -> no MAY chip.
Usage: python -I tools/make_w1_selftest.py [--src-dir out/fixture] [--out-dir out/w1_selftest]
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


REQUIREMENTS_TEST = """# W1 SELF-TEST INPUT - NOT PROJECT CONTENT. Written by tools/make_w1_selftest.py. Synthetic requirements for
# the merged code path of tools/build_viewer.py (findings = fixtures/R9_sample.yaml). Statements start with "TEST - ".
# REQ-905 cites R9-099, which does not exist on purpose (missing-finding display).
# modal: REQ-902 may (MAY chip on L3_A2 and L4_01_A2); REQ-905 has no modal on purpose (fallback display).
requirements:
  - id: REQ-901
    statement: "TEST - sponsor classifies each protocol deviation against the trial-specific iPD definition."
    binding: binding-ICH
    modal: must
    jurisdiction: [ICH]
    party: sponsor
    deadline: none
    record: "TEST - deviation log entry"
    findings: [R9-001, R9-002, R9-003, R9-007]
  - id: REQ-902
    statement: "TEST - sponsor assesses impact (draft guidance)."
    binding: guidance
    modal: may
    draft: true
    jurisdiction: [US]
    party: sponsor
    findings: [R9-006]
  - id: REQ-905
    statement: "TEST - sponsor notifies the authority."
    binding: binding-law
    jurisdiction: EU
    party: sponsor
    deadline: "xx days (TEST)"
    findings: [R9-004, R9-099]
    verify: ["[verify] TEST - deadline wording"]
  - id: REQ-903
    statement: "TEST - hand-off to the neighbouring process at the interface placeholder."
    binding: binding-ICH
    modal: should
    jurisdiction: [ICH]
    party_norm: sponsor
    trigger: "TEST - deviations ready for reporting"
    action: "TEST - hand over to the neighbouring process"
    recipient: "TEST - neighbouring process owner"
    binding_route: "EU: TEST; US: TEST"
    status: interface
    findings: [R9-003]
"""


def once(s, old, new):
    if s.count(old) != 1:
        raise SystemExit("ERROR: expected exactly one %r (found %d)" % (old[:70], s.count(old)))
    return s.replace(old, new)


def in_block(s, start_tag_prefix, end_tag, old, new):
    i = s.index(start_tag_prefix)
    j = s.index(end_tag, i) + len(end_tag)
    block = s[i:j]
    if block.count(old) != 1:
        raise SystemExit("ERROR: %r not unique in block %s" % (old, start_tag_prefix))
    return s[:i] + block.replace(old, new) + s[j:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-dir", default=os.path.join(ROOT, "out", "fixture"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "out", "w1_selftest"))
    a = ap.parse_args()
    x = open(os.path.join(a.src_dir, "ipd_fixture.bpmn"), encoding="utf-8").read()
    rep = json.load(open(os.path.join(a.src_dir, "ipd_fixture.report.json"), encoding="utf-8"))

    x = once(x, ' calledElement="L4_03_P_SPON_PROCESS"', "")
    x = in_block(x, '<bpmn:task id="L4_01_A1"', "</bpmn:task>",
                 '<ipd:req id="REQ-901"/>', '<ipd:req id="REQ-901"/>\n          <ipd:req id="REQ-902"/>')
    x = in_block(x, '<bpmn:task id="L4_01_A4"', "</bpmn:task>",
                 '<ipd:trace binding="binding-ICH" jurisdiction="ICH">',
                 '<ipd:trace binding="binding-ICH" jurisdiction="ICH" draft="true">')
    x = in_block(x, '<bpmn:task id="L4_01_A3"', "</bpmn:task>",
                 'deadline="xx days (FIXTURE)">',
                 'deadline="xx days (FIXTURE)" record="SELFTEST - notification record" party="SELFTEST - sponsor">')
    art = '''    <bpmn:textAnnotation id="L4_01_T1">
      <bpmn:text>SELFTEST - annotation without sources</bpmn:text>
    </bpmn:textAnnotation>
    <bpmn:textAnnotation id="L4_01_T2">
      <bpmn:documentation textFormat="text/plain">Sources: E6R3 FIXTURE</bpmn:documentation>
      <bpmn:extensionElements>
        <ipd:trace>
          <ipd:source key="E6R3" loc="FIXTURE"/>
        </ipd:trace>
      </bpmn:extensionElements>
      <bpmn:text>SELFTEST - annotation with a source</bpmn:text>
    </bpmn:textAnnotation>
    <bpmn:association id="L4_01_T1_G2_ASSOC" sourceRef="L4_01_T1" targetRef="L4_01_G2"/>
'''
    i = x.index('<bpmn:process id="L4_01_P_SPON_PROCESS"')
    j = x.index("</bpmn:process>", i)
    x = x[:j] + art.lstrip(" ") + "  " + x[j:]
    di = '''      <bpmndi:BPMNShape id="L4_01_T1_di" bpmnElement="L4_01_T1">
        <dc:Bounds x="700" y="1150" width="200" height="50"/>
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="L4_01_T2_di" bpmnElement="L4_01_T2">
        <dc:Bounds x="300" y="1060" width="200" height="50"/>
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="L4_01_T1_G2_ASSOC_di" bpmnElement="L4_01_T1_G2_ASSOC">
        <di:waypoint x="900" y="1175"/>
        <di:waypoint x="1060" y="1285"/>
      </bpmndi:BPMNEdge>
'''
    k = x.index('<bpmndi:BPMNPlane id="L4_01_PLANE"')
    m = x.index("</bpmndi:BPMNPlane>", k)
    x = x[:m] + di.lstrip(" ") + "    " + x[m:]
    x = x.replace('exporter="ipd spec2bpmn"', 'exporter="ipd W1 selftest (from spec2bpmn fixture)"')

    for mdl in rep["models"]:
        if mdl["model"] == "L4-01":
            mdl["overlay_zones"]["L4_01_T2"] = [300, 1116, 200, 70]
            mdl["overlay_zones"] = dict(sorted(mdl["overlay_zones"].items()))
    rep["notes"] = rep.get("notes", []) + ["W1 SELFTEST copy - not model content (tools/make_w1_selftest.py)"]
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "w1_selftest.bpmn"), "w", encoding="utf-8", newline="\n") as f:
        f.write(x)
    with open(os.path.join(a.out_dir, "w1_selftest.report.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(rep, f, indent=2, sort_keys=False)
        f.write("\n")
    with open(os.path.join(a.out_dir, "requirements_test.yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(REQUIREMENTS_TEST)
    print("wrote %s/w1_selftest.bpmn, .report.json and requirements_test.yaml" % os.path.relpath(a.out_dir, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
