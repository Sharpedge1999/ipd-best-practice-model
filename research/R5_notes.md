# R5 notes - industry best practice and data standards

Status: 06 Nov 2026. Findings file: `research/R5_industry.yaml` (R5-001 to R5-071).

Conventions used:
- `jurisdiction: ICH` = international scope for industry and data-standard sources (decisions.md S0-05); FDA documents use `US`.
- Unnumbered headings are written as `S<Heading-with-hyphens>` (e.g. `SConfirm`, `SClose-Out`), because the linter's `S<sec>` form allows no spaces.
- The task asked for CDISC locs in the form `variable:DVDECOD`. The linter (S0-02) does not accept that form, so CDISC CT findings use `S<NCI codelist code>` (e.g. `SC225352`) and name the variable in paraphrase/action. The orchestrator may want to add a `variable:` form to the grammar.

## 1. Coverage checklist per target

| Target | Status | Findings |
|---|---|---|
| Define trial-specific important deviation criteria up front | Covered | R5-009 to R5-016, R5-027, R5-055 to R5-059, R5-063, R5-064 |
| Link to CtQ factors and risks | Covered | R5-009, R5-015, R5-022, R5-048 to R5-050, R5-055, R5-058, R5-059 |
| Identification: monitoring (on-site) | Covered | R5-021 |
| Identification: data review, programmed checks, central monitoring | Covered | R5-020, R5-022, R5-034, R5-050, R5-060 |
| Identification: site self-reporting | Gap - no source read addresses sites reporting deviations to the sponsor (2nd PMC fetch: not mentioned in the paper) | - |
| Documentation / storage / reconciliation | Covered | R5-030, R5-032, R5-033 |
| Classification and confirmation | Covered | R5-001 to R5-005, R5-007, R5-024 to R5-026, R5-028 |
| Trending and aggregate review | Covered | R5-031, R5-034, R5-050 |
| Root cause and CAPA | Partial - only for QTL deviations (R5-052) and as a planning question (R5-062); the PD paper does not mention root cause; identifier feedback/retraining R5-029 | R5-029, R5-052, R5-062 |
| Escalation | Partial - company escalation paths and defined escalation process; no concrete escalation criteria | R5-008, R5-014, R5-061 |
| Reporting to IRB/EC and authorities | Partial - generic ("as required"); reporter role not stated | R5-008, R5-037 |
| CSR reporting | Covered | R5-036, R5-038 to R5-041, R5-053 |
| Close-out, archiving, finalisation, lessons learned | Covered | R5-042 to R5-046 |
| Analysis-set impact | Covered | R5-035, R5-047 |
| Training | Covered | R5-017 to R5-019 |
| Roles named | Study team, the identifier, independent study team member (or group), CRAs, companies, sponsor(s), site personnel (training recipient), CROs and vendors (training recipients); CTTI: study team, sponsor, investigators, site staff, patients | - |
| Recommended timelines | Only relative timing: before protocol finalisation (R5-009), PDAP alongside protocol development and until last study data reviewed (R5-010), classify upon identification (R5-024), periodic aggregate review (R5-031). No day/hour limits for deviation steps (the "24 h" in Table 1 is an SAE example) | - |
| CDISC DV purpose, variables, assumptions | Partial - DV definition via NCIt mirror (R5-068); variables expected by FDA (R5-070); CT codelists DVCAT and DVDECOD (R5-065, R5-066); draft DVCLASI (R5-067). SDTMIG v3.4 DV specification table and assumptions NOT read (login) | R5-065 to R5-070 |
| CDISC CT for deviations | Partial - codelists exist (C225352 DVCAT, C225353 DVDECOD, both extensible); terms not read | R5-065, R5-066 |
| SDTM required for submissions (FDA) | Covered as separate finding | R5-071 (binding-law, [verify binding]); R5-069, R5-070 (guidance) |
| Peer-reviewed consortium paper | Covered - found and read in full text (PMC + Springer, CC BY 4.0) | R5-001 to R5-044 |

## 2. Fetch log

All fetches on 2026-11-06 with WebFetch unless stated. "Full" = whole page within one window.

