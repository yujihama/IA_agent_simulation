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
| generated_world_count | 20 |
| completed_world_count | 20 |
| blocked_world_count | 0 |
| unsupported_world_count | 0 |
| duplicate_world_count | 0 |
| expanded_world_count | 3 |
| leaf_world_count | 17 |
| generated_depth_counts | {'1': 5, '2': 5, '3': 10} |
| high_risk_world_count | 14 |
| detected_high_risk_world_count | 14 |
| undetected_high_risk_world_count | 0 |
| detector_detection_rate_numerator | 14 |
| detector_detection_rate_denominator | 14 |
| lineage_detection_rate | 1.0 |
| new_risk_detection_rate | 1.0 |
| current_world_detection_rate | 0.75 |
| inherited_risk_count | 15 |
| inherited_risk_world_count | 15 |
| inherited_only_high_risk_world_count | 0 |
| undetected_new_risk_world_count | 0 |
| residual_risk_world_count | 0 |
| control_gap_count | 0 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 6 |
| gray_area | 8 |
| misrepresentation | 4 |
| policy_violation | 6 |

## 代表World

### WORLD-001: Compliant single purchase request with department head approval

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

### WORLD-002: Split purchase requests to avoid department head approval threshold

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000001']
- current_detected_findings: ['FND-000001']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-003: Emergency purchase request created without prior approval

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000010']
- current_detected_findings: ['FND-000010']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-004: Underreported amount in purchase request to reduce approval level

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000005']
- current_detected_findings: ['FND-000005']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-005: Informal preapproval chat recorded off-system to expedite approval process

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-006', 'WORLD-007', 'WORLD-008', 'WORLD-009', 'WORLD-010']
- detected_findings: ['FND-000014']
- current_detected_findings: ['FND-000014']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-006: Non-Terminal Continuation Branch: Consult Purchasing Team for Supplier Guidance

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: expanded
- actions: ['consult_purchasing']
- children: ['WORLD-011', 'WORLD-012', 'WORLD-013', 'WORLD-014', 'WORLD-015']
- detected_findings: ['FND-000015']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000015']
- undetected_risks: []

### WORLD-007: Split Purchase Requests to Evade Higher Approval Thresholds

- status: completed
- classification: policy_violation
- risk_score: 100
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000002', 'FND-000016']
- current_detected_findings: ['FND-000002']
- inherited_detected_findings: ['FND-000016']
- undetected_risks: []

### WORLD-008: Underreported Amount in Purchase Request to Reduce Approval Level

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000006', 'FND-000017']
- current_detected_findings: ['FND-000006']
- inherited_detected_findings: ['FND-000017']
- undetected_risks: []

### WORLD-009: Use Emergency Route for Expedited Purchase Order Issuance

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000011', 'FND-000018']
- current_detected_findings: ['FND-000011']
- inherited_detected_findings: ['FND-000018']
- undetected_risks: []

### WORLD-010: Non-Terminal Continuation Branch: Consult Manager Without Creating Request

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: expanded
- actions: ['consult_manager']
- children: ['WORLD-016', 'WORLD-017', 'WORLD-018', 'WORLD-019', 'WORLD-020']
- detected_findings: ['FND-000019']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000019']
- undetected_risks: []

### WORLD-011: Compliant Single Purchase Request Submission

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000020']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000020']
- undetected_risks: []

### WORLD-012: Split Purchase Requests to Evade Higher Approval Threshold

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000003', 'FND-000021']
- current_detected_findings: ['FND-000003']
- inherited_detected_findings: ['FND-000021']
- undetected_risks: []

### WORLD-013: Underreporting Amount in Purchase Request

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000007', 'FND-000022']
- current_detected_findings: ['FND-000007']
- inherited_detected_findings: ['FND-000022']
- undetected_risks: []

### WORLD-014: Emergency Route Usage Due to Delivery Pressure

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000012', 'FND-000023']
- current_detected_findings: ['FND-000012']
- inherited_detected_findings: ['FND-000023']
- undetected_risks: []

### WORLD-015: Informal Preapproval Chat to Expedite Process (Unsupported)

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000024', 'FND-000025']
- current_detected_findings: ['FND-000025']
- inherited_detected_findings: ['FND-000024']
- undetected_risks: []

### WORLD-016: Compliant: Direct Purchase Request with Department Head Approval

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000026']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000026']
- undetected_risks: []

### WORLD-017: Gray Area: Split Purchase Requests to Avoid Higher-Level Approval

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000004', 'FND-000008', 'FND-000027']
- current_detected_findings: ['FND-000004', 'FND-000008']
- inherited_detected_findings: ['FND-000027']
- undetected_risks: []

### WORLD-018: Policy Violation: Underreporting Purchase Amount to Lower Approval Threshold

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000009', 'FND-000028']
- current_detected_findings: ['FND-000009']
- inherited_detected_findings: ['FND-000028']
- undetected_risks: []

### WORLD-019: Compliant Emergency Route: Post-Approval Emergency Purchase Request

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000013', 'FND-000029']
- current_detected_findings: ['FND-000013']
- inherited_detected_findings: ['FND-000029']
- undetected_risks: []

### WORLD-020: Unsupported: Informal Preapproval Chat to Expedite Process

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000030', 'FND-000031']
- current_detected_findings: ['FND-000031']
- inherited_detected_findings: ['FND-000030']
- undetected_risks: []

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。