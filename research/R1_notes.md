# R1 notes - ICH E6(R3) (mandatory source)

Status: 06 Nov 2026, re-entry after gate G1. Findings file: `research/R1_ich_e6r3.yaml`, 144 records (R1-001..R1-144). All records are `binding-ICH`, `src: E6R3`, confidence high, no open verify items.

## 6. Document version actually read (first, because it governs every page reference)

- **Primary (key E6R3):** ICH E6(R3) Guideline for Good Clinical Practice, Final version, Step 4, consolidated with Annex 2, 16 June 2026. https://database.ich.org/sites/default/files/ICH%20E6%28R3%29_Step4_FinalConsolidatedGuideline_2026_0616_.pdf. The document history lists: Step 2 on 19 May 2023; Annex 2 Step 2 on 06 Nov 2024; Step 4 on 06 Jan 2025; error correction on 24 Oct 2025; Annex 2 Step 4 on 03 June 2026; consolidated Step 4 with minor and error corrections on 16 June 2026.
- **Re-entry basis:** the orchestrator downloaded the official PDF to the shell (99 pages, sha256 f62d668b7b3495cef26cb52417e051981ce5edd989ff023bf6d68a3b294ff84a) and converted it with pdftotext -layout to `vendor/sources/e6r3/E6R3_consolidated_2026-06-16.txt`, which was read as read-only data. Every record was re-checked against this text. Retrieval is "local pdftotext of official PDF (sha256 ...) 2026-11-06".
- **Page convention:** "printed N / PDF M". Form feeds separate the PDF pages and the printed number is the last line of each page. The offset is constant: printed = PDF - 8 (PDF 9 = printed 1, PDF 99 = printed 91). This replaces the WebFetch header calibration used in round 1.
- **Quote check:** each quote was matched programmatically against the local text, normalising only whitespace, line-break hyphenation and curly vs straight quote marks. The PDF page of each match was checked against the record's page. Result: 0 mismatches over 78 quotes, of which 56 date from round 1 and none had to be dropped. R1-076 now uses the source apostrophes.
- **Annex 2:** now cited from the consolidated ICH text (printed 52-63). The five Annex 2 passages used were also found verbatim in the EMA Step 5 copy (`vendor/sources/E6R3-A2-EMA/doc_2.txt`).
- **E6R3-S4 crosswalk (loc_alt):** unchanged from round 1. Numbering was checked in the EMA Step 5 copy of the Step 4 text (EMA/CHMP/ICH/135/1995, 23 Jan 2025), https://www.ema.europa.eu/en/documents/scientific-guideline/ich-e6-r3-guideline-good-clinical-practice-gcp-step-5_en.pdf. All 18 checked locations are identical. `loc_alt` is filled only for those 18.

## 1. Coverage checklist per target

