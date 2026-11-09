# X1 verification summary (blind, 2026-11-06)

Inputs: verification worklist (427 items), source registry, local official texts listed in vendor/sources/INDEX.md; WebFetch only for items without usable local text or where the cited part was not local. No other project folders were opened.

## Overall counts

| Verdict | Count |
|---|---|
| confirmed | 414 |
| paraphrase-distorted | 7 |
| page-wrong | 5 |
| loc-wrong | 1 |
| quote-mismatch | 0 |
| binding-wrong | 0 |
| not-found | 0 |

Severity of the 13 non-confirmed items: high 0, medium 3, low 10. All 170 quotes are verbatim in the cited source (163 matched automatically; 4 in multi-column tables verified by reading the column; 1 verbatim on the EMA web page rather than the cited cover; 2 verbatim per two WebFetch calls).

## Counts per source

| Source | Items | confirmed | loc-wrong | page-wrong | paraphrase-distorted | quote-mismatch | binding-wrong | not-found | high | medium | low |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E6R3 | 144 | 143 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| E8R1 | 51 | 50 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| E3 | 13 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E3QA | 11 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E9 | 21 | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| E9R1 | 14 | 13 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| M11 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| M11-TEMPLATE | 6 | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| EUCTR | 42 | 42 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EMA-SB | 31 | 30 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| EUCTR-QA | 6 | 5 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| EMA-E6R3 | 3 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 |
| CTIS-BT-SB24 | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CTIS-TM17 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 21CFR312 | 24 | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 21CFR56 | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 21CFR50 | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| FDA-PD24 | 13 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| FDA-E6R3 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| FDA-RBM13 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| FDA-RBM23 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| TCB-PD-TIRS | 15 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| TCB-PD | 2 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| TCB-RBQM | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| CTTI-CTQ | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CDISC-CT | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CDISC-SDTMIG40-PR | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| NCIT-DV | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| FDA-SDTCG | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| FDA-ESTUDY | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| **Total** | 427 | 414 | 1 | 5 | 7 | 0 | 0 | 0 | 0 | 3 | 10 |


## High-severity items

None. No item changes an obligation's actor, deadline or recipient against its source.

## Medium-severity items

- R3-048 (EMA-SB S3.2, paraphrase-distorted): guideline says the assessment "should" be timely and "should not extend" the 7-day period; paraphrase uses "must". The 7-day limit is binding through EU CTR Art. 52(1), so practical impact is limited.
- R3-089 (EMA-E6R3 web page, paraphrase-distorted): the "replacement for ICH E6(R2)" sentence refers to Annex 1 (with the principles), not Annex 2.
- R5-046 (TCB-PD web page, paraphrase-distorted): source defines finalising the PD process as closing out the living PDAP and recommends finalisation after the last study data have been reviewed; paraphrase redefines it and drops the recommendation as unconfirmed.

## Low-severity items

- R1-127 (E6R3 Appendix C table): asterisk list omits the safety plan.
- R2-017 (E8R1 3.3.1): "evidence used to inform the study design" widened to "evidence supporting quality decisions".
- R2-102 (E9R1 A.3.4): content on printed 12, not 13.
- R2-115, R2-116, R2-117 (M11 Template 10.2, 11.6, 11.10): pages one too high; correct printed 46, 52, 53 (footer and TOC agree).
- R3-085 (EUCTR-QA 1.5): "shall not be requested or submitted" weakened to "should not".
- R3-088 (EMA-E6R3): quote is on the EMA web page, not on the cover of EMA/CHMP/ICH/162879/2026 (cover table gives the same date in other words).
- R5-048 (TCB-RBQM): "In parallel" rendered as a sequence ("then").
- R5-071 (FDA-ESTUDY): pages one too high; lines 36-42 are printed 2, lines 234-248 printed 7.

## Method notes

