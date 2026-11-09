# Handover - Best-practice iPD reference model (BPMN 2.0)

Status: 07 Nov 2026, FINAL build. Outside-in reference model derived from ICH, EU and US sources plus industry best practice. Validation verdict: pass with documented exceptions. Not validated by process owners (GEN-06) - fit to the real process is open.

Interactive map (artifact, private to the owner until shared): https://claude.ai/artifact/KFND8HNzkGywuYu4RRgxmR

## 1. Purpose and scope

- Model the management of important protocol deviations (iPD) in clinical development as a best-practice reference process covering every regulatory binding step, with the sources shown under each modelled step.
- Mandatory sources: ICH E6(R3) GCP (consolidated Step 4 text incl. Annex 2, 16 Jun 2026) and critical to quality factors (ICH E8(R1) 3.2-3.3, E6(R3) Principle 6.2, Appendix B.12.1).
- Jurisdictions: ICH + EU (EU CTR 536/2014, EMA, EC Q&A v7.4) + US (21 CFR 312/56/50 as of 04 Nov 2026, FDA guidance incl. the Dec 2024 draft on protocol deviations - still draft) + industry best practice (TransCelerate, CTTI, CDISC). UK and devices out of scope (gaps).
- Lanes: generic GCP roles named by the sources ("Sponsor", "Monitor"). Pools: Sponsor (internal); Investigator/institution (external, expanded where it carries tasks - ROL-03 exception; collapsed on L3 and L4-07); IRB/IEC and Regulatory authority (collapsed).
- Depth: L3 overview plus exactly one L4 model per L3 step. Boundary: "CtQ factors identified" to "iPDs reported in clinical study report and records archived". "CTR" in As-Is step 6 is read as clinical study report; EU CTR is always written out.

## 2. Model (8 L3 steps, user-confirmed cut of 06 Nov 2026)

| L3 | Step (L4 model) | Trigger -> outcome(s) | As-Is | Nodes / activities | In-scope REQs |
|---|---|---|---|---|---|
| A1 | Define trial-specific iPD criteria (L4-01) | CtQ factors identified -> iPD criteria and plans approved | 1 | 24 / 16 | 34 |
| A2 | Identify protocol deviations (L4-02) | Monitoring activity scheduled -> potential protocol deviation identified / monitoring completed without finding | 2 + 3 | 26 / 16 | 35 |
| A3 | Manage intentional protocol deviations (L4-03) | Intentional protocol deviation communicated -> immediate hazard addressed / deviation request approved / rejected | new | 32 / 14 | 18 |
| A4 | Document and classify protocol deviations (L4-04) | Potential protocol deviation identified -> classified / handled outside the deviation process | 4 | 21 / 11 | 17 |
| A5 | Assess and notify reportable noncompliance (L4-05, parallel to A4) | Potential protocol deviation identified -> reportable noncompliance notified / no notification required | new | 28 / 12 | 22 |
| A6 | Remediate deviations and noncompliance (L4-06) | Deviation classified and reportability decided -> CAPA completed / investigator participation terminated | 5 (+4) | 28 / 14 | 27 |
| A7 | Finalise iPDs for clinical study report (L4-07) | Data finalisation initiated -> iPDs reported in clinical study report | 6 | 19 / 13 | 34 |
| A8 | Archive deviation records (L4-08) | iPDs reported in clinical study report -> deviation records archived | new | 16 / 8 | 15 |

L3 flow: start - A1 - AND split (A2 always | XOR "Intentional protocol deviation considered?" -> A3) - AND join - AND split (A4 | A5) - AND join - A6 - A7 - A8 - end. Steps A2-A6 recur during trial conduct (text annotation; no loop markers).

## 3. Evidence base

