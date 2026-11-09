# B2 build log - converter and layout

Owner: B2 (converter/layout builder). Status 06 Nov 2026: B2a (fixtures) done; re-entry done (S0-17, S0-18, layout quality); **B2b done**: `out/ipd_best_practice.bpmn`, `out/ipd_best_practice.report.json`, `out/models/*.bpmn`, PNGs in `out/b2_screens/`, built from the frozen specs (`sha256sum -c spec/FROZEN.sha256` all OK) - full gate PASS, see section "B2b" at the end. B2b changes to the tools: section 5. **V1 round 1 (07 Nov 2026)**: LAY-02 docking implemented and gated on a copy of the frozen specs (`/tmp/b2_r1_spec`, section "B2 r1 dev" at the end, outputs in `out/r1_dev/`); rebuilt as **B2b-r2** from the re-frozen specs (section "B2b-r2" at the end, PASS) - changes in section 6; the older "B2b" gate section documents the 06 Nov build.

## 1. Files and commands

| File | Purpose |
|---|---|
| `tools/spec2bpmn.py` | CLI converter: specs (YAML) to one BPMN 2.0 XML with DI plus one file per model; runs `tools/lint_spec.py` first and aborts on errors |
| `tools/layout.py` | deterministic layout and orthogonal edge router (imported by spec2bpmn by file path, so `python -I` works) |
| `tools/moddle_check.mjs` | bpmn-moddle import with `contracts/ipd_moddle.json`, warnings, export + re-import, graph and ipd:trace comparison, optional bpmnlint recommended smoke run |
| `tools/b2_gate.py` | B2 gate: runs the converter twice and checks G1-G8 on the written XML (independent of the layout code); writes its section into this log |
| `tools/render_screens.mjs` | headless render (bpmn-js NavigatedViewer, Chrome, offline) of every diagram to PNG; `--zones` draws the reserved overlay zones |
| `vendor/node/` | `package.json` + `package-lock.json`: bpmn-moddle 10.3.1, bpmn-js 18.31.1, bpmnlint 11.15.0, playwright-core 1.65.0 (render only) |

```
# B2a (fixtures)
python -I tools/spec2bpmn.py --specs /home/claude/ipd/fixtures --out /home/claude/ipd/out/fixture/ipd_fixture.bpmn --models-out /home/claude/ipd/out/fixture/models
python -I tools/b2_gate.py --specs fixtures --out out/fixture/ipd_fixture.bpmn --models-out out/fixture/models --log out/build_log.md --section "B2a fixture run" --screens out/fixture/screens
# B2b (frozen specs)
cd /home/claude/ipd && sha256sum -c spec/FROZEN.sha256
python -I tools/b2_gate.py --specs /home/claude/ipd/spec --out /home/claude/ipd/out/ipd_best_practice.bpmn --models-out /home/claude/ipd/out/models --log /home/claude/ipd/out/build_log.md --section B2b --screens /home/claude/ipd/out/b2_screens
```

Outputs per run: `<out>`, `<out stem>.report.json` (inputs with sha256, counts, warnings, pool order and slots, overlay zones per diagram, layout size), `<models-out>/<model>.bpmn`. The gate also writes the bpmn-moddle exports to `<out dir>/check/` (round-trip evidence, not deliverables). Spec discovery: every `*.yaml`/`*.yml` in `--specs` that is a mapping with `level: L3|L4`; anything else (`R9_sample.yaml`, `coverage.md`, `notes.md`) is skipped and listed. Runtime for the 9 models: about 12 s per converter run, about 75 s for the full gate.

Test inputs (not model content): `out/b2_selftest/specs/` (synthetic 28-node stress spec, gate in `out/b2_selftest/gate.md`); `out/snapshot/` holds the converter output for the spec snapshot (review only, not B2b).

## 2. Conventions the viewer builder (W1) and validator (V1) must know

**IDs.** As in decisions.md B3 (incl. `<M>_<node>_PROPERTY`, `<M>_<TA>`, `<M>_<TA>_ASSOC<n>`). Per model: collaboration `<M>_COLLAB`, diagram `<M>_DIAGRAM`, plane `<M>_PLANE`. Diagram `name` = `<model id> - <title>`. All diagrams are in one `definitions` (`IPD_DEFINITIONS`); open them with `viewer.open('<M>_DIAGRAM')`. Call activity `calledElement` = `<CALLED>_P_SPON_PROCESS`; interface call activities (`calls: null`, `interface: true`) have **no** `calledElement`.

**Pools.** Collapsed pools are `bpmn:participant` **without `processRef`** (no empty process); bpmn-js renders exactly that as a collapsed (black-box) pool. Vertical order is global per pool id, identical on every diagram (report: `pool_slots`, per model `pool_order`): top band (the always-collapsed pool with the highest share of message flows to external pools; used when there are two or more such pools), external pools that are expanded in any model (where collapsed in a model, e.g. Investigator/institution in L3 and L4-07, they are a band in the same slot), the internal (Sponsor) pool, the other bands. Result for the real specs: **IRB/IEC (top band) - Investigator/institution - Sponsor - Regulatory authority (bottom band)**. A message flow to the IRB/IEC band from the Sponsor pool crosses the Investigator band where that pool is collapsed (L3); crossing a band is allowed only for message flows, at high cost.

**Overlay clearance.** Every task, call activity, event, gateway, data element and every text annotation with sources has a reserved free zone directly below it, inside its lane: width `max(150, shape width)`, centred; height 70 px (74 reserved, no edge runs within 4 px of its sides). Zone top: tasks, call activities, annotations = shape bottom + 6 px; events, gateways, data = DI label bottom + 4 px (shape bottom + 8 px if unlabelled). Message flows: 150 x 70 px left-aligned with the DI label, 4 px below it, inside a pool gap. Exception (r1): an activity with message flows docked on its bottom edge gets a zone of exactly 150 px width, aligned away from its dock corridors (left-aligned with the shape when the docks are on the right, right-aligned when on the left, centred when on both sides), so the source box never covers a message flow line. W1 must therefore place overlays at the report rectangle, not at a centred default. Exact rectangles: `<out stem>.report.json` -> `models[].overlay_zones` (key = XML id, `[x, y, w, h]`); the gate checks every report zone against the rule.

**Call activities ("Open L4" chip).** At least 160 px wide; label text keeps >= 20 px free above the bottom border, so W1's 58 x 15 chip at the bottom-right (right of the collapsed marker) is clear of text and marker. The gate checks width >= 150 px and, in the bpmn-js render, >= 17 px between the rendered label text and the shape bottom (B2b: min 26 px).

**Labels.** Event, gateway, data, sequence flow, message flow and group labels have `BPMNLabel` bounds. bpmn-js wraps external labels at the DI label width and task labels at shape width - 14; the converter sizes boxes with a port of the diagram-js wrapping algorithm. diagram-js cuts the word after " - " mid-word (visible in "FIXTURE - ..." labels only).

**Flows.** Orthogonal waypoints only. Gateway bottom vertices are never used (overlay zone); a third branch docks on the upper diamond edge (waypoint on the edge, 12 px beside the top vertex). Edges never run along a shape's own border or along a group frame (5 px band). Message flows (r1, LAY-02) dock on activities only on the top edge (other pool above) or the bottom edge (other pool below), never on a side: bottom docks sit 12 px inside the left / right corner (a second one on the same side 14 px further in), top docks at the centre, the quarter points, 12 px inside the corners or in line with a bottom dock above; every bent message flow keeps a straight first and last run of >= 20 px. Events keep side docks where their label and zone block the bottom. Text annotation associations (`associationDirection="None"`, source = annotated element, target = annotation) attach to the bracket side; an association to a sequence flow starts on a point of that flow.

**Layout rules.** Column = longest path from the start events within each process (sequence flows weight 1, loop back edges ignored), refined by message flows between nodes (receiver never left of sender) so that hand-offs are vertical (LAY-02). Lanes are rows; per lane the bottom row is the happy path on one straight line (LAY-01); alt/exception nodes keep the row of their (lowest) predecessor, data elements and annotations take free rows above; an end event may move up to two columns right to stay on its predecessor's row (once per predecessor). Rows are content + overlay clearance + 30 px corridor; group headers get extra space only in their top row. Column width >= 150 px, channels 44 px. Routing order: sequence flows (2 rip-up passes, pair swap for crossing branches of one gateway), their labels (then obstacles), message flows and data associations (2 rip-up passes; message flows prefer vertical runs and keep >= 20 px from each other where possible), annotation associations. Hard halo 8 px around every foreign shape; running parallel to a foreign shape border at 8-16 px costs extra (soft clearance).

## 3. Converter decisions and contract notes

- **S0-17 implemented.** `ipd:trace` attributes `binding, jurisdiction, deadline, draft, record, party` in that order; documentation lines `Record:` then `Party:`; trace written whenever any trace field is present (`draft: false`, `deadline: none` absent); a `party` list is joined with "; ". `contracts/ipd_moddle.json` (already with `record`, `party`) imports with zero warnings and round-trips losslessly - not changed by B2.
- **S0-18 implemented.** Interface call activities without `calledElement`; `bpmn:textAnnotation` (trace when it has `src`) plus `bpmn:association` per `assoc` item in the process of the first `assoc` element; spec `notes` (string or list, joined with newlines) as `bpmn:documentation` on the internal pool's process.
- **conditionExpression** only on the non-default outgoing flows of a node that has a default flow (body = flow label); satisfies bpmnlint `conditional-flows`. A default flow from a parallel gateway or event aborts the conversion.
- **Groups**: `bpmn:group` in the collaboration, `bpmn:category`/`categoryValue` at definitions level, `bpmn:categoryValueRef` on every member flow node. A data element or annotation attached to a member may lie inside the frame; a non-member flow node inside a frame is a gate error.
- **Data on non-activities** is written as a directed `bpmn:association` with a converter warning (not used by the specs).
- **Model documentation**: each collaboration has one `bpmn:documentation` with model id, title, parent, interface, rule exceptions and open items; a node `justification` is a second `bpmn:documentation` after the trace text. Event definitions have no id; no `bpmn:message` is written.
- **Per-model files** are self-contained; `L3.bpmn` keeps `calledElement`, but the called L4 processes are only in the combined file and the L4 files.

## 4. Known limitations

