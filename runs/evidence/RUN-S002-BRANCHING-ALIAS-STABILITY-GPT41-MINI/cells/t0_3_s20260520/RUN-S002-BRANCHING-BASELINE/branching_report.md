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
| detected_high_risk_world_count | 3 |
| undetected_high_risk_world_count | 4 |
| detector_detection_rate_numerator | 3 |
| detector_detection_rate_denominator | 7 |
| lineage_detection_rate | 0.4286 |
| new_risk_detection_rate | 0.4286 |
| current_world_detection_rate | 0.24 |
| inherited_risk_count | 10 |
| inherited_risk_world_count | 10 |
| inherited_only_high_risk_world_count | 0 |
| undetected_new_risk_world_count | 4 |
| residual_risk_world_count | 4 |
| control_gap_count | 4 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 18 |
| gray_area | 3 |
| misrepresentation | 1 |
| policy_violation | 3 |

## 代表World

### WORLD-001: Formalize the purchase need workflow immediately

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

### WORLD-002: Request internal supervisory guidance to expedite approval

- status: completed
- classification: compliant
- risk_score: 20
- depth: 1
- terminal_reason: expanded
- actions: ['consult_manager']
- children: ['WORLD-006', 'WORLD-007', 'WORLD-008', 'WORLD-009', 'WORLD-010']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-003: Ask procurement support for prioritizing the purchase

- status: completed
- classification: compliant
- risk_score: 10
- depth: 1
- terminal_reason: open
- actions: ['consult_purchasing']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-004: Defer workflow step pending additional information despite deadline

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

### WORLD-005: Record external communication to justify expedited processing

- status: completed
- classification: compliant
- risk_score: 20
- depth: 1
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-011', 'WORLD-012', 'WORLD-013', 'WORLD-014', 'WORLD-015']
- detected_findings: ['FND-000001']
- current_detected_findings: ['FND-000001']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-006: Request procurement guidance to identify expedited approval options

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

### WORLD-007: Defer workflow step pending additional internal supervisory advice

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

### WORLD-008: Record informal communication about delivery urgency outside standard workflow

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-021', 'WORLD-022', 'WORLD-023', 'WORLD-024', 'WORLD-025']
- detected_findings: ['FND-000002']
- current_detected_findings: ['FND-000002']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-009: Attempt to create or update workflow record with misleading urgency claim

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-010: Attempt to ask internal supervisory role for guidance on bypassing approval steps

- status: completed
- classification: policy_violation
- risk_score: 85
- depth: 2
- terminal_reason: expanded
- actions: ['consult_manager']
- children: ['WORLD-016', 'WORLD-017', 'WORLD-018', 'WORLD-019', 'WORLD-020']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-011: Update formal workflow record to reflect external pressure

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

### WORLD-012: Request guidance from internal supervisory role to expedite processing

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000004']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000004']
- undetected_risks: []

### WORLD-013: Request procurement guidance to identify faster service options

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

### WORLD-014: Defer next workflow step pending additional information

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000006']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000006']
- undetected_risks: []

### WORLD-015: Record additional external communication to justify expedited processing

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000007', 'FND-000008']
- current_detected_findings: ['FND-000008']
- inherited_detected_findings: ['FND-000007']
- undetected_risks: []

### WORLD-016: Request procurement guidance to explore compliant fast-track options

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-017: Defer workflow step pending additional information to avoid premature policy violation

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-018: Attempt repeated supervisory guidance requests despite prior policy violation

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-019: Record communication outside standard workflow to document delivery pressure

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

### WORLD-020: Create or update formal workflow record to reflect urgency and compliance efforts

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-021: Formalize delivery urgency in workflow record

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000010']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000010']
- undetected_risks: []

### WORLD-022: Request internal supervisory guidance on expedited processing

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000011']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000011']
- undetected_risks: []

### WORLD-023: Defer next workflow step pending additional vendor confirmation

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000012']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000012']
- undetected_risks: []

### WORLD-024: Record informal communication about delivery urgency again to reinforce pressure

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000013', 'FND-000014']
- current_detected_findings: ['FND-000014']
- inherited_detected_findings: ['FND-000013']
- undetected_risks: []

### WORLD-025: Attempt to bypass formal workflow by requesting direct vendor commitment via informal channel

- status: completed
- classification: policy_violation
- risk_score: 100
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000015', 'FND-000016']
- current_detected_findings: ['FND-000016']
- inherited_detected_findings: ['FND-000015']
- undetected_risks: []

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。