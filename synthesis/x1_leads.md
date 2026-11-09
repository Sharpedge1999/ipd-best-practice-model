# X1 omission leads - disposition (Y1, gate G4)

Status: 06 Nov 2026, Y1 re-entry. Input: `verification/X1_omissions.md`. Y1 checked each lead against the existing findings (X1 saw only the worklist, i.e. a 25% sample of guidance and best-practice findings) and, where needed, against the local text. No new findings were created; new content belongs to the research owners.

## 1. Uncovered leads that matter (for the orchestrator)

No uncovered lead is binding-law or binding-ICH. Two guidance / best-practice leads would change a modelled step:

| Lead | Source and loc | Binding | Why it matters | Owner |
|---|---|---|---|---|
| L-01 | EMA-SB S4, first bullet (printed 6/21; local text lines 245-253) | guidance (EU) | A serious breach outside the EU/EEA while the CTA is submitted but not yet authorised is addressed in the CTA evaluation, not by CTIS serious breach notification, and may lead to withdrawal of the application. Adds a condition to the A5 EU branch ("Trial authorised in the EU/EEA?") and an interface to the CTA evaluation process; today REQ-111/REQ-112 assume an authorised trial. | R3 |
| L-02 | CDISC-CT codelist C225352 DVCAT (local text PDF 488, lines 30797-30815) | best-practice | The local copy lists seven DVCAT terms (DISCONTINUATION, INCLUSION/EXCLUSION, INFORMED CONSENT/ASSENT, PROHIBITED CONCOMITANT INTERVENTION, SAFETY REPORTING, STUDY INTERVENTION, TRIAL PROCEDURES); R5-065 says the terms could not be read. They appear to match the seven best-practice categories (R5-026) and would let the A4 categorise task (REQ-096) name a controlled list and close part of C-16. | R5 |

## 2. Uncovered leads without model impact

| Lead | Source and loc | Reason no action is needed |
|---|---|---|
| L-03 | EU CTR Recital (47), OJ L 158/6 | Non-binding recital; context for Art. 52, already modelled (REQ-111). |
| L-04 | TCB-PD close-out: "complete outstanding documentation" | Best practice; fits the existing A8 close-out task (REQ-200) without a new element. |

## 3. Leads already covered

| X1 lead | Covered by finding(s) | REQ(s) |
|---|---|---|
| EU CTR Art. 38(1) 15-day deadline | R3-013 (deadline field; paraphrase corrected) | REQ-216 |
| EU CTR Art. 53(1) 15-day deadline | R3-025 (deadline field; paraphrase corrected) | REQ-215 |
| EMA-SB S3.2 last paragraph (updates, follow-up reports) | R3-053, R3-092 | REQ-144 |
| EMA-SB S4 after bullets (CTIS fields, Appendix III b, updates) | R3-056, R3-084, R3-053 | REQ-113, REQ-144 |
| EMA-SB S5.1 root cause analysis and impact | R3-060 | REQ-115 |
| EMA-SB S5.1 important deviations in the CSR | R3-062, R3-064 | REQ-105, REQ-166 |
| EMA-SB S7 safety-related breaches | R3-074 | REQ-109 |
| EMA-SB Appendix II other trials of a service provider | R3-081 | REQ-105 |
| EUCTR-QA 11.3 point 522 (non-EU site) | R3-099 | REQ-112 |
| EUCTR-QA 10.9 point 500 (halt with USM) | R3-101 | REQ-219 |
| EUCTR-QA 7.27 point 368 (USM then substantial modification) | R3-103 | REQ-220 |
| CTIS-BT-SB24 slides 20 and 26 | R3-090, R3-091 | REQ-111, REQ-113 |
| 21 CFR 312.56(d) 5 working days | R4-016 (deadline field; paraphrase corrected) | REQ-226 |
| FDA-PD24 III.A.1 effectiveness-related examples | R4-045 | REQ-011 |
| FDA-PD24 III.A.2 other deviations | R4-046 | REQ-011 |
| FDA-PD24 III.B.1 investigator identification and reporting | R4-047 | REQ-066 |
| FDA-PD24 III.B.1 intentional single-participant departure | R4-048 | REQ-074 |
| FDA-PD24 III.B.2 training and oversight focus | R4-049, R4-050 | REQ-034, REQ-041 |
| FDA-PD24 III.B.2 sponsor receives all deviations | R4-052 | REQ-089 |
| FDA-PD24 III.B.2 CSR listing and DV domain | R4-056, R4-057 | REQ-169, REQ-185 |
| FDA-PD24 III.B.3 IRB review; non-important not immediately | R4-073, R4-074 | REQ-261, REQ-123 |
| FDA-RBM13 IV.D.3 noncompliance, RCA, CAPA in monitoring plan | R4-086 | REQ-025 |
| FDA-RBM23 Q7 documentation and communication | R4-095, R4-096 | REQ-138, REQ-152 |
| TCB-PD-TIRS Classify and Categorize | R5-024, R5-025, R5-026 | REQ-095, REQ-046, REQ-096 |
| TCB-PD-TIRS Identify and Collect | R5-020, R5-021, R5-023 | REQ-040, REQ-058, REQ-101 |
| TCB-PD-TIRS Confirm | R5-029, R5-030 | REQ-098, REQ-099 |
| TCB-PD-TIRS Review and Analyze | R5-035, R5-036 | REQ-159, REQ-166 |
| TCB-PD-TIRS Report | R5-037 to R5-041 | REQ-125, REQ-166, REQ-167, REQ-176, REQ-179 |
| TCB-PD close-out (archive non-important deviations, reuse at organisation level) | R5-043, R5-044 | REQ-200, REQ-202 |

## 4. Corrections applied from omission leads

R3-013, R3-025 and R4-016 already held the deadline in their `deadline` field; only the paraphrase omitted it. The paraphrases were corrected (x1 note "omission lead", see `synthesis/changes_X1.md`). REQ-216 and REQ-226 statements were sharpened (15 days from the date of the halt or termination; 5 working days attach to discontinuing the investigation, not to the notification). REQ-215 already carried its deadline.