- Width follows the time-ordered columns: B2b widths L3 2654, L4-01 3554, L4-02 2698, L4-03 3290, L4-04 3270, L4-05 2698, L4-06 4270, L4-07 3872, L4-08 1912 px; all except L4-08 are above one A3 page at 100 % (LAY-03, SHOULD, logged deviation). No gratuitous spacing: 150 px columns (overlay width) + 44 px channels.
- Message flows whose receiver sits many columns after the sender run horizontally inside a pool (snapshot L4-02, Investigator to Sponsor reports).
- Remaining crossings are mostly vertical message flows over sequence flows (LAY-02 trade-off): B2b L4-05 12, L4-03 6, L4-06 5, L4-02 3, L3 / L4-01 / L4-07 / L4-08 1, L4-04 0.
- Gateways with three branches on one side: the third branch docks on the upper diamond edge 12 px beside the top vertex, so two sibling flows run parallel about 12 px apart up to their turn ("double rail", e.g. L4-01 G1 and G2, L4-03 OR split/join, L4-08 OR join). Penalising the parallel run was tried in B2b and rejected (it only added jogs at the gateway).
- A branch that must leave a split towards a lower row takes the right vertex (the bottom vertex is reserved for the overlay zone); the same-row branch then bridges over the gateway (2 extra bends, no crossing), e.g. L4-02 G2, L4-06 "Participation terminated?".
- Message flows leave tasks on the side ports when the shape below / above is blocked by an overlay zone or label, so some arrive on a side next to a sequence flow arrow (12-20 px apart, e.g. L4-01 M1/M2, L4-04 M2).
- A text annotation or data element placed above a gateway column pins the flows into that gateway below its zone (L4-01 TA1 above G2: F11 arrives with a 5 px final vertical).
- If a message flow label plus its zone finds no free spot, the pool gap is enlarged and the layout re-run (up to 3 times); after that a warning is logged and G8 fails.
- Text widths are estimated with Arial/Liberation metrics plus 10 % safety; other fonts may wrap differently.
- bpmnlint is a smoke run (recommended config); its 8 `no-inclusive-gateway` warnings (B2b, same as the snapshot) are content (OR gateways with FLW-07 justification), for V1.
- r1 docking: a data element placed directly above an activity can leave only one top entry beside its own zone; the message flow then jogs around the data association (L4-08 M1, 24 px jogs). Message flow ends on events (message start events) still use side edges when the event label and zone are below.

## 5. B2b changes (06 Nov 2026)

- **Gate (`tools/b2_gate.py`)**: two G7 checks added. (1) Docking: the first / last waypoint of every edge lies on the outline of its source / target (bounding box for activities, data and pools, circle for events, diamond for gateways, polyline for associations from a sequence flow) - catches unrouted or fallback edges; B2b: 0 undocked ends. (2) Call activity label room: `tools/render_screens.mjs` now measures every call activity's rendered label text (bpmn-js SVG `getBBox`) and the gate fails below 17 px free to the shape bottom; B2b: 13 call activities, min 26 px. The G5-G8 table has two new columns for them.
- **Layout (`tools/layout.py`)**: soft clearance band `HUG_PX = 16` beside foreign shapes (outside the 8 px halo), cost +1 per px; bypass flows over a task and message flows now keep 16-24 px instead of 9-12 px (e.g. L4-04 M2 over "Categorise deviation", L4-05 "No" over "Notify serious noncompliance"). `MSG_NEAR_PX` 12 -> 20: L4-05 M9 (IRB/IEC to Investigator) no longer runs 16 px beside M8, so its label is unambiguous. All changes are deterministic (G1 identical on two runs).
- **Message flows to collapsed pools (risk check)**: every message flow in every diagram has a routed polyline that docks on both ends; the L3 and L4-07 flows to the Regulatory authority leave the Sponsor tasks on a side port and run straight down to the band, one bend each (L3 M3-M5, M8, M9; L4-07 M1, M2); L3 M6 to IRB/IEC crosses the collapsed Investigator band (allowed for message flows).
- **Regression**: the changed tools pass the gate on `fixtures/` and `out/b2_selftest/specs/` (run into `/tmp`). The fixture output differs from the logged B2a section (one route in the L4-01 fixture); `out/fixture/` was not refreshed because W1 builds from it - refresh on request. `out/snapshot/` is review history from the previous code.
- **Spec-side observations (not fixed, for B1 / orchestrator)**: (a) unused collapsed pools drawn as empty bands: L4-01 IRB/IEC and Regulatory authority, L4-02 Regulatory authority, L4-04 IRB/IEC and Regulatory authority, L4-07 IRB/IEC and Investigator/institution, L4-08 IRB/IEC and Regulatory authority (no message flow touches them; LBL-05 consistency vs. clutter - decide); (b) L4-05 M8 runs IRB/IEC -> Regulatory authority between two collapsed pools, so it crosses the expanded Investigator and Sponsor pools at the left margin; (c) L4-03 has 31 nodes, the SCP-03 maximum.

## 6. V1 round 1 changes (07 Nov 2026) - LAY-02 message flow docking

Finding (validation/report_r1.md, LAY-02, owner B2): message flows docked on a side edge in 44 activity ends, next to sequence-flow arrows. Result on the copy of the frozen specs: **0 side docks of 59 activity ends (26 bottom, 33 top)**; B2b build before the change: 44 side docks of 59 (26 facing down, 18 facing up). Full gate PASS (section "B2 r1 dev"); fixtures and `out/b2_selftest/specs/` pass (run into `/tmp/b2_r1/reg`).

- **Ports** (`tools/layout.py`): message flows on activities only use the edge facing the other pool (pool order is global, so up / down is known before routing). An activity with k down-facing message flows is widened (same height) to at least 150 + 26 k px; its overlay zone stays 150 px and moves away from the dock corridors (section 2). Two activities linked by a message flow in the same column get the same width, so a bottom dock lines up with a top port and the hand-off is one vertical line (e.g. L4-01 M2, L4-02 M3, L4-03 M4).
- **Routing**: message flows carry the current run length in the router state (capped at 20 px) and pay 5000 for a run under 20 px before a bend or at the target (no tiny jogs, visible arrowheads); the message spacing cost is now height-aware (only where two message verticals overlap vertically, 3 per px within 20 px; the old x-only cost charged 120 per grid step for any message vertical anywhere on that x); in pool gaps message verticals keep 158 px apart where possible (label + zone beside the line), and horizontal message runs in a gap cost extra; soft 16 px clearance along lane / pool borders (inside) and group frames. Gap label candidates now also come from verticals that turn inside the gap.
- **Gate** (`tools/b2_gate.py`): G7 LAY-02 - no message flow end on an activity side edge, and a first / last run of >= 20 px on bent message flows; G8 - zone rule for bottom-docked activities and a cross-check of every report zone against the rule (W1 places overlays from the report). New table column "message flow ends on activities: side / bottom / all".
- **Cost**: widths grow by 30-160 px (B2b -> r1 dev: L3 2654 -> 2724, L4-01 3554 -> 3584, L4-02 2698 -> 2758, L4-03 3290 -> 3450, L4-04 3270 -> 3300, L4-05 2698 -> 2728, L4-06 4270 -> 4360, L4-07 3872 -> 3932, L4-08 1912 -> 1942); heights unchanged; crossings 30 -> 32 in total (L4-02 3 -> 5, L4-08 1 -> 2, L4-03 6 -> 5), bends 155 -> 158, total edge length 78778 -> 77396 px. Negative test: the new gate checks fail the current B2b file with 54 errors (44 side docks, 10 end runs under 20 px).
- Rebuild after the spec re-freeze: `sha256sum -c spec/FROZEN.sha256`, then the B2b gate command in section 1 (no code change needed).
- **B2b-r2 (07 Nov 2026, re-frozen specs)**: built and gated (section "B2b-r2", PASS); two layout fixes after the PNG review: (1) a data element is not placed above an activity with a message flow to a pool above (L4-08 Trial master file: M1 is now one straight vertical); annotations keep their column (moving L3 TA1 put the group frame through its text - rejected); (2) annotation associations may start on the upper diamond edges of a gateway, so they no longer share the top vertex with a sequence flow (L3 TA1 from G1). Known: L3 M11 / M12 jog 24 px into A3, because "Identify protocol deviations" (Monitor lane) and TA1 sit above A3 in the same column. Tools frozen for V1 round 2.
- **B2b-r3 (07 Nov 2026, re-frozen specs; L3 identification block = AND split to A2 and to XOR G5 "Intentional protocol deviation considered?" before A3, XOR merge G6)**: built and gated (section "B2b-r3", PASS, 0 errors); no tool change. L3 3142 x 1319 px (r2 2724), 5 crossings (M11 / M12 over F5 and over the "No" bypass F17, M6 over F8). PNG review: no overlap, no edge through a shape, labels readable. Tight spot, accepted: F17 "No" runs 17 px above A3, so the M11 / M12 arrowheads sit in that channel, and the M12 jog (y 883) runs 7 px above F17 for 106 px (x 1174-1280); dashed vs solid stays distinguishable at 100 %.
- **B2b-r4 (07 Nov 2026, re-frozen specs; L4-02 G1 = two conditional flows without default, A14 before OR split G4 "Which additional reports are due?" with default F21 "No further report")**: built and gated (section "B2b-r4", PASS, 0 errors); no tool change; only L4-02 (and the combined file / report) changed, the other 8 model files are byte-identical to B2b-r3. L4-02 2778 x 1678 px (r3 2952), 4 crossings (M6 x F23, M7 x F26, M5 x F21, M2 x F6). PNG review: no overlap, no edge through a shape, labels readable; G4 default slash shown, branch labels sit beside their rails. Tight spots, accepted: (1) OR join G2 - F12 (from A9, Monitor lane) bridges over G2 into the top vertex (5 px final run) and F14 (to A10) leaves the upper-left diamond edge and wraps F12 at 7-10 px; same geometry as the published r3 build (mirror of section 4, gateway bottom vertex reserved for the overlay zone); a clean variant would cost one crossing with F8. (2) M2 jogs at y 1344, 5 px above the "Centralised data review" frame bottom, forced by A4 directly above A9 and A4's overlay zone.

<!-- BEGIN GATE: B2a fixture run -->
### B2a fixture run

Command: `python -I tools/spec2bpmn.py --specs fixtures --out out/fixture/ipd_fixture.bpmn --models-out out/fixture/models`  
Gate: `python -I tools/b2_gate.py --specs fixtures --out out/fixture/ipd_fixture.bpmn --models-out out/fixture/models --log out/build_log.md --section "B2a fixture run" --screens out/fixture/screens`

Result: **PASS** (0 error(s))

Inputs: `L3_fixture.yaml` (L3, sha256 `9f6e81700662e9c4...`), `L4_fixture.yaml` (L4-01, sha256 `23e7fab02bd32844...`); skipped (not a spec): `R9_sample.yaml`

**G1 determinism** - two consecutive runs, sha256 per output file:

