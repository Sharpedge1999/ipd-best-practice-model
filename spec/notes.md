# B1 notes - model specs for the best-practice iPD reference model

Status: 07 Nov 2026, B1 repair round after V1 round 1 (`validation/report_r1.md`, `synthesis/changes_V1r1.md`; changes in the last section). Earlier: 06 Nov 2026, B1 re-entry 1, which applies the orchestrator decisions on the B1 questions, the X1 corrections (`synthesis/changes_X1.md`) and contract S0-18. Inputs: confirmed L3 cut (`synthesis/l3_cut.md`), `synthesis/requirements.yaml` and `merged_findings.yaml` (post-X1), `req_to_step.yaml`, `glossary.yaml`, `conflicts.md`. Rules: `context/bpmn-design-criteria.md`, `contracts/decisions.md` (S0-01 to S0-18), `contracts/spec.schema.json`.

## 1. Result

| Model | Title | Nodes | Activities | Message flows | Lanes | Investigator/institution |
|---|---|---|---|---|---|---|
| L3 | Important protocol deviation management - overview | 16 | 8 call activities | 12 | Monitor, Sponsor | collapsed |
| L4-01 | Define trial-specific iPD criteria | 24 | 16 | 2 | Sponsor | expanded |
| L4-02 | Identify protocol deviations | 26 | 16 | 7 | Sponsor, Monitor | expanded |
| L4-03 | Manage intentional protocol deviations | 32 | 14 (1 interface call activity) | 9 | Sponsor | expanded |
| L4-04 | Document and classify protocol deviations | 21 | 11 | 3 | Sponsor | expanded |
| L4-05 | Assess and notify reportable noncompliance | 28 | 12 (1 interface call activity) | 9 | Sponsor | expanded |
| L4-06 | Remediate deviations and noncompliance | 28 | 14 | 9 | Sponsor, Monitor | expanded |
| L4-07 | Finalise iPDs for clinical study report | 19 | 13 (2 interface call activities) | 2 | Sponsor | collapsed |
| L4-08 | Archive deviation records | 16 | 8 | 1 | Sponsor | expanded |

Checks on the final files:
- `python -I tools/lint_spec.py spec/*.yaml`: 0 errors, also with `--parent spec/L3.yaml`.
- B1 self-check: FLW-03/04/09 structure, LBL-03 split labels, no em dash, middle dot or bare "CTR", binding equals the strongest REQ binding, draft flag consistent, no `[verify]` item dropped, SCP-06 hand-offs matched by label and pools - 0 errors.
- Coverage: 134/134 in-scope binding REQs, 202/202 in-scope REQs and 40/40 interface REQs (`spec/coverage.md`).
- Dry run: see section 10.

## 2. Re-entry 1 changes per model

All existing ids are unchanged (GEN-05). The changes come from the orchestrator decisions of 06 Nov 2026 (numbered D-B1-n below) and contract S0-18.

| Model | Element | Change | Basis |
|---|---|---|---|
| L3 | P_INV | collapsed (`expanded: false`); ROL-03 rule exception removed | D-B1-1 |
| L3 | E1 | "iPDs reported in CSR and records archived" -> "iPDs reported in clinical study report and records archived" (D3 wording, same terms as L4-07 E1 and L4-08 S1) | D-B1-2 cross-model check |
| L3 | TA1 | new text annotation with the reading convention, associated with G1; group GR_CONDUCT kept | S0-18, D-B1-7 |
| L3 | notes | updated (reading convention, collapsed pool, hand-off selection) | S0-18 |
| L4-01 | TA1 | new text annotation on A7: no ICH or legal basis for deriving iPD criteria from CtQ factors (C-02) | S0-18 |
| L4-02 | E1, G3 | "Potential protocol deviation detected(?)" -> "Potential protocol deviation identified(?)" | D-B1-2 (LBL-05) |
| L4-03 | A4 | task -> call activity, `calls: null`, `interface: true` ("Handle urgent safety measures") | S0-18 |
| L4-03 | E2 | "Intentional deviation approved and implemented" -> "Deviation request approved" | D-B1-3 |
| L4-03 | E1 | "Immediate-hazard deviation implemented and reported" -> "Immediate hazard addressed" (same principle as D-B1-3: the sponsor addresses the hazard; the investigator implements and reports the deviation, investigator end E4 keeps the l3_cut label) | D-B1-3 applied by B1 - please confirm |
| L4-05 | A3, A12, F11, F31, GR_EU | the interface REQ-215 and REQ-216 move from task A3 to the new interface call activity A12 "Handle other EU notifications"; A3 keeps REQ-117 (binding now guidance); F11 A3 -> A12 (retargeted), new F31 A12 -> G4; A12 added to GR_EU | S0-18 |
| L4-07 | P_INV | collapsed; ROL-03 rule exception removed | D-B1-1 |
| L4-07 | A4, A13 | task -> interface call activity (`calls: null`, `interface: true`) | S0-18 |
| L4-03, L4-07 | notes | updated | - |