| # | URL | Offset | Coverage / result |
|---|---|---|---|
| F01 | https://www.transceleratebiopharmainc.com/assets/protocol-deviations/ | 0 | Full; asset list, process summary |
| F02 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8238759 | 0 | Citation, headings, abstract and introduction (summary) |
| F03 | same | 0 | Methods, Define, GCP Compliance, Protocol |
| F04 | https://www.transceleratebiopharmainc.com/wp-content/uploads/2021/03/Protocol-Deviations_Process-Guide_March-2021.pdf | - | robots_disallowed, nothing retrieved |
| F05 | https://www.transceleratebiopharmainc.com/wp-content/uploads/2020/09/TransCelerate_Protocol-Deviations_Process-Guide_August-2020.pdf | - | robots_disallowed |
| F06 | PMC8238759 | 0 | Prepare, Train, Identify and Collect, Classify and Categorize, Confirm, Fig. 1-2 captions |
| F07 | PMC8238759 | 0 | Store, Review and Analyze, Report, Close Out, Conclusion |
| F08 | PMC8238759 | 0 | Appendix Table 1, Fig. 3-5 captions |
| F09 | https://www.transceleratebiopharmainc.com/initiatives/protocol-deviations/ | 0 | Full; initiative status and links |
| F10 | .../2020/03/Protocol-Deviations_Decision-Tree_TransCelerate_March-2021-1-scaled.jpg | - | robots_disallowed |
| F11 | .../2022/08/PD-Process-Map_081222-scaled.jpg | - | robots_disallowed |
| F12 | .../2023/01/Protocol-Deviations-Poster-Jan-23.pdf | - | robots_disallowed |
| F13 | https://link.springer.com/article/10.1007/s43441-021-00269-w | 0 | OA status, licence, three verbatim sentences |
| F14 | PMC8238759 | 0 | Heading hierarchy and sentence placement (2nd confirmation) |
| F15 | Springer s43441-021-00269-w | 0 | Heading list (page has no heading markup) |
| F16 | https://link.springer.com/article/10.1007/s43441-020-00209-0 | 0 | QTL paper headings and PD/CtQ passages |
| F17 | https://ctti-clinicaltrials.org/?p=16481 | 0 | Full; QbD recommendations page |
| F18 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7864825 | - | reCAPTCHA page, nothing retrieved |
| F19 | https://ctti-clinicaltrials.org/wp-content/uploads/2021/07/CTTI_QbD_Workshop_Principles_Document-1.pdf | 0 | TOC and topic summary |
| F20 | https://ctti-clinicaltrials.org/wp-content/uploads/2021/06/CTTI_QbD_Recs.pdf | 0 | Full (2 pages) |
| F21 | https://link.springer.com/doi/10.1007/s43441-020-00209-0 | 0 | Citation block; deviation sentences in Define/Monitor/Report stages |
| F22 | CTTI Principles PDF | 0 | p. 9, p. 19, p. 3, p. 13 questions |
| F23 | https://www.cdisc.org/standards/foundational/sdtmig | 0 | Version list |
| F24 | https://worldoftaxonomy.com/system/nci_thesaurus/node/C225352 | 0 | Concept stub (secondary; used only as pointer) |
| F25 | https://evs.nci.nih.gov/ftp1/CDISC/SDTM/ | 0 | No listing rendered |
| F26 | https://www.cdisc.org/standards/foundational/sdtmig/sdtmig-v3-4 | 0 | Files need sign-in |
| F27 | https://evs.nci.nih.gov/ftp1/CDISC/SDTM/?C=M&O=A | 0 | No listing rendered |
| F28 | https://mail.sbiaevents.com/files/Tech-Conf-Webinar-Nov-2018.pdf | 0 | FDA TCG v4.2 webinar slides on DV (supporting only) |
| F29 | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/study-data-technical-conformance-guide-technical-specifications-document | 0 | Full; Oct 2026, final, nonbinding |
| F30 | https://www.hhs.gov/guidance/sites/default/files/hhs-guidance-documents/FDA/sdTCG-v6.0-March-2025-FINAL.pdf | 0 | chars 0-100000 of 114903; DV section p. 15 of 88 |
| F31 | https://www.fda.gov/media/153632/download | 0 | chars 0-100000 of 115163; DV section (v6.3) |
| F32 | same | 0 | S1, S1.1, S1.2 legal status |
| F33 | same | 0 | DV variable sentence, page, adjacent headings (confirmation) |
| F34 | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/providing-regulatory-submissions-electronic-format-standardized-study-data | 0 | Full; status, download link |
| F35 | https://fda.gov/media/91152/download | 0 | 2015 FDA webinar deck (not used for findings) |
| F36 | https://www.fda.gov/media/82716/download | 0 | S I binding statement; S II.A, II.B, II.E.1 timetable |
| F37 | same | 0 | Binding phrase confirmation; SDTM/CDISC mentions; RTF/RTR |
| F38 | https://evs.nci.nih.gov/ftp1/CDISC/SDTM/Archive/SDTM%20CDISC%20ReadMe%202026-03-27.doc | - | Binary, unreadable |
| F39 | https://evs.nci.nih.gov/ftp1/CDISC/SDTM/SDTM%20Terminology.pdf | 0 | Release 2026-09-25; codelists C225352, C225353; extraction ends p. 14 of 1741 |
| F40 | https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/C225352/subsetMembers?include=minimal | - | client_error |
| F41 | SDTM Terminology.pdf | 100000 | Nothing left (text length 97233) |
| F42 | https://evs.nci.nih.gov/ftp1/CDISC/SDTM/SDTM%20Terminology.txt | 0 | First codelists only ("10-Meter..." to "Acute Physiology..."); no DV rows |
| F43 | SDTM Terminology.txt | 60000000 | Nothing left (text length 99118) |
| F44 | https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=C225352 | - | robots_disallowed |
| F45 | https://wiki.cdisc.org/pages/viewpage.action?pageId=55972896 | - | client_error |
| F46 | https://www.cdisc.org/sites/default/files/2025-05/ (file "4B 2025 Europe Interchange - [presenter name omitted] - CDISC Protocol Deviation Sub-Team SDTMIG 4.0 Updates and Open Topics - V1.2.pdf"; full URL withheld because it contains a personal name) | 0 | Slide summary (leads only) |
| F47 | https://www.cdisc.org/sites/default/files/pdf/SDTMIGv4.0_Webinar_Feb2026.pdf | 0 | Status, slides 35-36 |
| F48 | https://www.cdisc.org/sites/default/files/interchange/presentations/public/5B.2%20What's%20New%20in%20SDTMIG%204.0.pdf | 0 | Slides 18-19, 25 (leads only) |
| F49 | SDTMIGv4.0_Webinar_Feb2026.pdf | 0 | Slide 35 verbatim (confirmation) |
| F50 | https://www.cismef.org/page/detail/en/NCI_CO_C49585 | 0 | Full; NCIt C49585 with CDISC definition |
| F51 | PMC8238759 | 0 | Nine verbatim fragments (confirmation) |
| F52 | Springer s43441-021-00269-w | 0 | PDAP modal "should" (confirmation) |
| F53 | TransCelerate assets page | 0 | Close-out fragments, heading order |
| F54 | same | 0 | Carousel tab names (PREPARE, IDENTIFY & COLLECT, CONFIRM, REVIEW & ANALYZE, CLOSEOUT); tab text not in capture |
| F55 | Springer s43441-020-00209-0 | 0 | Six verbatim fragments (confirmation) |
| F56 | https://link.springer.com/10.1177/2168479014546336 | 0 | RBM technology paper 2014; abstract only, no PD content (not used) |
| F57 | CTTI Principles PDF | 0 | p. 9 quote, p. 19 questions, intro (confirmation) |
| F58 | SDTM Terminology.pdf | 0 | Codelists on p. 9 (confirmation) |
| F59 | TransCelerate assets page | 0 | Finalisation, impact, reconciliation, feedback fragments (confirmation) |
| F60 | PMC8238759 | 0 | Term search: root cause, CAPA, trend, site reporting, timelines, serious breach, escalation, data review, SDTM, CtQ |

