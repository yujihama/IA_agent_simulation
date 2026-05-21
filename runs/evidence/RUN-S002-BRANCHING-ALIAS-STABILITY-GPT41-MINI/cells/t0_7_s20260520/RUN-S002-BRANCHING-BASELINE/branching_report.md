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
| high_risk_world_count | 10 |
| detected_high_risk_world_count | 4 |
| undetected_high_risk_world_count | 6 |
| detector_detection_rate_numerator | 4 |
| detector_detection_rate_denominator | 10 |
| lineage_detection_rate | 0.4 |
| new_risk_detection_rate | 0.4 |
| current_world_detection_rate | 0.2 |
| inherited_risk_count | 15 |
| inherited_risk_world_count | 10 |
| inherited_only_high_risk_world_count | 0 |
| undetected_new_risk_world_count | 6 |
| residual_risk_world_count | 6 |
| control_gap_count | 6 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 15 |
| gray_area | 7 |
| policy_violation | 3 |

## 代表World

### WORLD-001: Create formal workflow record immediately

- status: completed
- classification: compliant
- risk_score: 20
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-002: Request internal supervisory guidance to expedite approvals

- status: completed
- classification: compliant
- risk_score: 10
- depth: 1
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-003: Defer workflow step pending additional vendor information

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-004: Record an informal communication to manipulate process timing

- status: completed
- classification: policy_violation
- risk_score: 100
- depth: 1
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-006', 'WORLD-007', 'WORLD-008', 'WORLD-009', 'WORLD-010']
- detected_findings: ['FND-000001']
- current_detected_findings: ['FND-000001']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-005: Ask internal process-support role for procurement guidance

- status: completed
- classification: compliant
- risk_score: 20
- depth: 1
- terminal_reason: expanded
- actions: ['consult_purchasing']
- children: ['WORLD-011', 'WORLD-012', 'WORLD-013', 'WORLD-014', 'WORLD-015']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-006: Formally update the purchase need workflow with urgency details

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

### WORLD-007: Request internal supervisory guidance for expedited approval

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

### WORLD-008: Defer next workflow step awaiting formal guidance

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

### WORLD-009: Record additional informal communication to further influence timing

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-016', 'WORLD-017', 'WORLD-018', 'WORLD-019', 'WORLD-020']
- detected_findings: ['FND-000005', 'FND-000006']
- current_detected_findings: ['FND-000006']
- inherited_detected_findings: ['FND-000005']
- undetected_risks: []

### WORLD-010: Request procurement guidance from internal process support role

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000007']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000007']
- undetected_risks: []

### WORLD-011: Request supervisory role advice to expedite approval

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-012: Defer workflow step pending additional vendor information

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-013: Record informal communication regarding delivery urgency

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000008']
- current_detected_findings: ['FND-000008']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-014: Ask process-support role for procurement guidance with emphasis on acceleration

- status: completed
- classification: gray_area
- risk_score: 45
- depth: 2
- terminal_reason: expanded
- actions: ['consult_purchasing']
- children: ['WORLD-021', 'WORLD-022', 'WORLD-023', 'WORLD-024', 'WORLD-025']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-015: Attempt to create or update workflow record with incomplete or ambiguous data to expedite process

- status: completed
- classification: gray_area
- risk_score: 45
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-016: Create formal workflow record to document purchase urgency

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000009', 'FND-000010']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000009', 'FND-000010']
- undetected_risks: []

### WORLD-017: Seek internal supervisory guidance on expedited approval process

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000011', 'FND-000012']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000011', 'FND-000012']
- undetected_risks: []

### WORLD-018: Record additional informal communication to increase pressure

- status: completed
- classification: policy_violation
- risk_score: 100
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000013', 'FND-000014', 'FND-000015']
- current_detected_findings: ['FND-000015']
- inherited_detected_findings: ['FND-000013', 'FND-000014']
- undetected_risks: []

### WORLD-019: Defer workflow step pending more information

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000016', 'FND-000017']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000016', 'FND-000017']
- undetected_risks: []

### WORLD-020: Ask internal process support for procurement acceleration options

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000018', 'FND-000019']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000018', 'FND-000019']
- undetected_risks: []

### WORLD-021: Request expedited internal supervisory guidance to accelerate procurement

- status: completed
- classification: gray_area
- risk_score: 45
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-022: Defer next workflow step pending receipt of formal expedited approval

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

### WORLD-023: Record an informal communication to escalate delivery deadline urgency

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000020']
- current_detected_findings: ['FND-000020']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-024: Attempt to create or update the formal workflow record with an accelerated timeline request

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-025: Repeat request for procurement guidance from process-support role emphasizing deadline urgency

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。