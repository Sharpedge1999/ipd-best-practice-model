# R3 EU - research notes

Status: 06 Nov 2026 (re-entry 1, quality fix). Owner: research stem R3 (EU). Companion to `research/R3_eu.yaml` (107 findings, R3-001 to R3-107).

Counts after re-entry: binding-law 42, guidance 63, binding-ICH 2. step_hint: notify 29, other 17, define 15, classify 15, archive 8, assess 7, mitigate 5, document 5, report-csr 4, identify 2. Sources: EUCTR 42, EMA-SB 42, EUCTR-QA 10, CTIS-BT-SB24 7, EMA-E6R3 3, CTIS-TM17 2, CTIS-TM05 1. Confidence: high 104, medium 2 (R3-056, R3-089), low 1 (R3-097). Open verify items remain on 5 records (R3-056, R3-065, R3-087, R3-088, R3-097).

## 0. Change log

- 2026-11-06 initial run: R3-001 to R3-097 (WebFetch only).
- 2026-11-06 re-entry 1 (coordinator quality fix, local official copies under `vendor/sources/`, see INDEX.md):
  - All 42 EUCTR findings: page set to the OJ page ("OJ L 158/n") from the original OJ text; article/paragraph numbers and all quotes checked against the OJ text; wording read in the consolidated text 02014R0536-20221205 is identical to the OJ text for every fragment compared (recorded in `retrieval`). No consolidated-vs-OJ wording difference found, so no difference verify items were needed. OJ page verify items removed.
  - EUCTR corrections from the OJ text: R3-013 party (Art. 38(1) is passive; the sponsor appears only in the article title); R3-014 loc confirmed `Art. 38(2)`; R3-015 24-hour rule sits in the second subparagraph of Art. 41(2); R3-022 record "monitoring plan" removed (not named in Art. 48); R3-030 Chapter III and VII titles confirmed; R3-037 party (second paragraph of Art. 58 is passive); R3-041 deadline wording "That opinion shall be delivered within seven days" (start of period not stated); R3-042 loc confirmed `Art. 78(6)`.
  - EMA-SB (R3-043 to R3-084): all single-fetch items confirmed against the local copy; paraphrases sharpened (R3-045, R3-047, R3-053, R3-055, R3-057, R3-060, R3-066, R3-067, R3-071, R3-074, R3-075, R3-077, R3-081, R3-084); pages corrected for Appendix I example 8.2 (printed 15) and Appendix III b (printed 20-21); R3-061 quote apostrophe set to the typographic form used in the source. All EMA-SB quotes match verbatim (R3-080 checked in reading order with pdftotext because the table layout splits the cell).
  - EUCTR-QA: the local copy is **version 7.4, October 2026** (supersedes 7.3); WebFetch had returned v7.3 (July 2026). R3-085/086 doc updated to v7.4; wording of Q&A 1.5 unchanged. New records R3-098 to R3-105 from Q&A 10.1, 10.9, 11.3, 11.4 and 7.27.
  - CTIS: R3-090 to R3-096 confirmed against local copies; R3-094 publication timing corrected (category-dependent; 30 months after EU/EEA end of trial for Category 1 adult trials). New records R3-106 (withdrawal on Member State request) and R3-107 (avoid over-reporting). CTIS-TM05 local copy is a 404 page, so R3-097 stays low.
  - EMA-E6R3: R3-087/088 dates confirmed in local copies; R3-089 wording confirmed and quote added, confidence raised to medium.

Conventions used in R3_eu.yaml:
- EU CTR loc uses `Art. <n>(<p>)`. Art. 47, 48, 57 and 58 have **unnumbered** paragraphs in the text (F11, F46); they are cited as `Art. <n>` and the paraphrase names the ordinal paragraph ("first (unnumbered) paragraph"). This follows the EUR-Lex citation style "Article 58, first paragraph".
- The brief asked for `QA:<n>` for Q&A items; the S0 linter (decisions.md S0-02) does not accept `QA:`. Q&A numbers are therefore written in the section form `S<n>` (e.g. `S1.5` = Q&A 1.5).
- Guidance appendices: `SAppI-8.2` (Appendix I example 8.2), `SAppII`, `SAppIIIb`; glossary `SGlossary`; slides `SSlide-<n>`; document covers `SCover`; EMA web page `SWebpage`.
- EU CTR pages are OJ pages of the original publication (OJ L 158, 27.5.2014), taken from the local pdftotext copy with "L 158/n" headers (re-entry 1). Article wording was read in the consolidated text and compared with the OJ text.
- Q&A page numbers are the printed footers, which restart per chapter in the Q&A document (e.g. "printed 1-2 (chapter 11)").

