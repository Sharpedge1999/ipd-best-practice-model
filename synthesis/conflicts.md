# Conflicts and tensions (Y1 synthesis)

Status: 07 Nov 2026 (C-27 added; earlier entries 06 Nov 2026), Y1 re-entry after the L3 checkpoint (steps renumbered A1-A8; every conflict carries its decision and date). Every conflict or tension found in the research notes R1-R5 and in the Y1 merge. Nothing is resolved silently: each entry names the finding ids on each side, the handling in the model and whether the user must decide. Field layout is parsed by `tools/render_register.py` (one `## C-nn` heading per conflict, then the bold fields).

## C-01 Four separate decisions: important protocol deviation, EU serious breach, serious noncompliance, IRB serious or continuing noncompliance

- **Side A:** Important protocol deviation - trial-specific criteria and definition (significant effect on data reliability or on participant rights, safety, well-being): R1-032, R1-033 (E6R3 A1-3.9.3), R2-067 (E3QA S3), R4-036 (FDA-PD24 SII, DRAFT).
- **Side B:** EU serious breach - breach of EU CTR or of the applicable protocol likely to affect to a significant degree safety and rights or data reliability and robustness; sponsor notifies Member States within 7 days: R3-023, R3-024 (EUCTR Art. 52), R3-043, R3-062 (EMA-SB: an important deviation is not necessarily a serious breach and vice versa).
- **Side C:** Serious noncompliance (E6(R3)) - issues likely to significantly impact participants or reliability of results; sponsor notifies authority and/or IRB/IEC per applicable requirements, no deadline: R1-074, R1-075, R1-077 (E6R3 A1-3.12.2, A1-3.12.3).
- **Side D:** IRB serious or continuing noncompliance (US) - IRB written procedures for prompt reporting to institutional officials and FDA; 21 CFR defines neither 'serious' nor 'continuing': R4-028 (21CFR56.108(b)(2)); investigator route R4-072, R4-074 (FDA-PD24, DRAFT).
- **Tension:** Similar wording ("significant", "serious") but different owners, triggers, recipients, clocks and binding classes. No source maps one concept onto another. Overlaps named by sources only: persistent or systematic non-compliance (R3-075), data removed from analysis (R3-076), potential fraud (R3-072).
- **Handling in the model:** Four separate decisions, each with its own jurisdiction badge: (1) "Important protocol deviation?" in A4 (REQ-094); (2) "Serious breach?" in A5, EU branch (REQ-105, REQ-111); (3) "Serious noncompliance?" in A5, ICH branch (REQ-118, REQ-119), with the persistent case in A6 (REQ-146); (4) the IRB/IEC decision stays inside the collapsed IRB/IEC pool and appears only as its binding message flows to the Regulatory authority and Investigator/institution pools (REQ-124). A4 and A5 run in parallel so that no decision waits for another. All iPDs and, for EU trials, all serious breaches go to the CSR (REQ-166, REQ-180).
- **User decision:** No (regulation-driven); the parallel A4/A5 cut was confirmed at U1.
- **Decision:** decided by user 06 Nov 2026 - L3 cut with A4 (iPD classification) and A5 (reportability) in parallel; the four decisions stay separate.

## C-02 CtQ factors to iPD criteria: no source states the link directly

- **Side A:** ICH texts that would carry the link do not state it: E6R3 A1-3.9.3 names no CtQ factors (R1-032 conflict note); none of the nine 'critical to quality' passages in E6(R3) links CtQ to iPD classification (R1 notes C3); E8R1 S3.2 does not mention deviations (R2-003, R2-004, R2-007); M11 S11.6 (CtQ) and S11.10 (deviations) are adjacent but unlinked (R2-116, R2-117).
- **Side B:** What the sources do say: E8R1 S6.1.1 counts many aspects of protocol adherence among the CtQ factors (R2-027, binding-ICH); E3QA S3 says the trial-specific iPD definition depends on design, critical procedures, data, protections and planned analyses (R2-073, binding-ICH); FDA-PD24 SIII.A.1 says iPDs should generally be those that could affect CtQ factors (R4-042, guidance, DRAFT); FDA-RBM13 SIV.A asks to identify critical data and processes (R4-080, guidance); best practice links risk assessment and CtQ review to deviation classification (R5-009, R5-015, R5-058, R5-059, R5-064).
- **Tension:** The mandatory CtQ part of the brief expects a CtQ-to-iPD chain, but the only explicit statement is draft US guidance plus best practice.
- **Handling in the model:** The chain is shown as a sequence of separately sourced steps, without inventing a requirement: start event "CtQ factors identified" (REQ-001 adherence aspects, E8R1 S6.1.1) -> "Identify risks to CtQ factors" (REQ-002) -> "Evaluate risks to CtQ factors" (REQ-003) -> "Document critical data and processes" (REQ-004, guidance) -> "Specify criteria for important protocol deviations" (REQ-010, binding-ICH: E6R3 A1-3.9.3 with E3QA S3 determinants). The explicit CtQ link is the separate task "Link iPD criteria to CtQ factors" (REQ-013, guidance, DRAFT), never shown as ICH or legal.
- **User decision:** No. The orchestrator should tell the user that the model does not claim an ICH or legal basis for deriving iPD criteria from CtQ factors.
- **Decision:** orchestrator default, not contested (06 Nov 2026) - the model claims no ICH or legal basis for deriving iPD criteria from CtQ factors; REQ-013 stays DRAFT.

