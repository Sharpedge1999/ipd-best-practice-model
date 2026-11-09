# REQ coverage of the model specs (B1)

Status: 06 Nov 2026; labels, hand-offs and the L4-03 deciding task A14 updated 07 Nov 2026 (V1 rounds 1 and 2). Generated from `spec/*.yaml` and `synthesis/requirements.yaml` (271 REQs). An element reference is `<model> <element id>`; L3 call activities additionally carry every in-scope REQ of their step and are not counted below. Graph and label checks belong to V1.

## Summary

| Class | REQs | On an L4 element | Result |
|---|---|---|---|
| In-scope, binding (binding-law, binding-ICH) | 134 | 134 | 100% |
| In-scope, all classes | 202 | 202 | 100% |
| Interface | 40 | 19 on a placeholder element, 21 in open_items | 100% |
| Out of scope | 29 | not modelled as elements (reasons in `synthesis/req_to_step.yaml`) | - |

Every in-scope REQ sits in the L4 model of its own L3 step (no REQ is placed in another step). Every element that carries a REQ repeats all `[verify]` items of that REQ.

## In-scope REQs by L3 step

### A1 - Define trial-specific iPD criteria (L4-01)

| REQ | Binding | Jurisdiction | Action | Elements (L4) |
|---|---|---|---|---|
| REQ-001 | binding-ICH | ICH | Count protocol adherence aspects among the CtQ factors | S1 CtQ factors identified |
| REQ-002 | binding-ICH | ICH | Identify risks to CtQ factors | A1 Identify risks to CtQ factors |
| REQ-003 | binding-ICH | ICH, US | Evaluate risks to CtQ factors | A2 Evaluate risks to CtQ factors |
| REQ-004 | guidance | ICH, US | Document critical data and processes | A5 Document critical data and processes |
| REQ-005 | binding-ICH | ICH, US | Define risk controls for CtQ risks | A3 Define risk controls for CtQ risks |
| REQ-006 | binding-ICH | ICH | Set acceptable ranges for CtQ risks | A4 Set acceptable ranges for CtQ risks |
| REQ-007 | binding-ICH | ICH, US | Document risk assessment and mitigations | A3 Define risk controls for CtQ risks |
| REQ-008 | binding-ICH | ICH | Communicate risks and mitigations | A3 Define risk controls for CtQ risks |
| REQ-009 | binding-ICH | ICH | Plan strategies against serious noncompliance | A3 Define risk controls for CtQ risks |
| REQ-010 | binding-ICH | ICH | Define trial-specific iPD criteria | A6 Specify criteria for important protocol deviations |
| REQ-011 | binding-ICH | ICH, US | Adapt iPD examples to the trial | A6 Specify criteria for important protocol deviations |
| REQ-012 | guidance DRAFT | US | Specify iPD types in the protocol | A7 Link iPD criteria to CtQ factors |
| REQ-013 | guidance DRAFT | ICH, US | Link iPD criteria to CtQ factors | A7 Link iPD criteria to CtQ factors |
| REQ-014 | best-practice | ICH | Prepare deviation assessment plan | A11 Prepare deviation assessment plan |
| REQ-015 | binding-ICH | ICH | Describe deviation handling in the protocol | A8 Describe deviation handling in the protocol |
| REQ-016 | binding-ICH | ICH | Describe CtQ factors and risks in the protocol | A8 Describe deviation handling in the protocol |
| REQ-017 | binding-ICH | ICH | Summarise monitoring approach in the protocol | A8 Describe deviation handling in the protocol |
| REQ-018 | binding-ICH | ICH | State compliance commitment in the protocol | A8 Describe deviation handling in the protocol |
| REQ-019 | binding-ICH | ICH | Pre-define analysis sets and exclusion criteria | A8 Describe deviation handling in the protocol |
| REQ-020 | binding-ICH | ICH | Specify handling of protocol violations in the protocol | A8 Describe deviation handling in the protocol |
| REQ-021 | binding-ICH | ICH, US | Build flexibility into protocol provisions | A9 Build flexibility into protocol provisions |
| REQ-022 | binding-ICH | ICH | Describe intervention adherence records in the protocol | A8 Describe deviation handling in the protocol |
| REQ-023 | binding-ICH | ICH | Develop risk-based monitoring plan | A10 Develop risk-based monitoring plan |
| REQ-024 | binding-law | EU | Determine extent and nature of monitoring | A10 Develop risk-based monitoring plan |
| REQ-025 | guidance | US | Specify deviation content of the monitoring plan | A10 Develop risk-based monitoring plan |
| REQ-026 | guidance DRAFT | US | Instruct investigators on deviation reporting | A13 Instruct investigators on deviation reporting, M1 Protocol and deviation reporting instructions provided |
| REQ-027 | guidance | EU | Set serious breach reporting duties in contracts | A12 Establish serious breach procedure, M1 Protocol and deviation reporting instructions provided |
| REQ-028 | guidance | EU | Provide serious breach contact and training | A12 Establish serious breach procedure |
| REQ-029 | guidance | EU | Establish serious breach procedure | A12 Establish serious breach procedure |
| REQ-030 | binding-ICH | ICH | Establish incident reporting route to sponsor | A3 Define risk controls for CtQ risks |
| REQ-031 | binding-ICH | ICH | Allocate trial roles and activities | A14 Obtain investigator agreement to comply |
| REQ-032 | binding-ICH | ICH | Obtain investigator agreement to comply | A14 Obtain investigator agreement to comply, A16 Sign agreement to comply, M1 Protocol and deviation reporting instructions provided, M2 Agreement to comply signed |
| REQ-033 | binding-ICH | ICH | Train study personnel | A15 Train study personnel |
| REQ-034 | guidance DRAFT | ICH, US | Train staff on iPD recognition | A15 Train study personnel |