## 1. Coverage checklist per target

| Target | Status | Findings | Notes |
|---|---|---|---|
| EU CTR Art. 2 definitions | Covered | R3-001 to R3-011 | Points (11) ethics committee, (12) MSC, (13) substantial modification, (14) sponsor, (15) investigator, (16) PI, (22) protocol, (26) end of trial, (30) GCP, (31) inspection, (35) CSR. Art. 2(2) has 35 points; **no definition of serious breach in Art. 2** (F01, F04, F10). Serious breach is defined only in Art. 52(2). |
| Art. 41 (boundary) | Covered | R3-015 | Title: "Reporting of adverse events and serious adverse events by the investigator to the sponsor" (OJ L 158/37); 4 numbered paragraphs; 24-hour SAE rule in the second subparagraph of Art. 41(2). Recorded as boundary (safety process interface). |
| Art. 47 | Covered | R3-016 to R3-020 | Three unnumbered paragraphs: (1st) conduct per protocol and GCP principles; (2nd) take appropriate account of quality standards and ICH GCP; (3rd) Commission publishes ICH GCP. Split per party. |
| Art. 48 (added, monitoring) | Covered | R3-021, R3-022 | Not in the target list; added because monitoring is the legal basis for site identification of deviations and for risk-proportionate monitoring. |
| Art. 52 | Covered | R3-023, R3-024 | Two numbered paragraphs. Who: sponsor. Recipient: Member States concerned. Channel: EU portal. Clock: without undue delay, not later than seven days of becoming aware. Scope: breach of the Regulation or of the protocol version applicable at the time of the breach. |
| Art. 53 | Covered | R3-025, R3-026 | (1) unexpected events affecting benefit-risk, not SUSARs (Art. 42): 15 days from awareness. (2) third-country inspection reports: no deadline stated. |
| Art. 54 | Covered | R3-027 to R3-030 | Confirmed: urgent safety measures are Art. 54 (not Art. 38 as in brief.md). (1) sponsor and investigator take USM; (2) sponsor notifies within 7 days from the date measures were taken; (3) without prejudice to Chapters III and VII. Notification content per text: the event and the measures taken. Art. 54 itself does not require a substantial modification; 54(3) keeps Chapter III (authorisation procedure for a substantial modification) and Chapter VII (safety reporting) applicable, and EUCTR-QA Q&A 7.27 expects a USM that needs a protocol update to be followed by a substantial modification (R3-103). |
| Art. 38 (added) | Covered | R3-013, R3-014 | Temporary halt / early termination for subject safety, 15 days (Art. 38(1) is passive; sponsor named in title). Restart = substantial modification (Art. 38(2)). If USMs accompany the halt, Q&A 10.9 applies the 7-day Art. 54 clock (R3-101). |
| Art. 37(4) (added) | Covered | R3-012 | CSR submission to EU database within 30 days after MA granted/procedure completed/withdrawn (applicant). Process-end boundary. |
| Art. 56 (added) | Covered | R3-031 | Record/store information so it can be accurately reported, interpreted and verified. |
| Art. 57-58 | Covered | R3-032 to R3-039 | Art. 57: sponsor and investigator keep CTMF, essential documents, readily available and directly accessible to Member States. Art. 58: six unnumbered paragraphs; at least 25 years after end of trial; medical files per national law; accessible to competent authorities; transfer documented; sponsor appoints archive individuals; media keep content complete and legible; alterations traceable. |
| Art. 77-78 (added) | Covered | R3-040 to R3-042 | Authority-side corrective measures (OJ L 158/46) and inspection report (Art. 78(6), OJ L 158/47). Confirmed against the OJ text in re-entry 1; high confidence. |
| EMA-SB definition, examples | Covered | R3-043 to R3-046, R3-079, R3-080 | Glossary definitions; Appendix I categories listed; only protocol compliance examples (8.1-8.5) recorded. Confirmed against the local copy. |
| EMA-SB decision process, who assesses | Covered | R3-050, R3-066, R3-067, R3-081 | Sponsor (or delegated party under contract) assesses; Appendix II is a bulleted points-to-consider list, not a decision tree. |
| EMA-SB timelines / becoming aware | Covered | R3-048, R3-049, R3-098 | 7 calendar days of sponsor awareness; assessment does not extend the clock. EUCTR-QA Q&A 11.3 sets the start at awareness of a potential breach (R3-098). Whose awareness counts (delegated party, CRO, monitor) is still not defined. |
| EMA-SB what to notify | Covered | R3-056, R3-057, R3-084 | Appendix III b items read in full (incl. A.7 most-affected-Member-State questions); Appendix III a form fields are not in the text layer of either copy. |
| EMA-SB follow-up | Covered | R3-053 | Projected timelines in initial report, follow-ups via CTIS; no fixed follow-up deadline found. |
| EMA-SB relation to protocol deviations | Covered | R3-062 to R3-065, R3-075 | See section 5. |
| EUCTR-QA (serious breach, PD, USM, GCP) | Covered (re-entry 1) | R3-085, R3-086, R3-098 to R3-105 | Local copy is v7.4 (October 2026). Q&A 1.5 (CTR precedence; sponsor submits), 10.1 (notification type table, Art. 36-38 and 52-54), 10.9 (USM with temporary halt), 11.3 (serious breaches in CTIS, start of the 7-day clock), 11.4 (third-country inspection reports) and 7.27 (USM followed by substantial modification; listing other affected trials) read and recorded. No Q&A on clinical-trial protocol deviations (only Q&A 1.20 on GLP study deviations); no dedicated TMF/archiving Q&A. |
| EMA-E6R3 | Covered | R3-087 to R3-089 | Principles and Annex 1: final CHMP adoption 12 Dec 2024, effective in the EU 23 July 2025. Annex 2: ICH adoption 3 June 2026, CHMP adoption 25 June 2026, effective 15 January 2027; consolidated guideline (EMA/CHMP/ICH/162879/2026) legal effective date 15/01/2027. Legal link: EU CTR Art. 47 (R3-016 to R3-019). EMA page itself does not mention Art. 47. |
| CTIS-HB | **Gap** | none | CTIS sponsor handbook v6.4 (EMA/148347/2026, 7 July 2026, 175 pages): section 4.9 "Notify on unexpected events, urgent safety measures, serious breaches, and third-country inspectorate inspections" (p. 140) and 4.9.1 (p. 141) exist per TOC, but the text extraction ends around p. 50. Not among the local copies either (re-entry 1), so the gap stays. Substituted by EMA CTIS training material (CTIS-BT-SB24, CTIS-TM17, CTIS-TM05; R3-090 to R3-097, R3-106, R3-107) and EUCTR-QA chapters 7, 10 and 11. |