WebSearch (standard; one extended for CDISC CT) was used to locate the sources; only the URLs above were opened.

## New source keys (item 3)

- `TCB-PD-TIRS` - Protocol Deviations: A Holistic Approach from Defining to Reporting, Ther Innov Regul Sci 55(4):733-742 (2021), TransCelerate working group, CC BY 4.0 - https://pmc.ncbi.nlm.nih.gov/articles/PMC8238759 (also https://link.springer.com/article/10.1007/s43441-021-00269-w, DOI 10.1007/s43441-021-00269-w)
- `CTTI-CTQ` - CTTI Quality by Design Project: Critical to Quality (CTQ) Factors Principles Document, version 19 May 2015 - https://ctti-clinicaltrials.org/wp-content/uploads/2021/07/CTTI_QbD_Workshop_Principles_Document-1.pdf
- `CDISC-CT` - CDISC SDTM Controlled Terminology, release 2026-09-25 (NCI EVS) - https://evs.nci.nih.gov/ftp1/CDISC/SDTM/SDTM%20Terminology.pdf
- `CDISC-SDTMIG40-PR` - CDISC webinar SDTMIG v4.0 and SDTM v3.0 Public Review, February 2026 (draft standard) - https://www.cdisc.org/sites/default/files/pdf/SDTMIGv4.0_Webinar_Feb2026.pdf
- `NCIT-DV` - NCI Thesaurus concept C49585 Protocol Deviations Domain (CDISC definition), via CISMeF mirror - https://www.cismef.org/page/detail/en/NCI_CO_C49585
- `FDA-SDTCG` - FDA Study Data Technical Conformance Guide, v6.3, October 2026 (nonbinding) - https://www.fda.gov/media/153632/download
- `FDA-ESTUDY` - FDA Guidance for Industry: Providing Regulatory Submissions in Electronic Format - Standardized Study Data, Revision 2, June 2021 (binding effect under FD&C Act 745A(a)) - https://www.fda.gov/media/82716/download

