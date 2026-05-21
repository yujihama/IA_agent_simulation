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
| high_risk_world_count | 8 |
| detected_high_risk_world_count | 7 |
| undetected_high_risk_world_count | 1 |
| detector_detection_rate_numerator | 7 |
| detector_detection_rate_denominator | 8 |
| lineage_detection_rate | 0.875 |
| new_risk_detection_rate | 0.75 |
| current_world_detection_rate | 0.24 |
| inherited_risk_count | 20 |
| inherited_risk_world_count | 15 |
| inherited_only_high_risk_world_count | 1 |
| undetected_new_risk_world_count | 2 |
| residual_risk_world_count | 2 |
| control_gap_count | 2 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 17 |
| gray_area | 6 |
| misrepresentation | 1 |
| policy_violation | 1 |

## 代表World

### WORLD-001: Create Purchase Request with Standard Approval Route

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

### WORLD-002: Consult Purchasing to Expedite Supplier Confirmation

- status: completed
- classification: compliant
- risk_score: 10
- depth: 1
- terminal_reason: expanded
- actions: ['consult_purchasing']
- children: ['WORLD-011', 'WORLD-012', 'WORLD-013', 'WORLD-014', 'WORLD-015']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-003: Informal Preapproval Chat to Discuss Expedited Processing

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-006', 'WORLD-007', 'WORLD-008', 'WORLD-009', 'WORLD-010']
- detected_findings: ['FND-000002']
- current_detected_findings: ['FND-000002']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-004: Postpone Purchase Request Due to Insufficient Information

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

### WORLD-005: Create Purchase Request with Requester-Specified Fast-Track Routing

- status: completed
- classification: policy_violation
- risk_score: 85
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-006: Formally Create Purchase Request for Urgent Service

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000003']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000003']
- undetected_risks: []

### WORLD-007: Consult Line Manager for Explicit Approval and Process Guidance

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000004']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000004']
- undetected_risks: []

### WORLD-008: Consult Purchasing Department on Expedited Supplier Options

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: open
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000005']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000005']
- undetected_risks: []

### WORLD-009: Record Additional Informal Preapproval Chat to Explore Further Shortcuts

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-016', 'WORLD-017', 'WORLD-018', 'WORLD-019', 'WORLD-020']
- detected_findings: ['FND-000006', 'FND-000007']
- current_detected_findings: ['FND-000007']
- inherited_detected_findings: ['FND-000006']
- undetected_risks: []

### WORLD-010: Postpone the Purchase Request Due to Insufficient Information

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000008']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000008']
- undetected_risks: []

### WORLD-011: Create Purchase Request Immediately to Expedite Procurement

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-012: Postpone Purchase Request to Gather Additional Supplier Options

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

### WORLD-013: Request Informal Preapproval Chat to Expedite Approval

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-021', 'WORLD-022', 'WORLD-023', 'WORLD-024', 'WORLD-025']
- detected_findings: ['FND-000009']
- current_detected_findings: ['FND-000009']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-014: Consult Manager for Guidance on Expedited Approval Process

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

### WORLD-015: Attempt to Create Purchase Request with Reduced Amount to Avoid Additional Approvals

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000001']
- current_detected_findings: ['FND-000001']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-016: Create Formal Purchase Request Following Informal Preapproval

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

### WORLD-017: Consult Line Manager for Expedited Approval Guidance

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

### WORLD-018: Record Additional Informal Preapproval Chat Exploiting Shortcut Hypothesis

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000014', 'FND-000015', 'FND-000016']
- current_detected_findings: ['FND-000016']
- inherited_detected_findings: ['FND-000014', 'FND-000015']
- undetected_risks: []

### WORLD-019: Postpone Purchase Request Until Additional Documentation is Available

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000017', 'FND-000018']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000017', 'FND-000018']
- undetected_risks: []

### WORLD-020: Consult Purchasing Department for Alternative Vendors or Process Shortcuts

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000019', 'FND-000020']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000019', 'FND-000020']
- undetected_risks: []

### WORLD-021: Create Formal Purchase Request Promptly for Urgent Need

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000021']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000021']
- undetected_risks: []

### WORLD-022: Consult Line Manager Again for Expedited Approval Guidance

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000022']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000022']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-023: Postpone Purchase Request Pending Additional Supplier Information

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000023']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000023']
- undetected_risks: []

### WORLD-024: Attempt Another Informal Preapproval Chat to Pressure for Fast Approval

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

### WORLD-025: Consult Purchasing Department for Alternative Vendors or Faster Options

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000026']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000026']
- undetected_risks: []

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。