## 2. Fetch log

All fetches 2026-11-06 via WebFetch. "Coverage" = characters of the page text returned.

| # | URL | Offset | Coverage | Purpose / result |
|---|---|---|---|---|
| F01 | https://health.ec.europa.eu/system/files/2016-11/reg_2014_536_en_0.pdf | 0 | 0-100000 of 136534 | OJ L 158/1 27.5.2014 original; Art. 2 definitions; text ends in Art. 18 (L 158/23) |
| F02 | same | 0 | 0-100000 | Art. 41/47 not in this part |
| F03 | same | 100000 | 100000-136534 | Art. 19-35 only; extraction ends in Art. 35 (L 158/33). Remaining articles not extractable from this PDF |
| F04 | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02014R0536-20221205 | 0 | 0-100000 of 143180 | Consolidated text 05.12.2022 (M1 Reg. 2022/641, M2 Del. Reg. 2022/2239, C1 OJ L 311 17.11.2016); Art. 2(2)(13), (22), (25), (31); ends in Art. 42(2)(b) |
| F05 | same | 100000 | 100000-143180 | Article list 42-90; Art. 47 and 52 text |
| F06 | same | 100000 | same | Art. 52 detail (who, recipient, portal, clock, scope, definition, 2 paragraphs) |
| F07 | same | 100000 | same | Art. 53, 54 per paragraph |
| F08 | same | 100000 | same | Art. 56, 57, 58 |
| F09 | same | 100000 | same | Art. 47, 48 |
| F10 | same | 0 | 0-100000 | Art. 2(2) list of 35 points; GCP and low-intervention definitions; Art. 37, 38, 41 |
| F11 | same | 100000 | same | Layout check: Art. 47, 57, 58 unnumbered; Art. 52(1) wording |
| F12 | https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX%3A32014R0536 | 100000 | 100000-end of extract | Page markers sought; extract again ends at Art. 35 (L 158/33) |
| F13 | consolidated HTML | 100000 | same | Verification Art. 52-54 numbering and time-limit wording |
| F14 | consolidated HTML | 0 | 0-100000 | Verification Art. 41, 37, 38 numbering and phrases |
| F15 | https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-notification-serious-breaches-regulation-eu-no-5362014-or-clinical-trial-protocol_en.pdf | 0 | full (21 pages) | EMA-SB reference, dates, TOC |
| F16 | same | 0 | full | Glossary, S1-S3.2 |
| F17 | same | 0 | full | Glossary entries |
| F18 | same | 0 | full | S3.2, S4, S5, S5.1 |
| F19 | same | 0 | full | S6-S8 |
| F20 | same | 0 | full | Appendix II, III a, III b; Appendix I categories |
| F21 | same | 0 | full | Appendix I protocol compliance 8.1-8.5; occurrences of deviation / E3 / E6 |
| F22 | same | 0 | full | S5.1 p. 8 quotes; S3.2 deadline sentence |
| F23 | same | 0 | full | Verification of 8 statements (S3.1, S3.2, S6.1, S7, S5.1) |
| F24 | https://health.ec.europa.eu/medicinal-products/eudralex/eudralex-volume-10_en | 0 | full | Q&A link and label; SB guideline link; GCP links (E6(R2) only) |
| F25 | https://health.ec.europa.eu/document/download/4ec3992a-ef9b-41f9-8e34-1dd6d0a479ae_en?filename=mp_ctr_qa_rules.pdf | 0 | 0-100000 of 122176 | Q&A v7.3 July 2026; document history; TOC; topic mapping |
| F26 | same | 0 | 0-100000 | Q&A 1.5 text; chapter 10 and 11 question titles |
| F27 | same | 100000 | 100000-122176 | Only chapter 3 content; Q&A 10.x/11.x not in extract |
| F28 | https://health.ec.europa.eu/document/download/bd165522-8acf-433a-9ab1-d7dceae58112_en?filename=regulation5362014_qa_en_0.pdf&prefLang=es | 0 | 0-100000 of 122200 | Older v7.2 (27 March 2026); truncated at p. 39; not used for findings |
| F29 | https://www.ema.europa.eu/en/documents/other/clinical-trial-information-system-ctis-sponsor-handbook_en.pdf | 0 | 0-100000 of 121179 | CTIS-HB v6.4 TOC; section 4.9 located at p. 140 |
| F30 | same | 100000 | 100000-121179 | Only pp. 40-50; section 4.9 not reachable |
| F31 | https://www.ema.europa.eu/en/documents/presentation/presentation-clinical-trials-information-system-ctis-bitesize-talk-notifications-part-2_en.pdf | 0 | full | Bitesize talk 23 Nov 2022 (superseded by F33); not used for findings |
| F32 | https://www.ema.europa.eu/system/files/documents/other/cttm17-faqs_en.pdf | 0 | full | CTIS Module 17 FAQs v1.3 Aug 2024 (authority ad hoc assessment) |
| F33 | https://www.ema.europa.eu/en/documents/presentation/presentation-ctis-bitesize-talk-end-transition-period-notifications-including-serious-breaches_en.pdf | 0 | full | Bitesize talk 16 Oct 2024 (serious breaches in CTIS) |
| F34 | https://www.ema.europa.eu/documents/other/step-step-guide-how-manage-ct-ctis-training-programme-module-05_en.pdf | 0 | full | CTIS Module 05 v1.0 Oct 2021; generic notification steps |
| F35 | https://www.ema.europa.eu/en/scientific-guidelines/ich-e6-good-clinical-practice | 0 | full | E6 versions, reference numbers, legal effective dates |
| F36 | same | 0 | full | Verification of E6(R3) dates and E6(R2) status |
| F37 | https://www.ema.europa.eu/en/documents/scientific-guideline/ich-e6r3-guideline-good-clinical-practice-step-5_en.pdf | 0 | cover (0-100000 of 141046) | Consolidated E6(R3) EMA/CHMP/ICH/162879/2026, 14 July 2026, 80 pages; step table |
| F38 | https://www.ema.europa.eu/en/documents/scientific-guideline/ich-e6-r3-guideline-good-clinical-practice-gcp-step-5_en.pdf | 0 | cover (0-100000 of 134455) | E6(R3) Step 5 EMA/CHMP/ICH/135/1995, 23 Jan 2025; step table |
| F39 | EudraLex Volume 10 page (as F24) | 0 | full | Re-check: only E6(R2) linked; Q&A label "CTR Q&A - October 2026" vs heading July 2026 |
| F40 | Q&A v7.3 (as F25) | 0 | 0-100000 | Verification: Q&A 1.5 quote; TOC vs body page numbers |
| F41 | EMA-SB (as F15) | 0 | full | Second check S3.2, S4, S6.3, S6.4, S7, S8 |
| F42 | consolidated HTML | 100000 | 100000-143180 | Art. 77, 78 |
| F43 | consolidated HTML | 0 | 0-100000 | Art. 2(2)(35); Art. 37(4) subparagraph |
| F44 | consolidated HTML | 0 | 0-100000 | Art. 2(2)(11), (12), (13), (14), (15), (16), (26) |
| F45 | CTIS bitesize 2024 (as F33) | 0 | full | Verification of 8 statements |
| F46 | consolidated HTML | 100000 | 100000-143180 | Verification Art. 48, 56(1), 57, 58 paragraph structure |
| F47 | consolidated HTML | 100000 | 100000-143180 | Exact quotes Art. 47 first and second paragraph |

