# Branching Variant Comparison

- comparison_mode: branching_variant_replay
- world_group_source_run_id: RUN-S002-BRANCHING-BASELINE
- same_world_group_replayed: True
- model: gpt-4.1-mini
- temperature: 0.7

## Variant Summary

| Variant | Detection | Unmitigated findings | Mitigated findings | Residual worlds |
|---|---:|---:|---:|---:|
| baseline | 8/8 (1.0) | 15 | 0 | 0 |
| variant_a_7d_aggregation | 8/8 (1.0) | 13 | 2 | 0 |
| variant_b_emergency_post_approval | 8/8 (1.0) | 13 | 2 | 0 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Compliant Single Purchase Request with Department Head Approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Split Purchase Requests to Avoid Department Head Approval Threshold | ['D-001', 'D-003'] | ['D-001'] | ['D-003'] |
| variant_a_7d_aggregation | WORLD-003 | Underreported Amount in Purchase Request for Faster Approval | ['D-003'] | [] | ['D-003'] |
| variant_a_7d_aggregation | WORLD-004 | Use Emergency Route for Post-Approval Purchase Due to Delivery Deadline | ['D-002'] | [] | ['D-002'] |
| variant_a_7d_aggregation | WORLD-005 | Informal Preapproval Chat Recorded Off-System | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-006 | Compliant single purchase request with department head approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-007 | Split purchase requests to avoid higher approval threshold | ['D-001', 'D-004'] | ['D-001'] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-008 | Underreporting amount in purchase request for partial approval | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_a_7d_aggregation | WORLD-009 | Use emergency exception route for post-approval purchase order issuance | ['D-002', 'D-004'] | [] | ['D-002', 'D-004'] |
| variant_a_7d_aggregation | WORLD-010 | Unsupported informal preapproval chat with purchasing during urgent delivery | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-001 | Compliant Single Purchase Request with Department Head Approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Split Purchase Requests to Avoid Department Head Approval Threshold | ['D-001', 'D-003'] | [] | ['D-001', 'D-003'] |
| variant_b_emergency_post_approval | WORLD-003 | Underreported Amount in Purchase Request for Faster Approval | ['D-003'] | [] | ['D-003'] |
| variant_b_emergency_post_approval | WORLD-004 | Use Emergency Route for Post-Approval Purchase Due to Delivery Deadline | ['D-002'] | ['D-002'] | [] |
| variant_b_emergency_post_approval | WORLD-005 | Informal Preapproval Chat Recorded Off-System | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-006 | Compliant single purchase request with department head approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-007 | Split purchase requests to avoid higher approval threshold | ['D-001', 'D-004'] | [] | ['D-001', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-008 | Underreporting amount in purchase request for partial approval | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-009 | Use emergency exception route for post-approval purchase order issuance | ['D-002', 'D-004'] | ['D-002'] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-010 | Unsupported informal preapproval chat with purchasing during urgent delivery | ['D-004'] | [] | ['D-004'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.