## C-03 21 CFR 312.66 "promptly report all changes in the research activity" vs FDA-PD24 on minor deviations

- **Side A:** The investigator assures prompt reporting to the IRB of all changes in the research activity (R4-023 21CFR312.66; R4-011 Form FDA-1572 commitment; IRB procedure R4-025 21CFR56.108(a)(3)); E6R3 A1-2.4.6 asks for prompt information of the IRB/IEC on changes significantly affecting conduct (R1-016, R1-013).
- **Side B:** FDA-PD24 SIII.B.3: iPDs to the IRB when identified (R4-072); non-important deviations without apparent immediate hazard need not be reported immediately (R4-074), both DRAFT.
- **Tension:** 21 CFR does not say whether a protocol deviation is a "change in the research activity"; E6(R3) does not say whether a deviation is a "change". If it is, every deviation would be promptly reportable.
- **Handling in the model:** A5 US branch: the investigator reports to the IRB under the IRB's written procedures; the binding REQ-121 is kept with a [verify] item; the DRAFT split (REQ-122 iPDs when identified, REQ-123 others not immediately) is shown as DRAFT. The model does not state that minor deviations are exempt from 312.66.
- **User decision:** Was optional; closed by orchestrator default.
- **Decision:** orchestrator default, not contested (06 Nov 2026) - the IRB's written procedures decide what is reported when; [verify] on 21 CFR 312.66 stays (REQ-121).

## C-04 "Acceptable ranges" in two senses, and "important deviation" meaning a QTL exceedance

- **Side A:** Trial-level acceptable ranges (quality tolerance limits as example) for risks to CtQ factors; "deviation beyond these ranges" is a range exceedance to be evaluated for systemic issues: R1-041, R1-042 (E6R3 A1-3.10.1.3); best practice QTL/KRI: R5-049, R5-050.
- **Side B:** Acceptable ranges for specific protocol provisions (windows) that reduce the number of protocol deviations: R1-109 (E6R3 AppB-Intro). In the QTL paper "important deviation" means a QTL threshold exceedance: R5-051, R5-052, R5-053.
- **Tension:** Same words, different objects; a QTL exceedance is not a protocol deviation.
- **Handling in the model:** Separate REQs and tasks: "Set acceptable ranges for CtQ risks" (REQ-006, A1), "Evaluate acceptable range exceedance" (REQ-044, A2), "Build flexibility into protocol provisions" (REQ-021, A1). Labels never call an exceedance a "deviation"; glossary.yaml records both senses.
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-05 EU 7-day serious breach clock: starts at awareness of a potential breach; whose awareness counts is undefined

- **Side A:** EUCTR Art. 52(1): at the latest seven days "of becoming aware of that breach" (R3-023).
- **Side B:** EUCTR-QA S11.3: the 7-day timeframe starts when the sponsor becomes aware of a potential breach; analysis and confirmation should be completed within it (R3-098); EMA-SB S3.2: the assessment should be done in a timely manner and should not extend the period; notify first where there are reasonable grounds (R3-048 as corrected after X1, R3-049).
- **Tension:** A reading of Art. 52(1) could start the clock at confirmation; the Q&A starts it earlier. No source defines whether awareness of a delegated party, CRO or monitor counts as sponsor awareness (R3-048 and R3-098 conflict notes); contracts must require immediate reporting to the sponsor contact point (R3-051).
- **Handling in the model:** Deadline label "at the latest 7 (calendar) days from sponsor awareness of the potential breach" on the serious breach message flow (REQ-111); the clock starts at the A5 start event, which is the same event as the A4 start; A4 and A5 run in parallel. The awareness party is left as written in the sources ("sponsor") with a [verify] item.
- **User decision:** Was yes; closed at U1.
- **Decision:** decided by user 06 Nov 2026 - the clock starts at sponsor awareness of a potential breach as the sources say; [verify] on whose awareness counts stays; no assumption about monitor, CRO or delegated party awareness.

