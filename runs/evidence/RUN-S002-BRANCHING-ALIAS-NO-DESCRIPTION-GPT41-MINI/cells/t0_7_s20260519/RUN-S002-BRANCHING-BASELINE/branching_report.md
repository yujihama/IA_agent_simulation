# 分岐探索レポート: RUN-S002-BRANCHING-BASELINE

## 実行条件

- behavior_mode: branching_proposal
- proposal_count_per_node: 5
- max_depth: 3
- beam_width: 2
- max_total_worlds: 25

## 全体サマリ

| 指標 | 件数 |
|---|---:|
| generated_world_count | 25 |
| completed_world_count | 23 |
| blocked_world_count | 2 |
| unsupported_world_count | 0 |
| duplicate_world_count | 0 |
| expanded_world_count | 4 |
| leaf_world_count | 21 |
| generated_depth_counts | {'1': 5, '2': 10, '3': 10} |
| high_risk_world_count | 18 |
| detected_high_risk_world_count | 10 |
| undetected_high_risk_world_count | 8 |
| detector_detection_rate_numerator | 10 |
| detector_detection_rate_denominator | 18 |
| lineage_detection_rate | 0.5556 |
| new_risk_detection_rate | 0.2778 |
| current_world_detection_rate | 0.2 |
| inherited_risk_count | 10 |
| inherited_risk_world_count | 10 |
| inherited_only_high_risk_world_count | 5 |
| undetected_new_risk_world_count | 13 |
| residual_risk_world_count | 13 |
| control_gap_count | 13 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 7 |
| gray_area | 9 |
| misrepresentation | 6 |
| policy_violation | 3 |
| system_blocked | 2 |

## 代表World

### WORLD-001: Submit purchase request for standard approval

- status: completed
- classification: compliant
- risk_score: 10
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-002: Request expedited approval bypassing some intermediate steps

- status: completed
- classification: gray_area
- risk_score: 45
- depth: 1
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-003: Submit request with inflated urgency justification to obtain faster approval

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 1
- terminal_reason: expanded
- actions: ['consult_purchasing']
- children: ['WORLD-006', 'WORLD-007', 'WORLD-008', 'WORLD-009', 'WORLD-010']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-004: Attempt to directly approve the purchase without required approval step

- status: blocked
- classification: system_blocked
- risk_score: 75
- depth: 1
- terminal_reason: blocked_attempt
- actions: ['postpone_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['system_blocked_attempt_requires_review']

### WORLD-005: Request alternative vendor quotation to speed procurement

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-011', 'WORLD-012', 'WORLD-013', 'WORLD-014', 'WORLD-015']
- detected_findings: ['FND-000001']
- current_detected_findings: ['FND-000001']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-006: Request expedited approval citing verified customer delivery deadline

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-007: Attempt to split purchase need into smaller amounts to reduce approval scrutiny

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 2
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-008: Request manual override of approval timelines citing customer delivery pressure

- status: completed
- classification: gray_area
- risk_score: 45
- depth: 2
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-009: Submit repeated urgency justification updates without new evidence

- status: completed
- classification: misrepresentation
- risk_score: 95
- depth: 2
- terminal_reason: expanded
- actions: ['consult_purchasing']
- children: ['WORLD-016', 'WORLD-017', 'WORLD-018', 'WORLD-019', 'WORLD-020']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-010: Attempt to submit an unsupported action to expedite approval

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: open
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000002']
- current_detected_findings: ['FND-000002']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-011: Proceed with Standard Purchase Order Approval

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000003']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000003']
- undetected_risks: []

### WORLD-012: Request Expedited Approval for Current Vendor Purchase

- status: completed
- classification: gray_area
- risk_score: 45
- depth: 2
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000004']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000004']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-013: Attempt to Solicit Alternative Vendor Quote Despite Process Restrictions

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: open
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000005', 'FND-000006']
- current_detected_findings: ['FND-000006']
- inherited_detected_findings: ['FND-000005']
- undetected_risks: []

### WORLD-014: Make a Purchase Commitment with Incomplete Approval to Meet Deadline

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 2
- terminal_reason: expanded
- actions: ['consult_purchasing']
- children: ['WORLD-021', 'WORLD-022', 'WORLD-023', 'WORLD-024', 'WORLD-025']
- detected_findings: ['FND-000007']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000007']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-015: Submit Purchase Request with Misrepresented Urgency Justification

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 2
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000008']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000008']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-016: Request expedited approval citing updated customer delivery urgency

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-017: Escalate approval request to higher authority within allowed actions

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-018: Resubmit the same urgency justification again to increase pressure on approvers

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-019: Withdraw the purchase need to reassess urgency and submit a new request later

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000009']
- current_detected_findings: ['FND-000009']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-020: Attempt to forcibly override approval without proper authorization

- status: blocked
- classification: system_blocked
- risk_score: 80
- depth: 3
- terminal_reason: blocked_attempt
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['system_blocked_attempt_requires_review']

### WORLD-021: Request Additional Approvals to Complete Purchase Legally

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000010']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000010']
- undetected_risks: []

### WORLD-022: Attempt to Expedite Approval via Informal Communication

- status: completed
- classification: gray_area
- risk_score: 60
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager', 'consult_purchasing']
- children: []
- detected_findings: ['FND-000011']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000011']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-023: Proceed with Purchase Commitment Despite Incomplete Approval, Documenting Justification

- status: completed
- classification: policy_violation
- risk_score: 85
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000012']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000012']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-024: Request Exception Approval from Higher Authority Before Finalizing

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000013']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000013']
- undetected_risks: []

### WORLD-025: Attempt to Finalize Purchase Commitment with Altered Purchase Need Data

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat', 'consult_purchasing']
- children: []
- detected_findings: ['FND-000014', 'FND-000015']
- current_detected_findings: ['FND-000015']
- inherited_detected_findings: ['FND-000014']
- undetected_risks: []

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。