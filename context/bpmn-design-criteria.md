---
name: bpmn-design-criteria
description: Design rules for descriptive BPMN 2.0 process models - scope and hierarchy, flow logic, labels, roles, layout, and LLM-based generation and validation. Use for any BPMN modelling, review or model generation, As-Is or To-Be.
metadata:
  version: 1.1.0
  last_changed: 2026-10-16
  depends_on: none
---

# BPMN 2.0 Design Criteria

- **Scope:** descriptive BPMN 2.0 models of clinical development processes (hierarchy levels L3-L5), documented in ARIS and validated by process owners. Not intended for executable models.
- **Precedence:** within this file, `MUST` rules come first, including the exceptions they name. Then come the decisions in section 7, then `SHOULD` defaults. The OMG specification settles any question of BPMN syntax that these rules leave open.
  - Cross-file precedence: (1) the user's explicit instruction for the current task - if it overrides a `MUST` rule or guard, name the rule and state the conflict before applying it, (2) bpmn-design-criteria.md for how a model is drawn, labelled and generated, (3) process-redesign-checks.md for which process changes are proposed.
- **Conventions:**
  - Keywords: `MUST` and `SHOULD` carry the meaning defined in BCP 14 (RFC 2119, RFC 8174) only when written in capitals.
  - Status tags: `[verify]` (optionally with a topic, e.g. `[verify binding]`) marks an unconfirmed fact or a gap in the source; `[proposal]` marks a To-Be change that awaits the process owner's decision; `[unresolved: <ID>]` marks a rule ID whose file is not loaded and whose title and gist do not settle the question.
  - Output rules: write model content in English; use no client names and no names of individuals; use a hyphen "-" instead of an em dash.
- **Terms:**
  - L3-L5 are levels of the process hierarchy. L3 is the process overview; L4 is the detailed model of one L3 step. The definition of L5 is `[verify]`.
  - Element IDs are the stable IDs in the model spec, e.g. S1, A1, G1, E1 (see Spec template).
- **Basis:** OMG BPMN 2.0.2 (still current; ISO/IEC 19510:2013 mirrors 2.0.1) and peer-reviewed BPM research.

## How to use this file

- **Modelers (human or LLM):** apply every `MUST`. Deviate from a `SHOULD` only with a one-line reason in the model notes.
- **Reviewers:** report findings by rule ID, e.g. `FLW-04 at G2`.
- **Check tags:** `auto` means the rule can be checked from the model spec by a script or an LLM self-check. `review` means it needs human judgement.

## 1. Scope and hierarchy (SCP)

- **SCP-01 `MUST` One purpose per model.** Model only what serves the stated purpose. Use the same conventions for As-Is and To-Be. `review` [GoM00]
- **SCP-02 `MUST` Clean sub-process boundaries.** Each sub-process has one trigger, one entry point and named outcomes. Cut at business milestones or around one business object. `review` [JOH12, MIL16]
- **SCP-03 `SHOULD` Size target.** Aim for 5-15 activities per diagram and at most 31 nodes. Nodes are activities, events and gateways. `auto` [M13, ZUG15]
- **SCP-04 `MUST` Decompose above 50 elements.** `auto` [7PMG, MNA07]
- **SCP-05 `SHOULD` Hierarchy across levels, groups within a level.** Decompose across levels (L3 -> L4). Inside one diagram, chunk related elements with Groups, not with collapsed sub-processes. `review` [TUR20, ZUG15]
- **SCP-06 `MUST` Lossless levels.** Each parent step maps to exactly one child model. The child's start and end events match the parent step's input and output. Every hand-off in the parent reappears in the child. `auto` [JOH12]
- **SCP-07 `SHOULD` Reuse instead of duplicating.** Model a step that appears in several models once, and reference it as a Call Activity. `auto` [OMG 10.3.6]

## 2. Elements and flow logic (FLW)