### A2 - Identify protocol deviations (L4-02)

| REQ | Binding | Jurisdiction | Action | Elements (L4) |
|---|---|---|---|---|
| REQ-035 | binding-ICH | ICH | Focus data review on critical data | A1 Review trial data for protocol deviations |
| REQ-036 | binding-ICH | ICH, US | Perform centralised monitoring | A1 Review trial data for protocol deviations |
| REQ-037 | binding-ICH | ICH | Review trial data for protocol deviations | A1 Review trial data for protocol deviations |
| REQ-038 | binding-ICH | ICH | Identify data integrity problems | A1 Review trial data for protocol deviations |
| REQ-039 | binding-ICH | ICH | Review audit trails and metadata | A2 Review audit trails and metadata |
| REQ-040 | best-practice | ICH | Run programmed deviation checks | A1 Review trial data for protocol deviations |
| REQ-041 | guidance DRAFT | ICH, US | Focus monitoring on critical elements | A1 Review trial data for protocol deviations |
| REQ-042 | binding-ICH | ICH, US | Select sites for targeted monitoring | A5 Select sites for targeted monitoring |
| REQ-043 | guidance | US | Decide on site visit for repeated issues | A5 Select sites for targeted monitoring |
| REQ-044 | binding-ICH | ICH | Evaluate acceptable range exceedance | A3 Evaluate acceptable range exceedance |
| REQ-045 | guidance | US | Track deviations that could unblind | A4 Review deviation trends |
| REQ-046 | guidance DRAFT | ICH, US | Review deviation trends | A4 Review deviation trends |
| REQ-047 | binding-ICH | ICH, US | Communicate detected deviations to investigator | A12 Communicate detected deviations to investigator, M1 Detected deviation communicated |
| REQ-048 | binding-law | EU | Monitor trial conduct | S1 Monitoring activity scheduled |
| REQ-049 | binding-law | US | Monitor IND investigations | S1 Monitoring activity scheduled |
| REQ-050 | binding-ICH | ICH | Perform site monitoring visit | A6 Perform site monitoring visit |
| REQ-051 | binding-ICH | ICH | Follow monitoring plan | A6 Perform site monitoring visit |
| REQ-052 | binding-ICH | ICH | Maintain site contact | A6 Perform site monitoring visit |
| REQ-053 | binding-ICH | ICH | Inform investigator of detected deviations | A12 Communicate detected deviations to investigator, M1 Detected deviation communicated |
| REQ-054 | binding-ICH | ICH | Verify protocol adherence at site | A7 Verify protocol adherence at site |
| REQ-055 | binding-ICH | ICH | Verify participant eligibility | A8 Verify participant eligibility |
| REQ-056 | binding-ICH | ICH | Request correction of source record errors | A9 Request correction of source record errors, M2 Source record correction requested |
| REQ-057 | guidance | US | Plan early site monitoring visit | A6 Perform site monitoring visit |
| REQ-058 | best-practice | ICH | Check non-programmable elements on site | A7 Verify protocol adherence at site |
| REQ-059 | binding-ICH | ICH, US | Document monitoring report | A10 Document monitoring report |
| REQ-060 | binding-ICH | ICH, US | Provide monitoring report to sponsor | A11 Review monitoring reports |
| REQ-061 | binding-ICH | ICH | Flag findings for escalation | A10 Document monitoring report |
| REQ-062 | binding-ICH | ICH | Document protocol deviation | A13 Document protocol deviation |
| REQ-063 | binding-ICH | ICH | Maintain source records | A13 Document protocol deviation |
| REQ-064 | binding-law | US | Maintain case histories | A13 Document protocol deviation |
| REQ-065 | binding-ICH | ICH | Review participant data | A13 Document protocol deviation |
| REQ-066 | guidance DRAFT | US | Report deviation to sponsor | A14 Report deviation to sponsor, M3 Protocol deviation reported |
| REQ-067 | binding-ICH | ICH | Explain premature unblinding to sponsor | A14 Report deviation to sponsor, M4 Premature unblinding explained |
| REQ-068 | binding-ICH | ICH | Report computerised system incident | A15 Report computerised system incident, M5 Computerised system incident reported, M6 Computerised system incident reported |
| REQ-069 | guidance | EU | Report suspected serious breach to sponsor | A16 Report suspected serious breach to sponsor, M7 Suspected serious breach reported |

