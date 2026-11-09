# Changes after V1 validation round 1 - targeted edits for B1 (GEN-05)

Status: 07 Nov 2026, Y1 re-entry for the V1 items owned by Y1 (`validation/report_r1.md`, GEN-03 and SCP-02 rows). REQ ids, l3_step, status, binding class, draft flag and jurisdiction are unchanged for every REQ.

## 1. New REQ field `modal`

Every REQ now carries `modal` = the strongest modal among the findings of its binding class (must > should > may > definition > example). Counts: must 59, should 183, may 16, definition 11, example 2. B1 can carry it into the element trace (V1 suggestion: a "may" marker on elements whose REQs are permissive).

| Modal | REQs |
|---|---|
| may | REQ-021, REQ-042, REQ-047, REQ-057, REQ-079, REQ-123, REQ-151, REQ-153, REQ-154, REQ-160, REQ-162, REQ-178, REQ-179, REQ-206, REQ-233, REQ-265 |
| definition | REQ-088, REQ-094, REQ-105, REQ-165, REQ-255, REQ-266, REQ-267, REQ-268, REQ-269, REQ-270, REQ-271 |
| example | REQ-011, REQ-096 |
| must / should | all other REQs (see requirements.yaml) |

## 2. REQ fields changed (old -> new)

| REQ | Field | Old | New | Reason |
|---|---|---|---|---|
| REQ-021 | statement | Build appropriate flexibility into the protocol (for example acceptable ranges or windows for specific provisions, fewer and simpler procedures) so that avoidable and intentional deviations are reduced without affecting participant safety or scientific validity. | May build flexibility into the protocol (for example acceptable ranges or windows for specific provisions, fewer and simpler procedures) to reduce avoidable and intentional deviations or amendments, provided participant safety and scientific validity are not adversely affected. | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-027 | deadline | immediately (for the reporting party) | none | V1 GEN-03 L4-01 A12: "immediately" is the duty the contracts impose, not the sponsor task deadline (stays in the statement) |
| REQ-042 | statement | Use centralised monitoring results, including deviation metrics that differ markedly between sites, to select sites and processes for targeted site monitoring. | Centralised monitoring results, including deviation metrics that differ markedly between sites, may be used to select sites and processes for targeted site monitoring (US guidance: such sites should be considered for targeted visits). | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-047 | statement | Communicate to the investigator the protocol deviations and monitoring findings detected by the sponsor that are relevant to the investigator's participants and conduct of the trial. | The sponsor may communicate to the investigator the protocol deviations it detects that are relevant to the investigator's participants and conduct of the trial (US guidance: sponsors should inform the investigator of relevant monitoring findings). | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-057 | statement | Consider an early monitoring visit at a site so that protocol deviations are detected sooner, with source data verification focused on critical data and processes. | An early monitoring visit at a site may be used so that protocol deviations are detected sooner, with source data verification focused on critical data and processes. | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-079 | deadline | immediately | none | V1 GEN-03: 21CFR312.30(b)(2)(ii) permits immediate implementation; "immediately" is not a submission deadline |
| REQ-151 | statement | Provide updated training or retraining, with feedback mechanisms, to address CtQ issues that arise during the study or protocol amendments. | Updated training or retraining may be provided to address CtQ issues that arise during the study or protocol amendments (best practice: retraining and feedback mechanisms are in place). | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-153 | statement | Treat a high number of deviations at a site as a possible signal that more resources, such as staffing or training, are needed. | A high number of deviations at a site may be treated as a signal that more resources, such as staffing or training, are needed. | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-154 | statement | During data finalisation before interim or final analysis, compile the protocol deviations and address their impact, and close out the deviation process (the living deviation assessment plan) at a company-defined point, recommended after the last study data have been reviewed. | Data finalisation before interim or final analysis may include compiling the protocol deviations and addressing their impact; best practice closes out the deviation process (the living deviation assessment plan) at a company-defined point, recommended after the last study data have been reviewed. | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-160 | statement | Characterise each important protocol deviation by when it occurred, its cause and its influence on the trial result, including its impact on the analysis sets defined in the statistical analysis plan. | Each important protocol deviation may be characterised by when it occurred, its cause and its influence on the trial result (ICH E9: desirable); best practice assesses its impact on the analysis sets defined in the statistical analysis plan. | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-162 | statement | Assess the pattern of protocol violations across treatment groups by frequency and time of occurrence. | The pattern of protocol violations across treatment groups may be assessed by frequency and time of occurrence (ICH E9: good practice). | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-178 | statement | Label the withdrawal reason 'protocol deviation' instead of 'protocol violation' in the subject disposition flowchart, or use another descriptor consistent with the stated definition. | Sponsors may replace 'protocol violation' with 'protocol deviation' as the withdrawal reason in the subject disposition flowchart (encouraged by the E3 Q&A), or use another descriptor consistent with the stated definition. | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-179 | statement | Describe GCP issues in a separate CSR section and, where useful, point from the important deviation section to the participants affected by them. | GCP issues may be described in a separate CSR section, with the important deviation section pointing to the participants affected by them. | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |
| REQ-206 | statement | Involve patients, investigators and site staff in protocol design so that procedures are feasible and not unduly burdensome, and engage regulators early for novel critical elements. | Patients, investigators and site staff may contribute to protocol design so that procedures are feasible and not unduly burdensome, and early engagement with regulators is encouraged for novel critical elements. | V1 GEN-03: all findings of the binding class are permissive (may); statement rephrased as a permission, binding class kept |

## 3. l3_cut.md items changed (old -> new)

| Item | Old | New |
|---|---|---|
| L3 G1 / G2 (between A1 and A4/A5) | and-split / and-join | or-split "Intentional protocol deviation considered?" with default flow G1-A2 / or-join (FLW-07, DEC-02; or-split needs a justification, S0-08) |
| A2 outcome (end event) | Potential protocol deviation detected | Potential protocol deviation identified (same label as the A4/A5 trigger) |
| A5 outcome (end event) | No notification required and rationale documented | No notification required (rationale task only on the EU serious breach path, REQ-116) |
| A3 trigger, Sponsor side | message start "Deviation request or immediate-hazard report received" | one message start event receiving the investigator's communication of an intentional deviation (immediate-hazard report or deviation request), followed by an XOR |
| A3 L3 hand-offs | not stated | both investigator message flows shown on L3 into A3: "Immediate-hazard deviation reported", "Intentional deviation request submitted" |
| Reading convention | AND gateways show parallel channels | gateways show parallel channels (G1/G2 OR, G3/G4 AND) |
| Decisions taken | Y1 default: AND gateway G1 | items 11-14 added (V1 round 1, 07 Nov 2026) |

## 4. Other files changed

- `synthesis/conflicts.md` C-10 handling: the binding US either-or duty (REQ-135) sits on the task "Secure compliance" with REQ-134, before the ICH consider-termination decision (REQ-145); no separate US branch.
- `register/iPD_Requirements_Register.md` re-rendered with a Modal column in sections 3 and 4.