- Research: 5 stems (ICH E6(R3); ICH E8(R1)/E3/E3 Q&A/E9/E9(R1)/M11; EU; US; industry), 537 findings. Official full texts of 34 documents downloaded and hash-logged for checking (EUR-Lex not reachable - EU CTR checked against the OJ L 158 text; TransCelerate toolkit files and SDTMIG v3.4 not accessible).
- Requirements: 271 REQs - 202 in scope, 40 interface, 29 out of scope; binding-law 59, binding-ICH 138, guidance 58 (24 rest on draft guidance only, marked DRAFT), best-practice 16; modal must 59, should 183, may 16 (shown as MAY), definition 11, example 2. 100% of the 134 in-scope binding REQs sit on model elements.
- Blind verification (X1): 427 findings (all binding findings, all quotes, 25% sample of the rest) checked against the source texts - 414 confirmed first pass, 13 corrected and re-confirmed; 170/170 quotes verbatim.
- Independent validation (V1, GEN-04, 3 rounds): round 3 verdict pass with documented exceptions; 0 open MUST.

## 4. Decisions and documented exceptions

- User decisions (06 Nov 2026): jurisdictions ICH + EU + US; generic GCP roles; L3 + one L4 per step; 8-step cut (identification channels merged into A2); EU 7-day serious breach clock starts at sponsor awareness of a potential breach, whose awareness counts stays [verify]; EU urgent safety measures as interface; eligibility waivers not permitted (ICH M11).
- Orchestrator decisions (not contested): IRB written procedures decide what is reported when under 21 CFR 312.66 [verify]; E3 Q&A and M11 binding-ICH [verify binding]; service providers as interface, no pool.
- C-27 (revisitable, user to confirm): L4-03 has one message start event "Intentional protocol deviation communicated" receiving two message types (immediate-hazard report, deviation request) - documented FLW-09/SCP-02 exception; alternative is splitting A3 into two L3 steps.
- Documented SHOULD deviations: SCP-03 (L4-01, L4-02 16 activities; L4-03 32 nodes); FLW-07 at L4-02 G1 (no default flow, because an OR default flow is only taken when no other branch applies); L4-06 and L4-07 wider than A3; conditionExpressions on flows written for bpmnlint; per-model L3.bpmn cannot resolve its callees alone; bpmn.io watermark (licence) can overlap pool labels.
- Key content conflicts handled (full list C-01 to C-27 in register part 5): four separate reportability decisions (iPD, EU serious breach, E6(R3) serious noncompliance, IRB serious or continuing noncompliance); no ICH or legal text links CtQ factors to iPD criteria directly - shown as separately sourced steps, the direct link only as DRAFT/best practice; "acceptable ranges" in two senses in E6(R3).

## 5. Deliverables and files

- Interactive map (published, see top): bpmn-js 18.31.1 and diagram-js-minimap 5.6.0 from cdn.jsdelivr.net with SRI; model and citations as own files. Offline single-file version: out/ipd_best_practice_map.html (build workspace).
- BPMN 2.0 XML: out/ipd_best_practice.bpmn (sha256 37a8b9c9...; one definitions file with L3 and eight L4 collaborations, DI, ipd:trace extension urn:ipd-best-practice:trace:1.0) and per-model files out/models/.
- Requirements register: project docs ipd-best-practice/iPD_Requirements_Register_part1.md to part6.md (part 1: status, method, summary, A1; part 2: A2-A5; part 3: A6-A8; part 4: interface and out-of-scope REQs; part 5: conflicts C-01 to C-27 and open [verify] items; part 6: source list).
- Build workspace (this session only): contracts/, research/R1-R5, synthesis/, spec/ (frozen, FROZEN.sha256), tools/, verification/, validation/report_r1-r3, vendor/sources/INDEX.md.

## 6. Open items

- Process-owner confirmation (GEN-06) before any use as a To-Be basis; the As-Is comparison and role mapping (As-Is roles vs generic GCP roles) are a separate next step.
- User confirmation of C-27 and of the L3 reading convention (text annotation, FLW-05 at L3 G5).
- [verify] items on requirements and elements (register part 5, section 6), e.g. whose awareness starts the EU 7-day clock, 21 CFR 56.104(c) window for immediate-hazard changes, regional adoption of E8(R1)/E3/E3 Q&A/E9/E9(R1)/M11.
- Gaps: CTIS sponsor handbook 4.9; TransCelerate toolkit files; SDTMIG DV assumptions; 21 CFR 312.32/312.33/312.57 not extracted; import into ARIS not tested.