### A3 - Manage intentional protocol deviations (L4-03)

| REQ | Binding | Jurisdiction | Action | Elements (L4) |
|---|---|---|---|---|
| REQ-070 | binding-ICH | ICH | Obtain IRB/IEC approval before deviating | A8 Assess immediate hazard to participants, A13 Obtain IRB/IEC approval before deviating, M6 Approval of intentional protocol deviation requested |
| REQ-071 | binding-law | US | Obtain IRB approval before change | A8 Assess immediate hazard to participants, A13 Obtain IRB/IEC approval before deviating, M6 Approval of intentional protocol deviation requested |
| REQ-072 | binding-law | US | IRB reviews proposed change | M7 IRB/IEC decision issued |
| REQ-073 | binding-law | US | Notify sponsor before protocol change | A12 Request approval of intentional protocol deviation, M3 Intentional protocol deviation request submitted |
| REQ-074 | guidance DRAFT | US | Request approval of intentional deviation | A12 Request approval of intentional protocol deviation, M3 Intentional protocol deviation request submitted |
| REQ-075 | binding-ICH | ICH | Reject eligibility waiver requests | A14 Review intentional protocol deviation communication, A6 Reject eligibility waiver requests, M4 Decision on deviation request |
| REQ-076 | guidance DRAFT | US | Decide on deviation request | A14 Review intentional protocol deviation communication, A7 Decide on deviation request, M5 Decision on deviation request |
| REQ-077 | guidance DRAFT | US | Engage IRB early on urgent changes | A2 Assess need for protocol amendment |
| REQ-078 | binding-ICH | ICH | Deviate to eliminate immediate hazard | A8 Assess immediate hazard to participants, A9 Implement protocol deviation to eliminate immediate hazard |
| REQ-079 | binding-law | US | Implement immediate-hazard change | A5 Submit protocol amendment to FDA |
| REQ-080 | binding-ICH | ICH | Inform sponsor of immediate-hazard deviation | A10 Inform sponsor of immediate-hazard deviation, M1 Immediate-hazard deviation reported |
| REQ-081 | binding-ICH | ICH | Report immediate-hazard deviation to IRB/IEC | A11 Report immediate-hazard deviation to IRB/IEC, M2 Immediate-hazard deviation reported |
| REQ-082 | binding-ICH | ICH | Submit immediate-hazard information to authority | A3 Submit immediate-hazard information to authority, M9 Immediate-hazard information submitted where required |
| REQ-083 | binding-ICH | ICH | Address immediate hazard and its causes | A14 Review intentional protocol deviation communication, A1 Address immediate hazard and its causes |
| REQ-084 | binding-ICH | ICH | Assess need for protocol amendment | A2 Assess need for protocol amendment |
| REQ-085 | binding-law | US | Submit protocol amendment to FDA | A5 Submit protocol amendment to FDA, M8 Protocol amendment submitted for immediate-hazard change |
| REQ-086 | binding-law | US | Notify IRB of immediate-hazard change | A11 Report immediate-hazard deviation to IRB/IEC, M2 Immediate-hazard deviation reported |
| REQ-087 | guidance DRAFT | US | Report implemented change as protocol deviation | A10 Inform sponsor of immediate-hazard deviation |

### A4 - Document and classify protocol deviations (L4-04)