| File | sha256 run 1 | run 2 identical |
|---|---|---|
| `out/fixture/ipd_fixture.bpmn` | `2451bfbab1095bcafe48b4e066e4d4824981144f6cad87803433ec01f70fc7f5` | yes |
| `out/fixture/ipd_fixture.report.json` | `a41f3712b156c4aee218ecdf6d6ead51a551cb5e71efdf83272798d27f1d14fa` | yes |
| `out/fixture/models/L3.bpmn` | `df2071685afd6f16636105dd790f212d4a2a98918f09177e6e50199b7822d612` | yes |
| `out/fixture/models/L4-01.bpmn` | `20b553936aebcc1f071d893e3a7515e81f8d8a85e09b2900e4311d6f9367d83d` | yes |

**G2 bpmn-moddle** (bpmn-moddle with `contracts/ipd_moddle.json`; export + re-import):

| File | import warnings | re-import warnings | graph lossless | ipd:trace lossless | traces (moddle / XML) | ipd:source (moddle / XML) |
|---|---|---|---|---|---|---|
| `out/fixture/ipd_fixture.bpmn` | 0 | 0 | True | True | 19 / 19 | 20 / 20 |
| `out/fixture/models/L3.bpmn` | 0 | 0 | True | True | 8 / 8 | 8 / 8 |
| `out/fixture/models/L4-01.bpmn` | 0 | 0 | True | True | 11 / 11 | 12 / 12 |

**G3 ipd:trace C14N** (canonical XML of every `ipd:trace` and all `bpmn:documentation` texts, written file vs bpmn-moddle export):

- `out/fixture/ipd_fixture.bpmn`: 19 traces, 0 differing; 22 documented elements, 0 differing
- `out/fixture/models/L3.bpmn`: 8 traces, 0 differing; 9 documented elements, 0 differing
- `out/fixture/models/L4-01.bpmn`: 11 traces, 0 differing; 13 documented elements, 0 differing

**G4 XSD** (OMG BPMN 2.0 XSD set from `vendor/node/node_modules/bpmn-moddle/resources/bpmn/xsd/`, origin github.com/bpmn-io/bpmn-moddle; sha256 BPMN20.xsd `4c5e3d2c8e14...`, BPMNDI.xsd `1bfaab6a1e3b...`, DC.xsd `b325cd3c0d03...`, DI.xsd `62fa0d89138a...`, Semantic.xsd `aa37542753e4...`):

- `out/fixture/ipd_fixture.bpmn`: valid
- `out/fixture/models/L3.bpmn`: valid
- `out/fixture/models/L4-01.bpmn`: valid

**G5-G8 DI, markers, overlaps, clearance** (combined file; per-model files re-checked: `L3.bpmn` 0 errors, `L4-01.bpmn` 0 errors):

| Diagram | size (px) | elements with DI | DI elements | missing | duplicate | XOR / marker visible | overlaps | edge through shape / label | diagonal segments | edge crossings | zones checked | min free below (px) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `L3_DIAGRAM` | 1380 x 1105 | 22 | 22 | 0 | 0 | 0 / 0 | 0 | 0 / 0 | 0 | 0 | 10 | 80 |
| `L4_01_DIAGRAM` | 2186 x 1571 | 41 | 41 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 5 | 17 | 78 |

**Smoke: bpmnlint recommended** (combined file; V1 owns the full lint): no findings

**Smoke: headless render** (bpmn-js NavigatedViewer, Chrome headless, offline): 2 diagrams, import warnings 0, console errors 0. PNGs: `out/fixture/screens/L3_DIAGRAM.png`, `out/fixture/screens/L4_01_DIAGRAM.png`, `out/fixture/screens/L3_DIAGRAM_zones.png`, `out/fixture/screens/L4_01_DIAGRAM_zones.png`

Converter warnings:

- L3 A2: called model L4-02 not in the spec set; calledElement set to L4_02_P_SPON_PROCESS by convention
- L3 A3: called model L4-03 not in the spec set; calledElement set to L4_03_P_SPON_PROCESS by convention

Note: Per-model files are self-contained (own collaboration, processes, diagram). L3.bpmn keeps calledElement on its call activities, but the called L4 processes are only in the combined file and in the L4 files.

<!-- END GATE: B2a fixture run -->

<!-- BEGIN GATE: B2 re-entry: snapshot of spec/ (not B2b) -->
### B2 re-entry: snapshot of spec/ (not B2b)

Command: `python -I tools/spec2bpmn.py --specs /tmp/b2_snapshot_spec --out out/snapshot/snapshot.bpmn --models-out out/snapshot/models`  
Gate: `python -I tools/b2_gate.py --specs /tmp/b2_snapshot_spec --out out/snapshot/snapshot.bpmn --models-out out/snapshot/models --log out/build_log.md --section "B2 re-entry: snapshot of spec/ (not B2b)" --screens out/snapshot/screens`

Result: **PASS** (0 error(s))

Inputs: `L3.yaml` (L3, sha256 `61f0b3108a19fe57...`), `L4-01.yaml` (L4-01, sha256 `991e32ab8df67656...`), `L4-02.yaml` (L4-02, sha256 `8e897933f8338aa0...`), `L4-03.yaml` (L4-03, sha256 `fe9860b44da8f6af...`), `L4-04.yaml` (L4-04, sha256 `28c62355470cc924...`), `L4-05.yaml` (L4-05, sha256 `b13cc917ad9ba0f1...`), `L4-06.yaml` (L4-06, sha256 `7249eb28129acb4e...`), `L4-07.yaml` (L4-07, sha256 `a6ec16cfcac2abe4...`), `L4-08.yaml` (L4-08, sha256 `a5f90f9c32330833...`)

**G1 determinism** - two consecutive runs, sha256 per output file:

| File | sha256 run 1 | run 2 identical |
|---|---|---|
| `out/snapshot/models/L3.bpmn` | `cda55f060ed171690b9d2ddf3f8551ea4a3f7f19a0f2fe0f6a90715a823d2c63` | yes |
| `out/snapshot/models/L4-01.bpmn` | `dece0f092b845b5041ee41165a7b8efb7cadb195fa49a75b3f83b52133e919ed` | yes |
| `out/snapshot/models/L4-02.bpmn` | `910b998f8ab0b31a36045fbc7e4ab4dc6422335df3d1b073f82c5625cf953261` | yes |
| `out/snapshot/models/L4-03.bpmn` | `8235ac6ef623af20a442a1acf543998bedb466d0614e1b166e9fffd3ef1bd820` | yes |
| `out/snapshot/models/L4-04.bpmn` | `ca6c2cc6266c17d24c7aecf39e177012eddcb3bb10452dc7b649653c953a4815` | yes |
| `out/snapshot/models/L4-05.bpmn` | `13e0aa847a7718380793ed380718f33f9ff16ac12827ecb602993d47b9eaa743` | yes |
| `out/snapshot/models/L4-06.bpmn` | `0b28a1afef9b379c9dfc36f5c5e268fba9aacc806948eb972a9f4c50949e4a42` | yes |
| `out/snapshot/models/L4-07.bpmn` | `626d1ef01348cdeeaa72adb50fd953d465c72de719350257e6135c1a244b8dd6` | yes |
| `out/snapshot/models/L4-08.bpmn` | `abd09290c940d0b1b7b2d47cde4b7fff06e05e5381bbae978eca2f013530d755` | yes |
| `out/snapshot/snapshot.bpmn` | `a7962480a5005750659b3084c271545894ac8dfd4b706ea44308d24978e89fcc` | yes |
| `out/snapshot/snapshot.report.json` | `026bd75ac4263d4582ac64e52cad5dbe4867cffdf272fd35ea6c51b74ffd4582` | yes |

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
| `L4_05_DIAGRAM` | 2698 x 1610 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 12 | 37 | 80 |
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

<!-- END GATE: B2 re-entry: snapshot of spec/ (not B2b) -->

<!-- BEGIN GATE: B2b -->
### B2b

Command: `python -I tools/spec2bpmn.py --specs /home/claude/ipd/spec --out /home/claude/ipd/out/ipd_best_practice.bpmn --models-out /home/claude/ipd/out/models`  
Gate: `python -I tools/b2_gate.py --specs /home/claude/ipd/spec --out /home/claude/ipd/out/ipd_best_practice.bpmn --models-out /home/claude/ipd/out/models --log /home/claude/ipd/out/build_log.md --section "B2b" --screens /home/claude/ipd/out/b2_screens`

Result: **PASS** (0 error(s))

Inputs: `L3.yaml` (L3, sha256 `f717f61494c4e693...`), `L4-01.yaml` (L4-01, sha256 `991e32ab8df67656...`), `L4-02.yaml` (L4-02, sha256 `8e897933f8338aa0...`), `L4-03.yaml` (L4-03, sha256 `5b14315f0fec3946...`), `L4-04.yaml` (L4-04, sha256 `28c62355470cc924...`), `L4-05.yaml` (L4-05, sha256 `b13cc917ad9ba0f1...`), `L4-06.yaml` (L4-06, sha256 `7249eb28129acb4e...`), `L4-07.yaml` (L4-07, sha256 `a6ec16cfcac2abe4...`), `L4-08.yaml` (L4-08, sha256 `a5f90f9c32330833...`)

**G1 determinism** - two consecutive runs, sha256 per output file:

| File | sha256 run 1 | run 2 identical |
|---|---|---|
| `/home/claude/ipd/out/ipd_best_practice.bpmn` | `70fc8b44c581cf0bedb93377fa87d5eb922ba139938e97795d5dfd80cd082038` | yes |
| `/home/claude/ipd/out/ipd_best_practice.report.json` | `8179759402071c07fdb7f2baf010a2dcdf79656afea89f34bca9b0f7326a9782` | yes |
| `/home/claude/ipd/out/models/L3.bpmn` | `17bdf728a1101bbee34e032eda6be84b8ede692b17c1e448882b6a34b4b9c0d4` | yes |
| `/home/claude/ipd/out/models/L4-01.bpmn` | `dece0f092b845b5041ee41165a7b8efb7cadb195fa49a75b3f83b52133e919ed` | yes |
| `/home/claude/ipd/out/models/L4-02.bpmn` | `0ffde881be8d1e168b556f732d455c4a8d14c6ce5d51f898e71419db01f3b963` | yes |
| `/home/claude/ipd/out/models/L4-03.bpmn` | `3d0bd54cf137e02c197f01c4bc37c3a9ddecc79c693ef76186bd10e4b071325c` | yes |
| `/home/claude/ipd/out/models/L4-04.bpmn` | `b530c375a1b4d6a90d12be797a3a00099a7f1243af7a5f17cbaafa2b4c1edbd9` | yes |
| `/home/claude/ipd/out/models/L4-05.bpmn` | `4f0873d1ee8bdda94776a2ad9f3727f2c14025c014e561fd05f7d2ba8fa21179` | yes |
| `/home/claude/ipd/out/models/L4-06.bpmn` | `7cee0f82419bb1b48f6a5184e6f892dde608c3837d4428dee9561de3571b550b` | yes |
| `/home/claude/ipd/out/models/L4-07.bpmn` | `626d1ef01348cdeeaa72adb50fd953d465c72de719350257e6135c1a244b8dd6` | yes |
| `/home/claude/ipd/out/models/L4-08.bpmn` | `abd09290c940d0b1b7b2d47cde4b7fff06e05e5381bbae978eca2f013530d755` | yes |