| Target | Status | Records |
|---|---|---|
| Principles 1-11 | read (local PDF 12-15) | R1-001..R1-010, R1-091 |
| Glossary (printed 82-91) | read in full; list of term headings checked | R1-130..R1-144 |
| - protocol deviation / important protocol deviation | read: **no glossary entry** | body text only: R1-032, R1-033 (A1-3.9.3) |
| - noncompliance / serious noncompliance | read: **no entry** (only "Compliance (in relation to trials)") | R1-130; body R1-074 (A1-3.12.2) |
| - critical to quality factors | read: **no entry** | body R1-091 (P6.2), R1-036 (A1-3.10) |
| - acceptable ranges / quality tolerance limits | read: **no entry** | body R1-041 (A1-3.10.1.3) |
| - serious breach | read: **term absent from whole document** (only "security breach(es)") | - |
| - essential records, monitoring, monitoring plan, monitoring report, protocol, protocol amendment, audit trail, source records, CSR, sponsor, investigator, IRB/IEC, regulatory authorities, service provider | read and extracted | R1-131..R1-144 |
| A1 section 1 IRB/IEC | read | R1-011..R1-014 |
| A1 2.1-2.5 | read | R1-015..R1-024 |
| A1 2.6-2.11 (item-read in round 2) | read | 2.10.6 R1-092, 2.11 R1-093. 2.6 (premature termination), 2.7 (medical care, safety reporting), 2.8 (consent) and 2.9 (end of participation) read, with no deviation or noncompliance obligation to extract |
| A1 2.12-2.13 | read | R1-025..R1-029, R1-094 (2.12.3), R1-095 (2.12.10(e)) |
| A1 3.1 | read | R1-030, R1-096 (3.1.4) |
| A1 3.2-3.8 (item-read in round 2) | read | 3.3 R1-097, 3.6.3(a) R1-098, 3.6.6 R1-099. 3.2, 3.4, 3.5, 3.7 and 3.8 read, not iPD-specific |
| A1 3.9-3.12 | read | R1-031..R1-078 |
| A1 3.13 | read (3.13.1-3.13.3) | R1-079, R1-080. 3.13.2(e) urgent safety issues not extracted (EU urgent safety measures belong to R3) |
| A1 3.14-3.15 | scanned, not item-read | no deviation or noncompliance terms (grep) |
| A1 3.16.1-3.16.4 | read | R1-081..R1-085. 3.16.3(b)-(c) and 3.16.4 read, not extracted |
| A1 3.17 incl. 3.17.2 (CSR) | read | R1-100 (3.17.2(a)). 3.17.2 does not mention deviations |
| A1 section 4 data governance | read in full (PDF 53-59) | R1-101..R1-108 (4.2.2, 4.2.3, 4.2.4, 4.2.6(b) x2, 4.2.6(c), 4.2.7, 4.3.4(a)) |
| Annex 2 | read in the consolidated text | R1-086..R1-090 (re-sourced). No "deviation" or "noncompliance" in Annex 2 |
| Appendix A (IB) | not read | out of scope |
| Appendix B | read (PDF 78-82) | R1-109..R1-114 (intro, B.2.5, B.10.4, B.12.1, B.12.2, B.12.3) |
| Appendix C | read in full (PDF 83-89) | R1-115..R1-129 (C.1.3, C.2.3, C.2.5, C.2.6, C.3.1(a)(r)(s), C.3.2 plus 7 table-row records) |

Appendix C references, exactly as printed:
- The Essential Records Table has no row numbers. Rows are cited as loc `AppC-C.3.2`, with the printed page and the row text quoted in the paraphrase.
- Deviation row (printed 81): "Records and reports of noncompliance including protocol deviations and corrective and preventative actions". It has no asterisk, so it is not a pre-start record.
- Monitoring rows (printed 81): site monitoring reports and centralised monitoring reports.
- Data finalisation and analysis-set decisions (printed 81).
- Trial-specific plans (printed 81): the risk management, monitoring, data management and data validation plans are asterisked, meaning they should generally be in place before the trial starts.
- Protocol amendments and authority authorisations/notifications, and interim/final clinical trial reports (printed 79).
- Retention text: C.3.2 says listed records "should be retained when produced", and the table header repeats this. Appendix C sets no fixed retention period: retention follows applicable regulatory requirements (C.1.3, A1-2.12.12, A1-3.16.3(a)).

## Change log (round 2)

- **New records:** R1-091..R1-144 (54), appended without renumbering.
- **All 90 earlier records:** page set to "printed N / PDF M" and retrieval set to the local text.
- **Content corrections:**
  - R1-009: P10.1 wording is "sponsor may transfer / investigator may delegate"; party fixed.
  - R1-010: party.
  - R1-039: the evaluation dimension is harm/hazard, not errors.
  - R1-040: "decide which risks to reduce or accept" is not in the text; CtQ tag removed.
  - R1-041: CtQ tag added, because the acceptable ranges support control of risks to CtQ factors.
  - R1-044: what is reviewed is the implemented quality management activities.
  - R1-048: the sponsor determines extent and nature of monitoring based on risks.
  - R1-050: persons named are medical monitor, data scientist/data manager and biostatistician.
  - R1-053: monitoring plan scope.
  - R1-055: party is "persons performing monitoring".
  - R1-063: the basis is "protocol and trial procedures".
  - R1-080: page 36 corrected to 37.
- **Wording enrichments:** R1-007, R1-008, R1-012, R1-013, R1-020, R1-028, R1-034, R1-042, R1-045, R1-051, R1-069, R1-081, R1-083, R1-084, R1-087, R1-088.
- **Verify items closed or confidence raised after text check:** R1-006, R1-014, R1-015, R1-019, R1-026, R1-030, R1-031, R1-033, R1-035, R1-043, R1-047, R1-049, R1-052, R1-060, R1-062, R1-065..R1-068, R1-070, R1-074, R1-077, R1-078, R1-082, R1-085.
- **Re-sourced:** R1-086..R1-090 moved from E6R3-A2-EMA to E6R3, with consolidated pages 55-62.
- **Quotes:** R1-089 gains a quote; R1-076 apostrophes set to the source characters; no quote dropped.
- **Total:** 58 earlier records changed beyond page/retrieval (corrections, enrichments, verify closures).

