# B2 build log

<!-- BEGIN GATE: B2 snapshot -->
### B2 snapshot

Command: `python -I tools/spec2bpmn.py --specs /tmp/b2_snapshot_spec --out out/snapshot/snapshot.bpmn --models-out out/snapshot/models`  
Gate: `python -I tools/b2_gate.py --specs /tmp/b2_snapshot_spec --out out/snapshot/snapshot.bpmn --models-out out/snapshot/models --log out/snapshot/gate.md --section "B2 snapshot" --screens out/snapshot/screens`

Result: **PASS** (0 error(s))

Inputs: `L3.yaml` (L3, sha256 `61f0b3108a19fe57...`), `L4-01.yaml` (L4-01, sha256 `991e32ab8df67656...`), `L4-02.yaml` (L4-02, sha256 `8e897933f8338aa0...`), `L4-03.yaml` (L4-03, sha256 `fe9860b44da8f6af...`), `L4-04.yaml` (L4-04, sha256 `28c62355470cc924...`), `L4-05.yaml` (L4-05, sha256 `b13cc917ad9ba0f1...`), `L4-06.yaml` (L4-06, sha256 `7249eb28129acb4e...`), `L4-07.yaml` (L4-07, sha256 `a6ec16cfcac2abe4...`), `L4-08.yaml` (L4-08, sha256 `a5f90f9c32330833...`)

**G1 determinism** - two consecutive runs, sha256 per output file:

| File | sha256 run 1 | run 2 identical |
|---|---|---|
| `out/snapshot/models/L3.bpmn` | `5880f7f0fad989961f6225ffa95bea4125edde0322d5ba45d9f0ad3a1236f810` | yes |
| `out/snapshot/models/L4-01.bpmn` | `dece0f092b845b5041ee41165a7b8efb7cadb195fa49a75b3f83b52133e919ed` | yes |
| `out/snapshot/models/L4-02.bpmn` | `8f9d7a2b6b67fb3bc9fa1cae568ebd2b94cf6968cf57056bb5c7b7a876dadcea` | yes |
| `out/snapshot/models/L4-03.bpmn` | `05b24461ea35dc061e910184a8fb5229f93153f2ffffaf0832656888c61e6109` | yes |
| `out/snapshot/models/L4-04.bpmn` | `ca6c2cc6266c17d24c7aecf39e177012eddcb3bb10452dc7b649653c953a4815` | yes |
| `out/snapshot/models/L4-05.bpmn` | `a3dedd2eec3ba338ec7c98dbae80ab55226417c91d48f1ff999a95124346886c` | yes |
| `out/snapshot/models/L4-06.bpmn` | `0b28a1afef9b379c9dfc36f5c5e268fba9aacc806948eb972a9f4c50949e4a42` | yes |
| `out/snapshot/models/L4-07.bpmn` | `626d1ef01348cdeeaa72adb50fd953d465c72de719350257e6135c1a244b8dd6` | yes |
| `out/snapshot/models/L4-08.bpmn` | `abd09290c940d0b1b7b2d47cde4b7fff06e05e5381bbae978eca2f013530d755` | yes |
| `out/snapshot/snapshot.bpmn` | `85736fea3f9bb8cb712044f6a159d1890ee57ec1ffccb3ecb323a951805ef1f4` | yes |
| `out/snapshot/snapshot.report.json` | `19467512d69e0a6197708480e7fffc9ee997f34337d14e25a4680688dbab5e3b` | yes |

**G2 bpmn-moddle** (bpmn-moddle with `contracts/ipd_moddle.json`; export + re-import):

| File | import warnings | re-import warnings | graph lossless | ipd:trace lossless | traces (moddle / XML) | ipd:source (moddle / XML) |
|---|---|---|---|---|---|---|
| `out/snapshot/snapshot.bpmn` | 0 | 0 | True | True | 221 / 221 | 1028 / 1028 |
| `out/snapshot/models/L3.bpmn` | 0 | 0 | True | True | 25 / 25 | 327 / 327 |
| `out/snapshot/models/L4-01.bpmn` | 0 | 0 | True | True | 24 / 24 | 127 / 127 |
| `out/snapshot/models/L4-02.bpmn` | 0 | 0 | True | True | 30 / 30 | 98 / 98 |
| `out/snapshot/models/L4-03.bpmn` | 0 | 0 | True | True | 27 / 27 | 76 / 76 |
| `out/snapshot/models/L4-04.bpmn` | 0 | 0 | True | True | 21 / 21 | 74 / 74 |
| `out/snapshot/models/L4-05.bpmn` | 0 | 0 | True | True | 29 / 29 | 98 / 98 |
| `out/snapshot/models/L4-06.bpmn` | 0 | 0 | True | True | 29 / 29 | 79 / 79 |
| `out/snapshot/models/L4-07.bpmn` | 0 | 0 | True | True | 20 / 20 | 86 / 86 |
| `out/snapshot/models/L4-08.bpmn` | 0 | 0 | True | True | 16 / 16 | 63 / 63 |

**G3 ipd:trace C14N** (canonical XML of every `ipd:trace` and all `bpmn:documentation` texts, written file vs bpmn-moddle export):