Local reads (re-entry 1, 2026-11-06; official copies retrieved by the orchestrator via the shell, see `vendor/sources/INDEX.md`; read-only):

| # | Local file | Source URL (per INDEX.md) | Purpose / result |
|---|---|---|---|
| L01 | vendor/sources/EUCTR-QA/doc_12.txt | as F25 | Q&A **v7.4, October 2026** (supersedes 7.3). Read Q&A 1.5, 7.27, 10.1, 10.9, 10.14, 11.2, 11.3, 11.4; searched for deviation, USM, archiving, E6 |
| L02 | vendor/sources/CTIS-BT-SB24/doc_15.txt | as F33 | Full text; confirmed R3-090 to R3-094; new R3-106, R3-107 |
| L03 | vendor/sources/EUCTR-OJ/reg_2014_536_en.txt | https://health.ec.europa.eu/system/files/2016-11/reg_2014_536_en_0.pdf | Original OJ L 158, 27.5.2014 with "L 158/n" headers. Read Art. 2, 37, 38, 41, 47-58, 77, 78 and chapter titles; OJ pages for all EUCTR findings; all EUCTR quotes verbatim |
| L04 | vendor/sources/EMA-SB/doc_11.txt (+ doc_11.pdf page 15 via pdftotext in reading order) | as F15 | Full text; confirmed all EMA-SB findings and quotes; page corrections |
| L05 | vendor/sources/CTIS-TM17/doc_16.txt | as F32 | Confirmed Q&A 1.3, 1.4, 2.5, 2.10, 4.7 (R3-095, R3-096) |
| L06 | vendor/sources/EMA-E6R3/doc_13.txt, doc_14.txt | as F35, F37 | Confirmed E6(R3) effective dates and the "replacement for ICH E6(R2)" wording |

