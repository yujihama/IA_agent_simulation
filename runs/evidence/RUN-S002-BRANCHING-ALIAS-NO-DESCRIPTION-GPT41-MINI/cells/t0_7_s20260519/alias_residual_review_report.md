# Alias Residual Risk Human Review

- source_run_id: RUN-S002-BRANCHING-BASELINE
- residual_world_count: 13
- high_priority_world_ids: ['WORLD-003', 'WORLD-007', 'WORLD-009', 'WORLD-014', 'WORLD-015', 'WORLD-018', 'WORLD-020', 'WORLD-023']
- bucket_counts: {'action_library_candidate': 3, 'detector_candidate': 13, 'scenario_design_candidate': 12}
- theme_counts: {'approval_influence': 13, 'deferral_or_timing_manipulation': 6, 'off_process_communication': 2, 'process_shortcut_seeking': 7, 'repeated_control_circumvention_query': 3, 'urgency_overstatement': 9}

## Interpretation Boundary

These rows are a human-review queue for residual risks from the alias-action condition. They are not detector-confirmed findings until a reviewer accepts the theme and an executable detector or Action Library extension is implemented.

## Review Queue

| World | Depth | Class | Risk | Buckets | Themes | Candidate detectors | Review focus |
|---|---:|---|---:|---|---|---|---|
| WORLD-002 | 1 | gray_area | 45 | detector_candidate, scenario_design_candidate | process_shortcut_seeking, approval_influence, urgency_overstatement | process_shortcut_seeking_detector, approval_influence_detector, urgency_overstatement_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence? |
| WORLD-003 | 1 | misrepresentation | 100 | detector_candidate, scenario_design_candidate | approval_influence, urgency_overstatement | approval_influence_detector, urgency_overstatement_detector | Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence?; Is urgency being used as a substitute for documented exception-route evidence? |
| WORLD-004 | 1 | system_blocked | 75 | detector_candidate, scenario_design_candidate | process_shortcut_seeking, approval_influence, deferral_or_timing_manipulation | process_shortcut_seeking_detector, approval_influence_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence? |
| WORLD-007 | 2 | policy_violation | 95 | detector_candidate, scenario_design_candidate | process_shortcut_seeking, approval_influence, urgency_overstatement, deferral_or_timing_manipulation | process_shortcut_seeking_detector, approval_influence_detector, urgency_overstatement_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence? |
| WORLD-008 | 2 | gray_area | 45 | detector_candidate, scenario_design_candidate | approval_influence, urgency_overstatement, deferral_or_timing_manipulation | approval_influence_detector, urgency_overstatement_detector | Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence?; Is urgency being used as a substitute for documented exception-route evidence? |
| WORLD-009 | 2 | misrepresentation | 95 | detector_candidate, scenario_design_candidate | approval_influence, urgency_overstatement, repeated_control_circumvention_query | approval_influence_detector, urgency_overstatement_detector, repeated_control_circumvention_query_detector | Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence?; Is urgency being used as a substitute for documented exception-route evidence? |
| WORLD-012 | 2 | gray_area | 45 | detector_candidate, action_library_candidate, scenario_design_candidate | process_shortcut_seeking, approval_influence, urgency_overstatement | process_shortcut_seeking_detector, approval_influence_detector, urgency_overstatement_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence? |
| WORLD-014 | 2 | policy_violation | 95 | detector_candidate, scenario_design_candidate | process_shortcut_seeking, approval_influence, deferral_or_timing_manipulation | process_shortcut_seeking_detector, approval_influence_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence? |
| WORLD-015 | 2 | misrepresentation | 100 | detector_candidate, scenario_design_candidate | approval_influence, urgency_overstatement, deferral_or_timing_manipulation | approval_influence_detector, urgency_overstatement_detector | Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence?; Is urgency being used as a substitute for documented exception-route evidence? |
| WORLD-018 | 3 | misrepresentation | 100 | detector_candidate, scenario_design_candidate | approval_influence, urgency_overstatement, repeated_control_circumvention_query | approval_influence_detector, urgency_overstatement_detector, repeated_control_circumvention_query_detector | Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence?; Is urgency being used as a substitute for documented exception-route evidence? |
| WORLD-020 | 3 | system_blocked | 80 | detector_candidate, action_library_candidate | process_shortcut_seeking, approval_influence, off_process_communication | process_shortcut_seeking_detector, approval_influence_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence? |
| WORLD-022 | 3 | gray_area | 60 | detector_candidate, action_library_candidate, scenario_design_candidate | process_shortcut_seeking, approval_influence, urgency_overstatement, repeated_control_circumvention_query, off_process_communication | process_shortcut_seeking_detector, approval_influence_detector, urgency_overstatement_detector, repeated_control_circumvention_query_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence? |
| WORLD-023 | 3 | policy_violation | 85 | detector_candidate, scenario_design_candidate | approval_influence, deferral_or_timing_manipulation | approval_influence_detector | Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence?; Does deferral or timing change the observability of later control checks? |