| REQ | Binding | Jurisdiction | Action | Elements (L4) |
|---|---|---|---|---|
| REQ-088 | binding-ICH | ICH, US | Confirm event is a protocol deviation | A1 Confirm event is a protocol deviation |
| REQ-089 | guidance DRAFT | US | Collect all deviation reports | A1 Confirm event is a protocol deviation |
| REQ-090 | binding-law | EU | Record deviation information | A2 Record deviation information |
| REQ-091 | guidance | EU | Document non-serious deviations | A2 Record deviation information |
| REQ-092 | best-practice | ICH | Store deviation in validated repository | A2 Record deviation information |
| REQ-093 | binding-ICH | ICH | Review deviation and explain if important | A4 Request explanation of important protocol deviation, A10 Review protocol deviation and explain if important, M1 Deviation review requested, M2 Important protocol deviation explained |
| REQ-094 | binding-ICH | ICH, US | Classify deviation importance | A3 Classify deviation importance, G2 Important protocol deviation? |
| REQ-095 | best-practice | ICH | Classify deviation on identification | A3 Classify deviation importance |
| REQ-096 | binding-ICH | ICH | Categorise deviation | A5 Categorise deviation |
| REQ-097 | best-practice | ICH | Confirm deviation classification | A6 Confirm deviation classification |
| REQ-098 | best-practice | ICH | Give classification feedback | A6 Confirm deviation classification |
| REQ-099 | best-practice | ICH | Reconcile deviation records | A8 Reconcile deviation records |
| REQ-100 | guidance DRAFT | US | Notify investigator of reclassification | A6 Confirm deviation classification, M3 Reclassification notified |
| REQ-101 | guidance DRAFT | ICH, US | Update iPD criteria | A7 Update iPD criteria |
| REQ-102 | binding-ICH | ICH | File deviation records | A9 File deviation records, A11 File deviation records |
| REQ-103 | binding-law | EU | Maintain sponsor clinical trial master file | A9 File deviation records |
| REQ-104 | binding-law | EU | Maintain investigator clinical trial master file | A11 File deviation records |

### A5 - Assess and notify reportable noncompliance (L4-05)

| REQ | Binding | Jurisdiction | Action | Elements (L4) |
|---|---|---|---|---|
| REQ-105 | binding-law | EU | Assess potential serious breach | A1 Assess potential serious breach, G3 Serious breach? |
| REQ-106 | guidance | EU | Assess breach impact on data reliability | A1 Assess potential serious breach |
| REQ-107 | guidance | EU | Assess persistent noncompliance as serious breach | A1 Assess potential serious breach |
| REQ-108 | guidance | EU | Report potential fraud as serious breach | A1 Assess potential serious breach |
| REQ-109 | guidance | EU | Assess safety-related breach | A1 Assess potential serious breach |
| REQ-110 | guidance | EU | Notify breach causing data removal | A1 Assess potential serious breach |
| REQ-111 | binding-law | EU | Notify serious breach via EU portal | S1 Potential protocol deviation identified, A2 Notify serious breach via EU portal, M1 Serious breach notified |
| REQ-112 | guidance | EU | Notify serious breach at non-EU site | A2 Notify serious breach via EU portal |
| REQ-113 | guidance | EU | Prepare serious breach notification content | A2 Notify serious breach via EU portal |
| REQ-114 | guidance | EU | State most affected Member State | A2 Notify serious breach via EU portal |
| REQ-115 | guidance | EU | Document breach assessment | A1 Assess potential serious breach |
| REQ-116 | guidance | EU | Document non-notification rationale | A4 Document non-notification rationale |
| REQ-117 | guidance | EU | Check need for other EU notifications | A3 Check need for other EU notifications |
| REQ-118 | binding-ICH | ICH | Assess serious noncompliance | A5 Assess serious noncompliance, G6 Serious noncompliance? |
| REQ-119 | binding-ICH | ICH | Notify serious noncompliance | A6 Notify serious noncompliance, M2 Serious noncompliance notified, M3 Serious noncompliance notified, M4 Serious noncompliance notified |
| REQ-120 | binding-ICH | ICH | Inform IRB/IEC of significant changes | A8 Inform IRB/IEC of significant changes, M5 Change significantly affecting conduct reported |
| REQ-121 | binding-law | US | Report changes in research activity to IRB | A9 Report changes in research activity to IRB, M6 Change in research activity reported |
| REQ-122 | guidance DRAFT | US | Submit iPD to IRB | A10 Submit iPD to IRB, M7 Important protocol deviation submitted |
| REQ-123 | guidance DRAFT | US | Defer IRB reporting of non-important deviations | A10 Submit iPD to IRB |
| REQ-124 | binding-law | US | Report serious or continuing noncompliance | M8 Serious or continuing noncompliance reported, M9 Serious or continuing noncompliance reported to institutional officials |
| REQ-125 | best-practice | ICH | Report deviations periodically where required | A7 Report deviations periodically where required |
| REQ-126 | best-practice | ICH | Escalate potentially reportable GCP issues | A11 Escalate potentially reportable GCP issues |

### A6 - Remediate deviations and noncompliance (L4-06)