Not usable: vendor/sources/CTIS-TM05/doc_17.txt (HTTP 404 page); no local copy of the CTIS sponsor handbook (CTIS-HB); EUR-Lex consolidated text not retrievable from the shell (empty files in vendor/sources/EUCTR and EUCTR-pdf).

Web searches (standard mode) used to locate documents: EU CTR on eur-lex; EMA-SB; EMA-SB revisions; EudraLex Volume 10 Q&A; CTIS sponsor handbook; CTIS training modules (2 searches); EMA E6(R3) page; Commission publication of E6(R3) under Art. 47; Q&A 11.3 text; EMA guidance on protocol deviations.

## New source keys (section 3)

- CTIS-BT-SB24: "CTIS Bitesize Talk: End of transition period and notifications including serious breaches", EMA presentation, 16 October 2024 - https://www.ema.europa.eu/en/documents/presentation/presentation-ctis-bitesize-talk-end-transition-period-notifications-including-serious-breaches_en.pdf (binding: guidance; training material)
- CTIS-TM17: "Supervise a CT - Ad Hoc Assessment: FAQs", CTIS Training Programme Module 17, v1.3, August 2024 - https://www.ema.europa.eu/system/files/documents/other/cttm17-faqs_en.pdf (binding: guidance; training material)
- CTIS-TM05: "How to manage a clinical trial - step-by-step guide", CTIS Training Programme Module 05, v1.0, October 2021 - https://www.ema.europa.eu/documents/other/step-step-guide-how-manage-ct-ctis-training-programme-module-05_en.pdf (binding: guidance; possibly outdated)
- EC-EUDRALEX-V10: EudraLex Volume 10 - Clinical trials guidelines (Commission web page) - https://health.ec.europa.eu/medicinal-products/eudralex/eudralex-volume-10_en (no findings; read for document versions and Art. 47 third paragraph publication status; cited in conflict notes)

