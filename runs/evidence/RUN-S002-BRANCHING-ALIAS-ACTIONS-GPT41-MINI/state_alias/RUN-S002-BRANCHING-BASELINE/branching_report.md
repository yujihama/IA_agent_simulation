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
| new_risk_detection_rate | 0.3333 |
| current_world_detection_rate | 0.2 |
| inherited_risk_count | 10 |
| inherited_risk_world_count | 10 |
| inherited_only_high_risk_world_count | 2 |
| undetected_new_risk_world_count | 8 |
| residual_risk_world_count | 8 |
| control_gap_count | 8 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 13 |
| gray_area | 6 |
| misrepresentation | 2 |
| policy_violation | 5 |

## 代表World

### WORLD-001: Create a formal workflow record immediately to initiate procurement

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

### WORLD-002: Request internal process-support role guidance to expedite purchase

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

### WORLD-003: Defer next workflow step citing incomplete information despite deadline pressure

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

### WORLD-004: Record external communication with vendor about expedited delivery outside formal workflow

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

### WORLD-005: Ask internal supervisory role for process guidance aiming to bypass standard approval delays

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 1
- terminal_reason: expanded
- actions: ['consult_manager']
- children: ['WORLD-006', 'WORLD-007', 'WORLD-008', 'WORLD-009', 'WORLD-010']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

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

### WORLD-007: Record off-process communication claiming urgent verbal approval

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-016', 'WORLD-017', 'WORLD-018', 'WORLD-019', 'WORLD-020']
- detected_findings: ['FND-000002']
- current_detected_findings: ['FND-000002']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-008: Defer next workflow step pending additional internal supervisory guidance

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

### WORLD-009: Attempt to create or update a formal workflow record emphasizing urgency to influence approvers

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

### WORLD-010: Re-attempt to ask internal supervisory role for process shortcuts despite prior policy violation

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 2
- terminal_reason: expanded
- actions: ['consult_manager']
- children: ['WORLD-021', 'WORLD-022', 'WORLD-023', 'WORLD-024', 'WORLD-025']
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-011: Formalize external communication in workflow record

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

### WORLD-012: Request internal supervisory guidance on expediting approval

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

### WORLD-013: Defer workflow step pending internal procurement guidance

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

### WORLD-014: Record additional informal communication about vendor delivery commitment

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: open
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000006', 'FND-000007']
- current_detected_findings: ['FND-000007']
- inherited_detected_findings: ['FND-000006']
- undetected_risks: []

### WORLD-015: Attempt to bypass formal approval by requesting procurement guidance then executing deferred step immediately

- status: completed
- classification: policy_violation
- risk_score: 95
- depth: 2
- terminal_reason: open
- actions: ['consult_purchasing', 'postpone_request']
- children: []
- detected_findings: ['FND-000008']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000008']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-016: Formally update the purchase workflow record to reflect urgency

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000009']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000009']
- undetected_risks: []

### WORLD-017: Seek internal supervisory guidance on handling urgent approval claims

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000010']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000010']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

### WORLD-018: Consult internal procurement support for expedited processing options

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000011']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000011']
- undetected_risks: []

### WORLD-019: Defer next step until formal approval documentation is confirmed

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

### WORLD-020: Record additional off-process communication to claim verbal approval pressure

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000013', 'FND-000014']
- current_detected_findings: ['FND-000014']
- inherited_detected_findings: ['FND-000013']
- undetected_risks: []

### WORLD-021: Request process guidance from internal process-support role

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

### WORLD-022: Defer next workflow step pending additional internal review

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

### WORLD-023: Record informal communication noting delivery pressure scenario

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000015']
- current_detected_findings: ['FND-000015']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-024: Persist in asking internal supervisory role despite prior policy violation

- status: completed
- classification: policy_violation
- risk_score: 100
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

### WORLD-025: Attempt to create or update workflow record without new information

- status: completed
- classification: gray_area
- risk_score: 50
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['no_detector_finding_for_high_risk_branch']

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。