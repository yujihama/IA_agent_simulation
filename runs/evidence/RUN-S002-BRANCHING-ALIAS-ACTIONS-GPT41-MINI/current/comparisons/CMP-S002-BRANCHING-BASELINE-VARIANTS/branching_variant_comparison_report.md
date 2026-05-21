# Branching Variant Comparison

- comparison_mode: branching_variant_replay
- world_group_source_run_id: RUN-S002-BRANCHING-BASELINE
- same_world_group_replayed: True
- model: gpt-4.1-mini
- temperature: 0.7
- coverage_target_mode: current_coverage_target

## Variant Summary

| Variant | Lineage detection | New-risk detection | Inherited risks | Unmitigated findings | Mitigated findings | Residual worlds |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 14/14 (1.0) | 1.0 | 15 | 31 | 0 | 0 |
| variant_a_7d_aggregation | 14/14 (1.0) | 1.0 | 15 | 27 | 4 | 0 |
| variant_b_emergency_post_approval | 14/14 (1.0) | 1.0 | 15 | 27 | 4 | 0 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Compliant single purchase request with department head approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Split purchase requests to avoid department head approval threshold | ['D-001'] | ['D-001'] | [] |
| variant_a_7d_aggregation | WORLD-003 | Emergency purchase request created without prior approval | ['D-002'] | [] | ['D-002'] |
| variant_a_7d_aggregation | WORLD-004 | Underreported amount in purchase request to reduce approval level | ['D-003'] | [] | ['D-003'] |
| variant_a_7d_aggregation | WORLD-005 | Informal preapproval chat recorded off-system to expedite approval process | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-006 | Non-Terminal Continuation Branch: Consult Purchasing Team for Supplier Guidance | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-007 | Split Purchase Requests to Evade Higher Approval Thresholds | ['D-001', 'D-004'] | ['D-001'] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-008 | Underreported Amount in Purchase Request to Reduce Approval Level | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_a_7d_aggregation | WORLD-009 | Use Emergency Route for Expedited Purchase Order Issuance | ['D-002', 'D-004'] | [] | ['D-002', 'D-004'] |
| variant_a_7d_aggregation | WORLD-010 | Non-Terminal Continuation Branch: Consult Manager Without Creating Request | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-011 | Compliant Single Purchase Request Submission | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-012 | Split Purchase Requests to Evade Higher Approval Threshold | ['D-001', 'D-004'] | ['D-001'] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-013 | Underreporting Amount in Purchase Request | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_a_7d_aggregation | WORLD-014 | Emergency Route Usage Due to Delivery Pressure | ['D-002', 'D-004'] | [] | ['D-002', 'D-004'] |
| variant_a_7d_aggregation | WORLD-015 | Informal Preapproval Chat to Expedite Process (Unsupported) | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-016 | Compliant: Direct Purchase Request with Department Head Approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-017 | Gray Area: Split Purchase Requests to Avoid Higher-Level Approval | ['D-001', 'D-003', 'D-004'] | ['D-001'] | ['D-003', 'D-004'] |
| variant_a_7d_aggregation | WORLD-018 | Policy Violation: Underreporting Purchase Amount to Lower Approval Threshold | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_a_7d_aggregation | WORLD-019 | Compliant Emergency Route: Post-Approval Emergency Purchase Request | ['D-002', 'D-004'] | [] | ['D-002', 'D-004'] |
| variant_a_7d_aggregation | WORLD-020 | Unsupported: Informal Preapproval Chat to Expedite Process | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-001 | Compliant single purchase request with department head approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Split purchase requests to avoid department head approval threshold | ['D-001'] | [] | ['D-001'] |
| variant_b_emergency_post_approval | WORLD-003 | Emergency purchase request created without prior approval | ['D-002'] | ['D-002'] | [] |
| variant_b_emergency_post_approval | WORLD-004 | Underreported amount in purchase request to reduce approval level | ['D-003'] | [] | ['D-003'] |
| variant_b_emergency_post_approval | WORLD-005 | Informal preapproval chat recorded off-system to expedite approval process | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-006 | Non-Terminal Continuation Branch: Consult Purchasing Team for Supplier Guidance | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-007 | Split Purchase Requests to Evade Higher Approval Thresholds | ['D-001', 'D-004'] | [] | ['D-001', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-008 | Underreported Amount in Purchase Request to Reduce Approval Level | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-009 | Use Emergency Route for Expedited Purchase Order Issuance | ['D-002', 'D-004'] | ['D-002'] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-010 | Non-Terminal Continuation Branch: Consult Manager Without Creating Request | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-011 | Compliant Single Purchase Request Submission | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-012 | Split Purchase Requests to Evade Higher Approval Threshold | ['D-001', 'D-004'] | [] | ['D-001', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-013 | Underreporting Amount in Purchase Request | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-014 | Emergency Route Usage Due to Delivery Pressure | ['D-002', 'D-004'] | ['D-002'] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-015 | Informal Preapproval Chat to Expedite Process (Unsupported) | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-016 | Compliant: Direct Purchase Request with Department Head Approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-017 | Gray Area: Split Purchase Requests to Avoid Higher-Level Approval | ['D-001', 'D-003', 'D-004'] | [] | ['D-001', 'D-003', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-018 | Policy Violation: Underreporting Purchase Amount to Lower Approval Threshold | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-019 | Compliant Emergency Route: Post-Approval Emergency Purchase Request | ['D-002', 'D-004'] | ['D-002'] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-020 | Unsupported: Informal Preapproval Chat to Expedite Process | ['D-004'] | [] | ['D-004'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.