Registry updates proposed for Y1 (existing keys, confirmed URLs and titles):
- EUCTR: wording read via EUR-Lex consolidated text 02014R0536-20221205 (05.12.2022) - https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02014R0536-20221205; pages and wording checked against the original OJ L 158, 27.5.2014 (seeded health.ec.europa.eu PDF, full local text L03). WebFetch extraction of that PDF ends at Art. 35, hence the local text. The undated ELI link https://eur-lex.europa.eu/eli/reg/2014/536 resolves (per search listing) to 02014R0536-20221205, i.e. no later consolidation was found.
- EMA-SB: "Guideline for the notification of serious breaches of Regulation (EU) No 536/2014 or the clinical trial protocol", EMA/698382/2021; final adopted by CTFG 7 Dec 2021 and GCP IWG 13 Dec 2021; effective 31 January 2022; document date 30 June 2023 (HMA logo, typographical corrections only) - URL as in F15. No newer version found (search 2026-11-06); EudraLex Volume 10 links the same document.
- EUCTR-QA: "Clinical Trials Regulation (EU) No 536/2014 Questions & Answers", EudraLex Volume 10, **version 7.4, October 2026** (supersedes 7.3) - URL as in F25. WebFetch returned v7.3 (July 2026), probably a cached copy; the local copy (L01) and the EudraLex link label "CTR Q&A - October 2026" show v7.4.
- EMA-E6R3: EMA page "ICH E6 Good clinical practice - Scientific guideline" (modified 15 July 2026) - https://www.ema.europa.eu/en/scientific-guidelines/ich-e6-good-clinical-practice; plus PDF covers F37, F38.
- CTIS-HB: "Clinical Trial Information System (CTIS) Sponsor Handbook", EMA/148347/2026, version 6.4, 7 July 2026 - https://www.ema.europa.eu/en/documents/other/clinical-trial-information-system-ctis-sponsor-handbook_en.pdf (TOC only; no findings).

## 4. Leads for other stems

- R1 (E6R3): In the EU, E6(R3) principles and Annex 1 have applied since 23 July 2025, but Annex 2 and the consolidated text only from 15 January 2027 (R3-088). Where R1 cites Annex 2 for EU, the effective-date caveat applies. EMA PDF of the consolidated text: EMA/CHMP/ICH/162879/2026 (80 pages, F37) - possible alternative source for R1 if the ICH database PDF is hard to read.
- R1 / Y1: Q&A 11.3 starts the EU 7-day serious breach clock at awareness of a potential breach (R3-098); relevant when Y1 sets the deviation intake-to-assessment timing in the EU branch.
- R1 / Y1: Art. 54 (USM) obliges sponsor and investigator to act on an unexpected event that seriously affects benefit-risk; E6(R3) immediate-hazard deviations are the ICH counterpart. The EU CTR text itself does not mention "deviation" in Art. 54 - do not merge without an R1 source.
- R1 / Y1: EMA-SB S7 states that persistent or systematic non-compliance is a serious breach where it significantly affects safety/rights or data (R3-075); this is the hook between deviation trending (E6(R3) RBQM, risk thresholds) and the EU notification path.
- R2 (E3 / E3QA): EMA-SB S5.1 defines "important deviation" by reference to ICH E3 and the ICH E3 Q&A (R1), and asks that important deviations be described in the CSR even if not serious breaches (R3-062, R3-064). R2 should confirm the E3 Q&A (R1) wording.
- R2 (E9): EMA-SB S7 makes "removal of data from the trial analysis" a trigger for serious breach notification (R3-076) - link to analysis-set decisions.
- R5 (industry): EMA-SB Appendix I gives categorised serious breach examples (IMP, temperature monitoring, IRT, potential fraud, source data, emergency unblinding, sample processing, protocol compliance, SAE reporting, consent, access to data, randomisation/stratification, DSMB/DMC, privacy) - can be compared with industry deviation category lists.
- R3 follow-up (not read, possible sources): European Commission "Risk proportionate approaches in clinical trials" (April 2017), linked from EudraLex Volume 10 - https://health.ec.europa.eu/document/download/be80ee91-f7b8-4100-be72-42efd8362d71_en?filename=2017_04_25_risk_proportionate_approaches_in_ct.pdf ; EMA "Reflection paper on risk based quality management in clinical trials" (seen in search results only). No EMA guidance dedicated to protocol deviations was found (search 2026-11-06).
- Y1 (US comparison, R4): EU serious breach (sponsor -> authority, 7 calendar days) has no direct investigator-to-authority leg; investigator reporting to the sponsor is guidance/contract only (R3-071). Compare with 21 CFR 56.108(b) IRB reporting found by R4.

