# L3 cut - best-practice iPD management (Y1 synthesis)

Status: 07 Nov 2026, Y1 re-entry after V1 validation rounds 1-3 (round 1 edits listed in `synthesis/changes_V1r1.md`; element names aligned with spec/*.yaml in round 3); cut as confirmed at the L3 checkpoint (U1, 06 Nov 2026). The user merged the two identification channels into one step; the cut has 8 steps, numbered A1-A8 in process order. REQ ids are unchanged; only their l3_step values were renumbered. REQ lists between the `REQS` / `INTS` markers are written by `tools/y1_build.py` from `synthesis/requirements.yaml`; edit `synthesis/requirements_src.yaml`, not the lists.

## Scope and conventions

- Boundary (D3): start event "CtQ factors identified", end event "iPDs reported in clinical study report and records archived".
- Pools (D1, LBL-05): Sponsor (internal, lanes "Sponsor" and "Monitor"), Investigator/institution (external, expanded, ROL-03 exception), IRB/IEC (collapsed), Regulatory authority (collapsed). Lane and pool names come from `synthesis/glossary.yaml`. Service providers and delegated parties are not pools (interface REQ-213).
- Reading convention (orchestrator default, not contested): A2-A6 run repeatedly throughout trial conduct. The L3 sequence shows the order in which one deviation passes through the steps; the AND gateways show channels that are open in parallel (G1/G2, G3/G4); the XOR pair G5/G6 makes A3 optional. L3 has no OR gateway. No loop markers are used (FLW-02). spec/L3.yaml shows it as text annotation TA1 and group "Runs repeatedly during trial conduct".
- Jurisdiction branches (EU, US) sit inside the L4 models as XOR gateways and groups (GR_EU, GR_US); the L3 cut is the same for all jurisdictions.
- Size check: every estimate is for one L4 collaboration (activities, events and gateways in all expanded pools). Target at most 31 nodes (SCP-03, SHOULD); decomposition required above 50 elements (SCP-04, MUST).
- Old-to-new step numbers (first Y1 run -> re-entry): A1 -> A1; A2 + A3 -> A2; A4 -> A3; A5 -> A4; A6 -> A5; A7 -> A6; A8 -> A7; A9 -> A8.

## L3 flow

```
S1  start  "CtQ factors identified"                       (Sponsor lane)
A1  call   "Define trial-specific iPD criteria"
G1  and-split
    A2  call  "Identify protocol deviations"
    G5  xor-split  "Intentional protocol deviation considered?"
        Yes -> A3  call  "Manage intentional protocol deviations"
        No  -> G6
    G6  xor-join
G2  and-join
G3  and-split
    A4  call  "Document and classify protocol deviations"
    A5  call  "Assess and notify reportable noncompliance"
G4  and-join
A6  call  "Remediate deviations and noncompliance"
A7  call  "Finalise iPDs for clinical study report"
A8  call  "Archive deviation records"
E1  end    "iPDs reported in clinical study report and records archived"

Flows: S1-A1, A1-G1, G1-A2, G1-G5, G5-A3 (Yes), G5-G6 (No), A3-G6, A2-G2, G6-G2, G2-G3, G3-A4, G3-A5, A4-G4, A5-G4, G4-A6, A6-A7, A7-A8, A8-E1
```

Why G3/G4 run A4 and A5 in parallel (decided by user 06 Nov 2026 as part of the L3 cut): the EU 7-day serious breach clock starts when the sponsor becomes aware of a potential breach (EUCTR-QA S11.3; EU CTR Art. 52(1)), and EMA-SB S5.1 makes the serious breach decision independent of the iPD classification. A sequential A4-A5 cut would let routine classification consume the notification window (C-01, C-05).

Why A2 and A3 sit in an AND block with an XOR around A3 (V1 round 2, 07 Nov 2026, as in spec/L3.yaml; replaces the OR split with default flow of round 1): A2 runs throughout conduct, so it takes its own AND branch; A3 runs only when an intentional protocol deviation is considered, so its branch asks "Intentional protocol deviation considered?" (Yes -> A3, No -> skip). An OR split with a default flow to A2 was wrong because a default flow is taken only when no other condition holds, so A2 would not run whenever A3 runs. An intentional protocol deviation then enters A4 like any other deviation (FDA-PD24 SIII.C: a hazard-driven change made before IRB approval is still a protocol deviation).

## A1 - Define trial-specific iPD criteria

- **Label:** Define trial-specific iPD criteria
- **Purpose:** Turn the identified CtQ factors and their risks into trial-specific criteria for important deviations, and set up what the later steps rely on: protocol text on deviation handling, monitoring plan content, deviation assessment plan, serious breach reporting duties (EU), reporting instructions, agreements and training.
- **Trigger (start event):** CtQ factors identified
- **Outcomes (end events):** iPD criteria and plans approved (Sponsor); Trial participation agreed (Investigator/institution, after "Sign agreement to comply").
- **Pools and lanes:** Sponsor (Sponsor lane); Investigator/institution (agreement, training).
- **Message flows:**
  - Sponsor -> Investigator/institution "Protocol and deviation reporting instructions provided" - E6R3 A1-3.6.3(a) (binding-ICH); FDA-PD24 SIII.B.2 (guidance, DRAFT, US); EMA-SB S3.2 (guidance, EU)
  - Investigator/institution -> Sponsor "Agreement to comply signed" - E6R3 A1-3.6.3(a) (binding-ICH)
- **CtQ-to-iPD chain (C-02):** start event "CtQ factors identified" (E8R1 S3.2, E6R3 P6.2, E8R1 S6.1.1 on adherence) -> "Identify risks to CtQ factors" (E6R3 A1-3.10.1.1) -> "Evaluate risks to CtQ factors" (E6R3 A1-3.10.1.2, E8R1 S3.2) -> "Specify criteria for important protocol deviations" (E6R3 A1-3.9.3, E3QA S3). The direct CtQ link is the separate task "Link iPD criteria to CtQ factors" (DRAFT/BP) (FDA-PD24 SIII.A.1, CTTI-CTQ, TCB-PD-TIRS), never as an ICH or legal requirement.
- **REQs carried:** <!--REQS:A1-->34 REQs - binding-law 1, binding-ICH 23, guidance 9 (of which draft 4), best-practice 1: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014, REQ-015, REQ-016, REQ-017, REQ-018, REQ-019, REQ-020, REQ-021, REQ-022, REQ-023, REQ-024, REQ-025, REQ-026, REQ-027, REQ-028, REQ-029, REQ-030, REQ-031, REQ-032, REQ-033, REQ-034<!--/REQS:A1-->
- **Interfaces (placeholders):** quality by design and protocol development (upstream, CtQ identification) and trial authorisation and IRB/IEC approval (upstream); not drawn as elements in spec/L4-01.yaml (the start event "CtQ factors identified" is the hand-over). Interface REQs: <!--INTS:A1-->REQ-203 (Identify CtQ factors), REQ-204 (Consider CtQ aspects in study planning), REQ-205 (Design feasible protocol), REQ-206 (Obtain stakeholder input on protocol), REQ-207 (Use M11 protocol template)<!--/INTS:A1-->
- **As-Is comparability:** Corresponds to As-Is step 1 "Define trial-specific iPD categories". Best practice widens it from categories to criteria (E6R3 A1-3.9.3) and adds the risk evaluation that feeds them, the protocol and monitoring plan content, the EU serious breach reporting set-up and training.
- **L4 size estimate:** about 19 nodes (Sponsor 15 incl. one EU XOR pair, Investigator/institution 4).

## A2 - Identify protocol deviations

- **Label:** Identify protocol deviations
- **Label basis:** E6R3 A1-3.11.4.5.4(b)(ii) (monitoring of trial data should "identify ... protocol deviations"), FDA-PD24 SIII.A (deviations "can be identified by" site staff, site or central monitoring, audits, inspections), TCB-PD-TIRS SIdentify-and-Collect. "Protocol deviations", not "iPDs": importance is decided in A4.
- **Purpose:** Detect potential protocol deviations through both identification channels and hand them to classification (A4) and reportability assessment (A5): channel 1, centralised data review by the sponsor (centralised monitoring, programmed checks, audit trail review, acceptable range evaluation, trend review of non-important deviations, targeting of sites); channel 2, the investigator site (on-site monitoring of protocol adherence and eligibility, and the investigator's own documentation and reports to the sponsor).
- **Trigger (start event):** Monitoring activity scheduled (Sponsor process, timer start per monitoring plan; E6R3 A1-3.11.4.3, A1-3.11.4.1(a)). The Investigator/institution process starts with "Protocol deviation identified at site" (E6R3 A1-2.5.3).
- **Two channels, one trigger (SCP-02):** The called Sponsor sub-process has one start event (S1 "Monitoring activity scheduled", timer), because both channels are run under one monitoring plan that sets the activities of all parties, their methods and frequency (E6R3 A1-3.11.4.3). An OR split G1 "Which monitoring channels are due?" has two conditional flows, "Centralised data review due" and "Site monitoring visit due", and no default flow; the OR join G2 closes them before "Document monitoring report", "Review monitoring reports", the XOR G3 "Potential protocol deviation identified?" and "Communicate detected deviations to investigator". OR, because one or both channels run in a cycle: centralised monitoring "can complement and reduce site monitoring or be used on its own" (E6R3 A1-3.11.4.2(b)), site visit frequency follows the risks (A1-3.11.4.1(a)) and quality control applies at each stage of data handling (A1-3.11.3). No default flow (documented FLW-07 SHOULD deviation in spec/notes.md): the trigger guarantees that at least one channel is due, and a default would suppress centralised review whenever a site visit is due. In the Investigator/institution process, "Report deviation to sponsor" runs for every deviation; the OR split G4 "Which additional reports are due?" then adds "Report computerised system incident" (flow "System incident") and "Report suspected serious breach to sponsor" (flow "Suspected serious breach (EU CTR)"), with default flow "No further report". "Premature unblinding explained" is a message flow of "Report deviation to sponsor". The investigator's start event belongs to the external participant's own process (D1, ROL-03 exception), not to the called sub-process, so it is no second entry point.
- **Outcomes (end events):** Potential protocol deviation identified; Monitoring completed without finding (Sponsor); Deviation reported to sponsor (Investigator/institution).
- **Pools and lanes:** Sponsor (Sponsor lane for channel 1, centralised monitoring by qualified sponsor staff, E6R3 A1-3.11.4.2(a); Monitor lane for channel 2); Investigator/institution; IRB/IEC (system incidents where applicable).
- **Groups (SCP-05):** GR_CENTRAL "Centralised data review" and GR_SITE "Site monitoring" around the two branches in the Sponsor pool, so the two former As-Is steps stay visible; jurisdiction groups GR_EU / GR_US where needed.
- **Message flows:**
  - Sponsor -> Investigator/institution "Detected deviation communicated" - E6R3 A1-2.5.3, A1-3.11.4.5.1(b) (binding-ICH); FDA-RBM23 SQ8 (guidance, US)
  - Monitor -> Investigator/institution "Source record correction requested" - E6R3 A1-3.11.4.5.1(c) (binding-ICH)
  - Investigator/institution -> Sponsor "Protocol deviation reported" - FDA-PD24 SIII.B.1 (guidance, DRAFT, US)
  - Investigator/institution -> Sponsor "Premature unblinding explained" - E6R3 A1-2.11 (binding-ICH, promptly)
  - Investigator/institution -> Sponsor and IRB/IEC "Computerised system incident reported" - E6R3 A1-2.12.10(e) (binding-ICH; IRB/IEC where applicable)
  - Investigator/institution -> Sponsor "Suspected serious breach reported" - EMA-SB S6.4 (guidance, EU, promptly)
- **REQs carried:** <!--REQS:A2-->35 REQs - binding-law 3, binding-ICH 23, guidance 7 (of which draft 3), best-practice 2: REQ-035, REQ-036, REQ-037, REQ-038, REQ-039, REQ-040, REQ-041, REQ-042, REQ-043, REQ-044, REQ-045, REQ-046, REQ-047, REQ-048, REQ-049, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054, REQ-055, REQ-056, REQ-057, REQ-058, REQ-059, REQ-060, REQ-061, REQ-062, REQ-063, REQ-064, REQ-065, REQ-066, REQ-067, REQ-068, REQ-069<!--/REQS:A2-->
- **Interfaces (placeholders):** data governance and computerised systems (audit trail configuration) and safety reporting (SAE to sponsor, EU CTR Art. 41(2)) as open items [verify interface] in spec/L4-02.yaml; risk-based quality management (QTL and KRI review), data management (query and data correction) and the informed consent process are not drawn as elements. Interface REQs: <!--INTS:A2-->REQ-209 (Configure audit trail and metadata review), REQ-214 (Report SAE to sponsor)<!--/INTS:A2-->
- **As-Is comparability:** Corresponds to As-Is steps 2 and 3 ("Identify iPDs through data review" and "Identify iPDs through site monitoring"), merged by user decision of 06 Nov 2026; the two former steps stay visible as Groups GR_CENTRAL and GR_SITE. Best practice identifies all protocol deviations here, not only iPDs, because importance is decided in A4 (E6R3 A1-2.5.3, TCB-PD-TIRS SConfirm), and it adds the investigator's own identification and reporting duties as tasks in the expanded Investigator/institution pool (D1).
- **L4 size estimate:** spec/L4-02.yaml has 26 nodes (Sponsor process with OR pair G1/G2 and XOR G3; Investigator/institution process with "Report deviation to sponsor" before OR pair G4/G5). Within SCP-03, far below 50 (SCP-04).

## A3 - Manage intentional protocol deviations

- **Label:** Manage intentional protocol deviations
- **Purpose:** Handle intentional protocol deviations, i.e. deviations decided before they happen: a deviation to eliminate an immediate hazard (implemented at once, then reported to sponsor, IRB/IEC and, in the US, FDA by protocol amendment) and a planned single-participant intentional protocol deviation (prior sponsor and IRB/IEC approval; eligibility waivers not permitted).
- **Trigger (start event):** Intentional protocol deviation considered (Investigator/institution process, S2). The Sponsor process starts with the message start event S1 "Intentional protocol deviation communicated" (spec/L4-03.yaml), which receives both investigator message flows - M1 "Immediate-hazard deviation reported" and M3 "Intentional protocol deviation request submitted" (one business trigger, SCP-02); the task "Review intentional protocol deviation communication" and the XOR G1 "Immediate-hazard deviation reported?" route the two cases. One start event receiving two message types is a documented FLW-09 rule exception (C-27).
- **L3 hand-offs:** both investigator communications are shown on L3 as message flows from the Investigator/institution pool into A3: "Immediate-hazard deviation reported" and "Intentional protocol deviation request submitted".
- **Outcomes (end events):** Sponsor: Immediate hazard addressed; Deviation request approved; Deviation request rejected. Investigator/institution: Immediate-hazard deviation implemented and reported; Intentional protocol deviation approved and implemented; Deviation request rejected (labels as in spec/L4-03.yaml).
- **Pools and lanes:** Investigator/institution; Sponsor (Sponsor lane); IRB/IEC; Regulatory authority.
- **Message flows:**
  - Investigator/institution -> Sponsor "Immediate-hazard deviation reported" - E6R3 A1-2.5.4 (binding-ICH, promptly)
  - Investigator/institution -> IRB/IEC "Immediate-hazard deviation reported" - E6R3 A1-1.4.8(a), A1-2.5.5 (binding-ICH, promptly); 21CFR312.30(b)(2)(ii) with 21CFR56.104(c) (binding-law, US, [verify] 5 working days)
  - Investigator/institution -> Sponsor "Intentional protocol deviation request submitted" - 21CFR312.53(c)(1)(vi)(a) (binding-law, US); FDA-PD24 SIII.B.1 (guidance, DRAFT, US)
  - Sponsor -> Investigator/institution "Decision on deviation request" - M11-TEMPLATE S5.1 (binding-ICH [verify]); FDA-PD24 SIII.B.2 (guidance, DRAFT, US)
  - Investigator/institution -> IRB/IEC "Approval of intentional protocol deviation requested" - E6R3 A1-1.4.7 (binding-ICH); 21CFR312.66 (binding-law, US)
  - IRB/IEC -> Investigator/institution "IRB/IEC decision issued" - 21CFR56.108(a)(4) (binding-law, US)
  - Sponsor -> Regulatory authority "Protocol amendment submitted for immediate-hazard change" - 21CFR312.30(b)(2)(ii) (binding-law, US)
  - Sponsor -> Regulatory authority "Immediate-hazard information submitted where required" - E6R3 A1-3.13.3 (binding-ICH)
- **REQs carried:** <!--REQS:A3-->18 REQs - binding-law 6, binding-ICH 8, guidance 4 (of which draft 4), best-practice 0: REQ-070, REQ-071, REQ-072, REQ-073, REQ-074, REQ-075, REQ-076, REQ-077, REQ-078, REQ-079, REQ-080, REQ-081, REQ-082, REQ-083, REQ-084, REQ-085, REQ-086, REQ-087<!--/REQS:A3-->
- **Interfaces (placeholders):** urgent safety measures (EU CTR Art. 54) as call activity "Handle urgent safety measures" behind the OR G2 "Which jurisdiction-specific actions apply?" (decided by user 06 Nov 2026, C-08); protocol amendment / substantial modification and safety reporting as open items [verify interface] in spec/L4-03.yaml. Interface REQs: <!--INTS:A3-->REQ-217 (Take urgent safety measures), REQ-218 (Take urgent safety measures (investigator)), REQ-219 (Notify urgent safety measures), REQ-220 (Submit substantial modification after USM)<!--/INTS:A3-->
- **As-Is comparability:** New - required by REQ-070, REQ-071, REQ-072, REQ-073, REQ-078, REQ-080, REQ-081, REQ-085, REQ-086. Regulation gives intentional protocol deviations their own trigger and their own binding IRB/IEC and FDA flows (E6R3 A1-1.4.7, A1-2.5.4; 21CFR312.30(b)(2)(ii), 312.66, 56.108(a)(4)); they cannot be cut as part of identification after the fact.
- **L4 size estimate:** about 27 nodes (Investigator/institution 14, Sponsor 13). Keep the protocol amendment and the EU USM notification as interface placeholders, not as sub-flows. Eligibility waiver requests pass "Reject eligibility waiver requests" and end in "Deviation request rejected" (decided by user 06 Nov 2026, C-09).

## A4 - Document and classify protocol deviations

- **Label:** Document and classify protocol deviations
- **Purpose:** Confirm that the event is a protocol deviation, record it, have the investigator review and explain it, classify it as important or non-important against the trial-specific criteria, categorise, confirm, reconcile and file it, and update the criteria when a new type of iPD appears.
- **Trigger (start event):** Potential protocol deviation identified
- **Outcomes (end events):** Protocol deviation classified; Issue handled outside the deviation process
- **Pools and lanes:** Sponsor (Sponsor lane); Investigator/institution.
- **Message flows:**
  - Sponsor -> Investigator/institution "Deviation review requested" - E6R3 A1-2.5.3 (binding-ICH)
  - Investigator/institution -> Sponsor "Important protocol deviation explained" - E6R3 A1-2.5.3 (binding-ICH)
  - Sponsor -> Investigator/institution "Reclassification notified" - FDA-PD24 SIII.B.2 (guidance, DRAFT, US)
- **REQs carried:** <!--REQS:A4-->17 REQs - binding-law 3, binding-ICH 5, guidance 4 (of which draft 3), best-practice 5: REQ-088, REQ-089, REQ-090, REQ-091, REQ-092, REQ-093, REQ-094, REQ-095, REQ-096, REQ-097, REQ-098, REQ-099, REQ-100, REQ-101, REQ-102, REQ-103, REQ-104<!--/REQS:A4-->
- **Interfaces (placeholders):** issues that are not protocol deviations leave through the end event "Issue handled outside the deviation process" (GCP noncompliance handling); data management (correction) and service provider reporting (service providers are not pools, D1) are open items [verify interface] in spec/L4-04.yaml. Interface REQs: <!--INTS:A4-->REQ-210 (Correct data errors), REQ-211 (Validate computerised systems), REQ-213 (Report incidents to sponsor (service provider))<!--/INTS:A4-->
- **As-Is comparability:** Corresponds to the documentation part of As-Is step 4 "Document and follow up iPDs"; the follow-up part sits in A6. The classification decision of this step is decision 1 of 4 in C-01 (important protocol deviation).
- **L4 size estimate:** about 19 nodes (Sponsor 16, Investigator/institution 3).

## A5 - Assess and notify reportable noncompliance

- **Label:** Assess and notify reportable noncompliance
- **Purpose:** Take the reportability decisions that regulation keeps separate from iPD classification and send the resulting notifications: EU serious breach (EU CTR Art. 52, 7 days), serious noncompliance (E6R3 A1-3.12.2, per applicable requirements), investigator reporting to the IRB/IEC (E6R3 A1-2.4.6; 21CFR312.66; FDA-PD24 DRAFT for iPDs) and the IRB's onward reporting of serious or continuing noncompliance (21CFR56.108(b)(2)).
- **Trigger (start event):** Potential protocol deviation identified (same event as A4; for the EU branch this is the sponsor's awareness of a potential breach and starts the 7-day clock, decided by user 06 Nov 2026, C-05)
- **Outcomes (end events):** Reportable noncompliance notified; No notification required (the task "Document non-notification rationale" applies on the EU serious breach path only, EMA-SB S5.1, REQ-116); Investigator/institution: IRB/IEC reporting completed
- **Pools and lanes:** Sponsor (Sponsor lane); Investigator/institution; IRB/IEC; Regulatory authority.
- **Message flows:**
  - Sponsor -> Regulatory authority "Serious breach notified" - EUCTR Art. 52(1) (binding-law, EU, at the latest 7 days from awareness of the potential breach; EUCTR-QA S11.3, EMA-SB S3.2)
  - Sponsor -> Regulatory authority and/or IRB/IEC "Serious noncompliance notified" - E6R3 A1-3.12.2 (binding-ICH, per applicable regulatory requirements)
  - Sponsor -> Investigator/institution "Serious noncompliance notified" - E6R3 A1-3.12.2 (binding-ICH, as appropriate)
  - Investigator/institution -> IRB/IEC "Change significantly affecting conduct reported" - E6R3 A1-2.4.6 (binding-ICH, promptly)
  - Investigator/institution -> IRB/IEC "Change in research activity reported" - 21CFR312.66 (binding-law, US, promptly; what is reported when follows the IRB's written procedures, C-03)
  - Investigator/institution -> IRB/IEC "Important protocol deviation submitted" - FDA-PD24 SIII.B.3 (guidance, DRAFT, US)
  - IRB/IEC -> Regulatory authority "Serious or continuing noncompliance reported" - 21CFR56.108(b)(2) (binding-law, US, prompt)
  - IRB/IEC -> Investigator/institution "Serious or continuing noncompliance reported to institutional officials" - 21CFR56.108(b)(2) (binding-law, US)
- **REQs carried:** <!--REQS:A5-->22 REQs - binding-law 4, binding-ICH 3, guidance 13 (of which draft 2), best-practice 2: REQ-105, REQ-106, REQ-107, REQ-108, REQ-109, REQ-110, REQ-111, REQ-112, REQ-113, REQ-114, REQ-115, REQ-116, REQ-117, REQ-118, REQ-119, REQ-120, REQ-121, REQ-122, REQ-123, REQ-124, REQ-125, REQ-126<!--/REQS:A5-->
- **Interfaces (placeholders):** unexpected events, urgent safety measures and temporary halt notifications (EU CTR Art. 53, 54, 38) as call activity "Handle other EU notifications" after "Check need for other EU notifications"; IND safety reporting (21 CFR 312.32), authority assessment and requests for information (CTIS), authority corrective measures (EU CTR Art. 77) and IRB/IEC approval suspension as open items [verify interface] in spec/L4-05.yaml. Interface REQs: <!--INTS:A5-->REQ-212 (Report data incidents), REQ-215 (Notify unexpected event), REQ-216 (Notify temporary halt or early termination), REQ-224 (Inform FDA and investigators of new risks), REQ-225 (Evaluate safety and effectiveness evidence), REQ-227 (Report unanticipated problem to IRB), REQ-228 (Report unanticipated problems onward), REQ-229 (Note contributing deviation in IND safety report), REQ-230 (Report suspension of IRB approval), REQ-231 (Assess notification (authority)), REQ-232 (Respond to authority request for information), REQ-233 (Impose corrective measure (authority)), REQ-234 (Give opinion on corrective measure)<!--/INTS:A5-->
- **As-Is comparability:** New - required by REQ-105, REQ-111 (EU CTR Art. 52), REQ-118, REQ-119 (E6R3 A1-3.12.2), REQ-120, REQ-121 (E6R3 A1-2.4.6; 21CFR312.66) and REQ-124 (21CFR56.108(b)(2)). These are decisions 2-4 of C-01; regulation makes them independent of the iPD classification, and the EU clock forces them to start at awareness.
- **L4 size estimate:** about 24 nodes (Sponsor 16 with EU and ICH branches, Investigator/institution 8 with ICH and US branches).

## A6 - Remediate deviations and noncompliance

- **Label:** Remediate deviations and noncompliance
- **Purpose:** Escalate and decide on findings, focus remediation on iPDs, run root cause analysis and CAPA for significant noncompliance, secure compliance or end the participation of a persistently noncompliant site (with the required notifications), submit serious breach follow-up reports (EU), and feed lessons into risk controls, monitoring plan and training.
- **Trigger (start event):** Deviation classified and reportability decided
- **Outcomes (end events):** Corrective and preventive actions completed; Investigator participation terminated (Sponsor); Site measures implemented (Investigator/institution, after "Implement site measures against recurrence").
- **Pools and lanes:** Sponsor (Sponsor lane, Monitor lane); Investigator/institution; IRB/IEC; Regulatory authority.
- **Message flows:**
  - Sponsor -> Investigator/institution "Corrective action required" - E6R3 A1-3.12.1 (binding-ICH); 21CFR312.56(b) (binding-law, US, promptly)
  - Sponsor -> Investigator/institution "Participation ended and drug return required" - 21CFR312.56(b) (binding-law, US)
  - Sponsor -> Regulatory authority "Investigator termination notified" - 21CFR312.56(b) (binding-law, US)
  - Sponsor -> Regulatory authority and IRB/IEC "Persistent serious noncompliance notified" - E6R3 A1-3.12.3 (binding-ICH, promptly)
  - Sponsor -> Regulatory authority "Serious breach follow-up report submitted" - EMA-SB S3.2 (guidance, EU)
  - Sponsor -> IRB/IEC, Regulatory authority, Investigator/institution "Significant issues and actions communicated" - FDA-RBM23 SQ7 (guidance, US)
- **REQs carried:** <!--REQS:A6-->27 REQs - binding-law 2, binding-ICH 14, guidance 10 (of which draft 3), best-practice 1: REQ-127, REQ-128, REQ-129, REQ-130, REQ-131, REQ-132, REQ-133, REQ-134, REQ-135, REQ-136, REQ-137, REQ-138, REQ-139, REQ-140, REQ-141, REQ-142, REQ-143, REQ-144, REQ-145, REQ-146, REQ-147, REQ-148, REQ-149, REQ-150, REQ-151, REQ-152, REQ-153<!--/REQS:A6-->
- **Interfaces (placeholders):** protocol amendment (21 CFR 312.30; EU CTR Chapter III), investigational product return (21 CFR 312.59), trial discontinuation for risk (21 CFR 312.56(d)) and quality assurance and audit, as open items [verify interface] in spec/L4-06.yaml. Interface REQs: <!--INTS:A6-->REQ-208 (Perform risk-based quality assurance), REQ-221 (Submit IND protocol amendment), REQ-222 (Justify protocol amendment), REQ-223 (Apply for restart after halt), REQ-226 (Discontinue investigation for risk)<!--/INTS:A6-->
- **As-Is comparability:** Corresponds to As-Is step 5 "Assess and mitigate iPD impact" plus the follow-up part of As-Is step 4. Best practice extends it from iPDs to noncompliance, because the binding remediation duties attach to noncompliance (E6R3 A1-3.12; 21CFR312.56(b)). The impact on analysis sets is assessed in A7, not here, because ICH E9 requires those decisions in the blind review before unblinding.
- **L4 size estimate:** about 26 nodes (Sponsor 22, Investigator/institution 4).

## A7 - Finalise iPDs for clinical study report

- **Label:** Finalise iPDs for clinical study report
- **Purpose:** At data finalisation compile and freeze the deviation list, review deviation handling in the blind review, decide analysis set exclusions before unblinding, characterise each iPD's impact, and write the iPD content of the CSR (section 10.2, appendix 16.2.2, quality management approach, serious breaches for EU trials) and, for US submissions, the SDTM DV dataset.
- **Trigger (start event):** Data finalisation initiated
- **Outcomes (end events):** iPDs reported in clinical study report
- **Pools and lanes:** Sponsor (Sponsor lane); Regulatory authority.
- **Message flows:**
  - Sponsor -> Regulatory authority "Clinical study report provided" - E6R3 A1-3.17.2(a) (binding-ICH, as required); FDA-PD24 SIII.B.2 (guidance, DRAFT, US, NDA/BLA)
  - Sponsor -> Regulatory authority "DV dataset submitted" - FDA-SDTCG S4.1.1.3 (guidance, US)
- **REQs carried:** <!--REQS:A7-->34 REQs - binding-law 0, binding-ICH 27, guidance 5 (of which draft 2), best-practice 2: REQ-154, REQ-155, REQ-156, REQ-157, REQ-158, REQ-159, REQ-160, REQ-161, REQ-162, REQ-163, REQ-164, REQ-165, REQ-166, REQ-167, REQ-168, REQ-169, REQ-170, REQ-171, REQ-172, REQ-173, REQ-174, REQ-175, REQ-176, REQ-177, REQ-178, REQ-179, REQ-180, REQ-181, REQ-182, REQ-183, REQ-184, REQ-185, REQ-186, REQ-187<!--/REQS:A7-->
- **Interfaces (placeholders):** statistical analysis and estimands (ICH E9, E9(R1)) as call activity "Handle statistical analysis and estimands"; CSR submission (EU CTR Art. 37(4); marketing application) and electronic study data submission as call activity "Handle clinical study report and study data submission". Interface REQs: <!--INTS:A7-->REQ-235 (Submit CSR to EU database), REQ-236 (Submit standardised study data), REQ-237 (Plan sensitivity to analysis set), REQ-238 (Harmonise deviation handling across trials), REQ-239 (Collect estimand-relevant data), REQ-240 (Report intercurrent events), REQ-241 (Report changes in conduct after start), REQ-242 (Report patient disposition)<!--/INTS:A7-->
- **As-Is comparability:** Corresponds to As-Is step 6 "Finalize iPDs for CTR reporting"; "CTR" there is read as clinical study report (CSR), not EU CTR (orchestrator default, not contested). Best practice adds the blind review sequencing (ICH E9 S5.2, S7.1).
- **L4 size estimate:** about 17 nodes (Sponsor only).

## A8 - Archive deviation records

- **Label:** Archive deviation records
- **Purpose:** Retain deviation, noncompliance and CAPA records with the related essential records for the required period, archive the master file (EU at least 25 years after end of trial; US investigator records 2 years after approval or discontinuation), keep them accessible to authorities, and capture lessons learned.
- **Trigger (start event):** iPDs reported in clinical study report
- **Outcomes (end events):** Deviation records archived (Sponsor); Investigator records archived (Investigator/institution, whose process starts with "End of clinical trial reached").
- **Pools and lanes:** Sponsor (Sponsor lane); Investigator/institution.
- **Message flows:**
  - Sponsor -> Investigator/institution "Records no longer needed notified" - E6R3 A1-2.12.12 (binding-ICH; the investigator retains essential records for the longest of the required period or until this notice)
  - Availability of archived records to authorities on request (EUCTR Art. 58, binding-law, EU; E6R3 AppC-C.2.6, binding-ICH) is request-driven and has no message flow in spec/L4-08.yaml; it is carried by the task "Keep records accessible" and the data stores "Trial master file" and "Investigator site file".
- **REQs carried:** <!--REQS:A8-->15 REQs - binding-law 6, binding-ICH 6, guidance 0 (of which draft 0), best-practice 3: REQ-188, REQ-189, REQ-190, REQ-191, REQ-192, REQ-193, REQ-194, REQ-195, REQ-196, REQ-197, REQ-198, REQ-199, REQ-200, REQ-201, REQ-202<!--/REQS:A8-->
- **Interfaces (placeholders):** trial master file management and retention of medical files under national law (EU CTR Art. 58), as open items [verify interface] in spec/L4-08.yaml. Interface REQs: <!--INTS:A8-->none<!--/INTS:A8-->
- **As-Is comparability:** New - required by REQ-188, REQ-191, REQ-194, REQ-195, REQ-199 (E6R3 Appendix C; EU CTR Art. 58; 21CFR312.62(c)) and by the D3 end milestone "records archived".
- **L4 size estimate:** about 12 nodes (Sponsor 8, Investigator/institution 4).

## Decisions taken

Decided by user 06 Nov 2026 (L3 checkpoint U1):
1. L3 cut with 8 steps: the two identification channels (former A2 centralised data review, former A3 investigator sites) are merged into A2 "Identify protocol deviations"; steps renumbered A1-A8 in process order; A4 and A5 run in parallel.
2. C-05: the EU 7-day clock starts at sponsor awareness of a potential breach, as the sources say; whose awareness counts stays a [verify] item; no assumption about monitor, CRO or delegated party awareness.
3. C-08: EU urgent safety measures stay an interface placeholder from A3.
4. C-09: eligibility waivers are not permitted (M11 S5.1); the FDA-PD24 example is recorded as DRAFT only.

Orchestrator defaults, not contested (06 Nov 2026):
5. C-03: the IRB's written procedures decide what is reported when, with a [verify] item on 21 CFR 312.66.
6. C-06: E3 Q&A (R1) and M11 are binding-ICH with [verify binding].
7. Service providers and delegated parties are an interface (REQ-213), not a pool.
8. "CTR" in As-Is step 6 is read as clinical study report.
9. Reading-convention text annotation on the L3 diagram (no loop markers).
10. The TCB-PD URL stays in the register's source list.

Y1 defaults presented at U1 and not changed: CtQ identification upstream of A1 as interface (D3); overarching conduct norms (EU CTR Art. 47, 21 CFR 312.50, 312.60, E6R3 A1-2.5.2, A1-3.9.2) out of scope and cited on the pools.

V1 validation round 1 (07 Nov 2026), consistency edits with the specs:
11. G1/G2 between A1 and A4/A5: OR split and join with default flow to A2 in round 1; replaced in V1 round 2 (07 Nov 2026) by an AND split/join with A2 on its own branch and XOR G5/G6 "Intentional protocol deviation considered?" around A3 (as in spec/L3.yaml).
12. A2 outcome "Potential protocol deviation identified" (was "detected"), matching the A4/A5 trigger.
13. A5 outcome "No notification required" (was "... and rationale documented").
14. A3: one message start event on the sponsor side for both intentional protocol deviation communications; both investigator hand-offs shown on L3.
15. A3 trigger quoted as in spec/L4-03.yaml S1 "Intentional protocol deviation communicated"; FLW-09 exception at L4-03 S1 decided by the orchestrator (07 Nov 2026, C-27).
16. A2 L4 (07 Nov 2026, as in spec/L4-02.yaml): G1 has two conditional flows and no default (FLW-07 SHOULD deviation recorded in spec/notes.md); "Report deviation to sponsor" runs for every deviation before G4 "Which additional reports are due?" (default "No further report").