**G2 bpmn-moddle** (bpmn-moddle with `contracts/ipd_moddle.json`; export + re-import):

| File | import warnings | re-import warnings | graph lossless | ipd:trace lossless | traces (moddle / XML) | ipd:source (moddle / XML) |
|---|---|---|---|---|---|---|
| `/home/claude/ipd/out/ipd_best_practice.bpmn` | 0 | 0 | True | True | 221 / 221 | 1028 / 1028 |
| `/home/claude/ipd/out/models/L3.bpmn` | 0 | 0 | True | True | 25 / 25 | 327 / 327 |
| `/home/claude/ipd/out/models/L4-01.bpmn` | 0 | 0 | True | True | 24 / 24 | 127 / 127 |
| `/home/claude/ipd/out/models/L4-02.bpmn` | 0 | 0 | True | True | 30 / 30 | 98 / 98 |
| `/home/claude/ipd/out/models/L4-03.bpmn` | 0 | 0 | True | True | 27 / 27 | 76 / 76 |
| `/home/claude/ipd/out/models/L4-04.bpmn` | 0 | 0 | True | True | 21 / 21 | 74 / 74 |
| `/home/claude/ipd/out/models/L4-05.bpmn` | 0 | 0 | True | True | 29 / 29 | 98 / 98 |
| `/home/claude/ipd/out/models/L4-06.bpmn` | 0 | 0 | True | True | 29 / 29 | 79 / 79 |
| `/home/claude/ipd/out/models/L4-07.bpmn` | 0 | 0 | True | True | 20 / 20 | 86 / 86 |
| `/home/claude/ipd/out/models/L4-08.bpmn` | 0 | 0 | True | True | 16 / 16 | 63 / 63 |

**G3 ipd:trace C14N** (canonical XML of every `ipd:trace` and all `bpmn:documentation` texts, written file vs bpmn-moddle export):

- `/home/claude/ipd/out/ipd_best_practice.bpmn`: 221 traces, 0 differing; 243 documented elements, 0 differing
- `/home/claude/ipd/out/models/L3.bpmn`: 25 traces, 0 differing; 27 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-01.bpmn`: 24 traces, 0 differing; 26 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-02.bpmn`: 30 traces, 0 differing; 34 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-03.bpmn`: 27 traces, 0 differing; 30 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-04.bpmn`: 21 traces, 0 differing; 23 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-05.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-06.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-07.bpmn`: 20 traces, 0 differing; 22 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-08.bpmn`: 16 traces, 0 differing; 19 documented elements, 0 differing

**G4 XSD** (OMG BPMN 2.0 XSD set from `vendor/node/node_modules/bpmn-moddle/resources/bpmn/xsd/`, origin github.com/bpmn-io/bpmn-moddle; sha256 BPMN20.xsd `4c5e3d2c8e14...`, BPMNDI.xsd `1bfaab6a1e3b...`, DC.xsd `b325cd3c0d03...`, DI.xsd `62fa0d89138a...`, Semantic.xsd `aa37542753e4...`):

- `/home/claude/ipd/out/ipd_best_practice.bpmn`: valid
- `/home/claude/ipd/out/models/L3.bpmn`: valid
- `/home/claude/ipd/out/models/L4-01.bpmn`: valid
- `/home/claude/ipd/out/models/L4-02.bpmn`: valid
- `/home/claude/ipd/out/models/L4-03.bpmn`: valid
- `/home/claude/ipd/out/models/L4-04.bpmn`: valid
- `/home/claude/ipd/out/models/L4-05.bpmn`: valid
- `/home/claude/ipd/out/models/L4-06.bpmn`: valid
- `/home/claude/ipd/out/models/L4-07.bpmn`: valid
- `/home/claude/ipd/out/models/L4-08.bpmn`: valid

**G5-G8 DI, markers, overlaps, clearance** (combined file; per-model files re-checked: `L3.bpmn` 0 errors, `L4-01.bpmn` 0 errors, `L4-02.bpmn` 0 errors, `L4-03.bpmn` 0 errors, `L4-04.bpmn` 0 errors, `L4-05.bpmn` 0 errors, `L4-06.bpmn` 0 errors, `L4-07.bpmn` 0 errors, `L4-08.bpmn` 0 errors):

| Diagram | size (px) | elements with DI | DI elements | missing | duplicate | XOR / marker visible | overlaps | edge through shape / label | diagonal segments | undocked edge ends | edge crossings | zones checked | min free below (px) | call activities / min px below label (render) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `L3_DIAGRAM` | 2654 x 1305 | 48 | 48 | 0 | 0 | 0 / 0 | 0 | 0 / 0 | 0 | 0 | 1 | 24 | 80 | 8 / 26 |
| `L4_01_DIAGRAM` | 3554 x 1215 | 59 | 59 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 1 | 26 | 80 | 0 / - |
| `L4_02_DIAGRAM` | 2698 x 1678 | 69 | 69 | 0 | 0 | 1 / 1 | 0 | 0 / 0 | 0 | 0 | 3 | 33 | 80 | 0 / - |
| `L4_03_DIAGRAM` | 3290 x 1646 | 80 | 80 | 0 | 0 | 8 / 8 | 0 | 0 / 0 | 0 | 0 | 6 | 40 | 78 | 1 / 26 |
| `L4_04_DIAGRAM` | 3270 x 977 | 50 | 50 | 0 | 0 | 5 / 5 | 0 | 0 / 0 | 0 | 0 | 0 | 24 | 80 | 0 / - |
| `L4_05_DIAGRAM` | 2698 x 1610 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 0 | 12 | 37 | 80 | 1 / 26 |
| `L4_06_DIAGRAM` | 4270 x 1396 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 0 | 5 | 37 | 80 | 0 / - |
| `L4_07_DIAGRAM` | 3872 x 827 | 48 | 48 | 0 | 0 | 4 / 4 | 0 | 0 / 0 | 0 | 0 | 1 | 21 | 80 | 2 / 26 |
| `L4_08_DIAGRAM` | 1912 x 1412 | 47 | 47 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 1 | 19 | 78 | 0 / - |

**Smoke: bpmnlint recommended** (combined file; V1 owns the full lint): no-inclusive-gateway: 8
  - no-inclusive-gateway: warn L4_02_G1: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G4: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G5: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G4: Element type <bpmn:InclusiveGateway> is discouraged

**Smoke: headless render** (bpmn-js NavigatedViewer, Chrome headless, offline): 9 diagrams, import warnings 0, console errors 0. PNGs: `/home/claude/ipd/out/b2_screens/L3_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_01_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_02_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_03_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_04_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_05_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_06_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_07_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_08_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L3_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_01_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_02_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_03_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_04_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_05_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_06_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_07_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_08_DIAGRAM_zones.png`

Note: Per-model files are self-contained (own collaboration, processes, diagram). L3.bpmn keeps calledElement on its call activities, but the called L4 processes are only in the combined file and in the L4 files.

<!-- END GATE: B2b -->

<!-- BEGIN GATE: B2 r1 dev: LAY-02 docking (copy of frozen specs, not B2b) -->
### B2 r1 dev: LAY-02 docking (copy of frozen specs, not B2b)

Command: `python -I tools/spec2bpmn.py --specs /tmp/b2_r1_spec --out /home/claude/ipd/out/r1_dev/ipd_r1_dev.bpmn --models-out /home/claude/ipd/out/r1_dev/models`  
Gate: `python -I tools/b2_gate.py --specs /tmp/b2_r1_spec --out /home/claude/ipd/out/r1_dev/ipd_r1_dev.bpmn --models-out /home/claude/ipd/out/r1_dev/models --log /home/claude/ipd/out/build_log.md --section "B2 r1 dev: LAY-02 docking (copy of frozen specs, not B2b)" --screens /home/claude/ipd/out/r1_dev/screens`

Result: **PASS** (0 error(s))

Inputs: `L3.yaml` (L3, sha256 `f717f61494c4e693...`), `L4-01.yaml` (L4-01, sha256 `991e32ab8df67656...`), `L4-02.yaml` (L4-02, sha256 `8e897933f8338aa0...`), `L4-03.yaml` (L4-03, sha256 `5b14315f0fec3946...`), `L4-04.yaml` (L4-04, sha256 `28c62355470cc924...`), `L4-05.yaml` (L4-05, sha256 `b13cc917ad9ba0f1...`), `L4-06.yaml` (L4-06, sha256 `7249eb28129acb4e...`), `L4-07.yaml` (L4-07, sha256 `a6ec16cfcac2abe4...`), `L4-08.yaml` (L4-08, sha256 `a5f90f9c32330833...`)

**G1 determinism** - two consecutive runs, sha256 per output file:

| File | sha256 run 1 | run 2 identical |
|---|---|---|
| `/home/claude/ipd/out/r1_dev/ipd_r1_dev.bpmn` | `6ff19cc1ff55635311e66437795ad172a371bb115be00fd95169086194765b6c` | yes |
| `/home/claude/ipd/out/r1_dev/ipd_r1_dev.report.json` | `4e11c3eadafff39f4d97dfec9a963757eb523937e4101de88a86ba1b8d1e9ddd` | yes |
| `/home/claude/ipd/out/r1_dev/models/L3.bpmn` | `a018368e2ca07af6877e31b377af80fd38326258947244f3442b199561c72996` | yes |
| `/home/claude/ipd/out/r1_dev/models/L4-01.bpmn` | `0c5e340da90d6b0277fede670c0d94ea354d100694357ebd0629d0e5aa567a4f` | yes |
| `/home/claude/ipd/out/r1_dev/models/L4-02.bpmn` | `d3cb54704097c0f527894724988cd288e5657c1c752b880f1689401279b4b932` | yes |
| `/home/claude/ipd/out/r1_dev/models/L4-03.bpmn` | `dc9b50357934e0e221fcba3bb9557b7f5976f75506ccab668dc89ec31e77a1e9` | yes |
| `/home/claude/ipd/out/r1_dev/models/L4-04.bpmn` | `e4f91801acbc34bde326043a7fe7eb129f14773d70c4eec2e07dbbca7324cb7e` | yes |
| `/home/claude/ipd/out/r1_dev/models/L4-05.bpmn` | `43854206001ddfeba3fbe675f2eaf2695988caef76cf67667bd414040bae8e23` | yes |
| `/home/claude/ipd/out/r1_dev/models/L4-06.bpmn` | `ca523d0b70415cbbf54416ebdba3a8df508f8fa5be770a7cf27b0566c1591584` | yes |
| `/home/claude/ipd/out/r1_dev/models/L4-07.bpmn` | `dbebeb879bf59f94925f466201eb6469d87fa91897c797d800cd57c5da746975` | yes |
| `/home/claude/ipd/out/r1_dev/models/L4-08.bpmn` | `4f5bd1add3341c07aa6c9e1abba79a15ad7362d70751a80d3523896d4a43af7f` | yes |