## 5. Open questions and conflicts

1. **Serious breach vs important protocol deviation (core).** EMA-SB S5.1: an important deviation (ICH E3 / E3 Q&A R1) is not necessarily a serious breach and vice versa; not every important deviation is reported through CTIS; all serious breaches and all important deviations go into the CSR; non-serious deviations are documented (CRF or CTMF) for CAPA (R3-062 to R3-065). Model implication: two independent classification gateways (iPD per protocol-defined criteria; serious breach per Art. 52(2)), with EU-only notification on the serious breach path and CSR reporting on both. Overlap points: persistent/systematic non-compliance (R3-075), data removal from analysis (R3-076), fraud (R3-072).
2. **Article numbers in brief.md.** brief.md lists "Art. 38 urgent safety measures"; the text shows Art. 38 = temporary halt or early termination for subject safety (15 days) and Art. 54 = urgent safety measures (7 days from the date measures were taken). Recorded in R3-013 and R3-027.
3. **Day 0 / "becoming aware" (partly resolved in re-entry 1).** EUCTR-QA Q&A 11.3 (v7.4) states that the 7-day timeframe starts when the sponsor becomes aware of a *potential* breach; the first analysis and confirmation of seriousness must fit inside the 7 days (R3-098). This is stricter than a reading of Art. 52(1) ('becoming aware of that breach') that starts the clock at confirmation. Still open: whether awareness by a delegated party, CRO or monitor counts as sponsor awareness. EMA-SB requires contracts to make all parties report immediately to the sponsor contact point (R3-051). Open for Y1/user.
4. **"seven days" vs "7 calendar days".** Art. 52(1) says seven days; EMA-SB S3.2 and the CTIS talk say calendar days. Model can use "7 calendar days (EMA-SB)" with the Art. 52 citation for the obligation.
5. **Protocol version.** Art. 52(1): version applicable at the time of the breach; EMA-SB glossary: approved protocol version. Minor; use the Regulation wording.
6. **Binding class of ICH E6(R3) in the EU.** EU CTR Art. 47 obliges compliance with GCP principles (defined in Art. 2(2)(30)) and to "take appropriate account" of ICH GCP; Q&A 1.5 says the EU CTR prevails over conflicting guideline rules. R3-087/088 use binding-ICH with this route and a [verify binding] item for Y1.
7. **Commission publication of ICH GCP (Art. 47 third paragraph).** EudraLex Volume 10 links only ICH E6(R2) (2016) under Regulation (EU) No 536/2014 (F24, F39), while EMA states E6(R3) principles and Annex 1 have been effective since 23 July 2025. EMA-SB also references E6(R2). Recorded in R3-020 and R3-087 conflict notes.
8. **E6(R3) effective dates.** Principles and Annex 1 effective in EU 23 July 2025; Annex 2 and consolidated text effective 15 January 2027. On the research date Annex 2 is adopted but not yet effective in the EU. The EMA page text calls Annex 2 "Step 4" while labelling the document Step 5 (minor).
9. **Investigator duties are partly guidance only.** Art. 52 and 54(2) place notification on the sponsor only; the investigator's duty to report suspected serious breaches to the sponsor comes from EMA-SB S3.2/S6.4 and contract/protocol, not from an EU CTR article (R3-051, R3-071). Investigator USM action itself is binding (Art. 54(1), R3-028).
10. **Access wording.** Art. 57: accessible to "the Member States"; Art. 58: accessible to "competent authorities". Minor.
11. **Art. 54(3) (resolved in re-entry 1).** OJ text: Chapter III = authorisation procedure for a substantial modification; Chapter VII = safety reporting. Q&A 7.27 expects a USM that requires a protocol update to be followed by a substantial modification (R3-103).
12. **Q&A document dating (resolved in re-entry 1).** The current file behind the EudraLex link is v7.4, October 2026 (local copy L01); WebFetch had served v7.3. v7.4 changes only Chapter 6 (summary of results) and Annex II per its history table. Page footers restart per chapter; findings cite printed footer pages with the chapter.
13. **CTIS steps.** The authoritative sponsor handbook section (CTIS-HB 4.9) was not readable; CTIS steps rest on EMA training material (2021-2024). The 2021 Module 05 statement that updates/withdrawals need a justification (R3-097) is low confidence.
14. **Follow-up deadline.** No fixed deadline for serious breach follow-up reports was found in EMA-SB, the Q&A or the CTIS talk (projected timelines set by the sponsor in the initial report; RFI deadlines proposed by the most affected or coordinating Member State).
15. **Temporary halt with urgent safety measures (new, re-entry 1).** Art. 38(1) allows 15 days for a safety-related halt or early termination; Q&A 10.9 requires a single notification within the 7-day Art. 54(2) clock when USMs accompany the halt, and routes partial halts as USM notifications (R3-100, R3-101). Q&A 10.1 also routes a decision to early terminate (parts of) a trial for benefit-risk reasons as a USM (R3-102). Model: one USM/TH decision with the shorter clock.
16. **Publication timing (new, re-entry 1).** Serious breach, USM and unexpected event notifications are published only after Member State assessment, and for Category 1 adult trials only 30 months after EU/EEA end of trial (R3-094). Withdrawn breaches (on Member State request) are not published (R3-106).