## 3. X1 corrections (`synthesis/changes_X1.md`)

The trace fields are derived from the current `requirements.yaml` and `merged_findings.yaml`. The files delivered at the end of the first entry (written after Y1's 14:27 rebuild) already used the corrected values, so re-entry 1 changes no field because of X1. Checked element by element:

| Change | Elements carrying it | Value in the spec |
|---|---|---|
| R2-115 page (REQ-019) | L4-01 A8, L3 A1 | M11-TEMPLATE S10.2 "printed 46 / PDF 55" |
| R2-116 page, page [verify] closed (REQ-016) | L4-01 A8, L3 A1 | S11.6 "printed 52 / PDF 61"; old [verify] absent |
| R2-117 page, page [verify] closed (REQ-015) | L4-01 A8, L3 A1 | S11.10 "printed 53 / PDF 62"; old [verify] absent |
| R5-071 pages (REQ-236) | L4-07 A13 | FDA-ESTUDY SII.E.1 "printed 7 ...; printed 2 ...; printed 3-5 ..." |
| REQ-154 deadline, record, [verify] closed | L4-07 A1 (deadline and record); L3 A7 ([verify] only, call activities carry no deadline or record) | deadline "before interim or final analysis; best practice: after the last study data have been reviewed"; record includes "closed-out PDAP"; old [verify] absent |
| REQ-111 statement | L4-05 S1, A2, M1; L3 M4 | statements are not spec fields; deadline unchanged |
| REQ-216 statement | L4-05 A12 | statement not a spec field; deadline unchanged |
| REQ-226 statement | L4-06 open_items #3 | the item names the process, not the statement; unchanged |
| REQ-252, R3-088 loc | none (REQ-252 is out of scope, cited nowhere in the specs) | - |
| Paraphrase corrections (R1-127, R2-017, R3-013, R3-025, R3-048, R3-085, R3-089, R4-016, R5-046, R5-048) | none: paraphrases are not spec fields; the viewer reads them from `merged_findings.yaml` | - |

## 4. How the specs are built

- GEN-02 stages per model: (1) activities and lanes, (2) flow and gateways, (3) L3 call activities and hand-offs, then SCP-06 matching (interface, identical labels and pools).
- Trace fields are derived from the REQs placed on an element, never typed by hand:
  - `src`: every finding of the element's REQs, `key` and `loc` exactly as in the finding plus its `page`; entries with the same key and loc are merged (pages joined with "; "); the strongest binding class comes first.
  - `binding`: strongest REQ binding. `draft: true` if any REQ of the element is draft.
  - `deadline` and `record`: from the REQs, with REQ ids where several differ. Call activities that call an L4 model carry no deadline or record.
  - `party`: verbatim finding party terms, research notes removed, overridden only where the derived list would name the wrong actor (L4-01 A16, M2; L4-04 A4, M1; L4-05 S1, M1; L4-08 M1). L4-03 A14 carries no `record`: the records of its REQs (protocol section 5.1; decision on request) are produced by A6 and A7.
  - `verify`: all `[verify]` items of the element's REQs, plus the element-specific items in section 7.
- L3 call activities carry every in-scope REQ of their step. Every in-scope REQ sits in the L4 of its own step.

## 5. Jurisdiction pattern

EU and US branches never exclude each other.

| Model | Pattern |
|---|---|
| L4-01 | XOR pair "EU CTR applies?" around A12 (GR_EU) |
| L4-02 | EU answer "Suspected serious breach (EU CTR)" on the investigator OR split G4 (GR_EU on A16) |
| L4-03 | OR split G2 "Which jurisdiction-specific actions apply?" with EU (A4) and US (A5) branches and default "Neither" |
| L4-05 | AND split G1 into an EU path (XOR "EU CTR applies?") and the ICH path; US XOR pair in the investigator process |
| L4-06 | XOR pairs at different points: EU G3-G4, US G7-G8 |
| L4-07 | XOR pairs in sequence: EU G1-G2, US G3-G4 |
| L4-08 | sponsor XOR pair EU G1-G2; investigator OR split G3 with EU, US and default "Neither" |

Jurisdiction branches are used only for obligations that exist in one region only; US guidance that refines a common step stays on the common task with `jurisdiction` showing US. Groups GR_EU "EU CTR", GR_EU2 (L4-08 investigator) and GR_US "US 21 CFR" cover adjacent members only.

## 6. FLW-05 - gateway and deciding element

All XOR and OR splits are listed. "Directly before" means that the activity directly before the gateway decides.

| Model | Gateway | Question | Deciding element |
|---|---|---|---|
| L4-01 | G3 | EU CTR applies? | trial attribute fixed at authorisation/set-up (no in-process decision) |
| L4-02 | G1 | Which monitoring channels are due? | L4-01 A10 "Develop risk-based monitoring plan" (the plan sets channels, methods and frequency, E6R3 A1-3.11.4.3), applied at timer start S1 |
| L4-02 | G3 | Potential protocol deviation identified? | L4-02 A11 "Review monitoring reports" (directly before) |
| L4-02 | G4 | Which additional reports are due? | L4-02 A13 "Document protocol deviation" (the documented deviation; A14 "Report deviation to sponsor" lies in between) |
| L3 | G5 | Intentional protocol deviation considered? | trigger attribute: the investigator's consideration of an intentional protocol deviation (the A3 trigger, L4-03 S2), communicated by M11/M12; no in-process sponsor decision |
| L4-03 | G1 | Immediate-hazard deviation reported? | L4-03 A14 "Review intentional protocol deviation communication" (directly before; added V1 round 1) |
| L4-03 | G2 | Which jurisdiction-specific actions apply? | trial attribute (EU CTR, IND) fixed at authorisation/set-up; whether the measure is an urgent safety measure follows from L4-03 A1 "Address immediate hazard and its causes" |
| L4-03 | G4 | Deviation from eligibility criteria requested? | L4-03 A14 "Review intentional protocol deviation communication" (reviews the request content sent by A12 "Request approval of intentional protocol deviation", message M3; G1 lies in between) |
| L4-03 | G6 | Deviation request approved? | L4-03 A6 "Reject eligibility waiver requests" or A7 "Decide on deviation request" (before join G5) |
| L4-03 | G7 | Immediate hazard to participants? | L4-03 A8 (directly before) |
| L4-03 | G8 | Deviation approved? | L4-03 A13 "Obtain IRB/IEC approval before deviating" (directly before; receives the sponsor and IRB/IEC decisions) |
| L4-03 | G9 | Submission of immediate-hazard information required? | applicable regulatory requirements (trial attribute), E6R3 A1-3.13.3 'if required' |
| L4-04 | G1 | Protocol deviation? | L4-04 A1 (directly before) |
| L4-04 | G2 | Important protocol deviation? | L4-04 A3 (directly before) |
| L4-04 | G4 | New type of iPD found? | L4-04 A6 (directly before) |
| L4-05 | G2 | EU CTR applies? | trial attribute fixed at authorisation/set-up (no in-process decision) |
| L4-05 | G3 | Serious breach? | L4-05 A1 (directly before) |
| L4-05 | G6 | Serious noncompliance? | L4-05 A5 (directly before) |
| L4-05 | G9 | Reportable noncompliance notified? | L4-05 A2 "Notify serious breach via EU portal" and A6 "Notify serious noncompliance" (outcomes of G3 and G6) |
| L4-05 | G10 | IND under 21 CFR 312? | trial attribute fixed at authorisation/set-up (no in-process decision) |
| L4-06 | G1 | Significant noncompliance? | L4-06 A1 "Decide action on escalated finding" (REQ-128; A2 "Set proportionate remedial actions" in the Monitor lane and A3 "Secure compliance" lie in between) |
| L4-06 | G3 | Serious breach notified under EU CTR? | L4-05 A2 "Notify serious breach via EU portal" (earlier step, carried in by S1) |
| L4-06 | G5 | Significant noncompliance persists? | L4-06 A5 "Implement and verify CAPA" (effectiveness check, REQ-137); "No" when G1 was "No" |
| L4-06 | G6 | Participation terminated? | L4-06 A8 "Consider terminating site participation" (A9 notifies in between) |
| L4-06 | G7 | IND under 21 CFR 312? | trial attribute fixed at authorisation/set-up (no in-process decision) |
| L4-07 | G1 | EU CTR applies? | trial attribute fixed at authorisation/set-up (no in-process decision) |
| L4-07 | G3 | Study data submitted to FDA? | submission attribute fixed at set-up (no in-process decision) |
| L4-08 | G1 | EU CTR applies? | trial attribute fixed at authorisation/set-up (no in-process decision) |
| L4-08 | G3 | Which retention rules apply? | trial attributes fixed at authorisation/set-up (no in-process decision) |

Every gateway has either a deciding element or a trial attribute. One deciding task was added in V1 round 1: L4-03 A14 before G1 (FLW-09/SCP-02 repair, orchestrator decision 1). The deciding tasks without their own named source step are L4-03 A8 and A14 (both marked [verify]).

## 7. Modelling choices

- **Interface placeholders (S0-18).** Interface call activities with `calls: null`, `interface: true`: L4-03 A4 "Handle urgent safety measures" (C-08), L4-05 A12 "Handle other EU notifications", L4-07 A4 "Handle statistical analysis and estimands", L4-07 A13 "Handle clinical study report and study data submission". Interfaces at a boundary event carry their REQs on that event: L4-01 S1 (REQ-203 to REQ-207), L4-04 S1 (REQ-213), L4-05 M1 (REQ-231). The remaining 21 interface REQs have no hand-off point inside the step and stay `open_items` entries tagged `[verify interface]`.
- **Text annotations (S0-18).** L3 TA1 (reading convention), L4-01 TA1 (C-02). Model-level `notes` (lists) are kept on every spec and are exported as process documentation under S0-18.
- **Collapsed Investigator/institution pool (D-B1-1).** Collapsed where it carries no tasks; D1 intent - investigator duties visible as tasks - unaffected. Same pool id and name on every model (LBL-05).
- **LBL-05 across models (D-B1-2).** One label per hand-off state: "Potential protocol deviation identified" (L4-02 E1, L4-04 S1, L4-05 S1); "iPDs reported in clinical study report" (L4-07 E1, L4-08 S1, now also inside L3 E1); "Protocol deviation identified at site" (L4-02 S2, L4-05 S2). A message and the start event that receives it use "<object> <participle>" and "<object> received" (for example "Deviation review requested" and "Deviation review request received"): message and receipt are different constructs. L3 has no event for the A2/A4 hand-off; the mapping is in coverage.md.
- **Sponsor end events (D-B1-3).** Sponsor ends state what the sponsor reaches. The l3_cut outcomes that the investigator reaches are investigator ends with the l3_cut label (coverage.md, "l3_cut outcomes").
- **C-10 (accepted, D-B1-4).** REQ-135 (21 CFR 312.56(b) either-or) is on L4-06 A3 "Secure compliance", before the ICH "consider termination" decision A8, and on A10; the termination path G6-G7-A10-E2 covers "end participation". The register text is aligned by the synthesis owner.
- **L3 hand-offs.** 12 hand-offs: 10 sent by a call activity (at most one per call activity and pool gap) and, since V1 round 1, the two investigator communications M11 "Immediate-hazard deviation reported" and M12 "Intentional protocol deviation request submitted" from the collapsed Investigator/institution pool into A3 (SCP-06); each reappears in its L4 with the same label and pools (L4-03 M1, M3).
- **Investigator reports in L4-02.** The deviation report and the premature unblinding explanation enter A1; the system incident and suspected serious breach reports enter the sponsor review A11.
- **L4-03 triggers.** Investigator process: one start event "Intentional protocol deviation considered"; A8 decides the immediate-hazard exception. Sponsor process (V1 round 1, orchestrator decision 1): one message start event "Intentional protocol deviation communicated" for the one business trigger, receiving M1 and M3; the deciding task A14 precedes G1. The label names the communication as a state (object + past participle, LBL-02) instead of the "<object> received" form, because it covers two messages.
- **Task orders where the sources set none** (L4-03 immediate-hazard path, L4-05 investigator process, L4-05 escalation task A11) keep message flow labels clear of each other (B2 gate G8).
- **C-12.** No investigator-to-authority flow is modelled; the sponsor submission follows l3_cut (REQ-082 with its EU [verify] item).
- **DEC-06** in `rule_exceptions`: L4-02 G3; L4-03 G1, G6, G7, G8; L4-04 G1; L4-05 G9; L4-06 G6.
- **Element-specific [verify] items:** L4-02 M6 (IRB/IEC only where applicable); L4-03 A8 (implied assessment step), A14 (implied review step); L4-06 M6 (drug disposition under 21 CFR 312.59 not extracted); L4-08 D1, D2 (request-driven access shown as data store).

## 8. SHOULD deviations (one-line reasons)

- SCP-03, L4-01: 16 activities - binding set-up steps (34 REQs, with the separations C-02 and C-04) need distinct tasks; 24 nodes.
- SCP-03, L4-02: 16 activities - user decision 06 Nov 2026 to merge the identification channels into one model; 26 nodes.
- SCP-03, L4-03: 32 nodes (target at most 31) - user-confirmed L3 cut; regulation gives both triggers (immediate-hazard deviation, deviation request) to one step, and the single Sponsor trigger needs the deciding task A14 (FLW-05); no node can be removed without losing sourced content.
- FLW-02 / FLW-07: OR gateways in L4-02, L4-03 and L4-08 for "one or more" cases, each with a `justification` (DEC-02); the default flows (L4-02 G4 "No further report", L4-03 G2 and L4-08 G3 "Neither") lead to the OR join.
- FLW-07, L4-02 G1: No default flow: the trigger 'Monitoring activity scheduled' guarantees at least one channel; a default flow would wrongly suppress centralised review whenever a site visit is due.
- ROL-03: Investigator/institution expanded in the L4 models with investigator tasks (D1); `rule_exceptions` there.
- LAY-03 (review): L4-01, L4-04, L4-06 and L4-07 were 3600-4700 px wide in the last successful render, more than one A3 page; the happy path stays on one line (LAY-01).

## 9. Open points

1. **L4-03 E1 relabel** "Immediate hazard addressed" applies decision D-B1-3 to the second sponsor end as well; please confirm.
2. **Layout with a collapsed Investigator/institution pool (for B2).** The layout puts collapsed pools other than the top band below the Sponsor pool in spec order. On L3 and L4-07 the collapsed P_INV therefore becomes a second bottom band between Sponsor and Regulatory authority. Sponsor-to-authority flows then find no route and get 0 waypoints. In a dry run without S0-18 constructs this produced XSD and G5 errors on L3 (M3, M4, M5, M8, M9) and L4-07 (M1, M2). Suggested converter fix: draw a collapsed pool that is expanded in other diagrams in its usual position, above the Sponsor pool, so the pool order is the same on every diagram. The spec-side alternative (changing the pool order per model) works for L4-07 only and was not applied.
3. **bpmnlint.** With P_INV collapsed, the start-event-required and end-event-required errors are gone (dry run without S0-18 constructs); only the expected no-inclusive-gateway warnings remain.

## 10. Dry run

`python -I tools/spec2bpmn.py --specs spec --out /tmp/b1_dry2/ipd.bpmn --models-out /tmp/b1_dry2/models` fails in spec2bpmn 1.0 (file dated 12:53) on the S0-18 construct `calls: null`: `flow_node` builds `calledElement` from `calls` (AttributeError on None). The converter is being updated in parallel and was not edited.

A scratch copy with only the S0-18 constructs reverted (interface call activities as tasks, no annotations) converts. Its B2 gate has failures only on L3 and L4-07, caused by the collapsed-pool layout in open point 2. All other diagrams pass.

## 11. Production note

The specs are generated by a scratch script outside the project (`/tmp/b1_work/gen.py`, `models.py`; not a deliverable). The YAML files in `spec/` are the source of truth. Repairs are targeted edits on the stable ids (GEN-05).

## B1 successor changes (06 Nov 2026)

- L4-03 E1 keeps "Immediate hazard addressed" (relabel reverted by the orchestrator: sponsor task A1 "Address immediate hazard and its causes", REQ-083, E6R3 A1-3.13.3); closes open point 1. L4-03 A3 made conditional: new XOR split G9 "Submission of immediate-hazard information required?" after A2 (F5 A2 -> G9 retargeted, new F31 "Yes" -> A3, F32 "No" -> G10) and XOR join G10 before G2 (F6 A3 -> G10 retargeted, new F33 G10 -> G2), FLW-04; REQ-082, its [verify] item and the "investigator/institution or sponsor" party text stay on A3; L4-03 now 31 nodes. Duplicate [verify] items removed on A6, M4, A11, M2 and L3 A3 (reverted in V1 round 1: every REQ verify string is carried verbatim).

## V1 round 1 repairs (07 Nov 2026)

Orchestrator decisions 1-10 on the B1 items of `validation/report_r1.md`, with `synthesis/changes_V1r1.md`. Targeted edits on stable ids (GEN-05); new ids: L4-03 A14, F34; L3 M11, M12.

| Model | Element | Change | Decision |
|---|---|---|---|
| L3 | G1, G2, F3, F4 | AND split/join -> OR split "Intentional protocol deviation considered?" (with `justification`) / OR join; F3 to A2 default "Always", F4 to A3 "Yes" | 3 (FLW-08) |
| L3 | M11, M12 | new hand-offs P_INV -> A3 "Immediate-hazard deviation reported", "Intentional protocol deviation request submitted" (trace as L4-03 M1, M3) | 2 (SCP-06) |
| L3 | TA1, notes | reading convention: gateways show channels open in parallel (OR and AND); 12 hand-offs | 2, 3 |
| L3 | A3 | REQ-075 and REQ-086 verify strings verbatim again | 8 |
| L3, L4-01 | M1 | deadline from REQ-026 only (REQ-027 deadline now none) | 10 |
| L4-01 | A6 | "Define trial-specific iPD criteria" -> "Specify criteria for important protocol deviations" | 4 (LBL-05) |
| L4-01 | A12 | deadline removed (REQ-027, REQ-028, REQ-029: none) | 10 |
| L4-02 | A10, F12-F14, GR_SITE | A10 after the OR join G2, Monitor lane (F12 A9 -> G2, F13 A10 -> A11, F14 G2 -> A10 retargeted); A10 leaves GR_SITE | 5 |
| L4-03 | S1, A14, F1, F34, interface | S1 "Deviation request or immediate-hazard report received" -> "Intentional protocol deviation communicated"; new deciding task A14 "Review intentional protocol deviation communication" (REQ-073, REQ-080, REQ-074); F1 S1 -> A14 retargeted, new F34 A14 -> G1; interface.message_flows M1, M3, M8 | 1 (FLW-09, SCP-02) |
| L4-03 | A9 | "Deviate to eliminate immediate hazard" -> "Implement protocol deviation to eliminate immediate hazard" (verb + object; the example "Deviate from protocol ..." keeps the intransitive "deviate from" that V1 LBL-01 flags; "implemented" matches E4) | 4 (LBL-01) |
| L4-03 | A12, E5, M3, M6 | "intentional deviation" -> "intentional protocol deviation" | 4 (LBL-04) |
| L4-03 | A5 | deadline "subsequently (no period stated)" (REQ-085 only) | 6, 10 |
| L4-03 | A6, M4, A11, M2 | REQ-075 and REQ-086 verify strings verbatim again | 8 |
| L4-04 | A4, A10, M2 | "important deviation" -> "important protocol deviation"; A10 "Review protocol deviation and explain if important" | 4 (LBL-04) |
| L4-05 | E2 | "No notification required and rationale documented" -> "No notification required" (l3_cut A5 outcome) | 7 (SCP-02) |
| L4-07 | A6, A9, A10, A13, notes | bare "CSR" -> "clinical study report" | 4 (LBL-04) |
| L4-08 | A1, A4, A7 | "non-important deviations" -> "non-important protocol deviations"; A4 and A7 "Archive content of clinical trial master file" (EU CTR Art. 58; sponsor and investigator part, distinguished by pool) | 4 (LBL-04) |

L3 labels stay identical to the L4 labels (LBL-05): L3 M11/M12 = L4-03 M1/M3; L3 has no event or task with any other changed label. Open for the l3_cut owner (Y1): the A3 trigger line names no Sponsor start label (V1 matches the Sponsor start against it), and l3_cut keeps the short forms "Intentional deviation considered?", "Intentional deviation request submitted" and the outcome "Intentional deviation approved and implemented" (L4-03 E5 now uses the glossary form; coverage.md documents the realisation).

Checks after the repairs (07 Nov 2026): `lint_spec` 0 errors, also with `--parent spec/L3.yaml`; `b2_gate --no-render` dry run into /tmp: PASS (layout.py sha256 22e18b23...; an earlier run with the layout.py version before 16:33 UTC failed G8 on L3 M2, M11 and L4-02 M2, the last also on the pre-repair specs); `tools/validate/v1_spec.py`: 6 items, of which 4 SHOULD are documented (SCP-03 L4-01, L4-02, L4-03; SCP-06 L4-03 E5 label) and 2 MUST stay open at L4-03 S1 outside B1: FLW-09 (V1 counts the two message labels into S1 as two triggers; decision 1 makes them one business trigger) and SCP-06 (V1 matches the Sponsor start against the l3_cut A3 trigger line, which names no Sponsor start label). Specs not re-frozen while V1 has open MUST items.

Orchestrator decision 07 Nov 2026 on V1 FLW-09 at L4-03 S1: one message start event for one business trigger, recorded as `rule_exceptions` entry FLW-09 on S1 (two message types; two starts would break SCP-02, splitting A3 would change the user-confirmed L3 cut; revisitable). SCP-06 at S1 stays with the synthesis owner (l3_cut A3 trigger line).

## V1 round 2 repairs (07 Nov 2026)

| Model | Element | Change | Basis |
|---|---|---|---|
| L3 | G1, G2, G5, G6, F3, F4, F6, F16-F18, GR_CONDUCT | OR split/join replaced (an OR default flow runs only when no other condition holds, so A2 would not start whenever A3 does): AND split G1 -> A2 (F3) and -> new XOR split G5 "Intentional protocol deviation considered?" (F4 retargeted); F16 "Yes" -> A3, F17 "No" -> new XOR join G6; F6 A3 -> G6 retargeted, new F18 G6 -> AND join G2; OR justification removed; G5, G6 added to GR_CONDUCT; L3 now 16 nodes | V1 r2 FLW-07 (MUST), orchestrator |
| L4-03 | A14 | REQs now the sponsor REQs of the routed paths: REQ-083 (immediate hazard), REQ-075 and REQ-076 (deviation request) instead of the investigator REQs REQ-073, REQ-080, REQ-074 (these stay on A10, A12, M1, M3); src, binding (binding-ICH), draft, jurisdiction, deadline, party and verify derived from them; [verify] "review step implied by the routing; no source names it as a separate step" | V1 r2 GEN-03, orchestrator |

Open for the l3_cut owner (Y1): l3_cut.md still shows G1/G2 as OR split/join with default flow to A2.

## OR default flow repairs (07 Nov 2026)

An OR default flow is taken only when no other outgoing condition holds (OMG BPMN 2.0.2 10.6.3). Checked every OR split: L4-03 G2 and L4-08 G3 default to the join ("Neither") and stay; L4-02 G1 and G4 changed.

| Model | Element | Change |
|---|---|---|
| L4-02 | G1, F2, F3 | both flows conditional, no default: "Centralised data review due", "Site monitoring visit due"; justification updated; FLW-07 SHOULD deviation in section 8 |
| L4-02 | A14, G4, F20, F21, F24 | A14 "Report deviation to sponsor" moved before the OR split (F20 A13 -> A14, F24 A14 -> G4 retargeted); G4 "Which reports are due?" -> "Which additional reports are due?"; F21 retargeted to the OR join G5 as default "No further report"; src, req, verify of A14 and its message flows M3, M4 unchanged; 26 nodes |

Open for the l3_cut owner (Y1): l3_cut.md A2 still describes "Centralised data review" as the default flow of the channel split.