- Helper tools under verification/tools/ (run with python3 -I): x1lib.py (text normalisation: NFKC, typographic quotes and dashes, whitespace, removal of running headers/footers and margin line numbers; offset-to-page mapping with printed page read from footers or OJ "L 158/n" headers), x1loc.py (locators for E6R3 annex/section/sub-item grammar, numeric and roman section headings, EU CTR article/paragraph/point, CFR sections), x1_report.py (per-source review blocks: verbatim quote check incl. all occurrences, located passage, best-matching sentence), x1_where.py, x1_lines.py (margin line numbers of FDA drafts), x1_e3qa_cols.py (column reconstruction for the E3 Q&A table), x1_assemble.py (builds X1_results.yaml, verifies every evidence snippet against the local text and cross-checks cited vs found pages).
- Quote checks were automatic; every paraphrase was judged by reading the located passage. Where a locator missed (TOC hits, glossary terms, slides, roman headings with line numbers) the passage was located by phrase search and read manually.
- Evidence snippets (max. 14 words) are verified verbatim against the local text by x1_assemble.py; six snippets from multi-column tables (R2-066 to R2-070 in the E3 Q&A, R5-058 in the CTTI CTQ table) fail the automatic check only because pdftotext interleaves columns and were verified by reading the column.
- Judgement files per source are in verification/work/judg_*.yaml; review dumps in verification/work/rep_*.txt.
- Page convention in X1_results.yaml: "PDF n / printed m" from the local pdftotext copy; CFR and HTML sources are unpaginated.
- Strictness: dropped qualifiers that do not change meaning ("as appropriate", "if applicable") and the extractors' own interpretive tails were noted, not failed. Modality changes (should to must, shall to should), subject changes and sequence changes were failed.
- binding-wrong: none. Document status in every doc label matches the source cover (FDA-PD24 and FDA-E6R3-A2 drafts; CDISC SDTMIG v4.0 public review draft; EUCTR-QA v7.4; FDA E6(R3) "Final Level 1 Guidance"; E6(R3) consolidated Step 4 of 16 June 2026).
- WebFetch used for: R3-087 (cover of EMA/CHMP/ICH/135/1995), R4-078 (Federal Register notice 2025-17311, two fetches; FDA guidance page), R5-045, R5-046 (two fetches), R5-048 (two fetches), R5-068. Every non-confirmed WebFetch verdict rests on two differently worded fetches.

## Not fully checkable

- TCB-PD-TIRS: local copy is PMC HTML; journal page numbers ("pp. 733-742, section page not confirmed") cannot be narrowed.
- EMA-SB S4 most-affected-Member-State diagram is an image; only the Appendix III b A.7 text could be checked (R3-057).
- TCB-PD, TCB-RBQM, NCIT-DV: no usable local text; checked through WebFetch summaries (verbatim wording requested), not against a fixed copy. NCIT-DV is a secondary mirror, not the NCI EVS primary record.
- EU CTR: wording checked against the original OJ L 158 text; the EUR-Lex consolidated version cited in the doc labels was not retrievable, so amendments to the cited articles could not be excluded (none expected for Art. 2, 37, 38, 41, 47, 48, 52-58, 77, 78).
- 21 CFR: local eCFR API text is as of 2026-11-04; the doc labels cite section stamps from 10/08-10/23/2026. No textual differences can be detected without the earlier version.
- CTIS public-portal publication behaviour (R3-094, R3-096, R3-106) is checked against the training material only, not against the live system.

## Re-check (gate G4, 2026-11-06)

Scope: the 16 entries of synthesis/x1_corrections.yaml (the only extra file opened). Corrected fields were checked against the local text; R5-046 and R5-048 (no usable local copy) by WebFetch, with each now resting on four differently worded fetches across both rounds. Details in X1_recheck.yaml.

- All 16 entries are now confirmed: 0 still not confirmed.
- Corrected and confirmed (12): R1-127, R2-017, R2-115, R2-116, R2-117, R3-048, R3-085, R3-088, R3-089, R5-046, R5-048, R5-071.
- Omission leads written into the paraphrases (3, confirmed before and after): R3-013 (Art. 38(1), 15 days), R3-025 (Art. 53(1), 15 days), R4-016 (312.56(d), 5 working days, attached to discontinuing the investigation).
- R2-102 was not corrected and is confirmed: the X1 page-wrong verdict was my error. The cited phrase is on PDF 15 / printed 13; only the opening words of the sentence are at the foot of printed 12. My original lookup had matched the sentence start.

Totals after re-check across the 427 items: 427 confirmed, 0 non-confirmed (X1_results.yaml keeps the first-pass verdicts as record).