## 6. Versions and dates read

| Key | Document as read | Version / date |
|---|---|---|
| EUCTR | Regulation (EU) No 536/2014, EUR-Lex consolidated text 02014R0536-20221205; original OJ text (L03) | consolidated 05.12.2022 (M1 Reg. (EU) 2022/641; M2 Del. Reg. (EU) 2022/2239; C1 corrigendum OJ L 311, 17.11.2016); original OJ L 158, 27.5.2014 (pages; wording identical for all articles compared) |
| EMA-SB | Guideline for the notification of serious breaches, EMA/698382/2021 | final adopted CTFG 7 Dec 2021, GCP IWG 13 Dec 2021; effective 31 Jan 2022; document date 30 June 2023; 21 pages |
| EUCTR-QA | Clinical Trials Regulation (EU) No 536/2014 Questions & Answers | v7.4, October 2026 (local copy, chapters 1, 7, 10, 11 used); v7.3 July 2026 seen via WebFetch; v7.2 of 27 March 2026 opened, not used |
| EMA-E6R3 | EMA E6 scientific guideline page; E6(R3) Step 5 EMA/CHMP/ICH/135/1995; consolidated E6(R3) Step 5 EMA/CHMP/ICH/162879/2026 | page modified 15 July 2026; PDF 23 Jan 2025; PDF 14 July 2026 (covers only); local copies L06 |
| CTIS-HB | CTIS Sponsor Handbook EMA/148347/2026 | v6.4, 7 July 2026 (TOC only; no local copy) |
| CTIS-BT-SB24 | CTIS Bitesize Talk, end of transition period and notifications incl. serious breaches | 16 Oct 2024 |
| CTIS-TM17 | CTIS Training Module 17 FAQs, Supervise a CT - Ad hoc assessment | v1.3, Aug 2024 |
| CTIS-TM05 | CTIS Training Module 05, How to manage a CT, step-by-step guide | v1.0, Oct 2021 (WebFetch only; local copy is a 404 page) |
| EC-EUDRALEX-V10 | EudraLex Volume 10 web page | fetched 2026-11-06; latest update item 28 Oct 2026 |