**G2 bpmn-moddle** (bpmn-moddle with `contracts/ipd_moddle.json`; export + re-import):

| File | import warnings | re-import warnings | graph lossless | ipd:trace lossless | traces (moddle / XML) | ipd:source (moddle / XML) |
|---|---|---|---|---|---|---|
| `/home/claude/ipd/out/r1_dev/ipd_r1_dev.bpmn` | 0 | 0 | True | True | 221 / 221 | 1028 / 1028 |
| `/home/claude/ipd/out/r1_dev/models/L3.bpmn` | 0 | 0 | True | True | 25 / 25 | 327 / 327 |
| `/home/claude/ipd/out/r1_dev/models/L4-01.bpmn` | 0 | 0 | True | True | 24 / 24 | 127 / 127 |
| `/home/claude/ipd/out/r1_dev/models/L4-02.bpmn` | 0 | 0 | True | True | 30 / 30 | 98 / 98 |
| `/home/claude/ipd/out/r1_dev/models/L4-03.bpmn` | 0 | 0 | True | True | 27 / 27 | 76 / 76 |
| `/home/claude/ipd/out/r1_dev/models/L4-04.bpmn` | 0 | 0 | True | True | 21 / 21 | 74 / 74 |
| `/home/claude/ipd/out/r1_dev/models/L4-05.bpmn` | 0 | 0 | True | True | 29 / 29 | 98 / 98 |
| `/home/claude/ipd/out/r1_dev/models/L4-06.bpmn` | 0 | 0 | True | True | 29 / 29 | 79 / 79 |
| `/home/claude/ipd/out/r1_dev/models/L4-07.bpmn` | 0 | 0 | True | True | 20 / 20 | 86 / 86 |
| `/home/claude/ipd/out/r1_dev/models/L4-08.bpmn` | 0 | 0 | True | True | 16 / 16 | 63 / 63 |

**G3 ipd:trace C14N** (canonical XML of every `ipd:trace` and all `bpmn:documentation` texts, written file vs bpmn-moddle export):

- `/home/claude/ipd/out/r1_dev/ipd_r1_dev.bpmn`: 221 traces, 0 differing; 243 documented elements, 0 differing
- `/home/claude/ipd/out/r1_dev/models/L3.bpmn`: 25 traces, 0 differing; 27 documented elements, 0 differing
- `/home/claude/ipd/out/r1_dev/models/L4-01.bpmn`: 24 traces, 0 differing; 26 documented elements, 0 differing
- `/home/claude/ipd/out/r1_dev/models/L4-02.bpmn`: 30 traces, 0 differing; 34 documented elements, 0 differing
- `/home/claude/ipd/out/r1_dev/models/L4-03.bpmn`: 27 traces, 0 differing; 30 documented elements, 0 differing
- `/home/claude/ipd/out/r1_dev/models/L4-04.bpmn`: 21 traces, 0 differing; 23 documented elements, 0 differing
- `/home/claude/ipd/out/r1_dev/models/L4-05.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/r1_dev/models/L4-06.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/r1_dev/models/L4-07.bpmn`: 20 traces, 0 differing; 22 documented elements, 0 differing
- `/home/claude/ipd/out/r1_dev/models/L4-08.bpmn`: 16 traces, 0 differing; 19 documented elements, 0 differing

**G4 XSD** (OMG BPMN 2.0 XSD set from `vendor/node/node_modules/bpmn-moddle/resources/bpmn/xsd/`, origin github.com/bpmn-io/bpmn-moddle; sha256 BPMN20.xsd `4c5e3d2c8e14...`, BPMNDI.xsd `1bfaab6a1e3b...`, DC.xsd `b325cd3c0d03...`, DI.xsd `62fa0d89138a...`, Semantic.xsd `aa37542753e4...`):

- `/home/claude/ipd/out/r1_dev/ipd_r1_dev.bpmn`: valid
- `/home/claude/ipd/out/r1_dev/models/L3.bpmn`: valid
- `/home/claude/ipd/out/r1_dev/models/L4-01.bpmn`: valid
- `/home/claude/ipd/out/r1_dev/models/L4-02.bpmn`: valid
- `/home/claude/ipd/out/r1_dev/models/L4-03.bpmn`: valid
- `/home/claude/ipd/out/r1_dev/models/L4-04.bpmn`: valid
- `/home/claude/ipd/out/r1_dev/models/L4-05.bpmn`: valid
- `/home/claude/ipd/out/r1_dev/models/L4-06.bpmn`: valid
- `/home/claude/ipd/out/r1_dev/models/L4-07.bpmn`: valid
- `/home/claude/ipd/out/r1_dev/models/L4-08.bpmn`: valid

**G5-G8 DI, markers, overlaps, clearance** (combined file; per-model files re-checked: `L3.bpmn` 0 errors, `L4-01.bpmn` 0 errors, `L4-02.bpmn` 0 errors, `L4-03.bpmn` 0 errors, `L4-04.bpmn` 0 errors, `L4-05.bpmn` 0 errors, `L4-06.bpmn` 0 errors, `L4-07.bpmn` 0 errors, `L4-08.bpmn` 0 errors):

| Diagram | size (px) | elements with DI | DI elements | missing | duplicate | XOR / marker visible | overlaps | edge through shape / label | diagonal segments | undocked edge ends | message flow ends on activities: side / bottom / all | edge crossings | zones checked | min free below (px) | call activities / min px below label (render) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `L3_DIAGRAM` | 2724 x 1305 | 48 | 48 | 0 | 0 | 0 / 0 | 0 | 0 / 0 | 0 | 0 | 0 / 5 / 10 | 1 | 24 | 80 | 8 / 26 |
| `L4_01_DIAGRAM` | 3584 x 1215 | 59 | 59 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 3 | 1 | 26 | 80 | 0 / - |
| `L4_02_DIAGRAM` | 2758 x 1678 | 69 | 69 | 0 | 0 | 1 / 1 | 0 | 0 / 0 | 0 | 0 | 0 / 4 / 11 | 5 | 33 | 78 | 0 / - |
| `L4_03_DIAGRAM` | 3450 x 1646 | 80 | 80 | 0 | 0 | 8 / 8 | 0 | 0 / 0 | 0 | 0 | 0 / 6 / 11 | 5 | 40 | 78 | 1 / 26 |
| `L4_04_DIAGRAM` | 3300 x 977 | 50 | 50 | 0 | 0 | 5 / 5 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 4 | 0 | 24 | 78 | 0 / - |
| `L4_05_DIAGRAM` | 2728 x 1610 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 0 | 0 / 2 / 7 | 12 | 37 | 78 | 1 / 26 |
| `L4_06_DIAGRAM` | 4360 x 1396 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 0 | 0 / 4 / 9 | 5 | 37 | 80 | 0 / - |
| `L4_07_DIAGRAM` | 3932 x 827 | 48 | 48 | 0 | 0 | 4 / 4 | 0 | 0 / 0 | 0 | 0 | 0 / 2 / 2 | 1 | 21 | 80 | 2 / 26 |
| `L4_08_DIAGRAM` | 1942 x 1412 | 47 | 47 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 2 | 2 | 19 | 78 | 0 / - |

**Smoke: bpmnlint recommended** (combined file; V1 owns the full lint): no-inclusive-gateway: 8
  - no-inclusive-gateway: warn L4_02_G1: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G4: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G5: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G4: Element type <bpmn:InclusiveGateway> is discouraged

**Smoke: headless render** (bpmn-js NavigatedViewer, Chrome headless, offline): 9 diagrams, import warnings 0, console errors 0. PNGs: `/home/claude/ipd/out/r1_dev/screens/L3_DIAGRAM.png`, `/home/claude/ipd/out/r1_dev/screens/L4_01_DIAGRAM.png`, `/home/claude/ipd/out/r1_dev/screens/L4_02_DIAGRAM.png`, `/home/claude/ipd/out/r1_dev/screens/L4_03_DIAGRAM.png`, `/home/claude/ipd/out/r1_dev/screens/L4_04_DIAGRAM.png`, `/home/claude/ipd/out/r1_dev/screens/L4_05_DIAGRAM.png`, `/home/claude/ipd/out/r1_dev/screens/L4_06_DIAGRAM.png`, `/home/claude/ipd/out/r1_dev/screens/L4_07_DIAGRAM.png`, `/home/claude/ipd/out/r1_dev/screens/L4_08_DIAGRAM.png`, `/home/claude/ipd/out/r1_dev/screens/L3_DIAGRAM_zones.png`, `/home/claude/ipd/out/r1_dev/screens/L4_01_DIAGRAM_zones.png`, `/home/claude/ipd/out/r1_dev/screens/L4_02_DIAGRAM_zones.png`, `/home/claude/ipd/out/r1_dev/screens/L4_03_DIAGRAM_zones.png`, `/home/claude/ipd/out/r1_dev/screens/L4_04_DIAGRAM_zones.png`, `/home/claude/ipd/out/r1_dev/screens/L4_05_DIAGRAM_zones.png`, `/home/claude/ipd/out/r1_dev/screens/L4_06_DIAGRAM_zones.png`, `/home/claude/ipd/out/r1_dev/screens/L4_07_DIAGRAM_zones.png`, `/home/claude/ipd/out/r1_dev/screens/L4_08_DIAGRAM_zones.png`

Note: Per-model files are self-contained (own collaboration, processes, diagram). L3.bpmn keeps calledElement on its call activities, but the called L4 processes are only in the combined file and in the L4 files.

<!-- END GATE: B2 r1 dev: LAY-02 docking (copy of frozen specs, not B2b) -->

<!-- BEGIN GATE: B2b-r2 -->
### B2b-r2

Command: `python -I tools/spec2bpmn.py --specs /home/claude/ipd/spec --out /home/claude/ipd/out/ipd_best_practice.bpmn --models-out /home/claude/ipd/out/models`  
Gate: `python -I tools/b2_gate.py --specs /home/claude/ipd/spec --out /home/claude/ipd/out/ipd_best_practice.bpmn --models-out /home/claude/ipd/out/models --log /home/claude/ipd/out/build_log.md --section "B2b-r2" --screens /home/claude/ipd/out/b2_screens`