## 3b. Registry keys used with confirmed documents (for Y1 to update titles/URLs)

- `TCB-PD` = TransCelerate Protocol Deviations Solutions page, https://www.transceleratebiopharmainc.com/assets/protocol-deviations/ (the Process Guide itself was not readable).
- `TCB-RBQM` = Quality Tolerance Limits: Framework for Successful Implementation in Clinical Development, Ther Innov Regul Sci 55(2):251-261 (2021), https://link.springer.com/article/10.1007/s43441-020-00209-0
- `CTTI-QbD` = CTTI Recommendations: Quality by Design (June 2015), https://ctti-clinicaltrials.org/wp-content/uploads/2021/06/CTTI_QbD_Recs.pdf
- `CDISC-DV` not used: the SDTMIG DV domain text was not accessible (login). Y1 may map CDISC findings to it once the SDTMIG is read.

## 4. Leads for other stems

- R1 (E6R3): the QTL paper (R5-053) cites an E6(R2) duty to report important QTL deviations and remedial actions in the CSR; check the E6(R3) equivalent. The PD paper's important deviation definition (R5-002) restates E3 Q&A and E6 risk thinking; check E6(R3) glossary wording.
- R2 (E3, E3QA, E9): E3 Q&A (R1) is the origin of the important deviation definition and of sponsor latitude; the paper says the PDAP uses four ICH E3 categories plus three more, but not which four (R5-026) - E3 10.2 should settle it. CDISC sub-team deck (F46, slide 18-20) says E9 uses "protocol violation" more often.
- R3 (EU): CDISC sub-team deck (F46) reports EMA-proposed deviation categories (IMP, temperature monitoring, potential fraud; slides 31-33) and an EMA note that an important deviation is not a serious breach (slide 21). Not verified - deck is a lead, not a source.
- R4 (US): (a) FDA-PD24 reportedly asks for a DV variable flagging importance and recommends submitting all deviations in DV (F46 slides 9, 36) - verify in the draft guidance. (b) FDA BIMO Technical Conformance Guide reportedly lists important and non-important deviations by subject and site (F46 slide 17) - https://www.fda.gov/regulatory-information/search-fda-guidance-documents/bioresearch-monitoring-technical-conformance-guide (not read). (c) R5-069 to R5-071 are FDA documents recorded here at the orchestrator's instruction; R4 owns FDA sources, so Y1 should deduplicate. (d) FDA Data Standards Catalog not read. (e) sdTCG S1.2 notes that SDTMIG "required" status is not necessarily an Agency requirement.
- Y1: the TransCelerate initiative is closed (no updates since Jan 2023), and its toolkit builds on E6(R2). Treat it as best practice that predates E6(R3) and FDA-PD24.
- CDISC "What's New in SDTMIG 4.0" (F48, slide 18) names a "TransCelerate Protocol Deviation Data Collection Optimization Initiative"; it was not found on the TransCelerate site (not searched further).
- Not read: PharmaSUG 2026 DS-265 and PHUSE US 2026 DS13 conference papers on DV / SDTMIG v4.0 (company-authored, outside scope); TransCelerate implementation-experience page; the toolkit video.

## 5. Open questions and conflicts

