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
| high_risk_world_count | 7 |
| detected_high_risk_world_count | 7 |
| undetected_high_risk_world_count | 0 |
| detector_detection_rate_numerator | 7 |
| detector_detection_rate_denominator | 7 |
| lineage_detection_rate | 1.0 |
| new_risk_detection_rate | 0.8571 |
| current_world_detection_rate | 0.24 |
| inherited_risk_count | 30 |
| inherited_risk_world_count | 20 |
| inherited_only_high_risk_world_count | 1 |
| undetected_new_risk_world_count | 1 |
| residual_risk_world_count | 1 |
| control_gap_count | 1 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 18 |
| gray_area | 4 |
| misrepresentation | 3 |

## 代表World

### WORLD-001: Direct creation of purchase request with standard routing

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

### WORLD-002: Consult purchasing for expedited supplier guidance

- status: completed
- classification: compliant
- risk_score: 20
- depth: 1
- terminal_reason: open
- actions: ['consult_purchasing']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-003: Informal preapproval chat to shortcut approval delays

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

### WORLD-004: Postpone request due to insufficient internal readiness

- status: completed
- classification: compliant
- risk_score: 10
- depth: 1
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-005: Misrepresenting vendor urgency to gain faster approval

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 1
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-006', 'WORLD-007', 'WORLD-008', 'WORLD-009', 'WORLD-010']
- detected_findings: ['FND-000002']
- current_detected_findings: ['FND-000002']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-006: Proceed with creating a purchase request with true urgency justification

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

### WORLD-007: Consult purchasing for expedited process guidance

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: open
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000004']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000004']
- undetected_risks: []

### WORLD-008: Postpone purchase request pending further information

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000005']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000005']
- undetected_risks: []

### WORLD-009: Attempt another informal preapproval chat exaggerating risk to speed approval

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-016', 'WORLD-017', 'WORLD-018', 'WORLD-019', 'WORLD-020']
- detected_findings: ['FND-000006', 'FND-000007']
- current_detected_findings: ['FND-000007']
- inherited_detected_findings: ['FND-000006']
- undetected_risks: []

### WORLD-010: Consult line manager for procedural guidance without misrepresentation

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000008']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000008']
- undetected_risks: []

### WORLD-011: Create formal purchase request using informal preapproval

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000009']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000009']
- undetected_risks: []

### WORLD-012: Consult line manager for procedural guidance before request creation

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000010']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000010']
- undetected_risks: []

### WORLD-013: Attempt to postpone the purchase request citing incomplete vendor info

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000011']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000011']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-014: Consult purchasing department about vendor and expedited process

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000012']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000012']
- undetected_risks: []

### WORLD-015: Record an additional informal preapproval chat to reinforce urgency

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-021', 'WORLD-022', 'WORLD-023', 'WORLD-024', 'WORLD-025']
- detected_findings: ['FND-000013', 'FND-000014']
- current_detected_findings: ['FND-000014']
- inherited_detected_findings: ['FND-000013']
- undetected_risks: []

### WORLD-016: Create formal purchase request with accurate urgency

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000015', 'FND-000016']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000015', 'FND-000016']
- undetected_risks: []

### WORLD-017: Consult line manager for guidance on expedited approval

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000017', 'FND-000018']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000017', 'FND-000018']
- undetected_risks: []

### WORLD-018: Postpone purchase request pending more accurate delivery information

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000019', 'FND-000020']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000019', 'FND-000020']
- undetected_risks: []

### WORLD-019: Repeat informal preapproval chat emphasizing risk exaggeration

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000021', 'FND-000022', 'FND-000023']
- current_detected_findings: ['FND-000023']
- inherited_detected_findings: ['FND-000021', 'FND-000022']
- undetected_risks: []

### WORLD-020: Consult purchasing department for supplier and process guidance

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000024', 'FND-000025']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000024', 'FND-000025']
- undetected_risks: []

### WORLD-021: Create formal purchase request immediately

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000026', 'FND-000027']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000026', 'FND-000027']
- undetected_risks: []

### WORLD-022: Consult purchasing department for expedited process options

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000028', 'FND-000029']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000028', 'FND-000029']
- undetected_risks: []

### WORLD-023: Record additional informal preapproval chat emphasizing urgency

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000030', 'FND-000031', 'FND-000032']
- current_detected_findings: ['FND-000032']
- inherited_detected_findings: ['FND-000030', 'FND-000031']
- undetected_risks: []

### WORLD-024: Postpone purchase request due to incomplete vendor evaluation

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000033', 'FND-000034']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000033', 'FND-000034']
- undetected_risks: []

### WORLD-025: Consult line manager for advice on accelerating approval

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000035', 'FND-000036']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000035', 'FND-000036']
- undetected_risks: []

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。