# Brief - Best-practice iPD process model (BPMN 2.0)

Status: 06 Nov 2026. Shared brief for every sub-agent in this workflow. Read it fully before starting.

## Goal

Model the process for managing **important protocol deviations (iPD)** in clinical development as a **best-practice reference process** (outside-in, derived from regulation, guidelines and recognised industry practice - NOT the sponsor's internal As-Is). The model must cover **every regulatory binding step** and show, for every modelled element, the source(s) it rests on.

## Mandatory sources

- **ICH E6(R3) GCP** (Step 4, 2025; consolidated with Annex 2, 2026) - principles, investigator and sponsor responsibilities on protocol compliance and deviations, risk-based quality management, monitoring, noncompliance, essential records.
- **Critical to Quality factors (CtQ)** - ICH E8(R1) sections 3.2-3.3 and how E6(R3) uses them (risk-based quality management, quality tolerance limits / risk thresholds, trial-specific definition of important deviations).

Further candidate sources (to be confirmed by scope): ICH E3 (CSR section 10.2) and E3 Q&A on protocol deviations, ICH E9/E9(R1) (analysis sets/intercurrent events), EU CTR 536/2014 (Art. 38 urgent safety measures, Art. 52 serious breach, Art. 47, CTIS), EMA serious breach guideline, EMA guidance on protocol deviations (if any), FDA 21 CFR 312 / 56 / 50, FDA draft guidance "Protocol Deviations for Clinical Investigations of Drugs, Biological Products, and Devices" (Dec 2024), TransCelerate protocol deviation toolkit, CDISC SDTM DV domain.

## Output

1. An **interactive BPMN 2.0 map** (self-contained HTML page) that renders genuine BPMN 2.0 notation, with an L3 overview and L4 detail models, and shows the sources **under each modelled step** (visible on the canvas, with full citation on click).
2. A standards-conformant **BPMN 2.0 XML file** (.bpmn with DI) so the model can be imported into modelling tools.
3. A **requirements / findings register** (markdown) that anchors every research finding with source, section, binding status and the model element(s) it supports. This register is persisted as a project document and summarised in persistent memory by the orchestrator.

## Hard rules (apply to every agent)

- **No invention.** Every element and every source claim must trace to a document the agent actually read. Section numbers and quotes are checked against the source text. If something cannot be confirmed, mark it `[verify]` - never fill the gap from memory.
- **Binding classification for every requirement:** `binding-law` (regulation/statute, e.g. EU CTR, 21 CFR), `binding-ICH` (ICH guideline adopted by authorities - binding via regional adoption, mark how), `guidance` (non-binding agency guidance, drafts flagged as draft), `best-practice` (industry, e.g. TransCelerate). If unsure: `[verify binding]`.
- **Quotes:** max one short quote (< 15 words) per source per finding; otherwise paraphrase. Always give document, section/article and (where available) page.
- **BPMN rules:** `/home/claude/ipd/context/bpmn-design-criteria.md` governs how the model is drawn, labelled, generated and validated (GEN-01 spec first, deterministic converter, GEN-04 validation).
- **Output language English.** Hyphen "-" instead of em dash. No middle dot "·". No client/company names, no names of individuals. Roles are named as roles.
- Write all files below `/home/claude/ipd/`. Never write outside it.

## Context: the sponsor's As-Is L3 cut (for later comparability only - do not copy content)

As-Is L3 "Trial Issue and Deviation Management" has six steps: 1 Define trial-specific iPD categories; 2 Identify iPDs through data review; 3 Identify iPDs through site monitoring; 4 Document and follow up iPDs; 5 Assess and mitigate iPD impact; 6 Finalize iPDs for CTR reporting. The best-practice model may align its L3 cut to this where the regulatory logic allows, to ease a later comparison, but must keep its own cut where regulation implies a different structure. It must not adopt sponsor-specific role names, systems or document names.