Result: **PASS** (0 error(s))

Inputs: `L3.yaml` (L3, sha256 `e612b5cc0d198a0e...`), `L4-01.yaml` (L4-01, sha256 `7a1de87b063b07d4...`), `L4-02.yaml` (L4-02, sha256 `5c4d2ebdcc90b9c9...`), `L4-03.yaml` (L4-03, sha256 `5063e989f073135f...`), `L4-04.yaml` (L4-04, sha256 `702062493f06ad36...`), `L4-05.yaml` (L4-05, sha256 `f913c90896330bac...`), `L4-06.yaml` (L4-06, sha256 `7249eb28129acb4e...`), `L4-07.yaml` (L4-07, sha256 `a55d080b2047d9a5...`), `L4-08.yaml` (L4-08, sha256 `fa5edf519c5b0a84...`)

**G1 determinism** - two consecutive runs, sha256 per output file:

| File | sha256 run 1 | run 2 identical |
|---|---|---|
| `/home/claude/ipd/out/ipd_best_practice.bpmn` | `f6f0ce114c3608ac13f560999435df287a6f217a7f0ebaf14557f78b7b73c582` | yes |
| `/home/claude/ipd/out/ipd_best_practice.report.json` | `25b6ef91b66829526fd6578110f93e3eb61d31dce52a74fbf9e5ddd1e567c0ec` | yes |
| `/home/claude/ipd/out/models/L3.bpmn` | `bcffa994c2790a74e3814c8e8e9cdc1ef67b16b00a17c113c24bee9625839aea` | yes |
| `/home/claude/ipd/out/models/L4-01.bpmn` | `e793412090f8474d67c1fb660b3c983301824f47de77a8928b90b45e6b33bd3c` | yes |
| `/home/claude/ipd/out/models/L4-02.bpmn` | `b9b6b768e92928861a41e8978064b7c19a0efba757d2285be4246f33e2ef53d9` | yes |
| `/home/claude/ipd/out/models/L4-03.bpmn` | `41aec5eb4004aaf27377dc7da2773300538d4ddfe3c2f26be8bd27178a2ab603` | yes |
| `/home/claude/ipd/out/models/L4-04.bpmn` | `951ecb058b349f058f0255a590770ebf0567cceffb651a3aad313052a5dde032` | yes |
| `/home/claude/ipd/out/models/L4-05.bpmn` | `7f14a1950afa5b1b6d89d4b6aa9a18d758a7cd1a3453606ad081ba4af29ad71b` | yes |
| `/home/claude/ipd/out/models/L4-06.bpmn` | `ca523d0b70415cbbf54416ebdba3a8df508f8fa5be770a7cf27b0566c1591584` | yes |
| `/home/claude/ipd/out/models/L4-07.bpmn` | `b13a7e7df8449971757268d5ec93147328d8109cf21a257c1b6cffec82176035` | yes |
| `/home/claude/ipd/out/models/L4-08.bpmn` | `a9553c297824d5b2df68e640fd3a20324a56a5a56a3c1d5c0ece1281f1f9c5d6` | yes |

**G2 bpmn-moddle** (bpmn-moddle with `contracts/ipd_moddle.json`; export + re-import):

| File | import warnings | re-import warnings | graph lossless | ipd:trace lossless | traces (moddle / XML) | ipd:source (moddle / XML) |
|---|---|---|---|---|---|---|
| `/home/claude/ipd/out/ipd_best_practice.bpmn` | 0 | 0 | True | True | 224 / 224 | 1034 / 1034 |
| `/home/claude/ipd/out/models/L3.bpmn` | 0 | 0 | True | True | 27 / 27 | 330 / 330 |
| `/home/claude/ipd/out/models/L4-01.bpmn` | 0 | 0 | True | True | 24 / 24 | 127 / 127 |
| `/home/claude/ipd/out/models/L4-02.bpmn` | 0 | 0 | True | True | 30 / 30 | 98 / 98 |
| `/home/claude/ipd/out/models/L4-03.bpmn` | 0 | 0 | True | True | 28 / 28 | 79 / 79 |
| `/home/claude/ipd/out/models/L4-04.bpmn` | 0 | 0 | True | True | 21 / 21 | 74 / 74 |
| `/home/claude/ipd/out/models/L4-05.bpmn` | 0 | 0 | True | True | 29 / 29 | 98 / 98 |
| `/home/claude/ipd/out/models/L4-06.bpmn` | 0 | 0 | True | True | 29 / 29 | 79 / 79 |
| `/home/claude/ipd/out/models/L4-07.bpmn` | 0 | 0 | True | True | 20 / 20 | 86 / 86 |
| `/home/claude/ipd/out/models/L4-08.bpmn` | 0 | 0 | True | True | 16 / 16 | 63 / 63 |

**G3 ipd:trace C14N** (canonical XML of every `ipd:trace` and all `bpmn:documentation` texts, written file vs bpmn-moddle export):

- `/home/claude/ipd/out/ipd_best_practice.bpmn`: 224 traces, 0 differing; 247 documented elements, 0 differing
- `/home/claude/ipd/out/models/L3.bpmn`: 27 traces, 0 differing; 30 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-01.bpmn`: 24 traces, 0 differing; 26 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-02.bpmn`: 30 traces, 0 differing; 34 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-03.bpmn`: 28 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-04.bpmn`: 21 traces, 0 differing; 23 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-05.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-06.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-07.bpmn`: 20 traces, 0 differing; 22 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-08.bpmn`: 16 traces, 0 differing; 19 documented elements, 0 differing

**G4 XSD** (OMG BPMN 2.0 XSD set from `vendor/node/node_modules/bpmn-moddle/resources/bpmn/xsd/`, origin github.com/bpmn-io/bpmn-moddle; sha256 BPMN20.xsd `4c5e3d2c8e14...`, BPMNDI.xsd `1bfaab6a1e3b...`, DC.xsd `b325cd3c0d03...`, DI.xsd `62fa0d89138a...`, Semantic.xsd `aa37542753e4...`):

- `/home/claude/ipd/out/ipd_best_practice.bpmn`: valid
- `/home/claude/ipd/out/models/L3.bpmn`: valid
- `/home/claude/ipd/out/models/L4-01.bpmn`: valid
- `/home/claude/ipd/out/models/L4-02.bpmn`: valid
- `/home/claude/ipd/out/models/L4-03.bpmn`: valid
- `/home/claude/ipd/out/models/L4-04.bpmn`: valid
- `/home/claude/ipd/out/models/L4-05.bpmn`: valid
- `/home/claude/ipd/out/models/L4-06.bpmn`: valid
- `/home/claude/ipd/out/models/L4-07.bpmn`: valid
- `/home/claude/ipd/out/models/L4-08.bpmn`: valid

**G5-G8 DI, markers, overlaps, clearance** (combined file; per-model files re-checked: `L3.bpmn` 0 errors, `L4-01.bpmn` 0 errors, `L4-02.bpmn` 0 errors, `L4-03.bpmn` 0 errors, `L4-04.bpmn` 0 errors, `L4-05.bpmn` 0 errors, `L4-06.bpmn` 0 errors, `L4-07.bpmn` 0 errors, `L4-08.bpmn` 0 errors):

| Diagram | size (px) | elements with DI | DI elements | missing | duplicate | XOR / marker visible | overlaps | edge through shape / label | diagonal segments | undocked edge ends | message flow ends on activities: side / bottom / all | edge crossings | zones checked | min free below (px) | call activities / min px below label (render) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `L3_DIAGRAM` | 2724 x 1319 | 50 | 50 | 0 | 0 | 0 / 0 | 0 | 0 / 0 | 0 | 0 | 0 / 5 / 12 | 4 | 26 | 80 | 8 / 26 |
| `L4_01_DIAGRAM` | 3584 x 1215 | 59 | 59 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 3 | 1 | 26 | 80 | 0 / - |
| `L4_02_DIAGRAM` | 2952 x 1678 | 69 | 69 | 0 | 0 | 1 / 1 | 0 | 0 / 0 | 0 | 0 | 0 / 4 / 11 | 5 | 33 | 78 | 0 / - |
| `L4_03_DIAGRAM` | 3644 x 1665 | 82 | 82 | 0 | 0 | 8 / 8 | 0 | 0 / 0 | 0 | 0 | 0 / 6 / 11 | 5 | 41 | 78 | 1 / 26 |
| `L4_04_DIAGRAM` | 3300 x 977 | 50 | 50 | 0 | 0 | 5 / 5 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 4 | 0 | 24 | 78 | 0 / - |
| `L4_05_DIAGRAM` | 2728 x 1610 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 0 | 0 / 2 / 7 | 12 | 37 | 78 | 1 / 26 |
| `L4_06_DIAGRAM` | 4360 x 1396 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 0 | 0 / 4 / 9 | 5 | 37 | 80 | 0 / - |
| `L4_07_DIAGRAM` | 3932 x 832 | 48 | 48 | 0 | 0 | 4 / 4 | 0 | 0 / 0 | 0 | 0 | 0 / 2 / 2 | 1 | 21 | 80 | 2 / 24 |
| `L4_08_DIAGRAM` | 1942 x 1412 | 47 | 47 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 2 | 1 | 19 | 78 | 0 / - |

**Smoke: bpmnlint recommended** (combined file; V1 owns the full lint): no-inclusive-gateway: 10
  - no-inclusive-gateway: warn L3_G1: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L3_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G1: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G4: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G5: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G4: Element type <bpmn:InclusiveGateway> is discouraged

**Smoke: headless render** (bpmn-js NavigatedViewer, Chrome headless, offline): 9 diagrams, import warnings 0, console errors 0. PNGs: `/home/claude/ipd/out/b2_screens/L3_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_01_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_02_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_03_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_04_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_05_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_06_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_07_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_08_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L3_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_01_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_02_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_03_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_04_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_05_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_06_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_07_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_08_DIAGRAM_zones.png`

Note: Per-model files are self-contained (own collaboration, processes, diagram). L3.bpmn keeps calledElement on its call activities, but the called L4 processes are only in the combined file and in the L4 files.

<!-- END GATE: B2b-r2 -->

<!-- BEGIN GATE: B2b-r3 -->
### B2b-r3