| REQ | Binding | Jurisdiction | Action | Elements (L4) |
|---|---|---|---|---|
| REQ-127 | binding-ICH | ICH | Escalate issues | A1 Decide action on escalated finding |
| REQ-128 | binding-ICH | ICH | Decide action on escalated finding | A1 Decide action on escalated finding |
| REQ-129 | binding-ICH | ICH | Set proportionate remedial actions | A2 Set proportionate remedial actions |
| REQ-130 | binding-ICH | ICH | Act to prevent recurrence | A2 Set proportionate remedial actions |
| REQ-131 | binding-ICH | ICH | Prioritise iPDs for remediation | A2 Set proportionate remedial actions |
| REQ-132 | guidance DRAFT | US | Remedy iPD promptly | A2 Set proportionate remedial actions |
| REQ-133 | binding-ICH | ICH | Implement site measures against recurrence | A14 Implement site measures against recurrence |
| REQ-134 | binding-ICH | ICH | Secure compliance | A3 Secure compliance, M1 Corrective action required |
| REQ-135 | binding-law | US | Secure compliance or end investigator participation | A3 Secure compliance, A10 Notify FDA of investigator termination, M1 Corrective action required, M6 Participation ended and drug return required |
| REQ-136 | binding-ICH | ICH | Perform root cause analysis | A4 Perform root cause analysis |
| REQ-137 | binding-ICH | ICH | Implement and verify CAPA | A5 Implement and verify CAPA |
| REQ-138 | guidance | US | Analyse root cause of recurrent deviations | A4 Perform root cause analysis |
| REQ-139 | guidance DRAFT | US | Document root cause and actions | A4 Perform root cause analysis |
| REQ-140 | best-practice | ICH | Define CAPA decision rule | A5 Implement and verify CAPA |
| REQ-141 | guidance | EU | Define serious breach CAPA plan | A6 Define serious breach CAPA plan |
| REQ-142 | guidance | EU | Inform affected subjects where needed | A6 Define serious breach CAPA plan |
| REQ-143 | guidance | EU | Check impact on other trials | A6 Define serious breach CAPA plan |
| REQ-144 | guidance | EU | Submit serious breach follow-up report | A7 Submit serious breach follow-up report, M2 Serious breach follow-up report submitted |
| REQ-145 | binding-ICH | ICH, US | Consider terminating site participation | A8 Consider terminating site participation |
| REQ-146 | binding-ICH | ICH | Notify persistent serious noncompliance | A9 Notify persistent serious noncompliance, M3 Persistent serious noncompliance notified, M4 Persistent serious noncompliance notified |
| REQ-147 | binding-ICH | ICH | Minimise impact of persistent noncompliance | A8 Consider terminating site participation |
| REQ-148 | binding-law | US | Notify FDA of investigator termination | A10 Notify FDA of investigator termination, M5 Investigator termination notified |
| REQ-149 | binding-ICH | ICH | Review and adjust risk controls | A11 Review and adjust risk controls |
| REQ-150 | guidance | US | Revise risk assessment and monitoring plan | A11 Review and adjust risk controls |
| REQ-151 | binding-ICH | ICH | Retrain study personnel | A12 Retrain study personnel |
| REQ-152 | guidance | US | Communicate significant issues and actions | A13 Communicate significant issues and actions, M7 Significant issues and actions communicated, M8 Significant issues and actions communicated, M9 Significant issues and actions communicated |
| REQ-153 | guidance DRAFT | US | Assess site resourcing | A8 Consider terminating site participation |

### A7 - Finalise iPDs for clinical study report (L4-07)