## Final counts

- 144 records, all binding-ICH.
- By step_hint: define 30, other 22, archive 18, document 16, identify 16, notify 14, mitigate 12, assess 9, report-csr 4, classify 3.
- Themes: CtQ 10 (R1-002, R1-005, R1-030, R1-036, R1-038, R1-041, R1-053, R1-089, R1-091, R1-112). RBQM 41.

## 2. Fetch log

Round 1 (WebFetch, 2026-11-06): F01-F41 as recorded in round 1. In summary, the consolidated PDF text was capped at 139,107 characters, ending in A1-3.16.3(c) at printed 44. The round-1 records rest on F03-F05, F11-F30 and F33-F41. EMA copies were F07, F08, F31, F32, F37 and F38. Searches S1-S7 were used only to locate files. Round-1 quotes were double-confirmed and all of them are now re-verified against the local text.

Round 2 (local text `vendor/sources/e6r3/E6R3_consolidated_2026-06-16.txt`, read-only):

| Step | PDF pages | Content |
|---|---|---|
| L01 | all | page map (printed = PDF - 8), full-text term scans: deviat, noncompliance, critical to quality, acceptable range, quality tolerance, serious breach, immediate hazard |
| L02 | 12-15 | Principles 2-11 |
| L03 | 18-23 | A1 1.3-1.5, 2.1-2.7 |
| L04 | 28-31 | A1 2.9-2.13, 3 intro, 3.1 |
| L05 | 32-34 | A1 3.2-3.9.2 |
| L06 | 35-45 | A1 3.9.3-3.14 |
| L07 | 47-51 | A1 3.16.1 (targeted), 3.16.1(x), 3.16.2, 3.16.3(a) |
| L08 | 51-59 | A1 3.16.3-3.17, section 4 |
| L09 | 60-71 | Annex 2 headings; 2.4, 2.4.1, 3.1, 3.2, 3.8 in full (PDF 63-65, 70) |
| L10 | 78, 81-82 | Appendix B intro, B.1-B.2, B.9-B.16 (B.3-B.8 by heading and grep) |
| L11 | 83-89 | Appendix C in full incl. Essential Records Table |
| L12 | 90-98 | Glossary in full (term heading list checked against the targets) |
| L13 | - | EMA Annex 2 copy `vendor/sources/E6R3-A2-EMA/doc_2.txt`: 5 passages matched |
| L14 | - | automated quote and page check of all 144 records (0 errors) |

## New source keys (section 3)

None. The key E6R3-A2-EMA proposed in round 1 is withdrawn: all Annex 2 findings now cite E6R3, and Y1 need not register it.

## Registry updates proposed for Y1 (existing keys)

- E6R3: url_status can be set to confirmed. Local copy sha256 f62d668b7b3495cef26cb52417e051981ce5edd989ff023bf6d68a3b294ff84a, 99 pages.
- E6R3-S4: the official ICH URL was not found. Numbering was checked in the EMA Step 5 copy (URL in section 6).

## 4. Leads for other stems

- **R2 (E8(R1)):** A1-3.10 anchors CtQ to "critical to quality factors as described in ICH E8(R1)". E6(R3) describes CtQ factors in P6.2 (R1-091). No E6(R3) text links CtQ factors to the iPD criteria in A1-3.9.3. Appendix B.12.1 places the CtQ factors, risks and mitigations in the protocol. The CtQ-to-iPD link must come from E8(R1) 3.2-3.3 or from R5.
- **R2 (E3):** 3.17.2(a) requires clinical trial reports to meet ICH E3 standards. 3.10 and 3.10.1.6 send the quality management approach and important quality issues to the CSR. E6(R3) states no CSR duty for important protocol deviations as such, so E3 10.2 and E3 Q&A must carry it.
- **R2 (E9/E9(R1)):** 3.16.2 says it should be read with ICH E9 and E9(R1). B.10.4 requires the protocol to cover analysis populations and intercurrent events, aligned with estimands. 4.2.6(b)-(c) place compiling protocol deviations, addressing their impact and determining analysis sets in data finalisation before analysis. This corrects the round-1 note "no E9 citation", which applied only to the text reachable then.
- **R3 (EU):**
  - Serious noncompliance (A1-3.12.2) has no time limit in E6(R3). Compare it with the EU CTR serious breach article and its clock; "serious breach" does not occur in E6(R3).
  - The immediate-hazard records (R1-012, R1-022..R1-024, R1-079, R1-080) and 3.13.2(e) (urgent safety issues "without undue delay") should be compared with the EU CTR urgent safety measures.
