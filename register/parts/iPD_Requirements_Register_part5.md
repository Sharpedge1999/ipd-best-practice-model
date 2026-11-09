# iPD Requirements Register - part 5 of 6

Part of ipd-best-practice/iPD_Requirements_Register_part1..6.md (status, scope and method in part 1). This part starts at: 5. Conflicts

## 5. Conflicts

| ID | Conflict | Findings | Handling in the model | Decision |
|---|---|---|---|---|
| C-01 | Four separate decisions: important protocol deviation, EU serious breach, serious noncompliance, IRB serious or continuing noncompliance | R1-032, R1-033, R1-074, R1-075, R1-077, R2-067, R3-023, R3-024, R3-043, R3-062, R3-072, R3-075, R3-076, R4-028, R4-036, R4-072, R4-074 | Four separate decisions, each with its own jurisdiction badge: (1) "Important protocol deviation?" in A4 (REQ-094); (2) "Serious breach?" in A5, EU branch (REQ-105, REQ-111); (3) "Serious noncompliance?" in A5, ICH branch (REQ-118, REQ-119), with the persistent case in A6 (REQ-146); (4) the IRB/IEC decision stays inside the collapsed IRB/IEC pool and appears only as its binding message flows to the Regulatory authority and Investigator/institution pools (REQ-124). A4 and A5 run in parallel so that no decision waits for another. All iPDs and, for EU trials, all serious breaches go to the CSR (REQ-166, REQ-180). | decided by user 06 Nov 2026 - L3 cut with A4 (iPD classification) and A5 (reportability) in parallel; the four decisions stay separate. |
| C-02 | CtQ factors to iPD criteria: no source states the link directly | R1-032, R2-003, R2-004, R2-007, R2-027, R2-073, R2-116, R2-117, R4-042, R4-080, R5-009, R5-015, R5-058, R5-059, R5-064 | The chain is shown as a sequence of separately sourced steps, without inventing a requirement: start event "CtQ factors identified" (REQ-001 adherence aspects, E8R1 S6.1.1) -> "Identify risks to CtQ factors" (REQ-002) -> "Evaluate risks to CtQ factors" (REQ-003) -> "Document critical data and processes" (REQ-004, guidance) -> "Specify criteria for important protocol deviations" (REQ-010, binding-ICH: E6R3 A1-3.9.3 with E3QA S3 determinants). The explicit CtQ link is the separate task "Link iPD criteria to CtQ factors" (REQ-013, guidance, DRAFT), never shown as ICH or legal. | orchestrator default, not contested (06 Nov 2026) - the model claims no ICH or legal basis for deriving iPD criteria from CtQ factors; REQ-013 stays DRAFT. |
| C-03 | 21 CFR 312.66 "promptly report all changes in the research activity" vs FDA-PD24 on minor deviations | R1-013, R1-016, R4-011, R4-023, R4-025, R4-072, R4-074 | A5 US branch: the investigator reports to the IRB under the IRB's written procedures; the binding REQ-121 is kept with a [verify] item; the DRAFT split (REQ-122 iPDs when identified, REQ-123 others not immediately) is shown as DRAFT. The model does not state that minor deviations are exempt from 312.66. | orchestrator default, not contested (06 Nov 2026) - the IRB's written procedures decide what is reported when; [verify] on 21 CFR 312.66 stays (REQ-121). |
| C-04 | "Acceptable ranges" in two senses, and "important deviation" meaning a QTL exceedance | R1-041, R1-042, R1-109, R5-049, R5-050, R5-051, R5-052, R5-053 | Separate REQs and tasks: "Set acceptable ranges for CtQ risks" (REQ-006, A1), "Evaluate acceptable range exceedance" (REQ-044, A2), "Build flexibility into protocol provisions" (REQ-021, A1). Labels never call an exceedance a "deviation"; glossary.yaml records both senses. | orchestrator default, not contested (06 Nov 2026) |
| C-05 | EU 7-day serious breach clock: starts at awareness of a potential breach; whose awareness counts is undefined | R3-023, R3-048, R3-049, R3-051, R3-098 | Deadline label "at the latest 7 (calendar) days from sponsor awareness of the potential breach" on the serious breach message flow (REQ-111); the clock starts at the A5 start event, which is the same event as the A4 start; A4 and A5 run in parallel. The awareness party is left as written in the sources ("sponsor") with a [verify] item. | decided by user 06 Nov 2026 - the clock starts at sponsor awareness of a potential breach as the sources say; [verify] on whose awareness counts stays; no assumption about monitor, CRO or delegated party awareness. |
| C-06 | Regional binding route of ICH guidelines | R1-086, R1-087, R1-088, R1-089, R1-090, R3-016, R3-017, R3-018, R3-019, R3-020, R3-085, R3-087, R3-088, R4-065, R4-078, R4-079, R5-002, R5-048 | ICH findings stay binding-ICH (never binding-law) and every ICH REQ carries its regional route in binding_route: EU via Art. 47 and EMA adoption dates, US guidance only. ICH-only REQs are guidance-level in the US. Annex 2-based content carries a [verify] on the EU effective date (REQ-035). REQs resting on E8R1, E3, E3QA, E9, E9R1 or M11 carry "[verify binding]". Registry binding_default of E3QA and M11 moved to binding-ICH (Step 4 documents) with a [verify binding] note. | orchestrator default, not contested (06 Nov 2026) - E3 Q&A (R1) and M11 are binding-ICH with [verify binding]. |
| C-07 | Article numbers in the brief | R3-013, R3-027 | Article numbers are taken from the regulation text only. | orchestrator default, not contested (06 Nov 2026) |
| C-08 | EU urgent safety measures vs immediate-hazard deviations | R1-022, R1-023, R1-024, R1-079, R1-080, R3-027, R3-028, R3-029, R3-030, R3-100, R3-101, R3-102, R3-103, R3-104 | Default: A3 hands off through the OR "Which jurisdiction-specific actions apply?" to the interface call activity "Handle urgent safety measures"; REQ-217 to REQ-220 are interface REQs with reason. No USM notification task inside A3. | decided by user 06 Nov 2026 - EU urgent safety measures stay an interface placeholder from A3 (REQ-217 to REQ-220). |
| C-09 | Prospective eligibility waivers: not permitted (M11) vs approved single-participant departure (FDA-PD24) | R2-113, R4-037, R4-048 | A3 follows the stronger class: "Deviation from eligibility criteria requested?" -> "Reject eligibility waiver requests" (REQ-075); the FDA example is recorded in REQ-021 (protocol flexibility) and REQ-074 (prior sponsor and IRB approval for other intentional deviations). | decided by user 06 Nov 2026 - eligibility waivers are not permitted (M11 S5.1, REQ-075); the FDA-PD24 example is recorded as DRAFT only. |
| C-10 | Site closure: "consider" vs binding either-or | R1-076, R4-013, R4-014, R4-071 | In A6 the binding US either-or duty (REQ-135, 21CFR312.56(b)) sits on the task "Secure compliance" together with REQ-134 (E6R3 A1-3.12.1), before the ICH task "Consider terminating site participation" (REQ-145); there is no separate US branch. Termination notifications: REQ-146 (ICH) and REQ-148 (US). Placement accepted in V1 round 1 (07 Nov 2026). | orchestrator default, not contested (06 Nov 2026) |
| C-11 | Immediate-hazard IRB notification timing | R1-012, R1-023, R4-005, R4-030 | Deadline label "promptly (ICH); US: per 21 CFR 56.104(c) [verify 5 working days]" (REQ-086). Notifying party not named; Investigator chosen with [verify]. | orchestrator default, not contested (06 Nov 2026) |
| C-12 | Who notifies authorities | R1-024, R1-080, R3-051, R3-071, R3-086 | EU authority message flows start only in the Sponsor pool; an Investigator-to-authority flow is labelled "where applicable (not EU)" (REQ-082). The investigator-to-sponsor serious breach flow is shown as guidance (REQ-069). | orchestrator default, not contested (06 Nov 2026) |
| C-13 | "Seven days" vs "7 calendar days" | R3-023, R3-048, R3-090 | Deadline "7 days (calendar days per EMA-SB S3.2)" with the Art. 52 citation (REQ-111). | orchestrator default, not contested (06 Nov 2026) |
| C-14 | Minor wording differences in EU texts | R3-023, R3-032, R3-037, R3-043 | Regulation wording is used in labels; differences recorded as [verify] on REQ-105. | orchestrator default, not contested (06 Nov 2026) |
| C-15 | Root cause analysis owner | R1-072, R3-060, R3-067, R4-068 | Root cause analysis tasks in the Sponsor lane (REQ-136, REQ-138); the investigator's own preventive measures are a separate task (REQ-133). | orchestrator default, not contested (06 Nov 2026) |
| C-16 | Deviation category schemes | R2-057, R3-079, R3-080, R4-044, R4-045, R5-026, R5-065 | The categorise task (REQ-096) requires a controlled category list without fixing a scheme; alignment is a [verify] item. | orchestrator default, not contested (06 Nov 2026) |
| C-17 | Terminology: important / major / critical / significant; violation / deviation | R2-069, R2-070, R2-077, R2-078, R2-079, R2-080, R2-081, R2-082, R2-083, R2-084, R2-085, R2-086, R2-087, R2-088, R2-089, R2-090, R2-091, R2-092, R2-093, R2-094, R4-041, R4-087, R5-004 | Labels use "important protocol deviation" and "protocol deviation"; E9 wording stays in the cited paraphrases only (REQ-270, glossary.yaml). | orchestrator default, not contested (06 Nov 2026) |
| C-18 | GCP compliance issues that are not protocol deviations | R1-071, R1-123, R4-038, R5-001, R5-007 | A4 asks "Protocol deviation?" first (REQ-088); a non-deviation exits A4 through the end event "Issue handled outside the deviation process", but it is still assessed in A5 (serious noncompliance, serious breach) and remediated in A6, because A5 runs from the same trigger. | orchestrator default, not contested (06 Nov 2026) |
| C-19 | Reporting of non-important deviations | R2-072, R3-065, R4-057, R5-003, R5-037, R5-069 | CSR text carries iPDs (A7, REQ-166 to REQ-168); the DV dataset carries all deviations for US submissions (REQ-185); non-important deviations are documented and filed in A4 (REQ-091, REQ-092). | orchestrator default, not contested (06 Nov 2026) |
| C-20 | Origin of reporting clocks | R1-012, R1-023, R1-093, R3-098, R4-054 | A1 sets the sponsor-defined reporting timeframe (REQ-026); each deadline label states its origin (occurrence, awareness, measures taken). | orchestrator default, not contested (06 Nov 2026) |
| C-21 | Premature unblinding as a deviation | R1-093, R4-039, R4-045 | A2 keeps the binding report-to-sponsor task (REQ-067); whether it is an iPD is decided by the trial-specific criteria in A4. | orchestrator default, not contested (06 Nov 2026) |
| C-22 | Basis for iPD content in the CSR | R1-045, R1-100, R2-055, R2-058, R3-064 | iPD CSR content rests on E3 (REQ-166 to REQ-168); E6(R3) is cited only for the quality management approach and important quality issues (REQ-181, REQ-182). R2-072 (E3QA) is marked dup_of R2-055. | orchestrator default, not contested (06 Nov 2026) |
| C-23 | Retention periods by region; US sponsor retention not extracted | R1-028, R3-035, R3-036, R4-021 | Separate EU and US archive tasks with jurisdiction groups (REQ-194, REQ-195, REQ-199); the US sponsor retention gap is listed for R4. | orchestrator default, not contested (06 Nov 2026) |
| C-24 | Weak binding basis for "site reports deviations to sponsor" | R1-018, R1-019, R1-023, R1-093, R1-095, R3-051, R3-071, R4-010, R4-047 | The A2 message flow "Protocol deviation reported" is shown as DRAFT guidance (REQ-066); binding flows are shown separately. | orchestrator default, not contested (06 Nov 2026) |
| C-25 | Lane attribution inferred where sources name no actor | R1-057, R1-058, R1-059, R1-060, R1-061, R1-062, R1-063, R1-064, R1-065, R1-066, R1-067, R1-068, R1-069, R1-101, R1-102, R1-103, R1-104, R1-105, R1-106, R1-107, R1-108, R5-024 | Monitor lane for the A1-3.11.4.5 items (lane source A1-3.11.4.4, A1-3.11.4.5.1(a)), Sponsor lane for section 4 items, each with a [verify] item in the REQ. | orchestrator default, not contested (06 Nov 2026) |
| C-26 | Y1 merge decisions across jurisdictions and duplicates |  | binding_route shows how each binding class arises. Six findings are dup_of a canonical finding of the same REQ (R5-002, R2-072, R1-013, R3-099, R3-092, R3-078); they stay in the REQ's source list. | orchestrator default, not contested (06 Nov 2026) |
| C-27 | One start event for two message types at L4-03 S1 (FLW-09 rule exception) | R1-023, R4-010, R4-048 | spec/L4-03.yaml S1 "Intentional protocol deviation communicated" is one message start event receiving M1 and M3, followed by an XOR that routes the immediate-hazard and the request case; recorded as a rule exception (FLW-09) in the spec. | orchestrator decision 07 Nov 2026 - documented FLW-09 rule exception (one business trigger, two message types); revisitable by the user. |

