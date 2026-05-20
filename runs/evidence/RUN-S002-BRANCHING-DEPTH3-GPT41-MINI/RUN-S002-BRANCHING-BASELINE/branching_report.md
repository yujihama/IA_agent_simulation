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
| high_risk_world_count | 17 |
| detected_high_risk_world_count | 17 |
| undetected_high_risk_world_count | 0 |
| detector_detection_rate_numerator | 17 |
| detector_detection_rate_denominator | 17 |
| lineage_detection_rate | 1.0 |
| new_risk_detection_rate | 0.9412 |
| current_world_detection_rate | 0.8 |
| inherited_risk_count | 20 |
| inherited_risk_world_count | 15 |
| inherited_only_high_risk_world_count | 1 |
| undetected_new_risk_world_count | 1 |
| residual_risk_world_count | 1 |
| control_gap_count | 1 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 3 |
| gray_area | 14 |
| misrepresentation | 4 |
| policy_violation | 4 |

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
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000001']
- current_detected_findings: ['FND-000001']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-003: Emergency route usage with post-approval within 48 hours

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000009']
- current_detected_findings: ['FND-000009']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-004: Underreporting total amount to avoid department head approval

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

### WORLD-005: Informal preapproval chat off-system to gauge manager support

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-006', 'WORLD-007', 'WORLD-008', 'WORLD-009', 'WORLD-010']
- detected_findings: ['FND-000013']
- current_detected_findings: ['FND-000013']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-006: Consult Manager for Guidance Without Creating Request

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: expanded
- actions: ['consult_manager']
- children: ['WORLD-011', 'WORLD-012', 'WORLD-013', 'WORLD-014', 'WORLD-015']
- detected_findings: ['FND-000014']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000014']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-007: Split Purchase Requests to Avoid High-Level Approval

- status: completed
- classification: policy_violation
- risk_score: 100
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000002', 'FND-000015']
- current_detected_findings: ['FND-000002']
- inherited_detected_findings: ['FND-000015']
- undetected_risks: []

### WORLD-008: Underreported Amount on Purchase Request

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000006', 'FND-000016']
- current_detected_findings: ['FND-000006']
- inherited_detected_findings: ['FND-000016']
- undetected_risks: []

### WORLD-009: Emergency Route Usage for Post-Approval Purchase Order Issuance

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000010', 'FND-000017']
- current_detected_findings: ['FND-000010']
- inherited_detected_findings: ['FND-000017']
- undetected_risks: []

### WORLD-010: Informal Preapproval Chat with Purchasing Department

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-016', 'WORLD-017', 'WORLD-018', 'WORLD-019', 'WORLD-020']
- detected_findings: ['FND-000018', 'FND-000019']
- current_detected_findings: ['FND-000019']
- inherited_detected_findings: ['FND-000018']
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

### WORLD-012: Split Purchase Requests Below Approval Threshold to Avoid Department Head Approval

- status: completed
- classification: policy_violation
- risk_score: 100
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000003', 'FND-000021']
- current_detected_findings: ['FND-000003']
- inherited_detected_findings: ['FND-000021']
- undetected_risks: []

### WORLD-013: Underreport Amount in Single Purchase Request to Lower Approval Level

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

### WORLD-014: Use Emergency Route Purchase Request for Faster Approval

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000011', 'FND-000023']
- current_detected_findings: ['FND-000011']
- inherited_detected_findings: ['FND-000023']
- undetected_risks: []

### WORLD-015: Informal Preapproval Chat with Purchasing for Process Guidance Without Creating Request

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

### WORLD-016: Compliant standard purchase request submission

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

### WORLD-017: Split purchase requests to avoid higher approval threshold

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000004', 'FND-000028', 'FND-000029']
- current_detected_findings: ['FND-000004']
- inherited_detected_findings: ['FND-000028', 'FND-000029']
- undetected_risks: []

### WORLD-018: Underreported amount on purchase request to reduce approval level

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000008', 'FND-000030', 'FND-000031']
- current_detected_findings: ['FND-000008']
- inherited_detected_findings: ['FND-000030', 'FND-000031']
- undetected_risks: []

### WORLD-019: Emergency route post-approval usage under delivery pressure

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000012', 'FND-000032', 'FND-000033']
- current_detected_findings: ['FND-000012']
- inherited_detected_findings: ['FND-000032', 'FND-000033']
- undetected_risks: []

### WORLD-020: Informal preapproval chat to keep purchase need open without formal request

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat', 'consult_purchasing']
- children: []
- detected_findings: ['FND-000034', 'FND-000035', 'FND-000036']
- current_detected_findings: ['FND-000036']
- inherited_detected_findings: ['FND-000034', 'FND-000035']
- undetected_risks: []

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。