| REQ | Binding | Jurisdiction | Action | Elements (L4) |
|---|---|---|---|---|
| REQ-154 | binding-ICH | ICH | Compile and finalise deviations | A1 Compile and finalise deviations |
| REQ-155 | binding-ICH | ICH | Document data finalisation | A1 Compile and finalise deviations |
| REQ-156 | binding-ICH | ICH | Conduct blind review of deviations | A2 Conduct blind review of deviations |
| REQ-157 | binding-ICH | ICH | Document per protocol exclusions | A3 Determine analysis sets |
| REQ-158 | binding-ICH | ICH | Restrict full analysis set exclusions | A3 Determine analysis sets |
| REQ-159 | binding-ICH | ICH | Determine analysis sets | A3 Determine analysis sets |
| REQ-160 | binding-ICH | ICH | Characterise impact of each iPD | A5 Characterise impact of each iPD |
| REQ-161 | binding-ICH | ICH | Assess effect on main analyses | A5 Characterise impact of each iPD |
| REQ-162 | binding-ICH | ICH | Compare deviation patterns across groups | A2 Conduct blind review of deviations |
| REQ-163 | binding-ICH | ICH | Summarise other protocol violations | A2 Conduct blind review of deviations |
| REQ-164 | binding-ICH | ICH | Document exclusion reasons | A3 Determine analysis sets |
| REQ-165 | binding-ICH | ICH | Separate deviations from intercurrent events | A5 Characterise impact of each iPD |
| REQ-166 | binding-ICH | ICH, EU | Describe iPDs in CSR section 10.2 | A6 Describe iPDs in clinical study report section 10.2 |
| REQ-167 | binding-ICH | ICH | Summarise deviations by centre and category | A6 Describe iPDs in clinical study report section 10.2 |
| REQ-168 | binding-ICH | ICH | List patients with deviations in appendix 16.2.2 | A7 List patients with deviations in appendix 16.2.2 |
| REQ-169 | guidance DRAFT | US | Report iPDs in CSR for NDA/BLA | A11 Prepare clinical study report, M1 Clinical study report provided |
| REQ-170 | binding-ICH | ICH | Report conduct differences from protocol | A6 Describe iPDs in clinical study report section 10.2 |
| REQ-171 | binding-ICH | ICH | Report frequency and type of violations | A6 Describe iPDs in clinical study report section 10.2 |
| REQ-172 | binding-ICH | ICH | Describe subjects with severe violations | A8 List and analyse efficacy exclusions |
| REQ-173 | binding-ICH | ICH | List and analyse efficacy exclusions | A8 List and analyse efficacy exclusions |
| REQ-174 | binding-ICH | ICH | Report timing of exclusion decisions | A8 List and analyse efficacy exclusions |
| REQ-175 | binding-ICH | ICH | Discuss effect of efficacy exclusions | A8 List and analyse efficacy exclusions |
| REQ-176 | best-practice | ICH | Report participants excluded due to iPDs | A6 Describe iPDs in clinical study report section 10.2 |
| REQ-177 | binding-ICH | ICH | Explain changes to E3 iPD examples | A6 Describe iPDs in clinical study report section 10.2 |
| REQ-178 | binding-ICH | ICH | Label disposition reason as protocol deviation | A7 List patients with deviations in appendix 16.2.2 |
| REQ-179 | best-practice | ICH | Cross-reference GCP issues in CSR | A6 Describe iPDs in clinical study report section 10.2 |
| REQ-180 | guidance | EU | Report serious breaches in CSR | A10 Report serious breaches in clinical study report |
| REQ-181 | binding-ICH | ICH | Describe quality management approach in CSR | A9 Describe quality management approach in clinical study report |
| REQ-182 | binding-ICH | ICH | Report important quality issues in CSR | A9 Describe quality management approach in clinical study report |
| REQ-183 | binding-ICH | ICH | Describe CtQ factors in CSR | A9 Describe quality management approach in clinical study report |
| REQ-184 | binding-ICH | ICH | Prepare clinical study report | A11 Prepare clinical study report, M1 Clinical study report provided |
| REQ-185 | guidance | ICH, US | Provide deviations in SDTM DV dataset | A12 Provide deviations in SDTM DV dataset, M2 DV dataset submitted |
| REQ-186 | guidance DRAFT | ICH, US | Flag importance in DV dataset | A12 Provide deviations in SDTM DV dataset |
| REQ-187 | guidance | US | Populate DV variables | A12 Provide deviations in SDTM DV dataset |

### A8 - Archive deviation records (L4-08)

| REQ | Binding | Jurisdiction | Action | Elements (L4) |
|---|---|---|---|---|
| REQ-188 | binding-ICH | ICH | Retain deviation and CAPA records | A1 Archive important and non-important protocol deviations, A6 Retain investigator essential records |
| REQ-189 | binding-ICH | ICH | Retain related essential records | A2 Retain related essential records |
| REQ-190 | binding-ICH | ICH | Retain sponsor essential records | A2 Retain related essential records |
| REQ-191 | binding-ICH | ICH | Retain investigator essential records | A6 Retain investigator essential records, M1 Records no longer needed notified |
| REQ-192 | binding-ICH | ICH | Keep records accessible | A3 Keep records accessible |
| REQ-193 | binding-ICH | ICH | Archive trial data and metadata | A2 Retain related essential records |
| REQ-194 | binding-law | EU | Archive sponsor master file for 25 years | A4 Archive content of clinical trial master file |
| REQ-195 | binding-law | EU | Archive investigator master file for 25 years | A7 Archive content of clinical trial master file |
| REQ-196 | binding-law | EU | Keep archive accessible to authorities | A4 Archive content of clinical trial master file |
| REQ-197 | binding-law | EU | Appoint archive responsible persons | A4 Archive content of clinical trial master file |
| REQ-198 | binding-law | EU | Trace changes to archived master file | A4 Archive content of clinical trial master file |
| REQ-199 | binding-law | US | Retain investigator records for 2 years | A8 Retain investigator records for 2 years |
| REQ-200 | best-practice | ICH | Archive important and non-important deviations | A1 Archive important and non-important protocol deviations |
| REQ-201 | best-practice | ICH | File deviation assessment plan | A1 Archive important and non-important protocol deviations |
| REQ-202 | best-practice | ICH | Capture deviation lessons learned | A5 Capture deviation lessons learned |

