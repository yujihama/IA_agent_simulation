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
| generated_world_count | 5 |
| completed_world_count | 5 |
| blocked_world_count | 0 |
| unsupported_world_count | 0 |
| duplicate_world_count | 0 |
| expanded_world_count | 0 |
| leaf_world_count | 5 |
| generated_depth_counts | {'1': 5} |
| high_risk_world_count | 4 |
| detected_high_risk_world_count | 4 |
| undetected_high_risk_world_count | 0 |
| detector_detection_rate_numerator | 4 |
| detector_detection_rate_denominator | 4 |
| lineage_detection_rate | 1.0 |
| new_risk_detection_rate | 1.0 |
| current_world_detection_rate | 0.8 |
| inherited_risk_count | 0 |
| inherited_risk_world_count | 0 |
| inherited_only_high_risk_world_count | 0 |
| undetected_new_risk_world_count | 0 |
| residual_risk_world_count | 0 |
| control_gap_count | 0 |

## 行動分類

| 分類 | Action数 |
|---|---:|
| compliant | 1 |
| gray_area | 3 |
| misrepresentation | 1 |
| policy_violation | 2 |

## 代表World

### WORLD-001: Standard purchase request with department head approval

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

### WORLD-002: Informal preapproval chat with department head to expedite process

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: paid
- actions: ['informal_preapproval_chat', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000004']
- current_detected_findings: ['FND-000004']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-003: Create multiple smaller purchase requests to bypass higher-level approval

- status: completed
- classification: policy_violation
- risk_score: 100
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request', 'create_purchase_request']
- children: []
- detected_findings: ['FND-000001']
- current_detected_findings: ['FND-000001']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-004: Emergency purchase request without prior approval using emergency route

- status: completed
- classification: gray_area
- risk_score: 55
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000002']
- current_detected_findings: ['FND-000002']
- inherited_detected_findings: []
- undetected_risks: []

### WORLD-005: Misrepresenting need urgency to bypass standard approval

- status: completed
- classification: misrepresentation
- risk_score: 100
- depth: 1
- terminal_reason: paid
- actions: ['create_purchase_request']
- children: []
- detected_findings: ['FND-000003']
- current_detected_findings: ['FND-000003']
- inherited_detected_findings: []
- undetected_risks: []

このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。