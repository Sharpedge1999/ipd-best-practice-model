# B2 build log

<!-- BEGIN GATE: B2 selftest -->
### B2 selftest

Command: `python -I tools/spec2bpmn.py --specs out/b2_selftest/specs --out out/b2_selftest/selftest.bpmn --models-out out/b2_selftest/models`  
Gate: `python -I tools/b2_gate.py --specs out/b2_selftest/specs --out out/b2_selftest/selftest.bpmn --models-out out/b2_selftest/models --log out/b2_selftest/gate.md --section "B2 selftest" --screens out/b2_selftest/screens`

Result: **PASS** (0 error(s))

Inputs: `L3.yaml` (L3, sha256 `a94c9a79bfd91863...`), `L4-01.yaml` (L4-01, sha256 `0681970f7d722342...`)

**G1 determinism** - two consecutive runs, sha256 per output file:

| File | sha256 run 1 | run 2 identical |
|---|---|---|
| `out/b2_selftest/models/L3.bpmn` | `53c8a68df239a4d154ec733b03695f3da0b0a784de50851a0e12ef65afe10f94` | yes |
| `out/b2_selftest/models/L4-01.bpmn` | `5a231b402015933e93d0ace86e31fe39bd6eedeb000ac0c78083cab1c6d46ba0` | yes |
| `out/b2_selftest/selftest.bpmn` | `144518e917f4fbb4336f7675e55dcda4a33906b73e36835c15617b7eb8a09243` | yes |
| `out/b2_selftest/selftest.report.json` | `ca76da491fc6234984de509b3a155b283144d3086e8185931448a5039e914e64` | yes |

**G2 bpmn-moddle** (bpmn-moddle with `contracts/ipd_moddle.json`; export + re-import):

| File | import warnings | re-import warnings | graph lossless | ipd:trace lossless | traces (moddle / XML) | ipd:source (moddle / XML) |
|---|---|---|---|---|---|---|
| `out/b2_selftest/selftest.bpmn` | 0 | 0 | True | True | 35 / 35 | 36 / 36 |
| `out/b2_selftest/models/L3.bpmn` | 0 | 0 | True | True | 14 / 14 | 14 / 14 |
| `out/b2_selftest/models/L4-01.bpmn` | 0 | 0 | True | True | 21 / 21 | 22 / 22 |

**G3 ipd:trace C14N** (canonical XML of every `ipd:trace` and all `bpmn:documentation` texts, written file vs bpmn-moddle export):

- `out/b2_selftest/selftest.bpmn`: 35 traces, 0 differing; 38 documented elements, 0 differing
- `out/b2_selftest/models/L3.bpmn`: 14 traces, 0 differing; 15 documented elements, 0 differing
- `out/b2_selftest/models/L4-01.bpmn`: 21 traces, 0 differing; 23 documented elements, 0 differing

**G4 XSD** (OMG BPMN 2.0 XSD set from `vendor/node/node_modules/bpmn-moddle/resources/bpmn/xsd/`, origin github.com/bpmn-io/bpmn-moddle; sha256 BPMN20.xsd `4c5e3d2c8e14...`, BPMNDI.xsd `1bfaab6a1e3b...`, DC.xsd `b325cd3c0d03...`, DI.xsd `62fa0d89138a...`, Semantic.xsd `aa37542753e4...`):

- `out/b2_selftest/selftest.bpmn`: valid
- `out/b2_selftest/models/L3.bpmn`: valid
- `out/b2_selftest/models/L4-01.bpmn`: valid

**G5-G8 DI, markers, overlaps, clearance** (combined file; per-model files re-checked: `L3.bpmn` 0 errors, `L4-01.bpmn` 0 errors):

| Diagram | size (px) | elements with DI | DI elements | missing | duplicate | XOR / marker visible | overlaps | edge through shape / label | diagonal segments | edge crossings | zones checked | min free below (px) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `L3_DIAGRAM` | 2166 x 1407 | 37 | 37 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 1 | 18 | 80 |
| `L4_01_DIAGRAM` | 4056 x 1812 | 79 | 79 | 0 | 0 | 7 / 7 | 0 | 0 / 0 | 0 | 12 | 36 | 78 |

**Smoke: bpmnlint recommended** (combined file; V1 owns the full lint): no findings

**Smoke: headless render** (bpmn-js NavigatedViewer, Chrome headless, offline): 2 diagrams, import warnings 0, console errors 0. PNGs: `out/b2_selftest/screens/L3_DIAGRAM.png`, `out/b2_selftest/screens/L4_01_DIAGRAM.png`, `out/b2_selftest/screens/L3_DIAGRAM_zones.png`, `out/b2_selftest/screens/L4_01_DIAGRAM_zones.png`

Converter warnings:

- L3 A2: called model L4-02 not in the spec set; calledElement set to L4_02_P_SPON_PROCESS by convention
- L3 A3: called model L4-03 not in the spec set; calledElement set to L4_03_P_SPON_PROCESS by convention
- L3 A4: called model L4-04 not in the spec set; calledElement set to L4_04_P_SPON_PROCESS by convention
- L3 A5: called model L4-05 not in the spec set; calledElement set to L4_05_P_SPON_PROCESS by convention
- L3 A6: called model L4-06 not in the spec set; calledElement set to L4_06_P_SPON_PROCESS by convention

Note: Per-model files are self-contained (own collaboration, processes, diagram). L3.bpmn keeps calledElement on its call activities, but the called L4 processes are only in the combined file and in the L4 files.

<!-- END GATE: B2 selftest -->