## Interface REQs

Placeholders are interface call activities (`calls: null`, `interface: true`, S0-18) or the boundary event through which the neighbouring process hands over. Where no hand-off point exists in the flow, the interface is an `open_items` entry tagged `[verify interface]`.

| REQ | Binding | Near step | Interface element or annotation |
|---|---|---|---|
| REQ-203 | binding-ICH | A1 | L3 S1 CtQ factors identified, L4-01 S1 CtQ factors identified |
| REQ-204 | binding-ICH | A1 | L3 S1 CtQ factors identified, L4-01 S1 CtQ factors identified |
| REQ-205 | binding-ICH | A1 | L3 S1 CtQ factors identified, L4-01 S1 CtQ factors identified |
| REQ-206 | binding-ICH | A1 | L3 S1 CtQ factors identified, L4-01 S1 CtQ factors identified |
| REQ-207 | binding-ICH | A1 | L3 S1 CtQ factors identified, L4-01 S1 CtQ factors identified |
| REQ-208 | binding-ICH | A6 | L4-06 open_items #1 |
| REQ-209 | binding-ICH | A2 | L4-02 open_items #1 |
| REQ-210 | binding-ICH | A4 | L4-04 open_items #1 |
| REQ-211 | binding-ICH | A4 | L4-04 open_items #2 |
| REQ-212 | binding-ICH | A5 | L4-05 open_items #1 |
| REQ-213 | binding-ICH | A4 | L4-04 S1 Potential protocol deviation identified |
| REQ-214 | binding-law | A2 | L4-02 open_items #2 |
| REQ-215 | binding-law | A5 | L4-05 A12 Handle other EU notifications |
| REQ-216 | binding-law | A5 | L4-05 A12 Handle other EU notifications |
| REQ-217 | binding-law | A3 | L4-03 A4 Handle urgent safety measures |
| REQ-218 | binding-law | A3 | L4-03 A4 Handle urgent safety measures |
| REQ-219 | binding-law | A3 | L4-03 A4 Handle urgent safety measures |
| REQ-220 | binding-law | A3 | L4-03 A4 Handle urgent safety measures |
| REQ-221 | binding-law | A6 | L4-06 open_items #2 |
| REQ-222 | binding-ICH | A6 | L4-06 open_items #2 |
| REQ-223 | binding-law | A6 | L4-06 open_items #3 |
| REQ-224 | binding-law | A5 | L4-05 open_items #2 |
| REQ-225 | binding-law | A5 | L4-05 open_items #2 |
| REQ-226 | binding-law | A6 | L4-06 open_items #3 |
| REQ-227 | binding-law | A5 | L4-05 open_items #2 |
| REQ-228 | binding-law | A5 | L4-05 open_items #2 |
| REQ-229 | guidance | A5 | L4-05 open_items #2 |
| REQ-230 | binding-law | A5 | L4-05 open_items #3 |
| REQ-231 | guidance | A5 | L4-05 M1 Serious breach notified |
| REQ-232 | guidance | A5 | L4-05 open_items #4 |
| REQ-233 | binding-law | A5 | L4-05 open_items #4 |
| REQ-234 | binding-law | A5 | L4-05 open_items #4 |
| REQ-235 | binding-law | A7 | L4-07 A13 Handle clinical study report and study data submission |
| REQ-236 | binding-law | A7 | L4-07 A13 Handle clinical study report and study data submission |
| REQ-237 | binding-ICH | A7 | L4-07 A4 Handle statistical analysis and estimands |
| REQ-238 | binding-ICH | A7 | L4-07 A13 Handle clinical study report and study data submission |
| REQ-239 | binding-ICH | A7 | L4-07 A4 Handle statistical analysis and estimands |
| REQ-240 | binding-ICH | A7 | L4-07 A4 Handle statistical analysis and estimands |
| REQ-241 | binding-ICH | A7 | L4-07 open_items #1 |
| REQ-242 | binding-ICH | A7 | L4-07 open_items #1 |

## Out-of-scope REQs