## C-06 Regional binding route of ICH guidelines

- **Side A (EU):** EU CTR Art. 47 obliges conduct per GCP principles and "appropriate account" of ICH GCP (R3-016 to R3-019); E6(R3) Principles and Annex 1 effective in the EU since 23 Jul 2025, Annex 2 and the consolidated text from 15 Jan 2027 (R3-087, R3-088); EU CTR prevails over conflicting guideline rules (R3-085); EudraLex Volume 10 still links only ICH E6(R2) (R3-020 note); EMA-SB references E6(R2).
- **Side B (US):** E6(R3) Principles and Annex 1 are final FDA guidance (nonbinding), Annex 2 is draft guidance (R4-078, R4-079); FDA-PD24 still cites E6(R2) (R4-065 note); 21 CFR binds.
- **Side C:** The research used the 2026 consolidated E6(R3) incl. Annex 2 (R1-086 to R1-090); industry sources build on E6(R2) (R5-002, R5-048). Adoption of E8(R1), E3, E3 Q&A, E9, E9(R1) and M11 was not checked; E3QA and M11 were seeded as verify-binding (R2 notes 3-4).
- **Handling in the model:** ICH findings stay binding-ICH (never binding-law) and every ICH REQ carries its regional route in binding_route: EU via Art. 47 and EMA adoption dates, US guidance only. ICH-only REQs are guidance-level in the US. Annex 2-based content carries a [verify] on the EU effective date (REQ-035). REQs resting on E8R1, E3, E3QA, E9, E9R1 or M11 carry "[verify binding]". Registry binding_default of E3QA and M11 moved to binding-ICH (Step 4 documents) with a [verify binding] note.
- **User decision:** Was optional; closed by orchestrator default.
- **Decision:** orchestrator default, not contested (06 Nov 2026) - E3 Q&A (R1) and M11 are binding-ICH with [verify binding].

## C-07 Article numbers in the brief

- **Side A:** brief.md lists "Art. 38 urgent safety measures".
- **Side B:** The regulation text places urgent safety measures in Art. 54 and temporary halt / early termination in Art. 38 (R3-013, R3-027).
- **Handling in the model:** Article numbers are taken from the regulation text only.
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-08 EU urgent safety measures vs immediate-hazard deviations

- **Side A:** E6R3: deviate only to eliminate an immediate hazard, inform the sponsor and IRB/IEC promptly; hazard information goes to authorities "per applicable regulatory requirements" (R1-022, R1-023, R1-024, R1-079, R1-080).
- **Side B:** EUCTR Art. 54: urgent safety measures are triggered by an unexpected event likely to seriously affect the benefit-risk balance; sponsor notifies within 7 days of the measures; Art. 54 does not mention deviations (R3-027 to R3-030; EUCTR-QA S10.1, S10.9, S7.27: R3-100 to R3-104). R3 warns against merging without an E6(R3) source.
- **Tension:** In the EU, the "applicable regulatory requirement" for an immediate-hazard action may be Art. 54, but not every immediate-hazard deviation is a USM.
- **Handling in the model:** Default: A3 hands off through the OR "Which jurisdiction-specific actions apply?" to the interface call activity "Handle urgent safety measures"; REQ-217 to REQ-220 are interface REQs with reason. No USM notification task inside A3.
- **User decision:** Was yes; closed at U1.
- **Decision:** decided by user 06 Nov 2026 - EU urgent safety measures stay an interface placeholder from A3 (REQ-217 to REQ-220).

## C-09 Prospective eligibility waivers: not permitted (M11) vs approved single-participant departure (FDA-PD24)