Command: `python -I tools/spec2bpmn.py --specs /home/claude/ipd/spec --out /home/claude/ipd/out/ipd_best_practice.bpmn --models-out /home/claude/ipd/out/models`  
Gate: `python -I tools/b2_gate.py --specs /home/claude/ipd/spec --out /home/claude/ipd/out/ipd_best_practice.bpmn --models-out /home/claude/ipd/out/models --log /home/claude/ipd/out/build_log.md --section "B2b-r3" --screens /home/claude/ipd/out/b2_screens`

Result: **PASS** (0 error(s))

Inputs: `L3.yaml` (L3, sha256 `b50546c242f64309...`), `L4-01.yaml` (L4-01, sha256 `7a1de87b063b07d4...`), `L4-02.yaml` (L4-02, sha256 `5c4d2ebdcc90b9c9...`), `L4-03.yaml` (L4-03, sha256 `b013a218e6eb047c...`), `L4-04.yaml` (L4-04, sha256 `702062493f06ad36...`), `L4-05.yaml` (L4-05, sha256 `f913c90896330bac...`), `L4-06.yaml` (L4-06, sha256 `7249eb28129acb4e...`), `L4-07.yaml` (L4-07, sha256 `a55d080b2047d9a5...`), `L4-08.yaml` (L4-08, sha256 `fa5edf519c5b0a84...`)

**G1 determinism** - two consecutive runs, sha256 per output file:

| File | sha256 run 1 | run 2 identical |
|---|---|---|
| `/home/claude/ipd/out/ipd_best_practice.bpmn` | `9e57f49706816f64af22b092557563c0800bf13c6568a3db0d695c637b097380` | yes |
| `/home/claude/ipd/out/ipd_best_practice.report.json` | `4b1f3d9d9708537e4603fa8f46fa23be167a3faab0af0dee71086a052615c3cb` | yes |
| `/home/claude/ipd/out/models/L3.bpmn` | `2bc59930db46af6aa8d3de90d244fa200a53efc655007a5e4cb651cecced829e` | yes |
| `/home/claude/ipd/out/models/L4-01.bpmn` | `e793412090f8474d67c1fb660b3c983301824f47de77a8928b90b45e6b33bd3c` | yes |
| `/home/claude/ipd/out/models/L4-02.bpmn` | `b9b6b768e92928861a41e8978064b7c19a0efba757d2285be4246f33e2ef53d9` | yes |
| `/home/claude/ipd/out/models/L4-03.bpmn` | `d03230a79793c95f04988ba857de6245f64d0447811892073c018dc1e7ffb81d` | yes |
| `/home/claude/ipd/out/models/L4-04.bpmn` | `951ecb058b349f058f0255a590770ebf0567cceffb651a3aad313052a5dde032` | yes |
| `/home/claude/ipd/out/models/L4-05.bpmn` | `7f14a1950afa5b1b6d89d4b6aa9a18d758a7cd1a3453606ad081ba4af29ad71b` | yes |
| `/home/claude/ipd/out/models/L4-06.bpmn` | `ca523d0b70415cbbf54416ebdba3a8df508f8fa5be770a7cf27b0566c1591584` | yes |
| `/home/claude/ipd/out/models/L4-07.bpmn` | `b13a7e7df8449971757268d5ec93147328d8109cf21a257c1b6cffec82176035` | yes |
| `/home/claude/ipd/out/models/L4-08.bpmn` | `a9553c297824d5b2df68e640fd3a20324a56a5a56a3c1d5c0ece1281f1f9c5d6` | yes |

**G2 bpmn-moddle** (bpmn-moddle with `contracts/ipd_moddle.json`; export + re-import):

| File | import warnings | re-import warnings | graph lossless | ipd:trace lossless | traces (moddle / XML) | ipd:source (moddle / XML) |
|---|---|---|---|---|---|---|
| `/home/claude/ipd/out/ipd_best_practice.bpmn` | 0 | 0 | True | True | 224 / 224 | 1034 / 1034 |
| `/home/claude/ipd/out/models/L3.bpmn` | 0 | 0 | True | True | 27 / 27 | 330 / 330 |
| `/home/claude/ipd/out/models/L4-01.bpmn` | 0 | 0 | True | True | 24 / 24 | 127 / 127 |
| `/home/claude/ipd/out/models/L4-02.bpmn` | 0 | 0 | True | True | 30 / 30 | 98 / 98 |
| `/home/claude/ipd/out/models/L4-03.bpmn` | 0 | 0 | True | True | 28 / 28 | 79 / 79 |
| `/home/claude/ipd/out/models/L4-04.bpmn` | 0 | 0 | True | True | 21 / 21 | 74 / 74 |
| `/home/claude/ipd/out/models/L4-05.bpmn` | 0 | 0 | True | True | 29 / 29 | 98 / 98 |
| `/home/claude/ipd/out/models/L4-06.bpmn` | 0 | 0 | True | True | 29 / 29 | 79 / 79 |
| `/home/claude/ipd/out/models/L4-07.bpmn` | 0 | 0 | True | True | 20 / 20 | 86 / 86 |
| `/home/claude/ipd/out/models/L4-08.bpmn` | 0 | 0 | True | True | 16 / 16 | 63 / 63 |

**G3 ipd:trace C14N** (canonical XML of every `ipd:trace` and all `bpmn:documentation` texts, written file vs bpmn-moddle export):

- `/home/claude/ipd/out/ipd_best_practice.bpmn`: 224 traces, 0 differing; 246 documented elements, 0 differing
- `/home/claude/ipd/out/models/L3.bpmn`: 27 traces, 0 differing; 29 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-01.bpmn`: 24 traces, 0 differing; 26 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-02.bpmn`: 30 traces, 0 differing; 34 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-03.bpmn`: 28 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-04.bpmn`: 21 traces, 0 differing; 23 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-05.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-06.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-07.bpmn`: 20 traces, 0 differing; 22 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-08.bpmn`: 16 traces, 0 differing; 19 documented elements, 0 differing

**G4 XSD** (OMG BPMN 2.0 XSD set from `vendor/node/node_modules/bpmn-moddle/resources/bpmn/xsd/`, origin github.com/bpmn-io/bpmn-moddle; sha256 BPMN20.xsd `4c5e3d2c8e14...`, BPMNDI.xsd `1bfaab6a1e3b...`, DC.xsd `b325cd3c0d03...`, DI.xsd `62fa0d89138a...`, Semantic.xsd `aa37542753e4...`):

- `/home/claude/ipd/out/ipd_best_practice.bpmn`: valid
- `/home/claude/ipd/out/models/L3.bpmn`: valid
- `/home/claude/ipd/out/models/L4-01.bpmn`: valid
- `/home/claude/ipd/out/models/L4-02.bpmn`: valid
- `/home/claude/ipd/out/models/L4-03.bpmn`: valid
- `/home/claude/ipd/out/models/L4-04.bpmn`: valid
- `/home/claude/ipd/out/models/L4-05.bpmn`: valid
- `/home/claude/ipd/out/models/L4-06.bpmn`: valid
- `/home/claude/ipd/out/models/L4-07.bpmn`: valid
- `/home/claude/ipd/out/models/L4-08.bpmn`: valid

**G5-G8 DI, markers, overlaps, clearance** (combined file; per-model files re-checked: `L3.bpmn` 0 errors, `L4-01.bpmn` 0 errors, `L4-02.bpmn` 0 errors, `L4-03.bpmn` 0 errors, `L4-04.bpmn` 0 errors, `L4-05.bpmn` 0 errors, `L4-06.bpmn` 0 errors, `L4-07.bpmn` 0 errors, `L4-08.bpmn` 0 errors):

| Diagram | size (px) | elements with DI | DI elements | missing | duplicate | XOR / marker visible | overlaps | edge through shape / label | diagonal segments | undocked edge ends | message flow ends on activities: side / bottom / all | edge crossings | zones checked | min free below (px) | call activities / min px below label (render) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `L3_DIAGRAM` | 3142 x 1319 | 55 | 55 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 0 / 5 / 12 | 5 | 28 | 80 | 8 / 26 |
| `L4_01_DIAGRAM` | 3584 x 1215 | 59 | 59 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 3 | 1 | 26 | 80 | 0 / - |
| `L4_02_DIAGRAM` | 2952 x 1678 | 69 | 69 | 0 | 0 | 1 / 1 | 0 | 0 / 0 | 0 | 0 | 0 / 4 / 11 | 5 | 33 | 78 | 0 / - |
| `L4_03_DIAGRAM` | 3644 x 1665 | 82 | 82 | 0 | 0 | 8 / 8 | 0 | 0 / 0 | 0 | 0 | 0 / 6 / 11 | 5 | 41 | 78 | 1 / 26 |
| `L4_04_DIAGRAM` | 3300 x 977 | 50 | 50 | 0 | 0 | 5 / 5 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 4 | 0 | 24 | 78 | 0 / - |
| `L4_05_DIAGRAM` | 2728 x 1610 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 0 | 0 / 2 / 7 | 12 | 37 | 78 | 1 / 26 |
| `L4_06_DIAGRAM` | 4360 x 1396 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 0 | 0 / 4 / 9 | 5 | 37 | 80 | 0 / - |
| `L4_07_DIAGRAM` | 3932 x 832 | 48 | 48 | 0 | 0 | 4 / 4 | 0 | 0 / 0 | 0 | 0 | 0 / 2 / 2 | 1 | 21 | 80 | 2 / 24 |
| `L4_08_DIAGRAM` | 1942 x 1412 | 47 | 47 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 2 | 1 | 19 | 78 | 0 / - |

**Smoke: bpmnlint recommended** (combined file; V1 owns the full lint): no-inclusive-gateway: 8
  - no-inclusive-gateway: warn L4_02_G1: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G4: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G5: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G4: Element type <bpmn:InclusiveGateway> is discouraged

**Smoke: headless render** (bpmn-js NavigatedViewer, Chrome headless, offline): 9 diagrams, import warnings 0, console errors 0. PNGs: `/home/claude/ipd/out/b2_screens/L3_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_01_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_02_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_03_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_04_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_05_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_06_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_07_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_08_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L3_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_01_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_02_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_03_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_04_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_05_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_06_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_07_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_08_DIAGRAM_zones.png`

Note: Per-model files are self-contained (own collaboration, processes, diagram). L3.bpmn keeps calledElement on its call activities, but the called L4 processes are only in the combined file and in the L4 files.

<!-- END GATE: B2b-r3 -->

<!-- BEGIN GATE: B2b-r4 -->
### B2b-r4

Command: `python -I tools/spec2bpmn.py --specs /home/claude/ipd/spec --out /home/claude/ipd/out/ipd_best_practice.bpmn --models-out /home/claude/ipd/out/models`  
Gate: `python -I tools/b2_gate.py --specs /home/claude/ipd/spec --out /home/claude/ipd/out/ipd_best_practice.bpmn --models-out /home/claude/ipd/out/models --log /home/claude/ipd/out/build_log.md --section "B2b-r4" --screens /home/claude/ipd/out/b2_screens`

