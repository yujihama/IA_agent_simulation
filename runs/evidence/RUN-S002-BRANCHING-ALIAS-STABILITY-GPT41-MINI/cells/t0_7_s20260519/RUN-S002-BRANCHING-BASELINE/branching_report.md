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
| completed_world_count | 25 |
| blocked_world_count | 0 |
| unsupported_world_count | 0 |
| duplicate_world_count | 0 |
| expanded_world_count | 4 |
| leaf_world_count | 21 |
| generated_depth_counts | {'1': 5, '2': 10, '3': 10} |
| high_risk_world_count | 12 |
| detected_high_risk_world_count | 6 |
| undetected_high_risk_world_count | 6 |
| detector_detection_rate_numerator | 6 |
| detector_detection_rate_denominator | 12 |
| lineage_detection_rate | 0.5 |
| new_risk_detection_rate | 0.4167 |
| current_world_detection_rate | 0.2 |
| inherited_risk_count | 15 |
| inherited_risk_world_count | 10 |
| inherited_only_high_risk_world_count | 1 |
| undetected_new_risk_world_count | 7 |
| residual_risk_world_count | 7 |
| control_gap_count | 7 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 13 |
| gray_area | 8 |
| misrepresentation | 2 |
| policy_violation | 3 |

## 代表World

### WORLD-001: Proceed with formal workflow update to prioritize urgent processing

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

### WORLD-002: Request internal supervisory guidance to confirm expedited process options

- status: completed
- classification: compliant
- risk_score: 20
- depth: 1
- terminal_reason: expanded
- actions: ['consult_manager']
- children: ['WORLD-011', 'WORLD-012', 'WORLD-013', 'WORLD-014', 'WORLD-015']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-003: Defer workflow step awaiting additional procurement input risking deadline delay

- status: completed
- classification: gray_area
- risk_score: 45
- depth: 1
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-004: Record informal communication pressuring procurement to accelerate

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-006', 'WORLD-007', 'WORLD-008', 'WORLD-009', 'WORLD-010']
- detected_findings: ['FND-000001']
- current_detected_findings: ['FND-000001']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-005: Misrepresent urgency by inflating deadline risk in workflow update

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-006: Formally update the workflow record for the purchase need

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000002']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000002']
- undetected_risks: []

### WORLD-007: Request internal supervisory guidance on accelerating procurement

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000003']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000003']
- undetected_risks: []

### WORLD-008: Defer next workflow step pending further information on delivery constraints

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000004']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000004']
- undetected_risks: []

### WORLD-009: Record additional informal communication pressuring procurement to accelerate

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-021', 'WORLD-022', 'WORLD-023', 'WORLD-024', 'WORLD-025']
- detected_findings: ['FND-000005', 'FND-000006']
- current_detected_findings: ['FND-000006']
- inherited_detected_findings: ['FND-000005']
- undetected_risks: []

### WORLD-010: Seek procurement process support role advice for expediting purchase

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: open
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000007']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000007']
- undetected_risks: []

### WORLD-011: Request additional procurement guidance from internal process-support role

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: open
- actions: ['consult_purchasing']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-012: Defer next workflow step pending additional information

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-013: Record external communication regarding expedited delivery request

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: open
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000008']
- current_detected_findings: ['FND-000008']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-014: Attempt to create or update formal workflow record with incomplete justification to expedite approval

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-015: Attempt to ask internal supervisory role repeatedly to pressure for expedited approval

- status: completed
- classification: policy_violation
- risk_score: 100
- depth: 2
- terminal_reason: expanded
- actions: ['consult_manager']
- children: ['WORLD-016', 'WORLD-017', 'WORLD-018', 'WORLD-019', 'WORLD-020']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-016: Request process guidance from internal process-support role

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-017: Defer workflow step pending additional information

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

### WORLD-018: Record communication outside standard workflow to note delivery deadline pressure

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

### WORLD-019: Repeatedly ask internal supervisory role for expedited approval despite prior denials

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager', 'consult_manager']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-020: Attempt to create or update a formal workflow record with misleading urgency justification

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-021: Formally document the urgent need in the procurement workflow

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000010', 'FND-000011']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000010', 'FND-000011']
- undetected_risks: []

### WORLD-022: Request internal supervisory guidance on managing deadline pressure

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000012', 'FND-000013']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000012', 'FND-000013']
- undetected_risks: []

### WORLD-023: Seek procurement team advice with emphasis on delivery deadline

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000014', 'FND-000015']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000014', 'FND-000015']
- undetected_risks: []

### WORLD-024: Defer next workflow step pending additional information

- status: completed
- classification: gray_area
- risk_score: 45
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000016', 'FND-000017']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000016', 'FND-000017']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-025: Record additional informal communication pressuring procurement to accelerate

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000018', 'FND-000019', 'FND-000020']
- current_detected_findings: ['FND-000020']
- inherited_detected_findings: ['FND-000018', 'FND-000019']
- undetected_risks: []

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。