Not on any element. The overarching conduct norms REQ-243 to REQ-251 are cited as `src` on the Sponsor and Investigator/institution pools of every model, as their Y1 reasons state; pools carry no `req` field in the schema.

REQ-243, REQ-244, REQ-245, REQ-246, REQ-247, REQ-248, REQ-249, REQ-250, REQ-251, REQ-252, REQ-253, REQ-254, REQ-255, REQ-256, REQ-257, REQ-258, REQ-259, REQ-260, REQ-261, REQ-262, REQ-263, REQ-264, REQ-265, REQ-266, REQ-267, REQ-268, REQ-269, REQ-270, REQ-271

## SCP-06 hand-offs (L3 message flows realised in the L4 models)

| L3 flow | Label | L4 model | L4 flow |
|---|---|---|---|
| L3 M1 | Protocol and deviation reporting instructions provided | L4-01 | M1 |
| L3 M2 | Detected deviation communicated | L4-02 | M1 |
| L3 M3 | Protocol amendment submitted for immediate-hazard change | L4-03 | M8 |
| L3 M4 | Serious breach notified | L4-05 | M1 |
| L3 M5 | Serious noncompliance notified | L4-05 | M2 |
| L3 M6 | Serious noncompliance notified | L4-05 | M3 |
| L3 M7 | Corrective action required | L4-06 | M1 |
| L3 M8 | Investigator termination notified | L4-06 | M5 |
| L3 M9 | Clinical study report provided | L4-07 | M1 |
| L3 M10 | Records no longer needed notified | L4-08 | M1 |
| L3 M11 | Immediate-hazard deviation reported | L4-03 | M1 |
| L3 M12 | Intentional protocol deviation request submitted | L4-03 | M3 |

## SCP-06 triggers and outcomes

| L3 step | L4 start (interface) | L4 ends (interface) |
|---|---|---|
| A1 | S1 CtQ factors identified | E1 iPD criteria and plans approved |
| A2 | S1 Monitoring activity scheduled | E1 Potential protocol deviation identified; E2 Monitoring completed without finding |
| A3 | S1 Intentional protocol deviation communicated | E1 Immediate hazard addressed; E2 Deviation request approved; E3 Deviation request rejected |
| A4 | S1 Potential protocol deviation identified | E1 Protocol deviation classified; E2 Issue handled outside the deviation process |
| A5 | S1 Potential protocol deviation identified | E1 Reportable noncompliance notified; E2 No notification required |
| A6 | S1 Deviation classified and reportability decided | E1 Corrective and preventive actions completed; E2 Investigator participation terminated |
| A7 | S1 Data finalisation initiated | E1 iPDs reported in clinical study report |
| A8 | S1 iPDs reported in clinical study report | E1 Deviation records archived |

## l3_cut outcomes and the L4 end events that realise them

Sponsor end events state what the sponsor reaches (orchestrator decision 06 Nov 2026); where the l3_cut outcome is reached by the investigator, the Investigator/institution end event carries the l3_cut label.

| L3 step | l3_cut outcome | Realised by |
|---|---|---|
| A1 | iPD criteria and plans approved | L4-01 E1 (Sponsor, same label) |
| A2 | Potential protocol deviation identified | L4-02 E1 (Sponsor, same label; also the L4-04 and L4-05 start S1) |
| A2 | Monitoring completed without finding | L4-02 E2 (Sponsor, same label) |
| A2 | Deviation reported to sponsor | L4-02 E3 (Investigator/institution, same label) |
| A3 | Immediate-hazard deviation implemented and reported | L4-03 E4 (Investigator/institution, same label); Sponsor end E1 'Immediate hazard addressed' |
| A3 | Intentional deviation approved and implemented | L4-03 E5 'Intentional protocol deviation approved and implemented' (Investigator/institution, glossary form of the l3_cut label, LBL-04; after IRB/IEC approval); Sponsor end E2 'Deviation request approved' |
| A3 | Deviation request rejected | L4-03 E3 (Sponsor) and E6 (Investigator/institution), same label |
| A4 | Protocol deviation classified | L4-04 E1 (same label) |
| A4 | Issue handled outside the deviation process | L4-04 E2 (same label) |
| A5 | Reportable noncompliance notified | L4-05 E1 (same label) |
| A5 | No notification required | L4-05 E2 (same label) |
| A6 | Corrective and preventive actions completed | L4-06 E1 (same label) |
| A6 | Investigator participation terminated | L4-06 E2 (same label) |
| A7 | iPDs reported in clinical study report | L4-07 E1 (same label; also the L4-08 start S1) |
| A8 | Deviation records archived | L4-08 E1 (same label) |