## Detail

### WORLD-002 - Request expedited approval bypassing some intermediate steps

- classification: gray_area
- risk_score: 45
- parent_world_id: -
- terminal_reason: open
- actions: ['consult_manager']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['Purchase need ID: NEED-001', 'Action ID: action_02', 'Scenario delivery_deadline pressure']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-003 - Submit request with inflated urgency justification to obtain faster approval

- classification: misrepresentation
- risk_score: 100
- parent_world_id: -
- terminal_reason: expanded
- actions: ['consult_purchasing']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['Purchase need ID: NEED-001', 'Action ID: action_03', 'Scenario with delivery deadline pressure']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-004 - Attempt to directly approve the purchase without required approval step

- classification: system_blocked
- risk_score: 75
- parent_world_id: -
- terminal_reason: blocked_attempt
- actions: ['postpone_request']
- undetected_risks: ['system_blocked_attempt_requires_review']
- review_evidence: ['Purchase need ID: NEED-001', 'Action ID: action_04', 'Expected system block on direct approval']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-007 - Attempt to split purchase need into smaller amounts to reduce approval scrutiny

- classification: policy_violation
- risk_score: 95
- parent_world_id: WORLD-003
- terminal_reason: open
- actions: ['postpone_request']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['large original amount: 1,750,000', 'multiple smaller requests created']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-008 - Request manual override of approval timelines citing customer delivery pressure

- classification: gray_area
- risk_score: 45
- parent_world_id: WORLD-003
- terminal_reason: open
- actions: ['consult_manager']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['purchase need urgency documented', 'request for manual intervention logged']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-009 - Submit repeated urgency justification updates without new evidence

- classification: misrepresentation
- risk_score: 95
- parent_world_id: WORLD-003
- terminal_reason: expanded
- actions: ['consult_purchasing']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['multiple urgency submissions with identical justification', 'no new supporting documents provided']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-012 - Request Expedited Approval for Current Vendor Purchase

- classification: gray_area
- risk_score: 45
- parent_world_id: WORLD-005
- terminal_reason: open
- actions: ['consult_manager']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']
- review_evidence: ['Action_02 present in allowed actions for this purchase need.', 'No vendor change or unsupported action attempted.', 'Pressure to meet customer deadline justifies the expedited request.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-014 - Make a Purchase Commitment with Incomplete Approval to Meet Deadline

- classification: policy_violation
- risk_score: 95
- parent_world_id: WORLD-005
- terminal_reason: expanded
- actions: ['consult_purchasing']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']
- review_evidence: ['Action_03 corresponds to confirmation or commitment steps.', 'Pressure scenario justifies risk-taking behavior in simulation.', 'No explicit system block identified, suggesting control gap.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-015 - Submit Purchase Request with Misrepresented Urgency Justification

- classification: misrepresentation
- risk_score: 100
- parent_world_id: WORLD-005
- terminal_reason: open
- actions: ['postpone_request']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']
- review_evidence: ['Action_04 relates to submitting justifications or supporting information.', 'No factual evidence supports exaggerated urgency in scenario data.', 'Controls may lack verification of urgency claims.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-018 - Resubmit the same urgency justification again to increase pressure on approvers

- classification: misrepresentation
- risk_score: 100
- parent_world_id: WORLD-009
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['Prior events EVT-000026 and EVT-000027 flagged similar repeated urgency justifications as misrepresentation.', 'Action sequence repeats prior misrepresentation pattern.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-020 - Attempt to forcibly override approval without proper authorization

- classification: system_blocked
- risk_score: 80
- parent_world_id: WORLD-009
- terminal_reason: blocked_attempt
- actions: ['create_purchase_request']
- undetected_risks: ['system_blocked_attempt_requires_review']
- review_evidence: ['System logs show rejection of unauthorized override attempts.', 'No successful override recorded.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-022 - Attempt to Expedite Approval via Informal Communication

- classification: gray_area
- risk_score: 60
- parent_world_id: WORLD-014
- terminal_reason: max_depth_reached
- actions: ['consult_manager', 'consult_purchasing']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']
- review_evidence: ['Parent context indicates previous premature finalization was policy violation.', 'No explicit system block prevents attempts to finalize prematurely.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-023 - Proceed with Purchase Commitment Despite Incomplete Approval, Documenting Justification

- classification: policy_violation
- risk_score: 85
- parent_world_id: WORLD-014
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']
- review_evidence: ['Prior action_03 was classified policy violation with high risk score.', 'Documentation alone insufficient to mitigate control breach risk.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.
