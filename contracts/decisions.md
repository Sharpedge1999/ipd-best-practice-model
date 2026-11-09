# Decisions and naming conventions (contract S0)

Status: 06 Nov 2026. Section A is a verbatim copy of workflow_plan.md section 0 (owner: orchestrator; the orchestrator's file wins if they diverge). Sections B and C are the S0 contract; changes go through the orchestrator.

## A. Decisions log (O0) - copy of workflow_plan section 0

User decisions (06 Nov 2026):
- Jurisdictions: ICH + EU + US, plus industry best practice. UK (MHRA) out of scope (R6 not run; record as gap).
- Lanes: generic GCP roles as named in ICH/regulation. Sponsor-internal lanes only where a source names the role (e.g. monitor); otherwise "Sponsor". No client role names.
- Depth: L3 overview plus exactly one L4 per L3 step.

Orchestrator defaults (user may revise at U1):
- D1: Investigator/institution = expanded pool on all levels (ROL-03 exception, recorded in `rule_exceptions`), because investigator obligations are binding steps that must appear as tasks. IRB/IEC and Regulatory authority = collapsed pools linked by message flows.
- D2: Devices (21 CFR 812, MDR/IVDR) out of scope; recorded as gap.
- D3: Process boundary from "CtQ factors identified" (protocol design / trial planning) to "iPDs reported in clinical study report and records archived". L3 cut follows the six As-Is steps where regulation allows; extra steps only where binding logic requires them (e.g. serious breach notification, immediate-hazard deviation).
- D4: Independent verification (X1) checks 100% of binding findings and all quotes, plus a 25% sample of guidance and best-practice findings.
- Terminology: "CTR" is ambiguous. Use "clinical study report (CSR)" and "EU CTR" explicitly; never bare "CTR".

## B. Naming conventions

### B1. Identifiers in research and synthesis

| Item | Format | Notes |
|---|---|---|
| Finding ID | `R<stem>-<nnn>`, e.g. `R3-004` | stem 1-6; never reused; file sorted by id. `R9-nnn` reserved for test fixtures (accepted only in `fixtures/`). |
| Research files | `research/R<n>_<slug>.yaml`, `research/R<n>_notes.md` | stem of the file name must equal the id prefix |
| Source key | registry key, e.g. `EUCTR`, `21CFR312`, `E6R3-S4` | new keys UPPER-CASE with hyphens, listed in `Rn_notes.md` under a heading "New source keys", one per list item or table row, key first, with URL |
| Requirement ID | `REQ-<nnn>`, e.g. `REQ-031` | assigned by Y1; `REQ-9nn` reserved for fixtures |

### B2. Model and spec element IDs

| Item | Format | Example |
|---|---|---|
| Model ID | `L3`, `L4-01` .. `L4-0n` (n <= 9), numbered in L3 call-activity order | `L4-03` |
| Spec file | `spec/<model id>.yaml` | `spec/L4-03.yaml` |
| Start events | `S<n>` | `S1` |
| End events | `E<n>` | `E2` |
| Tasks, call activities | `A<n>` | `A4` |
| Gateways | `G<n>` | `G1` |
| Intermediate events | `I<n>` | `I1` |
| Sequence flows | `F<n>` | `F3` |
| Message flows | `M<n>` | `M2` |
| Data objects / stores | `D<n>` | `D1` |
| Groups | `GR_<NAME>` | `GR_EU` |
| Text annotations | `TA<n>` | `TA1` |
| Pools | `P_SPON` Sponsor, `P_INV` Investigator/institution, `P_IEC` IRB/IEC, `P_RA` Regulatory authority | same ID and name on every level (LBL-05) |
| Lanes | `L_<ROLE>`, short upper-case role code | `L_MON` (monitor), `L_SPON` (sponsor) |

- IDs are stable (GEN-05): never renumber; insert with a lower-case suffix (`A2a`). The numeric part has 1-3 digits.
- IDs are unique across all ID kinds within one model. The same ID may recur in different models.
- Lane names are role terms from the glossary/source and carry `src`.

### B3. XML IDs (converter output; join key for viewer, citations.json and validator)

Rule: `<MODEL>` = model ID with "-" replaced by "_" (`L4-01` -> `L4_01`); every spec element becomes `<MODEL>_<spec id>`.

| BPMN element | XML ID | Example |
|---|---|---|
| definitions | `IPD_DEFINITIONS` | |
| collaboration | `<MODEL>_COLLAB` | `L4_01_COLLAB` |
| participant (pool) | `<MODEL>_<pool>` | `L4_01_P_SPON` |
| process (expanded pools only) | `<MODEL>_<pool>_PROCESS` | `L4_01_P_INV_PROCESS` |
| laneSet | `<MODEL>_<pool>_LANESET` | `L4_01_P_SPON_LANESET` |
| lane | `<MODEL>_<lane>` | `L4_01_L_MON` |
| flow node, sequence flow, message flow | `<MODEL>_<id>` | `L3_A2`, `L4_01_F3`, `L4_01_M2` |
| message (if a messageRef is written) | `<MODEL>_<message flow>_MESSAGE` | `L4_01_M2_MESSAGE` |
| data object reference / data store reference | `<MODEL>_<data>` | `L4_01_D1` |
| data object / data store (root) | `<MODEL>_<data>_OBJECT` / `<MODEL>_<data>_STORE` | `L4_01_D1_OBJECT` |
| data association | `<MODEL>_<data>_<node>_IN` (data read by node, `dir: in`) / `_OUT` (data written by node, `dir: out`) | `L4_01_D1_A1_OUT` |
| property (targetRef of a node's data input associations, as the XSD requires; one per node with `dir: in` data) | `<MODEL>_<node>_PROPERTY` | `L4_01_A2_PROPERTY` |
| text annotation | `<MODEL>_<TA id>` | `L4_01_TA1` |
| association (annotation to its n-th `assoc` element, n from 1 in list order) | `<MODEL>_<TA id>_ASSOC<n>` | `L4_01_TA1_ASSOC1` |
| group / category / categoryValue | `<MODEL>_<group>` / `<MODEL>_<group>_CATEGORY` / `<MODEL>_<group>_VALUE` | `L4_01_GR_FX` |
| BPMNDiagram / BPMNPlane | `<MODEL>_DIAGRAM` / `<MODEL>_PLANE` (plane bpmnElement = `<MODEL>_COLLAB`) | `L3_DIAGRAM` |
| BPMNShape / BPMNEdge | `<XML ID>_di` | `L4_01_A3_di` |
| call activity `calledElement` | process of the internal pool of the called model: `<CALLED MODEL>_P_SPON_PROCESS`; omitted on interface call activities (`interface: true`, `calls: null`) | `L4_01_P_SPON_PROCESS` |

Reserved suffixes `_COLLAB`, `_PROCESS`, `_LANESET`, `_MESSAGE`, `_OBJECT`, `_STORE`, `_IN`, `_OUT`, `_PROPERTY`, `_ASSOC<n>`, `_CATEGORY`, `_VALUE`, `_DIAGRAM`, `_PLANE`, `_di` must not end a spec pool, lane or group ID.

## C. S0 contract decisions (other agents must know)

- **S0-01 Fixture stems.** Schema id pattern stays `^R[1-6]-\d{3}$`. `tools/lint_findings.py` accepts `R9` only for files whose parent directory is named `fixtures`. REQ IDs `REQ-9nn` are fixture-only.
- **S0-02 Loc grammar (rule LOC).** Accepted forms: `P<n>[.<n>]`, `GL:<term>`, `A1-<sec>`, `A2-<sec>`, `AppB-<sec>`, `AppC-<sec>`, `Art. <n>(<p>)...` (canonical with one space as in the plan examples; `Art.<n>` without space also accepted; paragraph groups optional and repeatable), `21CFR<part>.<sec>(<p>)...` (no spaces), `S<sec>` (section as printed; letters, digits, `.` and `-`, optional `(x)` groups, e.g. `S10.2`, `SIII.B.2`). `<sec>` = alphanumeric parts separated by `.`, optional `(x)` groups, e.g. `A1-3.11.4.5.1(b)`, `AppC-C.2.1`. A trailing ` [verify]` is allowed when the numbering itself is unconfirmed. `S<sec>` is the fallback for every source, including E6R3 when the annex is unclear.
- **S0-03 Lint rules beyond the task list.** PAGE (G1): `binding-law` and `binding-ICH` findings need a non-empty `page` or at least one `verify` item. ORDER: ids sorted ascending (section 3). SRC: new keys in notes must be UPPER-CASE with hyphens (the given key `CTTI-QbD` is grandfathered via the registry). Warnings only: THEME (case variant of CtQ/RBQM/safety/data), DRAFT-SRC (finding from a registry `draft: true` source without `draft: true`), CHARS (em dash or middle dot in findings, e.g. inside verbatim quotes; in specs CHARS is an error).
- **S0-04 Registry fields.** Besides key, title, owner_stem, url, url_status, binding_default the registry carries `jurisdiction`, `draft` and `notes`. Research agents never edit the registry; Y1 reconciles new keys and confirmed URLs/titles. Seeded binding_default: ICH guidelines `binding-ICH`; `E3QA`, `M11`, `EMA-E6R3` `verify-binding`; EU CTR and 21 CFR `binding-law`; agency guidance `guidance`; industry `best-practice`.
- **S0-05 Jurisdiction of non-regional sources.** The enum stays `ICH|EU|US`. Industry best practice and data standards (TCB-*, CTTI-*, CDISC-*) use `ICH` meaning "international scope"; `src` and `binding: best-practice` disambiguate. The ICH rule (never `binding-law`) applies to every finding with jurisdiction `ICH` and to every ICH source key (`^[EM]\d`, registry `binding_default: binding-ICH` or registry jurisdiction ICH). Orchestrator may revise.
- **S0-06 Themes.** Free tags (`^[A-Za-z][A-Za-z0-9-]*$`); canonical spellings `CtQ`, `RBQM`, `safety`, `data`.
- **S0-07 Trace fields on specs.** Tasks and call activities require `src` (>= 1 item), `req` (>= 1 item, read from the B1 gate "every task has src, req, binding") and `binding`. Events, gateways, message flows, data and pools may carry them. Spec `src` items are `{key, loc, page?}`; `loc` uses the findings grammar in real specs (not checked by lint_spec; fixtures use `FIXTURE`).
- **S0-08 Intermediate events.** The node type enum adds `intermediate-catch-message`, `intermediate-throw-message`, `intermediate-catch-timer` for the FLW-02 case. Each needs a `justification` and a `rule_exceptions` entry with rule `FLW-01` for that node (FLW-01 palette is MUST). `or-split` needs a `justification` (FLW-02/FLW-07, DEC-02). No other event types.
- **S0-09 Node placement.** A node gives `lane` (pool derived from the lane) or `pool` (only for an expanded pool without lanes). If a pool has lanes, every node in it needs a lane. Collapsed pools have no lanes and no nodes; they appear only as message flow endpoints.
- **S0-10 rule_exceptions.** Used for ROL-03 (expanded `P_INV`, D1), FLW-01 (intermediate events) and as the machine-readable DEC-05 / DEC-06 annotation for V1 layer L2 (element = the gateway or end event concerned).
- **S0-11 interface (SCP-06).** Required on L4, optional on L3. `start`/`ends` list the internal process's start and end events that match the parent step's input/output; `message_flows` list the child's message flows that realise the parent's hand-offs. Matching to the parent is by pool and identical label (LBL-05), so the child repeats the parent's message flow label verbatim.
- **S0-12 Structural checks in lint_spec.** Besides schema and reference resolution, lint_spec rejects what the converter cannot build: sequence flows across pools, message flows inside one pool or touching a gateway or lane, data entries associated with nodes in more than one pool or with gateways, more than one `default: true` flow per source node, node ID prefix not matching the type, unknown src keys. Graph rules (reachability, block structure, labels, sizes) stay with V1.
- **S0-13 open_items.** Each item starts with a status tag: `[verify...]`, `[proposal]` or `[unresolved: <ID>]`.
- **S0-14 Gateway labels.** `label` is required on every node except `and-split`, `and-join`, `xor-join`, `or-join`, which stay unlabelled by convention. XOR/OR splits carry a question ending in "?" (LBL-03, checked by V1).
- **S0-15 YAML quoting.** Quote every label and free-text value. Unquoted `Yes`, `No`, `On`, `Off` parse as booleans in YAML 1.1 (PyYAML) and fail the schema; unquoted `:` or `#` break parsing.
- **S0-16 Moddle descriptor.** `contracts/ipd_moddle.json` was written offline and is not runtime-tested; B2 confirms zero bpmn-moddle warnings and a lossless round trip, and reports any needed change.
- **S0-17 Trace record and party (ipd_extension 1.1, requested by W1/B2).** `ipd:trace` gains optional attributes `record` (record produced by the element, from spec `record`) and `party` (verbatim party term of the element's REQs, several joined with `"; "`, from spec `party`). Attribute order: `binding`, `jurisdiction`, `deadline`, `draft`, `record`, `party`. The plain-text documentation gains a `Party:` line after `Record:`. The spec schema allows an optional string `party` on nodes and message flows. Placement rule (single rule, ipd_extension section 4): write `ipd:trace` whenever any trace field (`src`, `req`, `binding`, `jurisdiction`, `deadline`, `draft`, `verify`, `record`, `party`) is present; `draft: false` and `deadline: none` count as absent. The change only adds optional items, so the namespace URI stays `urn:ipd-best-practice:trace:1.0`. B3 adds the XML ID `<MODEL>_<node>_PROPERTY`.
- **S0-18 Interface call activities, text annotations, model notes (requested by B1; FLW-01 allows both constructs).** (1) A `call-activity` may have `calls: null` to stand for a neighbouring process outside this model set (e.g. "Handle urgent safety measures"); it is marked with the optional boolean `interface: true`. Rule: `interface: true` requires `calls: null`, and `calls: null` requires `interface: true`; `interface` is not allowed on other node types. Interface call activities still require `src`, `req` and `binding`; the converter writes no `calledElement` for them. (2) Top-level `annotations: [{id: TA<n>, text, assoc: [<node or sequence flow id>], src?}]`; `text` is free text (quote it, English, hyphen not em dash). An annotation sits in the pool/process of its first `assoc` element; lint_spec resolves every `assoc` reference and rejects an annotation whose elements lie in more than one pool (an association cannot cross processes). (3) Top-level `notes` may be a string (new) or a list of strings (as before; joined with newlines on export); the converter exports it as `bpmn:documentation` on the internal pool's process. (4) XML IDs: `<MODEL>_<TA id>` and `<MODEL>_<TA id>_ASSOC<n>` (table B3). All changes are additive; existing specs stay valid.

## D. Tools

- `python -I tools/lint_findings.py <file.yaml> [...]` - findings lint (options: `--registry`, `--notes-dir`, `--any-stem` for merged files whose ids span stems).
- `python -I tools/lint_spec.py <spec.yaml> [...]` - spec schema + reference resolution (option `--registry`).
- `python -I tools/test_lint.py` - contract self-test (5 seeded findings faults, valid sample, both fixtures).
- Exit codes: 0 = no errors (warnings allowed), 1 = errors found, 2 = usage or I/O error. Output lines: `ERROR|WARN [RULE] <id> (<file>): <message>`.
