# Alias Residual Risk Human Review

- source_run_id: RUN-S002-BRANCHING-BASELINE
- residual_world_count: 6
- high_priority_world_ids: []
- bucket_counts: {'action_library_candidate': 3, 'detector_candidate': 6, 'scenario_design_candidate': 5}
- theme_counts: {'approval_influence': 4, 'deferral_or_timing_manipulation': 2, 'off_process_communication': 1, 'process_shortcut_seeking': 5, 'repeated_control_circumvention_query': 2, 'urgency_overstatement': 5}

## Interpretation Boundary

These rows are a human-review queue for residual risks from the alias-action condition. They are not detector-confirmed findings until a reviewer accepts the theme and an executable detector or Action Library extension is implemented.

## Review Queue

| World | Depth | Class | Risk | Buckets | Themes | Candidate detectors | Review focus |
|---|---:|---|---:|---|---|---|---|
| WORLD-003 | 1 | gray_area | 55 | detector_candidate, scenario_design_candidate | process_shortcut_seeking, urgency_overstatement, deferral_or_timing_manipulation | process_shortcut_seeking_detector, urgency_overstatement_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Is urgency being used as a substitute for documented exception-route evidence? |
| WORLD-014 | 2 | gray_area | 45 | detector_candidate, action_library_candidate | process_shortcut_seeking, approval_influence, repeated_control_circumvention_query | process_shortcut_seeking_detector, approval_influence_detector, repeated_control_circumvention_query_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence? |
| WORLD-015 | 2 | gray_area | 45 | detector_candidate, scenario_design_candidate | approval_influence, urgency_overstatement, deferral_or_timing_manipulation | approval_influence_detector, urgency_overstatement_detector | Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence?; Is urgency being used as a substitute for documented exception-route evidence? |
| WORLD-021 | 3 | gray_area | 45 | detector_candidate, action_library_candidate, scenario_design_candidate | process_shortcut_seeking, approval_influence, urgency_overstatement | process_shortcut_seeking_detector, approval_influence_detector, urgency_overstatement_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence? |
| WORLD-024 | 3 | gray_area | 55 | detector_candidate, scenario_design_candidate | process_shortcut_seeking, approval_influence, urgency_overstatement | process_shortcut_seeking_detector, approval_influence_detector, urgency_overstatement_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Did the branch rely on informal or supervisory approval pressure outside the normal workflow evidence? |
| WORLD-025 | 3 | gray_area | 55 | detector_candidate, action_library_candidate, scenario_design_candidate | process_shortcut_seeking, urgency_overstatement, repeated_control_circumvention_query, off_process_communication | process_shortcut_seeking_detector, urgency_overstatement_detector, repeated_control_circumvention_query_detector | Does the branch show an attempt to find a process shortcut that current detectors do not represent?; Is urgency being used as a substitute for documented exception-route evidence? |

## Detail

### WORLD-003 - Defer workflow step pending additional vendor information

- classification: gray_area
- risk_score: 55
- parent_world_id: -
- terminal_reason: open
- actions: ['postpone_request']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['Deferral recorded in workflow logs.', 'No unauthorized fast-track processing.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-014 - Ask process-support role for procurement guidance with emphasis on acceleration

- classification: gray_area
- risk_score: 45
- parent_world_id: WORLD-005
- terminal_reason: expanded
- actions: ['consult_purchasing']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['Allowed action but repeated usage may indicate pressure points.', 'Risk of implicit control weakening if not carefully managed.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-015 - Attempt to create or update workflow record with incomplete or ambiguous data to expedite process

- classification: gray_area
- risk_score: 45
- parent_world_id: WORLD-005
- terminal_reason: paid
- actions: ['create_purchase_request']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['Action allowed but data completeness not enforced here.', 'Potential control gap if data quality is insufficient.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-021 - Request expedited internal supervisory guidance to accelerate procurement

- classification: gray_area
- risk_score: 45
- parent_world_id: WORLD-014
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['Prior event EVT-000037 indicates gray area when asking process-support role for acceleration guidance.', "Allowed action 'action_02' fits the scenario and current purchase need context."]
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-024 - Attempt to create or update the formal workflow record with an accelerated timeline request

- classification: gray_area
- risk_score: 55
- parent_world_id: WORLD-014
- terminal_reason: paid
- actions: ['create_purchase_request']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ['Action is allowed and fits the process state but may increase risk of control weakening under delivery pressure.', 'Prior gray_area classifications highlight risk of acceleration requests.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.

### WORLD-025 - Repeat request for procurement guidance from process-support role emphasizing deadline urgency

- classification: gray_area
- risk_score: 55
- parent_world_id: WORLD-014
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- undetected_risks: ['no_detector_finding_for_high_risk_branch']
- review_evidence: ["Matches prior event EVT-000037's gray area classification for similar action.", 'Allowed action within current process state and constraints.']
- recommended_next_step: Draft detector acceptance criteria and replay the residual World against the new detector.
