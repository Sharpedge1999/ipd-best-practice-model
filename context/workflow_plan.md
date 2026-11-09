# Workflow plan - best-practice iPD BPMN model (contract for all agents)

Status: 06 Nov 2026. Approved by the orchestrator. Read together with `brief.md` and `bpmn-design-criteria.md`.

## 0. Decisions log (O0)

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

## 1. Steps and owners (each step = exactly one sub-agent; repairs = re-entry of the same agent)

| ID | Owner | Starts after | Outputs (under /home/claude/ipd/) | Gate |
|---|---|---|---|---|
| S0 | contracts agent | O0 | contracts/findings.schema.json, contracts/spec.schema.json, contracts/source_registry.yaml, contracts/ipd_extension.md, contracts/decisions.md, fixtures/L3_fixture.yaml, fixtures/L4_fixture.yaml, tools/lint_findings.py | lint passes valid fixture, rejects 5 seeded faults |
| R1-R5 | one research agent per stem | O0 (parallel with S0) | research/Rn_<slug>.yaml, research/Rn_notes.md | G1: lint passes; target sections read or gap justified; binding findings have loc + page or [verify]; mandatory coverage complete |
| Y1 | synthesis agent | G1 | synthesis/merged_findings.yaml, requirements.yaml, conflicts.md, l3_cut.md, req_to_step.yaml, glossary.yaml, verification_worklist.yaml, tools/render_register.py, register/iPD_Requirements_Register.md | G2: 100% binding REQs mapped or out_of_scope with reason; conflicts listed; 5-9 L3 call activities; each L3 step has trigger, outcome, pools, message flows, As-Is comparability note |
| U1 | orchestrator + user | G2 | confirmed L3 cut | explicit user confirmation |
| X1 | blind verification agent | G2 | verification/X1_results.yaml, X1_omissions.md, X1_summary.md | G4 |
| B1 | spec builder | U1 | spec/L3.yaml, spec/L4-01..0n.yaml, spec/coverage.md, spec/notes.md | schema-valid; 100% in-scope binding REQ coverage; every task has src, req, binding |
| B2 | converter/layout builder | S0 | tools/spec2bpmn.py, tools/layout.py, out/ipd_best_practice.bpmn, out/models/<id>.bpmn, out/build_log.md | deterministic (sha256 twice), bpmn-moddle zero warnings, DI complete |
| W1 | viewer builder | B2 fixture run | viewer/package.json + lockfile, tools/build_viewer.py, out/citations.json, out/ipd_best_practice_map.html, out/screens/*.png | headless test: zero console errors, no network, every diagram opens, overlay count = elements with src |
| V1 | independent validator | B1, B2, W1 final | tools/validate/*, validation/report_rN.{json,md} | GEN-04 layers L0-L5 |
| F1 | orchestrator | V1 pass + G4 | project docs, memory pointer, published artifact | no MUST errors; X1 closed |

Conventions: downloaded packages/XSDs go to /home/claude/ipd/vendor/; scripts in /home/claude/ipd/tools/; run Python with `python -I`.

## 2. Research stems

Target sections are search anchors. Find them by content and record the numbering actually seen.

| Stem | Source keys | Targets | Extract | Exclusions | Output |
|---|---|---|---|---|---|
| R1 ICH GCP (mandatory) | E6R3 (consolidated 2026, primary); E6R3-S4 (Step 4 2025, numbering crosswalk only) | Principles (esp. 7, 10), glossary (deviation, noncompliance, critical to quality factors, risk thresholds/QTL), Annex 1 sec 2 (investigator, esp. 2.5.x protocol compliance), sec 3 (sponsor: 3.9-3.12 incl. 3.10 risk-based quality management, 3.11 monitoring/3.11.4.x, 3.12 noncompliance), Appendix B, Appendix C essential records, Annex 2. Tag every CtQ use with theme `CtQ` | investigator and sponsor duties to define, identify, document, report, assess, correct deviations; immediate-hazard deviations; risk thresholds; records | anything outside E6(R3); E6(R2) | research/R1_ich_e6r3.yaml |
| R2 ICH design and reporting (mandatory CtQ part) | E8R1, E3, E3QA, E9, E9R1, M11 (only if Step 4, else [verify]) | E8(R1) 3.2-3.3 in full (CtQ); E3 10.2; E3 Q&A (R1) on protocol deviations; E9 5.2 analysis sets; E9(R1) deviations vs intercurrent events | CtQ definition and link to trial-specific iPD definition; CSR reporting of important deviations; analysis-set impact | E6(R3) (R1 owns it); E2A-F | research/R2_ich_other.yaml |
| R3 EU | EUCTR, EMA-SB, EUCTR-QA, EMA-E6R3, CTIS-HB | EU CTR Art. 2 (definitions), 41 (boundary), 47, 52, 53, 54, 57-58 (take numbers from the text) | serious breach trigger, 7-day clock, notifying party and recipient; urgent safety measures; protocol and GCP compliance; TMF/archiving | national law; Directive 2001/20/EC; MDR/IVDR | research/R3_eu.yaml |
| R4 US | 21CFR312, 21CFR56, 21CFR50, FDA-PD24 (Dec 2024 draft + current status), FDA-E6R3, FDA-RBM13, FDA-RBM23 | 312.30, 312.50, 312.56, 312.60, 312.62, 312.66; 56.108(a)(3)-(4), 56.108(b); 50.20, 50.27; FDA-PD24 in full | IRB reporting of noncompliance, immediate-hazard changes, sponsor securing compliance, FDA definition of "important" and reporting expectations | Part 812, Part 11, state law | research/R4_us.yaml |
| R5 Industry and data standards | TCB-PD, TCB-RBQM, CTTI-QbD, CDISC-DV, peer-reviewed PD consortium paper [verify] | process guide, classification, DV variables and assumptions | best-practice steps, categories, data capture | vendor/CRO marketing, blogs, SOPs; content behind login logged as gap | research/R5_industry.yaml |

Adoption notices sit with the region (EMA in R3, FDA in R4), so no document has two owners. New source keys: UPPER-CASE with hyphens, listed in Rn_notes.md under "New source keys" with URL.

## 3. Common findings schema (YAML, one atomic obligation per record, one file per stem, sorted by id)

```yaml
- id: R3-004            # stem prefix + 3 digits, never reused
  src: EUCTR            # key from contracts/source_registry.yaml (or a new key listed in notes)
  doc: "<title, version, date>"
  url: "<url>"
  loc: "Art. 52(1)"     # grammar: P<n> | GL:<term> | A1-<sec> | A2-<sec> | AppB-<sec> | AppC-<sec> | Art.<n>(<p>) | 21CFR<part>.<sec>(<p>) | S<sec> (other documents: section number as printed)
  loc_alt: ""           # numbering in other version (E6R3-S4)
  page: "printed 12 / PDF 14"
  retrieval: "WebFetch 2026-11-06 offset 0"
  paraphrase: "..."
  quote: ""             # optional, fewer than 15 words, confirmed by a 2nd fetch
  modal: must|should|may|definition|example
  binding: binding-law|binding-ICH|guidance|best-practice|verify-binding
  draft: false
  binding_route: "EU: <how>; US: <how>"
  jurisdiction: ICH|EU|US
  party: "<verbatim role term>"
  party_norm: sponsor|investigator|irb-iec|authority|monitor|participant|other
  trigger: "..."
  action: "..."
  deadline: "..."       # or "none"
  recipient: "..."
  record: "..."
  step_hint: define|identify|document|classify|assess|mitigate|notify|report-csr|archive|other
  themes: [CtQ, RBQM, safety, data]
  related: []
  conflict_note: ""
  confidence: high|medium|low
  verify: []
```

ICH guidelines are never `binding-law`; record their regional route in `binding_route`.

## 4. YAML spec extensions (beyond the GEN-01 template)

```yaml
id: L4-03
level: L4
parent: {model: L3, node: A3}                # SCP-06
interface: {start: [S1], ends: [E1, E2], message_flows: [M2]}
pools:
  - {id: P_SPON, name: Sponsor, kind: internal, expanded: true}
  - {id: P_INV, name: Investigator/institution, kind: external, expanded: true}   # D1
  - {id: P_IEC, name: IRB/IEC, kind: external, expanded: false}
  - {id: P_RA, name: Regulatory authority, kind: external, expanded: false}
lanes: [{id: L_MON, name: <glossary role>, pool: P_SPON, src: [...]}]
nodes:
  - {id: A2, type: task, label: ..., lane: L_MON, calls: null,
     src: [{key: EUCTR, loc: "Art. 52(1)"}], req: [REQ-031],
     binding: binding-law, jurisdiction: [EU], deadline: "7 days",
     record: ..., group: GR_EU, path: main, verify: []}
flows: [{id: F3, from: G1, to: A4, label: "Yes", default: false}]
message_flows: [{id: M2, from: A3, to: P_RA, label: ..., src: [...], req: [...], binding: ..., deadline: ...}]
data: [{id: D1, type: data-object|data-store, label: ..., assoc: [{node: A2, dir: out}], src: [...]}]
groups: [{id: GR_EU, label: "EU CTR", members: [A2, A3]}]
rule_exceptions: [{rule: ROL-03, element: P_INV, reason: "..."}]
open_items: ["[verify] ..."]
```

Node types: task, call-activity, start, start-message, start-timer, end, xor-split, xor-join, and-split, and-join, or-split, or-join; intermediate events only as FLW-02 allows. The converter writes trace fields twice: plain text in `bpmn:documentation`, and `bpmn:extensionElements/ipd:trace` per `contracts/ipd_extension.md`. XML IDs: `<model>_<node>` (model id with "-" replaced by "_").

Model structure: one `definitions` file. L3 = collaboration (Sponsor pool with role lanes + external pools per D1); L3 steps are call activities referencing the L4 processes (SCP-07). Each L4 = its own collaboration, repeating the same external pools (LBL-05) and the L3 hand-offs (SCP-06). One BPMNDiagram per model; per-model exports too.

## 5. Validation loop (V1 reports; the owner repairs; max 3 rounds; escalate if a MUST error persists 2 rounds)

| Layer | Checks | Owner |
|---|---|---|
| L0 Contract | spec schema; IDs unique; references resolve; src keys in registry; REQ IDs exist | B1 |
| L1 Syntax | well-formed XML; XSD (OMG BPMN 2.0, from GitHub copy, SHA recorded, else logged not run); bpmn-moddle zero warnings; DI complete; isMarkerVisible; bpmnlint recommended | B2 |
| L2 Graph | reachability; block structure (DEC-05/06 annotated); FLW-03, FLW-08, FLW-09 | B1 |
| L3 Auto rules | SCP-03/04/06/07, FLW-01/06/07, LBL-01/02/03, ROL-01/02, LAY-04 | B1 (B2 for LAY-04, DI) |
| L4 Traceability | 100% in-scope binding REQs on an element; every task has src; element binding = strongest REQ binding; draft guidance shows DRAFT; verify findings give [verify] | B1 (Y1 if the finding is wrong) |
| L5 Render | W1 test suite re-run; self-containment | W1 |

Error record: rule_id, layer, model, element, message, owner.

## 6. Viewer requirements (W1)

bpmn-js NavigatedViewer bundle + CSS inlined from node_modules (page CSP: no external CSS; must be fully self-contained). XML and citations.json embedded. Call activity click opens its L4 diagram, breadcrumb back. Overlays under each task, event, gateway and message flow: short src keys + text badge (LAW, ICH, GUIDANCE, DRAFT, BP, VERIFY) - meaning never by colour alone (LAY-04). Click panel: document, loc, page, paraphrase, quote, binding route, REQ IDs, open [verify] items. Search/filter by source key, binding class, jurisdiction. Legend in the footer, not on the canvas. Copy-to-clipboard button for the .bpmn XML (page downloads are blocked by the sandbox). No alert/confirm/prompt. Storage only inside try/catch.

## 7. Risks to keep in view

1. E6(R3) numbering differs between consolidated 2026 and Step 4 2025; Principles vs Annex 1 vs Annex 2 can be confused - use the loc grammar with annex prefix and loc_alt.
2. WebFetch passes text through a small model: ask for verbatim text of a named section, page with offsets, confirm each quote with a second fetch; prefer paraphrase.
3. FDA-PD24 is a draft: guidance + draft: true, never the only basis for a binding step; check whether finalised.
4. "Important protocol deviation" (ICH/FDA) differs from "serious breach" (EU CTR Art. 52) and from IRB noncompliance reporting (21 CFR 56.108(b)): separate decisions and REQs, each with jurisdiction; conflicts logged.
5. ICH binding route differs by region: EU via CTR Art. 47 / EMA adoption [verify]; US guidance only, 21 CFR binds.
6. Article numbers in brief.md are not authoritative (e.g. urgent safety measures); take numbers from the regulation text.
7. Sponsor vs investigator duties: every finding carries a party; lanes only from glossary roles with src.
8. L4 size: if an L4 exceeds 31 nodes, re-cut via Y1 (never two child models per L3 step).