- **Side A:** M11-TEMPLATE S5.1: prospective approval of deviations from recruitment and enrolment criteria (protocol waivers or exemptions) is not permitted (R2-113, binding-ICH [verify]). In the local template text the sentence follows the "Enter Description of Trial Population and Rationale" placeholder as body text, not inside the instruction bullets; formatting is not visible in the text layer, so the [verify] stays.
- **Side B:** FDA-PD24 SII example: an investigator seeks and receives sponsor and IRB approval to enrol a participant above the maximum age; such departures should be rare (R4-037, R4-048, DRAFT).
- **Tension:** Direct contradiction for eligibility criteria.
- **Handling in the model:** A3 follows the stronger class: "Deviation from eligibility criteria requested?" -> "Reject eligibility waiver requests" (REQ-075); the FDA example is recorded in REQ-021 (protocol flexibility) and REQ-074 (prior sponsor and IRB approval for other intentional deviations).
- **User decision:** Was yes; closed at U1.
- **Decision:** decided by user 06 Nov 2026 - eligibility waivers are not permitted (M11 S5.1, REQ-075); the FDA-PD24 example is recorded as DRAFT only.

## C-10 Site closure: "consider" vs binding either-or

- **Side A:** E6R3 A1-3.12.3: consider terminating a party whose significant noncompliance persists (R1-076); FDA-PD24: consider closing a site (R4-071, DRAFT).
- **Side B:** 21CFR312.56(b): once investigator noncompliance is discovered, promptly secure compliance or end participation; notify FDA on termination (R4-013, R4-014).
- **Handling in the model:** In A6 the binding US either-or duty (REQ-135, 21CFR312.56(b)) sits on the task "Secure compliance" together with REQ-134 (E6R3 A1-3.12.1), before the ICH task "Consider terminating site participation" (REQ-145); there is no separate US branch. Termination notifications: REQ-146 (ICH) and REQ-148 (US). Placement accepted in V1 round 1 (07 Nov 2026).
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-11 Immediate-hazard IRB notification timing

- **Side A:** E6R3: "promptly", no number (R1-012, R1-023).
- **Side B:** 21CFR312.30(b)(2)(ii) requires IRB notification "in accordance with" 21CFR56.104(c), which sets 5 working days for emergency use of a test article (R4-005, R4-030). The 56.104(c) wording is confirmed in the local eCFR text; whether its window applies to hazard-eliminating protocol changes is not stated.
- **Handling in the model:** Deadline label "promptly (ICH); US: per 21 CFR 56.104(c) [verify 5 working days]" (REQ-086). Notifying party not named; Investigator chosen with [verify].
- **User decision:** No (open [verify] item for X1 or a regulatory expert).
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-12 Who notifies authorities

- **Side A:** E6R3 A1-2.5.5, A1-3.13.3: the investigator/institution or the sponsor submits hazard information to authorities where applicable (R1-024, R1-080).
- **Side B:** EU: all submissions are made by or on behalf of the sponsor, not the investigator (R3-086, EUCTR-QA S1.5); Art. 52 and 54 place notification on the sponsor; the investigator's duty to report suspected serious breaches to the sponsor is guidance and contract only (R3-051, R3-071).
- **Handling in the model:** EU authority message flows start only in the Sponsor pool; an Investigator-to-authority flow is labelled "where applicable (not EU)" (REQ-082). The investigator-to-sponsor serious breach flow is shown as guidance (REQ-069).
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-13 "Seven days" vs "7 calendar days"

- **Side A:** EUCTR Art. 52(1) "seven days" (R3-023).
- **Side B:** EMA-SB S3.2 and CTIS material "7 calendar days" (R3-048, R3-090).
- **Handling in the model:** Deadline "7 days (calendar days per EMA-SB S3.2)" with the Art. 52 citation (REQ-111).
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-14 Minor wording differences in EU texts

- **Side A:** Art. 52(1): protocol version applicable at the time of the breach (R3-023); Art. 57: records accessible to "the Member States" (R3-032).
- **Side B:** EMA-SB glossary: "approved protocol version" (R3-043); Art. 58: accessible to "competent authorities" (R3-037).
- **Handling in the model:** Regulation wording is used in labels; differences recorded as [verify] on REQ-105.
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-15 Root cause analysis owner

- **Side A:** E6R3 A1-3.12.2 and EMA-SB S5.1/S6.1: the sponsor performs the root cause analysis (R1-072, R3-060, R3-067).
- **Side B:** FDA-PD24 SIII.B.2: "the sponsor or clinical investigator" for recurrent deviations (R4-068, DRAFT).
- **Handling in the model:** Root cause analysis tasks in the Sponsor lane (REQ-136, REQ-138); the investigator's own preventive measures are a separate task (REQ-133).
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-16 Deviation category schemes