## 6. Open [verify] items

201 items on 127 REQs (finding-level items carry the finding id in brackets).

- **REQ-001** (in_scope, A1): [verify] carried by the A1 start event 'CtQ factors identified' (no separate task); closest ICH text to a CtQ-to-iPD link (C-02); [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06)
- **REQ-003** (in_scope, A1): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F02) (R2-008)
- **REQ-004** (in_scope, A1): [verify] single fetch (R5-063)
- **REQ-005** (in_scope, A1): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06)
- **REQ-006** (in_scope, A1): [verify] trial-level sense of 'acceptable ranges' (A1-3.10.1.3), distinct from the protocol-provision sense of AppB-Intro (C-04)
- **REQ-008** (in_scope, A1): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F02) (R2-010)
- **REQ-009** (in_scope, A1): [verify] principle without named party; Sponsor lane assigned by context
- **REQ-010** (in_scope, A1): [verify binding] EU/US adoption of E3QA not checked by the research stems (C-06)
- **REQ-011** (in_scope, A1): [verify binding] EU/US adoption of E3QA not checked by the research stems (C-06); [verify] examples from one fetch (R5-027)
- **REQ-012** (in_scope, A1): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-013** (in_scope, A1): [verify] no ICH guideline or regulation states that iPD criteria derive from CtQ factors; the link rests on FDA-PD24 (draft) and best practice (C-02); [verify] single fetch (R5-015); [verify] single fetch (R5-064); [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-014** (in_scope, A1): [verify] element list from one detailed fetch; PDAP template (XLSX) not readable (R5-013); [verify] element list from one detailed fetch (R5-014)
- **REQ-015** (in_scope, A1): [verify binding] EU/US adoption of M11-TEMPLATE not checked by the research stems (C-06)
- **REQ-016** (in_scope, A1): [verify binding] EU/US adoption of M11-TEMPLATE, E8R1 not checked by the research stems (C-06)
- **REQ-019** (in_scope, A1): [verify binding] EU/US adoption of E9, M11-TEMPLATE not checked by the research stems (C-06); [verify] sentence content from a single fetch (F19) (R2-076); [verify] instruction text from a single fetch (F29); heading listed in F28 (R2-115)
- **REQ-020** (in_scope, A1): [verify binding] EU/US adoption of E9, E9R1 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F19) (R2-078)
- **REQ-021** (in_scope, A1): [verify] protocol-provision sense of 'acceptable ranges' (AppB-Intro), distinct from A1-3.10.1.3 (C-04)
- **REQ-022** (in_scope, A1): [verify binding] EU/US adoption of M11-TEMPLATE not checked by the research stems (C-06)
- **REQ-025** (in_scope, A1): [verify] Sub-section (IV.D.1 vs IV.D.2) and printed page of the sentence on recording and reporting critical deviations differ between fetches (R4-084); [verify] Printed page of IV.D.2 passage (TOC says 15; fetches gave 16 and 17) (R4-085)
- **REQ-026** (in_scope, A1): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-033** (in_scope, A1): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F05) (R2-029); [verify] full verbatim role wording of bullet 7 (fetch F08 truncated after 'by sponsor') (R2-040)
- **REQ-034** (in_scope, A1): [verify] single detailed fetch for the study-team part (R5-018); [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-035** (in_scope, A2): [verify] R1-089 is Annex 2: effective in the EU from 15 Jan 2027; FDA Annex 2 guidance still draft (C-06)
- **REQ-036** (in_scope, A2): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06)
- **REQ-037** (in_scope, A2): [verify] gerund item under A1-3.11.4.5; actor not named (R1 C7)
- **REQ-039** (in_scope, A2): [verify] section 4 duty of the 'responsible party' (investigator or sponsor); Sponsor lane chosen (R1 C14)
- **REQ-041** (in_scope, A2): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-044** (in_scope, A2): [verify] 'deviation beyond these ranges' is a range exceedance, not a protocol deviation (C-04)
- **REQ-046** (in_scope, A2): [verify] single fetch (R5-025); [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-053** (in_scope, A2): [verify] gerund item; Monitor lane inferred from A1-3.11.4.4 and A1-3.11.4.5.1(a) (R1 C7)
- **REQ-054** (in_scope, A2): [verify] gerund item; Monitor lane inferred (R1 C7)
- **REQ-055** (in_scope, A2): [verify] gerund item; Monitor lane inferred (R1 C7)
- **REQ-056** (in_scope, A2): [verify] gerund item; Monitor lane inferred (R1 C7)
- **REQ-064** (in_scope, A2): [verify] 21 CFR 312.62(b) does not name deviations; applied as the US record basis for site documentation
- **REQ-066** (in_scope, A2): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-067** (in_scope, A2): [verify] E6(R3) does not label premature unblinding a protocol deviation; trial-specific criteria decide (R1 C13)
- **REQ-070** (in_scope, A3): [verify] E6(R3) A1-1.4.7 frames this as an IRB/IEC written procedure; the party initiating the change is not named
- **REQ-072** (in_scope, A3): [verify] represented by the IRB/IEC approval message flow; IRB/IEC is a collapsed pool (D1)
- **REQ-074** (in_scope, A3): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-075** (in_scope, A3): [verify] whether the M11 Template sentence is fixed text or instructional text (R2-113); [verify binding] EU/US adoption of M11-TEMPLATE not checked by the research stems (C-06); [verify] whether the sentence is fixed universal text or instructional text of the template (R2-113)
- **REQ-076** (in_scope, A3): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-077** (in_scope, A3): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-082** (in_scope, A3): [verify] in the EU all submissions are made by the sponsor, not the investigator (EUCTR-QA Q&A 1.5) (C-12)
- **REQ-085** (in_scope, A3): [verify] Whether the 5-working-day window of 21CFR56.104(c) applies to IRB notification of immediate-hazard protocol changes, or only the manner of notification; regulation text gives the cross-reference only (R4-005)
- **REQ-086** (in_scope, A3): [verify] whether the 5-working-day window of 21 CFR 56.104(c) applies to immediate-hazard protocol changes (C-11); [verify] notifying party not named (passive voice); Investigator chosen because 21 CFR 312.66 places IRB reporting on the investigator; [verify] Whether the 5-working-day window of 21CFR56.104(c) applies to IRB notification of immediate-hazard protocol changes, or only the manner of notification; regulation text gives the cross-reference only (R4-005); [verify] eCFR text of 56.104(c) not retrievable (robots); confirm against eCFR or govinfo before X1 (R4-030)
- **REQ-087** (in_scope, A3): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-088** (in_scope, A4): [verify binding] EU/US adoption of E3QA not checked by the research stems (C-06); [verify] the Q&A item is unnumbered under heading '3. TERMINOLOGY'; fetch tool rendered its row label as '7 June 2012', which may be a row number 7 plus 'June 2012' (R2-066)
- **REQ-089** (in_scope, A4): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-090** (in_scope, A4): [verify] Art. 56(1) applies to 'the sponsor or the investigator, as applicable'; applies equally in the Investigator/institution pool
- **REQ-091** (in_scope, A4): [verify] documenting party not named in the text (R3-065)
- **REQ-094** (in_scope, A4): [verify binding] EU/US adoption of E3QA not checked by the research stems (C-06); [verify] single detailed fetch; wording 'reasonable to consider' not confirmed verbatim (R5-003); [verify] Decision Tree image (TCB asset, robots-blocked) not read; branch logic unknown (R5-005); [verify] Fig. 5 content not readable (R5-016)
- **REQ-095** (in_scope, A4): [verify] 'the identifier' may sit in the Sponsor or the Investigator/institution pool; source does not say
- **REQ-096** (in_scope, A4): [verify] alignment of ICH E3, best-practice and CDISC DVCAT categories unknown (C-16); [verify binding] EU/US adoption of E3 not checked by the research stems (C-06); [verify] which four categories are ICH E3 (R2 to cross-check E3 10.2) (R5-026); [verify] codelist terms not read; check whether they match the seven TCB categories (R5-065); [verify] codelist terms and first release date not read (R5-066)
- **REQ-100** (in_scope, A4): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-101** (in_scope, A4): [verify] single fetch (R5-023); [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-105** (in_scope, A5): [verify] EMA-SB glossary refers to the 'approved protocol version', Art. 52(1) to the version applicable at the time of the breach (C-14)
- **REQ-111** (in_scope, A5): [verify] whose awareness (delegated party, CRO, monitor) starts the clock is not defined (C-05); [verify] 'seven days' (Art. 52(1)) read as calendar days per EMA-SB S3.2 (C-13)
- **REQ-113** (in_scope, A5): [verify] Appendix III a form content not in the text layer (local copy also empty; form is an image or form object) (R3-056)
- **REQ-120** (in_scope, A5): [verify] E6(R3) does not state whether a protocol deviation counts as such a 'change' (C-03); [verify] duty may lie with investigator or sponsor (A1-2.4.6)
- **REQ-121** (in_scope, A5): [verify] 21 CFR does not state whether a protocol deviation is a 'change in the research activity'; IRB written procedures decide (C-03)
- **REQ-122** (in_scope, A5): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-123** (in_scope, A5): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-124** (in_scope, A5): [verify] represented by message flows from the collapsed IRB/IEC pool to the Regulatory authority and Investigator/institution pools (D1); [verify] 21 CFR defines neither 'serious' nor 'continuing'; no source maps iPD to this trigger (C-01)
- **REQ-125** (in_scope, A5): [verify] reporting party not stated in the source (R5-037); [verify] single fetch (R5-037)
- **REQ-129** (in_scope, A6): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06)
- **REQ-130** (in_scope, A6): [verify] gerund item; Monitor lane inferred (R1 C7)
- **REQ-131** (in_scope, A6): [verify] gerund item; Monitor lane inferred (R1 C7)
- **REQ-132** (in_scope, A6): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-138** (in_scope, A6): [verify] FDA-PD24 names 'the sponsor or clinical investigator' for the root cause analysis (C-15)
- **REQ-139** (in_scope, A6): [verify] 'updating their analysis' (lines 324-325) does not say which analysis is meant (root-cause or statistical analysis) (R4-069); [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-143** (in_scope, A6): [verify] party is the party where the breach occurred (sponsor, CRO or investigator); Sponsor lane by default
- **REQ-144** (in_scope, A6): [verify] against CTIS sponsor handbook v6.4 section 4.9 (p. 140) (R3-097); [verify] printed section label of the guide not captured (loc names the topic 'other types of notifications') (R3-097); [verify] local copy not available (shell fetch returned HTTP 404 page, vendor/sources/CTIS-TM05/doc_17.txt) (R3-097)
- **REQ-149** (in_scope, A6): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06)
- **REQ-151** (in_scope, A6): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06); [verify] single fetch (R5-019)
- **REQ-153** (in_scope, A6): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-156** (in_scope, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F19) (R2-085); [verify] glossary wording from a single fetch (F20) (R2-096)
- **REQ-157** (in_scope, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06); [verify] printed page: 23 per F19, 24 per F21 (R2-087); [verify] printed page: 23 per F19, 24 per F21 (R2-086)
- **REQ-158** (in_scope, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F19) (R2-084)
- **REQ-160** (in_scope, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06)
- **REQ-161** (in_scope, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06)
- **REQ-162** (in_scope, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F20) (R2-089)
- **REQ-163** (in_scope, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06)
- **REQ-164** (in_scope, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06)
- **REQ-165** (in_scope, A7): [verify binding] EU/US adoption of E9R1 not checked by the research stems (C-06)
- **REQ-166** (in_scope, A7): [verify binding] EU/US adoption of E3, E3QA not checked by the research stems (C-06); [verify] single fetch (R5-036); [verify] single fetch (R5-038)
- **REQ-167** (in_scope, A7): [verify binding] EU/US adoption of E3 not checked by the research stems (C-06); [verify] single fetch (R5-040)
- **REQ-168** (in_scope, A7): [verify binding] EU/US adoption of E3 not checked by the research stems (C-06)
- **REQ-169** (in_scope, A7): [verify] Exact wording and modal of footnote 16 (BIMO Technical Conformance Guide reference) not double-checked (R4-055); [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-170** (in_scope, A7): [verify binding] EU/US adoption of E3 not checked by the research stems (C-06)
- **REQ-171** (in_scope, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06)
- **REQ-172** (in_scope, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06)
- **REQ-173** (in_scope, A7): [verify binding] EU/US adoption of E3 not checked by the research stems (C-06)
- **REQ-174** (in_scope, A7): [verify binding] EU/US adoption of E3, E9 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F11) (R2-059)
- **REQ-175** (in_scope, A7): [verify binding] EU/US adoption of E3 not checked by the research stems (C-06)
- **REQ-176** (in_scope, A7): [verify] single fetch (R5-039)
- **REQ-177** (in_scope, A7): [verify binding] EU/US adoption of E3QA not checked by the research stems (C-06)
- **REQ-178** (in_scope, A7): [verify binding] EU/US adoption of E3QA, E3 not checked by the research stems (C-06); [verify] annex page numbers read from footers; fetch F13 warned they may be off by one (R2-064)
- **REQ-179** (in_scope, A7): [verify] single fetch (R5-041)
- **REQ-183** (in_scope, A7): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06)
- **REQ-184** (in_scope, A7): [verify binding] EU/US adoption of E3QA not checked by the research stems (C-06); [verify] answer content from a single fetch (F33); topic confirmed in F16 (R2-065)
- **REQ-185** (in_scope, A7): [verify] page number: fetches gave 16 and 17 of 97 (R5-069); [verify] secondary mirror of NCIt; SDTMIG v3.4 DV text (purpose, assumptions) behind CDISC login, not read (R5-068)
- **REQ-186** (in_scope, A7): [verify] DVCLASI is in the SDTMIG v4.0 public review draft only (R5-067); [verify] SDTMIG v4.0 publication status and final DVCLASI definition (R5-067); [verify] slide 36 wording from one fetch (R5-067); [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-187** (in_scope, A7): [verify] page number: fetches gave 16 and 17 of 97 (R5-070); [verify] variable meanings glossed from CDISC naming, SDTMIG text not read (R5-070)
- **REQ-188** (in_scope, A8): [verify] duty of 'sponsor and investigator/institution'; applies in both pools
- **REQ-201** (in_scope, A8): [verify] single fetch (R5-033)
- **REQ-202** (in_scope, A8): [verify] single fetch (R5-006)
- **REQ-203** (interface, A1): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F02) (R2-005); [verify] sentence content from a single fetch (F02) (R2-006)
- **REQ-204** (interface, A1): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06)
- **REQ-205** (interface, A1): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F03) (R2-014); [verify] sentence content from a single fetch (F03) (R2-017)
- **REQ-206** (interface, A1): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06); [verify] detail from web page fetch only (R5-057)
- **REQ-207** (interface, A1): [verify binding] EU/US adoption of M11, M11-TEMPLATE not checked by the research stems (C-06); [verify] section content from a single fetch (F30); Step 4 status confirmed in F26 (R2-111); [verify] section label of the conventions part and wording; single fetch (F31) (R2-112)
- **REQ-222** (interface, A6): [verify binding] EU/US adoption of E8R1 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F05) (R2-028)
- **REQ-229** (interface, A5): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-236** (interface, A7): [verify binding] schema has no 'binding guidance' class; mapped to binding-law because the statute (745A(a)) plus guidance text state binding effect (R5-071); [verify] Data Standards Catalog not read; confirm SDTM/SDTMIG versions supported (R5-071); [verify] start dates from one fetch (R5-071)
- **REQ-237** (interface, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06); [verify] section content from a single fetch (F20); start page 24 per TOC and F22, 25 per F20 (R2-090)
- **REQ-238** (interface, A7): [verify binding] EU/US adoption of E9 not checked by the research stems (C-06)
- **REQ-239** (interface, A7): [verify binding] EU/US adoption of E9R1 not checked by the research stems (C-06); [verify] exact sentence boundaries; confirmed only as short phrases (F24) (R2-103)
- **REQ-240** (interface, A7): [verify binding] EU/US adoption of E9R1 not checked by the research stems (C-06)
- **REQ-241** (interface, A7): [verify binding] EU/US adoption of E3 not checked by the research stems (C-06); [verify] section content from a single fetch (F14); section number confirmed in TOC (F10) (R2-053)
- **REQ-242** (interface, A7): [verify binding] EU/US adoption of E3 not checked by the research stems (C-06)
- **REQ-250** (out_of_scope): [verify] single fetch (R5-054)
- **REQ-252** (out_of_scope): [verify binding] Y1 to confirm class: 'take appropriate account' (Art. 47) is weaker than law; binding-ICH used per brief definition (ICH adopted by authority, route stated) (R3-087); [verify binding] same class question as R3-087 (R3-088)
- **REQ-255** (out_of_scope): [verify] Check fda.gov for a final E6(R3) Annex 2 guidance before B1; only the guidance landing page was read (content current as of 12/30/2024) (R4-079)
- **REQ-261** (out_of_scope): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-265** (out_of_scope): [verify] basis is draft guidance only - shown as DRAFT, never a binding step
- **REQ-270** (out_of_scope): [verify binding] EU/US adoption of E3QA not checked by the research stems (C-06)
- **REQ-271** (out_of_scope): [verify binding] EU/US adoption of E9R1 not checked by the research stems (C-06); [verify] sentence content from a single fetch (F23) (R2-098); [verify] sentence content from a single fetch (F23) (R2-099); [verify] sentence content from a single fetch (F23) (R2-101); [verify] only the opening words of the glossary definition were returned verbatim (F24) (R2-110)