- **FLW-01 `MUST` Restricted palette.** Use the Descriptive conformance set: tasks, sub-processes and call activities; start events (none, message, timer) and end events; XOR and AND gateways; sequence flows and message flows; pools, lanes, data objects, data stores, groups and text annotations. `auto` [OMG 2.2, ZMR08]
- **FLW-02 `SHOULD` Analytic elements only on demand.** Add OR gateways, default and conditional flows, boundary and intermediate events, or loop markers only when the business rule requires them. `review` [OMG 2.2]
- **FLW-03 `MUST` Explicit gateways.** Route every split and every join through a gateway. Every activity has exactly one incoming and one outgoing sequence flow. `auto` [COR18, LMG16; DEC-01]
- **FLW-04 `MUST` Block structure.** Close every split with a join of the same type. A gateway either splits or joins, never both. The exceptions are set out in DEC-05 and DEC-06. `auto` [7PMG, MNA07; OMG 10.6]
- **FLW-05 `MUST` Gateways route, activities decide.** Place the decision in the activity before the gateway. `review` [OMG 10.6]
- **FLW-06 `SHOULD` Lean gateways.** Give a gateway at most 3 branches. Use as few gateway types per diagram as possible. `auto` [MNA07, RM11, M13]
- **FLW-07 `SHOULD` OR only for "one or more".** Use an OR gateway only where several paths may run together. Pair it with an OR join and a default flow so that at least one path is always taken. `auto` [7PMG, SAP08; OMG 10.6.3; DEC-02]
- **FLW-08 `MUST` AND only for concurrent work.** Never join alternative paths with an AND join. `auto` [MNA07; OMG 10.6.4]
- **FLW-09 `MUST` Start and end events.** Use one start event per trigger, and one end event per distinct business outcome; keep end events few. Start events have no incoming flow, and end events have no outgoing flow. `auto` [7PMG, COR18; OMG 10.5; DEC-03, DEC-06]

## 3. Labels and terminology (LBL)

- **LBL-01 `MUST` Activities: verb + object, imperative.** Good: `Classify potential iPD`. Bad: `iPD classification` (action noun), `CRA: classify PD` (compound with ":"). `auto` [MRR10, LSM11]
- **LBL-02 `MUST` Events: object + past participle, written as a state.** The start event names the trigger; the end event names the outcome. Good: `iPD identified`. Bad: `Identify iPD`, `End`. `auto` [LEM13]
- **LBL-03 `MUST` Splitting gateways: a question ending in "?"** Label each outgoing flow with its answer. Good: `Important protocol deviation?` with flows `Yes` and `No`. `auto` [LEM13; OMG By Example]
- **LBL-04 `MUST` Terms verbatim.** Take terms from the source document and the project glossary, with one term per concept. `review` [LMG16, MRR10]
- **LBL-05 `MUST` One construct per meaning.** On every level, the same real-world thing keeps the same element type and the same name. `review` [FMS13]

## 4. Roles and collaboration (ROL)

- **ROL-01 `MUST` Lanes are roles.** Use one partition type per pool, and never mix roles with systems or organisational units. Name roles, never persons. `auto` [OMG 10.8, FIG17]
- **ROL-02 `MUST` Pool boundaries.** Sequence flows stay inside one pool. Message flows connect only separate pools and never attach to gateways or lanes. `auto` [OMG 7.6, 9.3-9.4]
- **ROL-03 `SHOULD` Internal vs external.** Show internal roles as lanes of one pool. Show external parties (e.g. sites, vendors, authorities) as collapsed pools linked by message flows. `review` [OMG 9.3-9.4]

## 5. Layout (LAY)

- **LAY-01 `SHOULD` Left-to-right in time order.** Keep the happy path on one straight line and branch exceptions off it. `review` [FS15, BUR18, COR18]
- **LAY-02 `SHOULD` Minimise edge crossings first, then bends.** Run message flows at 90 degrees to the main flow. `review` [PUR97; OMG 7.6]
- **LAY-03 `SHOULD` One A3 page per diagram.** `review` [LMG16]
- **LAY-04 `MUST` Visible markers, no colour-only meaning.** Show the X marker on every XOR gateway. Never carry meaning by colour alone. `auto` [FMS13; OMG 2.2.3, 12.1.1]

## 6. LLM generation and validation (GEN)

