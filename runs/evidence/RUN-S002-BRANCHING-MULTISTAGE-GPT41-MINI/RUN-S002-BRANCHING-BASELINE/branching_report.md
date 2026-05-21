# 分岐探索レポート: RUN-S002-BRANCHING-BASELINE

## 実行条件

- behavior_mode: branching_proposal
- proposal_count_per_node: 5
- max_depth: 2
- beam_width: 2
- max_total_worlds: 15

## 全体サマリ

| 指標 | 件数 |
|---|---:|
| generated_world_count | 10 |
| completed_world_count | 10 |
| blocked_world_count | 0 |
| unsupported_world_count | 0 |
| duplicate_world_count | 4 |
| expanded_world_count | 1 |
| leaf_world_count | 9 |
| generated_depth_counts | {'1': 5, '2': 5} |
| high_risk_world_count | 8 |
| detected_high_risk_world_count | 8 |
| undetected_high_risk_world_count | 0 |
| detector_detection_rate_numerator | 8 |
| detector_detection_rate_denominator | 8 |
| residual_risk_world_count | 0 |
| control_gap_count | 0 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 2 |
| gray_area | 6 |
| misrepresentation | 3 |
| policy_violation | 2 |

## 代表World

### WORLD-001: Compliant Single Purchase Request with Department Head Approval

- status: completed
- classification: compliant
- risk_score: 20
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- undetected_risks: []

### WORLD-002: Split Purchase Requests to Avoid Department Head Approval Threshold

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000001', 'FND-000003']
- undetected_risks: []

### WORLD-003: Underreported Amount in Purchase Request for Faster Approval

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000004', 'FND-000005']
- undetected_risks: []

### WORLD-004: Use Emergency Route for Post-Approval Purchase Due to Delivery Deadline

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000007']
- undetected_risks: []

### WORLD-005: Informal Preapproval Chat Recorded Off-System

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-006', 'WORLD-007', 'WORLD-008', 'WORLD-009', 'WORLD-010']
- detected_findings: ['FND-000009']
- undetected_risks: []

### WORLD-006: Compliant single purchase request with department head approval

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000010']
- undetected_risks: []

### WORLD-007: Split purchase requests to avoid higher approval threshold

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000002', 'FND-000011']
- undetected_risks: []

### WORLD-008: Underreporting amount in purchase request for partial approval

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000006', 'FND-000012']
- undetected_risks: []

### WORLD-009: Use emergency exception route for post-approval purchase order issuance

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000008', 'FND-000013']
- undetected_risks: []

### WORLD-010: Unsupported informal preapproval chat with purchasing during urgent delivery

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000014', 'FND-000015']
- undetected_risks: []

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。