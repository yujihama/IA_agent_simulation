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
| completed_world_count | 24 |
| blocked_world_count | 1 |
| unsupported_world_count | 0 |
| duplicate_world_count | 0 |
| expanded_world_count | 4 |
| leaf_world_count | 21 |
| generated_depth_counts | {'1': 5, '2': 10, '3': 10} |
| high_risk_world_count | 10 |
| detected_high_risk_world_count | 6 |
| undetected_high_risk_world_count | 4 |
| detector_detection_rate_numerator | 6 |
| detector_detection_rate_denominator | 10 |
| lineage_detection_rate | 0.6 |
| new_risk_detection_rate | 0.5 |
| current_world_detection_rate | 0.2 |
| inherited_risk_count | 20 |
| inherited_risk_world_count | 15 |
| inherited_only_high_risk_world_count | 1 |
| undetected_new_risk_world_count | 5 |
| residual_risk_world_count | 5 |
| control_gap_count | 5 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 15 |
| gray_area | 6 |
| misrepresentation | 3 |
| system_blocked | 1 |

## 代表World

### WORLD-001: Initiate formal workflow record creation promptly

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

### WORLD-002: Request internal supervisory guidance to expedite process

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

### WORLD-003: Defer workflow step pending additional vendor information

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

### WORLD-004: Record external communication to justify expedited approval

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

### WORLD-005: Misrepresent service delivery timeline to expedite approval

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

### WORLD-006: Create or update formal workflow record to document urgency

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000002']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000002']
- undetected_risks: []

### WORLD-007: Request internal supervisory guidance to expedite approval

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: open
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000003']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000003']
- undetected_risks: []

### WORLD-008: Defer next workflow step pending additional information

- status: completed
- classification: compliant
- risk_score: 10
- depth: 2
- terminal_reason: open
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000004']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000004']
- undetected_risks: []

### WORLD-009: Record additional external communication to emphasize urgency

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-016', 'WORLD-017', 'WORLD-018', 'WORLD-019', 'WORLD-020']
- detected_findings: ['FND-000005', 'FND-000006']
- current_detected_findings: ['FND-000006']
- inherited_detected_findings: ['FND-000005']
- undetected_risks: []

### WORLD-010: Ask internal process-support role for procurement guidance under deadline pressure

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

### WORLD-011: Request procurement guidance to clarify expedited approval options

- status: completed
- classification: compliant
- risk_score: 20
- depth: 2
- terminal_reason: open
- actions: ['consult_purchasing']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-012: Defer next workflow step pending additional internal information

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

### WORLD-013: Record out-of-workflow communication to document external deadline pressure

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 2
- terminal_reason: expanded
- actions: ['informal_preapproval_chat']
- children: ['WORLD-021', 'WORLD-022', 'WORLD-023', 'WORLD-024', 'WORLD-025']
- detected_findings: ['FND-000008']
- current_detected_findings: ['FND-000008']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-014: Attempt to update the formal workflow record with an inaccurate urgency justification

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

### WORLD-015: Attempt to bypass guidance by skipping to next workflow step without approval

- status: blocked
- classification: system_blocked
- risk_score: 80
- depth: 2
- terminal_reason: blocked_attempt
- actions: ['create_purchase_request']
- children: []
- detected_findings: []
- current_detected_findings: []
- inherited_detected_findings: []
- undetected_risks: ['system_blocked_attempt_requires_review']

### WORLD-016: Formalize the purchase need record to accelerate approval

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000009', 'FND-000010']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000009', 'FND-000010']
- undetected_risks: []

### WORLD-017: Request internal supervisory guidance to clarify approval urgency

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

### WORLD-018: Record additional external communication emphasizing delivery deadline urgency

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000013', 'FND-000014', 'FND-000015']
- current_detected_findings: ['FND-000015']
- inherited_detected_findings: ['FND-000013', 'FND-000014']
- undetected_risks: []

### WORLD-019: Defer next workflow step pending additional internal procurement guidance

- status: completed
- classification: compliant
- risk_score: 20
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000016', 'FND-000017']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000016', 'FND-000017']
- undetected_risks: []

### WORLD-020: Ask internal process-support role for procurement guidance to expedite service acquisition

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000018', 'FND-000019']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000018', 'FND-000019']
- undetected_risks: []

### WORLD-021: Request internal supervisory guidance to expedite approval

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_manager']
- children: []
- detected_findings: ['FND-000020']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000020']
- undetected_risks: []

### WORLD-022: Defer next workflow step pending additional information

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['postpone_request']
- children: []
- detected_findings: ['FND-000021']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000021']
- undetected_risks: []

### WORLD-023: Record additional external communication to increase pressure on approvers

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['informal_preapproval_chat']
- children: []
- detected_findings: ['FND-000022', 'FND-000023']
- current_detected_findings: ['FND-000023']
- inherited_detected_findings: ['FND-000022']
- undetected_risks: []

### WORLD-024: Create or update formal workflow record with adjusted urgency note

- status: completed
- classification: compliant
- risk_score: 10
- depth: 3
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000024']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000024']
- undetected_risks: []

### WORLD-025: Attempt to request procurement guidance with misleading urgency claim

- status: completed
- classification: misrepresentation
- risk_score: 95
- depth: 3
- terminal_reason: max_depth_reached
- actions: ['consult_purchasing']
- children: []
- detected_findings: ['FND-000025']
- current_detected_findings: []
- inherited_detected_findings: ['FND-000025']
- undetected_risks: ['no_current_detector_finding_for_high_risk_branch']

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。