- **GEN-01 `MUST` Structured spec, not XML.** The LLM writes a schema-bound text spec (template below). A deterministic converter builds the target format. `auto` [KOU24a, SAF25]
- **GEN-02 `SHOULD` Generate in stages.** Order: (1) activities and roles, (2) flow and gateways, (3) sub-processes. `review` [BEL22, KOU24a]
- **GEN-03 `MUST` No invention.** Every As-Is element traces to the source. Gaps and ambiguities become `[verify]` items, never assumptions. To-Be changes are proposals: mark them `[proposal]` and state their basis. `review` [KLI24, KOU24b]
- **GEN-04 `MUST` Layered validation with a bounded repair loop.** 1. Check syntax and references. 2. Check reachability and block structure. 3. Check all `auto` rules in this file. Feed each error back with its rule ID. After a fixed number of attempts, stop and escalate. `auto` [SOU26, KOU24a]
- **GEN-05 `SHOULD` Targeted edits, not regeneration.** Revise the model on its stable IDs, and re-check every format conversion. `auto` [KLI24, HOR26]
- **GEN-06 `MUST` Process owners confirm content.** Check syntactic correctness first. Fit to the real process is confirmed by the process owner, never by the LLM. `review` [GoM00, KLI24]

### Spec template (GEN-01)

```yaml
id: L4-xx
title: <L3 step name>
lanes: [<role>, <role>]
nodes:
  - {id: S1, type: start, label: <object + past participle>, lane: <role>}
  - {id: A1, type: task, label: <verb + object>, lane: <role>, src: <source section>}
  - {id: G1, type: xor-split, label: <question?>, lane: <role>}
  - {id: E1, type: end, label: <outcome as state>, lane: <role>}
flows:
  - {from: S1, to: A1}
  - {from: A1, to: G1}
  - {from: G1, to: A2, label: "Yes"}
open_items:
  - "[verify] <gap or ambiguity in the source>"
```

## 7. Decisions where sources conflict (DEC)

- **DEC-01 Explicit gateways.** Decision: explicit gateways, because the readers are business users.
- **DEC-02 OR gateways.** Decision: allowed as an exception under FLW-07.
- **DEC-03 End events.** Decision: one end event per business outcome.
- **DEC-04 Lanes.** Decision: keep lanes, roles only.
- **DEC-05 Structuredness.** Decision (project): FLW-04 applies, but an unstructured fragment is accepted, with a note, when restructuring would duplicate activities.
- **DEC-06 Exclusive branches with their own outcome.** Decision (project): an XOR branch that represents a distinct business outcome may end in its own end event without a join; AND and OR branches always rejoin, because their joins synchronise.

## 8. Evidence limits

- The size and gateway thresholds come from EPC error data and student experiments, not from descriptive BPMN.
- Answer labels on gateway flows (LBL-03) rest on OMG examples, not on empirical studies.
- The LLM evidence covers models from 2023-2025, and part of it is preprints.

## Regulatory sources already cited in the project's redesign-check file (starting points, not exhaustive)

- E6R3: ICH E6(R3) Guideline for Good Clinical Practice, Step 4 (2025), consolidated with Annex 2 (2026): https://database.ich.org/sites/default/files/ICH%20E6%28R3%29_Step4_FinalConsolidatedGuideline_2026_0616_.pdf
  - Sections referenced in the project: Principle 7, Principle 10.1, 2.5.3, 2.5.4, 3.9.3, 3.9.6, 3.10.1, 3.10.1.3, 3.11.4.2(b), 3.11.4.5.1(b), 3.11.4.6(c), 3.12.2, Appendix C (essential records), Annex 1 3.1.4
- E8R1: ICH E8(R1) General considerations for clinical studies, Step 4 (2021), sections 3.2-3.3 (critical to quality factors): https://database.ich.org/sites/default/files/E8-R1_Guideline_Step4_2021_1006.pdf
- EUCTR: Regulation (EU) No 536/2014 - Art. 41 (SAE investigator to sponsor 24 h), Art. 42 (SUSARs 7/15 days), Art. 52 (serious breach 7 days), Art. 4: https://health.ec.europa.eu/system/files/2016-11/reg_2014_536_en_0.pdf
- EMA23: EMA Guideline on computerised systems and electronic data in clinical trials (2023)
- 21CFR11 / FDA24: FDA 21 CFR Part 11 and Q&A Rev. 1 (2024)