- `out/snapshot/snapshot.bpmn`: 221 traces, 0 differing; 243 documented elements, 0 differing
- `out/snapshot/models/L3.bpmn`: 25 traces, 0 differing; 27 documented elements, 0 differing
- `out/snapshot/models/L4-01.bpmn`: 24 traces, 0 differing; 26 documented elements, 0 differing
- `out/snapshot/models/L4-02.bpmn`: 30 traces, 0 differing; 34 documented elements, 0 differing
- `out/snapshot/models/L4-03.bpmn`: 27 traces, 0 differing; 30 documented elements, 0 differing
- `out/snapshot/models/L4-04.bpmn`: 21 traces, 0 differing; 23 documented elements, 0 differing
- `out/snapshot/models/L4-05.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `out/snapshot/models/L4-06.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `out/snapshot/models/L4-07.bpmn`: 20 traces, 0 differing; 22 documented elements, 0 differing
- `out/snapshot/models/L4-08.bpmn`: 16 traces, 0 differing; 19 documented elements, 0 differing

**G4 XSD** (OMG BPMN 2.0 XSD set from `vendor/node/node_modules/bpmn-moddle/resources/bpmn/xsd/`, origin github.com/bpmn-io/bpmn-moddle; sha256 BPMN20.xsd `4c5e3d2c8e14...`, BPMNDI.xsd `1bfaab6a1e3b...`, DC.xsd `b325cd3c0d03...`, DI.xsd `62fa0d89138a...`, Semantic.xsd `aa37542753e4...`):

- `out/snapshot/snapshot.bpmn`: valid
- `out/snapshot/models/L3.bpmn`: valid
- `out/snapshot/models/L4-01.bpmn`: valid
- `out/snapshot/models/L4-02.bpmn`: valid
- `out/snapshot/models/L4-03.bpmn`: valid
- `out/snapshot/models/L4-04.bpmn`: valid
- `out/snapshot/models/L4-05.bpmn`: valid
- `out/snapshot/models/L4-06.bpmn`: valid
- `out/snapshot/models/L4-07.bpmn`: valid
- `out/snapshot/models/L4-08.bpmn`: valid

**G5-G8 DI, markers, overlaps, clearance** (combined file; per-model files re-checked: `L3.bpmn` 0 errors, `L4-01.bpmn` 0 errors, `L4-02.bpmn` 0 errors, `L4-03.bpmn` 0 errors, `L4-04.bpmn` 0 errors, `L4-05.bpmn` 0 errors, `L4-06.bpmn` 0 errors, `L4-07.bpmn` 0 errors, `L4-08.bpmn` 0 errors):

| Diagram | size (px) | elements with DI | DI elements | missing | duplicate | XOR / marker visible | overlaps | edge through shape / label | diagonal segments | edge crossings | zones checked | min free below (px) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `L3_DIAGRAM` | 2654 x 1305 | 48 | 48 | 0 | 0 | 0 / 0 | 0 | 0 / 0 | 0 | 1 | 24 | 80 |
| `L4_01_DIAGRAM` | 3554 x 1215 | 59 | 59 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 1 | 26 | 80 |
| `L4_02_DIAGRAM` | 2698 x 1678 | 69 | 69 | 0 | 0 | 1 / 1 | 0 | 0 / 0 | 0 | 3 | 33 | 80 |
| `L4_03_DIAGRAM` | 2902 x 1824 | 75 | 75 | 0 | 0 | 6 / 6 | 0 | 0 / 0 | 0 | 6 | 38 | 78 |
| `L4_04_DIAGRAM` | 3270 x 977 | 50 | 50 | 0 | 0 | 5 / 5 | 0 | 0 / 0 | 0 | 0 | 24 | 80 |
| `L4_05_DIAGRAM` | 2698 x 1729 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 12 | 37 | 80 |
| `L4_06_DIAGRAM` | 4270 x 1396 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 4 | 37 | 78 |
| `L4_07_DIAGRAM` | 3872 x 827 | 48 | 48 | 0 | 0 | 4 / 4 | 0 | 0 / 0 | 0 | 1 | 21 | 80 |
| `L4_08_DIAGRAM` | 1912 x 1412 | 47 | 47 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 1 | 19 | 78 |

**Smoke: bpmnlint recommended** (combined file; V1 owns the full lint): no-inclusive-gateway: 8
  - no-inclusive-gateway: warn L4_02_G1: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G4: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G5: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G4: Element type <bpmn:InclusiveGateway> is discouraged

**Smoke: headless render** (bpmn-js NavigatedViewer, Chrome headless, offline): 9 diagrams, import warnings 0, console errors 0. PNGs: `out/snapshot/screens/L3_DIAGRAM.png`, `out/snapshot/screens/L4_01_DIAGRAM.png`, `out/snapshot/screens/L4_02_DIAGRAM.png`, `out/snapshot/screens/L4_03_DIAGRAM.png`, `out/snapshot/screens/L4_04_DIAGRAM.png`, `out/snapshot/screens/L4_05_DIAGRAM.png`, `out/snapshot/screens/L4_06_DIAGRAM.png`, `out/snapshot/screens/L4_07_DIAGRAM.png`, `out/snapshot/screens/L4_08_DIAGRAM.png`, `out/snapshot/screens/L3_DIAGRAM_zones.png`, `out/snapshot/screens/L4_01_DIAGRAM_zones.png`, `out/snapshot/screens/L4_02_DIAGRAM_zones.png`, `out/snapshot/screens/L4_03_DIAGRAM_zones.png`, `out/snapshot/screens/L4_04_DIAGRAM_zones.png`, `out/snapshot/screens/L4_05_DIAGRAM_zones.png`, `out/snapshot/screens/L4_06_DIAGRAM_zones.png`, `out/snapshot/screens/L4_07_DIAGRAM_zones.png`, `out/snapshot/screens/L4_08_DIAGRAM_zones.png`

Note: Per-model files are self-contained (own collaboration, processes, diagram). L3.bpmn keeps calledElement on its call activities, but the called L4 processes are only in the combined file and in the L4 files.

<!-- END GATE: B2 snapshot -->