Result: **PASS** (0 error(s))

Inputs: `L3.yaml` (L3, sha256 `b50546c242f64309...`), `L4-01.yaml` (L4-01, sha256 `7a1de87b063b07d4...`), `L4-02.yaml` (L4-02, sha256 `b2bb4ff422a50324...`), `L4-03.yaml` (L4-03, sha256 `b013a218e6eb047c...`), `L4-04.yaml` (L4-04, sha256 `702062493f06ad36...`), `L4-05.yaml` (L4-05, sha256 `f913c90896330bac...`), `L4-06.yaml` (L4-06, sha256 `7249eb28129acb4e...`), `L4-07.yaml` (L4-07, sha256 `a55d080b2047d9a5...`), `L4-08.yaml` (L4-08, sha256 `fa5edf519c5b0a84...`)

**G1 determinism** - two consecutive runs, sha256 per output file:

| File | sha256 run 1 | run 2 identical |
|---|---|---|
| `/home/claude/ipd/out/ipd_best_practice.bpmn` | `37a8b9c9e596a9f857a983d6750542d8d0893f1700333a14183b2376f02ada2e` | yes |
| `/home/claude/ipd/out/ipd_best_practice.report.json` | `8d77136f4c9972b7714ec6d68c8b35ad802605c643f7568b4b5380291e832195` | yes |
| `/home/claude/ipd/out/models/L3.bpmn` | `2bc59930db46af6aa8d3de90d244fa200a53efc655007a5e4cb651cecced829e` | yes |
| `/home/claude/ipd/out/models/L4-01.bpmn` | `e793412090f8474d67c1fb660b3c983301824f47de77a8928b90b45e6b33bd3c` | yes |
| `/home/claude/ipd/out/models/L4-02.bpmn` | `5eab0d70f8913adbd529150db503f0e0e2eac399bdba155c999f038e1d298d54` | yes |
| `/home/claude/ipd/out/models/L4-03.bpmn` | `d03230a79793c95f04988ba857de6245f64d0447811892073c018dc1e7ffb81d` | yes |
| `/home/claude/ipd/out/models/L4-04.bpmn` | `951ecb058b349f058f0255a590770ebf0567cceffb651a3aad313052a5dde032` | yes |
| `/home/claude/ipd/out/models/L4-05.bpmn` | `7f14a1950afa5b1b6d89d4b6aa9a18d758a7cd1a3453606ad081ba4af29ad71b` | yes |
| `/home/claude/ipd/out/models/L4-06.bpmn` | `ca523d0b70415cbbf54416ebdba3a8df508f8fa5be770a7cf27b0566c1591584` | yes |
| `/home/claude/ipd/out/models/L4-07.bpmn` | `b13a7e7df8449971757268d5ec93147328d8109cf21a257c1b6cffec82176035` | yes |
| `/home/claude/ipd/out/models/L4-08.bpmn` | `a9553c297824d5b2df68e640fd3a20324a56a5a56a3c1d5c0ece1281f1f9c5d6` | yes |

**G2 bpmn-moddle** (bpmn-moddle with `contracts/ipd_moddle.json`; export + re-import):

| File | import warnings | re-import warnings | graph lossless | ipd:trace lossless | traces (moddle / XML) | ipd:source (moddle / XML) |
|---|---|---|---|---|---|---|
| `/home/claude/ipd/out/ipd_best_practice.bpmn` | 0 | 0 | True | True | 224 / 224 | 1034 / 1034 |
| `/home/claude/ipd/out/models/L3.bpmn` | 0 | 0 | True | True | 27 / 27 | 330 / 330 |
| `/home/claude/ipd/out/models/L4-01.bpmn` | 0 | 0 | True | True | 24 / 24 | 127 / 127 |
| `/home/claude/ipd/out/models/L4-02.bpmn` | 0 | 0 | True | True | 30 / 30 | 98 / 98 |
| `/home/claude/ipd/out/models/L4-03.bpmn` | 0 | 0 | True | True | 28 / 28 | 79 / 79 |
| `/home/claude/ipd/out/models/L4-04.bpmn` | 0 | 0 | True | True | 21 / 21 | 74 / 74 |
| `/home/claude/ipd/out/models/L4-05.bpmn` | 0 | 0 | True | True | 29 / 29 | 98 / 98 |
| `/home/claude/ipd/out/models/L4-06.bpmn` | 0 | 0 | True | True | 29 / 29 | 79 / 79 |
| `/home/claude/ipd/out/models/L4-07.bpmn` | 0 | 0 | True | True | 20 / 20 | 86 / 86 |
| `/home/claude/ipd/out/models/L4-08.bpmn` | 0 | 0 | True | True | 16 / 16 | 63 / 63 |

**G3 ipd:trace C14N** (canonical XML of every `ipd:trace` and all `bpmn:documentation` texts, written file vs bpmn-moddle export):

- `/home/claude/ipd/out/ipd_best_practice.bpmn`: 224 traces, 0 differing; 246 documented elements, 0 differing
- `/home/claude/ipd/out/models/L3.bpmn`: 27 traces, 0 differing; 29 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-01.bpmn`: 24 traces, 0 differing; 26 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-02.bpmn`: 30 traces, 0 differing; 34 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-03.bpmn`: 28 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-04.bpmn`: 21 traces, 0 differing; 23 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-05.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-06.bpmn`: 29 traces, 0 differing; 31 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-07.bpmn`: 20 traces, 0 differing; 22 documented elements, 0 differing
- `/home/claude/ipd/out/models/L4-08.bpmn`: 16 traces, 0 differing; 19 documented elements, 0 differing

**G4 XSD** (OMG BPMN 2.0 XSD set from `vendor/node/node_modules/bpmn-moddle/resources/bpmn/xsd/`, origin github.com/bpmn-io/bpmn-moddle; sha256 BPMN20.xsd `4c5e3d2c8e14...`, BPMNDI.xsd `1bfaab6a1e3b...`, DC.xsd `b325cd3c0d03...`, DI.xsd `62fa0d89138a...`, Semantic.xsd `aa37542753e4...`):

- `/home/claude/ipd/out/ipd_best_practice.bpmn`: valid
- `/home/claude/ipd/out/models/L3.bpmn`: valid
- `/home/claude/ipd/out/models/L4-01.bpmn`: valid
- `/home/claude/ipd/out/models/L4-02.bpmn`: valid
- `/home/claude/ipd/out/models/L4-03.bpmn`: valid
- `/home/claude/ipd/out/models/L4-04.bpmn`: valid
- `/home/claude/ipd/out/models/L4-05.bpmn`: valid
- `/home/claude/ipd/out/models/L4-06.bpmn`: valid
- `/home/claude/ipd/out/models/L4-07.bpmn`: valid
- `/home/claude/ipd/out/models/L4-08.bpmn`: valid

**G5-G8 DI, markers, overlaps, clearance** (combined file; per-model files re-checked: `L3.bpmn` 0 errors, `L4-01.bpmn` 0 errors, `L4-02.bpmn` 0 errors, `L4-03.bpmn` 0 errors, `L4-04.bpmn` 0 errors, `L4-05.bpmn` 0 errors, `L4-06.bpmn` 0 errors, `L4-07.bpmn` 0 errors, `L4-08.bpmn` 0 errors):

| Diagram | size (px) | elements with DI | DI elements | missing | duplicate | XOR / marker visible | overlaps | edge through shape / label | diagonal segments | undocked edge ends | message flow ends on activities: side / bottom / all | edge crossings | zones checked | min free below (px) | call activities / min px below label (render) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `L3_DIAGRAM` | 3142 x 1319 | 55 | 55 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 0 / 5 / 12 | 5 | 28 | 80 | 8 / 26 |
| `L4_01_DIAGRAM` | 3584 x 1215 | 59 | 59 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 3 | 1 | 26 | 80 | 0 / - |
| `L4_02_DIAGRAM` | 2778 x 1678 | 69 | 69 | 0 | 0 | 1 / 1 | 0 | 0 / 0 | 0 | 0 | 0 / 4 / 11 | 4 | 33 | 78 | 0 / - |
| `L4_03_DIAGRAM` | 3644 x 1665 | 82 | 82 | 0 | 0 | 8 / 8 | 0 | 0 / 0 | 0 | 0 | 0 / 6 / 11 | 5 | 41 | 78 | 1 / 26 |
| `L4_04_DIAGRAM` | 3300 x 977 | 50 | 50 | 0 | 0 | 5 / 5 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 4 | 0 | 24 | 78 | 0 / - |
| `L4_05_DIAGRAM` | 2728 x 1610 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 0 | 0 / 2 / 7 | 12 | 37 | 78 | 1 / 26 |
| `L4_06_DIAGRAM` | 4360 x 1396 | 75 | 75 | 0 | 0 | 9 / 9 | 0 | 0 / 0 | 0 | 0 | 0 / 4 / 9 | 5 | 37 | 80 | 0 / - |
| `L4_07_DIAGRAM` | 3932 x 832 | 48 | 48 | 0 | 0 | 4 / 4 | 0 | 0 / 0 | 0 | 0 | 0 / 2 / 2 | 1 | 21 | 80 | 2 / 24 |
| `L4_08_DIAGRAM` | 1942 x 1412 | 47 | 47 | 0 | 0 | 2 / 2 | 0 | 0 / 0 | 0 | 0 | 0 / 1 / 2 | 1 | 19 | 78 | 0 / - |

**Smoke: bpmnlint recommended** (combined file; V1 owns the full lint): no-inclusive-gateway: 8
  - no-inclusive-gateway: warn L4_02_G1: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G4: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_02_G5: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G2: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_03_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G3: Element type <bpmn:InclusiveGateway> is discouraged
  - no-inclusive-gateway: warn L4_08_G4: Element type <bpmn:InclusiveGateway> is discouraged

**Smoke: headless render** (bpmn-js NavigatedViewer, Chrome headless, offline): 9 diagrams, import warnings 0, console errors 0. PNGs: `/home/claude/ipd/out/b2_screens/L3_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_01_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_02_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_03_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_04_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_05_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_06_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_07_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L4_08_DIAGRAM.png`, `/home/claude/ipd/out/b2_screens/L3_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_01_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_02_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_03_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_04_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_05_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_06_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_07_DIAGRAM_zones.png`, `/home/claude/ipd/out/b2_screens/L4_08_DIAGRAM_zones.png`

Note: Per-model files are self-contained (own collaboration, processes, diagram). L3.bpmn keeps calledElement on its call activities, but the called L4 processes are only in the combined file and in the L4 files.

<!-- END GATE: B2b-r4 -->