- **Side A:** ICH E3 10.2 example categories (R2-057); FDA-PD24 example lists (R4-044, R4-045).
- **Side B:** Best practice seven categories, of which four are said to come from E3 without saying which (R5-026); CDISC DVCAT codelist exists but its terms were not read (R5-065); EMA-SB Appendix I serious breach categories (only protocol compliance examples recorded, R3-079, R3-080).
- **Handling in the model:** The categorise task (REQ-096) requires a controlled category list without fixing a scheme; alignment is a [verify] item.
- **User decision:** No for the model; the category scheme is an implementation choice.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-17 Terminology: important / major / critical / significant; violation / deviation

- **Side A:** FDA-PD24 recommends "important" for all of major, critical, significant (R4-041, DRAFT); best practice treats them as synonyms (R5-004); E3QA prefers "protocol deviation" and notes "violation" can mean other things (R2-069, R2-070).
- **Side B:** FDA-RBM13 uses "significant protocol deviations" (R4-087); ICH E9 uses "protocol violation" throughout (R2-077 to R2-094).
- **Handling in the model:** Labels use "important protocol deviation" and "protocol deviation"; E9 wording stays in the cited paraphrases only (REQ-270, glossary.yaml).
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-18 GCP compliance issues that are not protocol deviations

- **Side A:** FDA-PD24 SII and best practice: GCP issues for procedures not written in the protocol (e.g. delegation log signature) are handled outside the deviation process (R4-038 DRAFT, R5-001, R5-007).
- **Side B:** E6(R3) handles noncompliance with protocol, SOPs, GCP and regulations together and files "noncompliance including protocol deviations" as one essential record (R1-071, R1-123).
- **Handling in the model:** A4 asks "Protocol deviation?" first (REQ-088); a non-deviation exits A4 through the end event "Issue handled outside the deviation process", but it is still assessed in A5 (serious noncompliance, serious breach) and remediated in A6, because A5 runs from the same trigger.
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-19 Reporting of non-important deviations

- **Side A:** E3QA does not say whether non-important deviations are reported in the CSR (R2-072).
- **Side B:** FDA-PD24: all deviations in the SDTM DV domain (R4-057, DRAFT; R5-069 guidance); best practice: both kinds collected and reported by different pathways (R5-003, R5-037); EMA-SB: non-serious deviations documented for CAPA (R3-065).
- **Handling in the model:** CSR text carries iPDs (A7, REQ-166 to REQ-168); the DV dataset carries all deviations for US submissions (REQ-185); non-important deviations are documented and filed in A4 (REQ-091, REQ-092).
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-20 Origin of reporting clocks

- **Side A:** FDA-PD24 example: important deviations to the sponsor "within x days of occurrence" (R4-054, DRAFT).
- **Side B:** EU serious breach clock from awareness (R3-098); E6(R3) "promptly" without a number (R1-012, R1-023, R1-093).
- **Handling in the model:** A1 sets the sponsor-defined reporting timeframe (REQ-026); each deadline label states its origin (occurrence, awareness, measures taken).
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-21 Premature unblinding as a deviation

- **Side A:** E6R3 A1-2.11: document and explain premature unblinding to the sponsor promptly; not called a deviation (R1-093).
- **Side B:** FDA-PD24: premature unblinding for reasons not in the protocol is an example of an important deviation and a study-level deviation (R4-045, R4-039, DRAFT).
- **Handling in the model:** A2 keeps the binding report-to-sponsor task (REQ-067); whether it is an iPD is decided by the trial-specific criteria in A4.
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-22 Basis for iPD content in the CSR

- **Side A:** E6R3 A1-3.17.2 does not mention deviations (R1-100 note); E6R3 A1-3.10.1.6 speaks of "important quality issues" (R1-045).
- **Side B:** ICH E3 10.2 and appendix 16.2.2 carry the iPD content (R2-055, R2-058); EMA-SB S5.1 asks for iPDs in the CSR even if they are not serious breaches (R3-064).
- **Handling in the model:** iPD CSR content rests on E3 (REQ-166 to REQ-168); E6(R3) is cited only for the quality management approach and important quality issues (REQ-181, REQ-182). R2-072 (E3QA) is marked dup_of R2-055.
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-23 Retention periods by region; US sponsor retention not extracted

- **Side A:** EU: master file archived at least 25 years after end of trial (R3-035, R3-036).
- **Side B:** US: investigator records 2 years after approval or discontinuation (R4-021); E6(R3): per applicable requirements, investigator for the longest period (R1-028). Sponsor retention under 21 CFR 312.57 was not extracted.
- **Handling in the model:** Separate EU and US archive tasks with jurisdiction groups (REQ-194, REQ-195, REQ-199); the US sponsor retention gap is listed for R4.
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-24 Weak binding basis for "site reports deviations to sponsor"