- **R4 (US):** A1-3.12.3 maps to the 21 CFR 312 rules on the sponsor securing compliance. A1-1.4.8 and 2.5.5 map to 21 CFR 56.108 and 312.66. A1-2.11 (premature unblinding explained to the sponsor) is a candidate deviation category to compare with FDA-PD24.
- **R5:** Appendix B intro (acceptable ranges for protocol provisions reduce deviations) and B.12.3 (protocol describes how noncompliance is handled) are E6(R3) anchors to compare with the TransCelerate deviation categories and process guide.

## 5. Open questions and conflicts

- **C1 Pages: resolved.** All pages come from the local text. Round 1 had one wrong page (R1-080, 36 instead of 37); the fetches that ran one page high had already been overruled in round 1.
- **C2 Limits terminology: confirmed and extended.** The Glossary defines neither "acceptable ranges" nor "quality tolerance limits". A1-3.10.1.3 uses "acceptable ranges", with QTL at trial level as an example. The Appendix B intro uses "acceptable ranges" in a second sense: windows for specific protocol provisions that reduce deviations (R1-109). The model must keep the two senses apart.
- **C3 iPD vs CtQ: confirmed.** Neither the Glossary nor any of the 9 "critical to quality" occurrences (Intro, P6.2 x2, P7.3, A1-3.10, 3.10.1.1, 3.10.1.3, 3.11.4.3, A2-3.8, B.12.1) links CtQ factors to iPD classification. A1-3.9.3 defines iPDs by impact on data and participants only.
- **C4 Decision concepts: unchanged.** Important protocol deviation (A1-3.9.3), serious noncompliance (A1-3.12.2, notified per applicable requirements, no deadline) and the EU serious breach (R3, term absent in E6(R3)) stay separate decisions.
- **C5 Immediate-hazard timing: unchanged.** E6(R3) says "promptly" and sets no numeric deadline.
- **C6 CSR reporting: confirmed.** 3.17.2 does not mention deviations. The E6(R3) steps closest to CSR reporting are A1-4.2.6(b) (compile protocol deviations and address their impact at data finalisation, modal "may") and 3.10.1.6 (important quality issues in the CSR).
- **C7 Actor of monitoring sub-items: unchanged.** These are gerund lists under the 3.11.4.5 lead-in; the monitor lane is inferred from 3.11.4.5.1(a) and 3.11.4.4.
- **C8 CSR naming: resolved.** The Glossary entry "Clinical Trial/Study Report (CSR)" (R1-139) makes "clinical trial report" and "CSR" the same term.
- **C9 Non-protocol uses of "deviation":** "deviation beyond these ranges" (3.10.1.3, range exceedance), "deviations from the planned statistical analysis" (3.16.2(e)) and "deviation(s) from the statistical analysis plan" (B.10.5) are not protocol deviations. 3.16.2(e) and B.10.5 are not recorded.
- **C10 3.12.3 trigger: resolved.** Notification is tied to "these circumstances" (persistent significant noncompliance where termination is considered), not to completed termination.
- **C11 Annex 2 identity: resolved** for the passages cited (consolidated text equals the EMA copy).
- **C12 P10.1 modal: resolved** ("may transfer / may delegate ... retain overall responsibility").
- **C13 New:** premature unblinding (A1-2.11) must be documented and explained to the sponsor promptly. E6(R3) does not call it a deviation; whether it is an iPD category is a trial-specific criterion (A1-3.9.3).
- **C14 New:** section 4 duties sit with the "responsible party (i.e., investigators and sponsors)". party_norm is set to sponsor in R1-101..R1-108, and Y1 may split lanes.