1. PDAP modal: the first PMC summary said "must"; verbatim PMC and Springer fetches show "should". Resolved to "should" (R5-012).
2. Heading placement: the Springer page has no heading markup and attributed two sentences to other headings; PMC markup (2 fetches) used (R5-009, R5-028).
3. sdTCG v6.3 page for the DV paragraph: 16 vs 17 of 97 across two fetches (R5-069, R5-070) [verify].
4. SDTMIG v4.0 timeline: "What's New" deck targets public review Q4 2025; sub-team deck gives review 13 Aug to 14 Oct (year not stated); Feb 2026 webinar says review closes 6 Apr 2026, publication targeted Q4 2026. Final status as of Nov 2026 unknown.
5. Terminology clash: in the QTL paper "important deviation" means a QTL threshold exceedance, not a protocol deviation (R5-051 to R5-053). Keep them apart in the model.
6. Reporter role: the PD paper does not say who reports deviations to IRB/EC or authorities (R5-037); the regulatory stems decide.
7. "Lessons learned" is only on the TransCelerate web page, not in the paper (R5-045).
8. Finalisation timing "ideally after the last study data has been reviewed" seen in one fetch only (R5-046).
9. TransCelerate initiative page: the meta description says the toolkit is being "developed", the body says the initiative is complete (Jan 2023).
10. Category scheme: TransCelerate's seven categories vs CDISC DVCAT codelist terms (not read) vs FDA/EMA proposals (lead): alignment unknown.
11. Binding class of FDA-ESTUDY: the guidance states binding effect under statute, and the schema has no "binding guidance" class, so it is mapped to binding-law with [verify binding] (R5-071).
12. Loc grammar has no `variable:` form; see conventions above.
13. Theme: none of the sources gives day or hour limits for deviation steps.

## 6. Versions and dates read; access gaps

Read:
- Protocol Deviations: A Holistic Approach from Defining to Reporting - TIRS 55(4):733-742, 2021 (PMC HTML and Springer HTML, CC BY 4.0).
- TransCelerate Protocol Deviations Solutions page (last modified 17 Jan 2023) and initiative page (modified 1 Oct 2025; initiative complete Jan 2023).
- Quality Tolerance Limits: Framework for Successful Implementation in Clinical Development - TIRS 55(2):251-261, 2021 (Springer HTML, CC BY 4.0; online 3 Sep 2020).
- CTTI Recommendations: Quality by Design (June 2015) and web page (published 24 Mar 2025).
- CTTI CTQ Factors Principles Document, version 19 May 2015 (24 pages).
- CDISC SDTM Controlled Terminology 2026-09-25 (first 14 of 1741 pages only).
- CDISC SDTMIG v4.0 / SDTM v3.0 public review webinar, Feb 2026 (slides 35-36).
- NCIt C49585 via CISMeF mirror (3 Nov 2026).
- FDA Study Data Technical Conformance Guide v6.3, Oct 2026 (chars 0-100000 of 115163; DV section and S1 read); v6.0 Mar 2025 copy for comparison.
- FDA eStudy Data guidance, Revision 2, June 2021.
- Leads only: CDISC PD sub-team deck (2025 Europe Interchange, V1.2); CDISC "What's New in SDTMIG 4.0" (undated).

Access gaps (logged, not reconstructed):
- TransCelerate toolkit files under wp-content are robots-disallowed: PD Process Guide (Aug 2020 and Mar 2021 PDFs), PD Process Map (JPG, Aug 2022), PD Decision Tree (JPG, Mar 2021), PD Assessment Plan template (XLSX, Mar 2020), overview poster (PDF, Jan 2023). Decision Tree branch logic, process map lanes and PDAP template fields are therefore unknown.
- CDISC SDTMIG v3.4 files and CDISC Library need sign-in; the CDISC wiki DV page returned a client error. The DV specification table (core status, roles, CDISC notes) and DV assumptions were not read.
- NCI EVS SDTM CT: PDF and TXT extraction stop at about 100k characters; EVS REST API returned client error; NCIt browser is robots-disallowed; the ReadMe is binary. DVCAT and DVDECOD terms were not read.
- PMC copy of the QTL paper (PMC7864825) returned a captcha; the Springer copy was used.
- FDA Data Standards Catalog not opened.
- TransCelerate RBM methodology papers (2013-2014) and RACT: not covered beyond one abstract with no deviation content.
- UK and device-specific standards: out of scope per decisions.