- **Side A:** E6R3 A1-2.5.3 obliges the investigator to document all deviations; the sponsor may communicate deviations it finds (R1-018, R1-019). Binding investigator-to-sponsor reports exist only for immediate hazards, premature unblinding and system incidents (R1-023, R1-093, R1-095) and, in the US, before protocol changes (R4-010).
- **Side B:** Reporting every deviation to the sponsor rests on FDA-PD24 (R4-047, DRAFT); EU serious breach reporting by the investigator rests on EMA-SB and contracts (R3-051, R3-071); no best-practice source covers site self-reporting (R5 notes).
- **Handling in the model:** The A2 message flow "Protocol deviation reported" is shown as DRAFT guidance (REQ-066); binding flows are shown separately.
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-25 Lane attribution inferred where sources name no actor

- **Side A:** E6(R3) monitoring items in A1-3.11.4.5 are gerund lists without an actor (R1-057 to R1-069, R1 notes C7); section 4 duties sit with the "responsible party (investigators and sponsors)" (R1-101 to R1-108, R1 notes C14); best practice names "the identifier" without a pool (R5-024).
- **Side B:** The model needs one lane per task (ROL-01).
- **Handling in the model:** Monitor lane for the A1-3.11.4.5 items (lane source A1-3.11.4.4, A1-3.11.4.5.1(a)), Sponsor lane for section 4 items, each with a [verify] item in the REQ.
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-26 Y1 merge decisions across jurisdictions and duplicates

- **Side A:** Findings from different jurisdictions that state the same obligation with the same trigger, deadline and recipient were merged into one REQ (e.g. REQ-003 E6R3 with FDA-RBM13; REQ-105 EU CTR with EMA-SB; REQ-166 E3 with EMA-SB S5.1); the REQ's binding is the strongest class and its jurisdiction lists all.
- **Side B:** Where trigger, deadline or recipient differ, EU, US and ICH obligations were kept apart (e.g. REQ-080 ICH vs REQ-073 US investigator-to-sponsor; REQ-119 ICH vs REQ-111 EU notifications; REQ-188 ICH vs REQ-194 EU vs REQ-199 US retention).
- **Handling in the model:** binding_route shows how each binding class arises. Six findings are dup_of a canonical finding of the same REQ (R5-002, R2-072, R1-013, R3-099, R3-092, R3-078); they stay in the REQ's source list.
- **User decision:** No.
- **Decision:** orchestrator default, not contested (06 Nov 2026)

## C-27 One start event for two message types at L4-03 S1 (FLW-09 rule exception)

- **Side A:** FLW-09: one start event per trigger; the Sponsor side of A3 receives two investigator message types - M1 "Immediate-hazard deviation reported" (E6R3 A1-2.5.4, R1-023) and M3 "Intentional protocol deviation request submitted" (21CFR312.53(c)(1)(vi)(a), R4-010; FDA-PD24 SIII.B.1, R4-048, DRAFT).
- **Side B:** SCP-02: each sub-process has one trigger and one entry point; both messages are the same business trigger (the investigator communicates an intentional protocol deviation), and the user-confirmed L3 cut (06 Nov 2026) keeps both cases in A3.
- **Tension:** Two start events would break SCP-02 for the called Sponsor process; splitting A3 into two steps would change the user-confirmed cut.
- **Handling in the model:** spec/L4-03.yaml S1 "Intentional protocol deviation communicated" is one message start event receiving M1 and M3, followed by an XOR that routes the immediate-hazard and the request case; recorded as a rule exception (FLW-09) in the spec.
- **User decision:** Not asked yet; flagged to the user as revisitable.
- **Decision:** orchestrator decision 07 Nov 2026 - documented FLW-09 rule exception (one business trigger, two message types); revisitable by the user.
- **Note (V1 round 2, 07 Nov 2026):** on L3, A3 is entered through XOR G5 "Intentional protocol deviation considered?" (Yes -> A3, No -> skip) inside the AND block G1/G2, next to A2; the earlier OR split with default flow to A2 was removed because a default flow is taken only when no other condition holds. In spec/L4-02.yaml G1 now has two conditional flows without default (FLW-07 SHOULD deviation, spec/notes.md) and G4 follows an unconditional "Report deviation to sponsor".

