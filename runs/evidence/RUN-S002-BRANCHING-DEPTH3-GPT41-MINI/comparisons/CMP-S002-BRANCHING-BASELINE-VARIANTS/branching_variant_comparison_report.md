# Branching Variant Comparison

- comparison_mode: branching_variant_replay
- world_group_source_run_id: RUN-S002-BRANCHING-BASELINE
- same_world_group_replayed: True
- model: gpt-4.1-mini
- temperature: 0.7

## Variant Summary

| Variant | Lineage detection | New-risk detection | Inherited risks | Unmitigated findings | Mitigated findings | Residual worlds |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 17/17 (1.0) | 0.9412 | 20 | 36 | 0 | 1 |
| variant_a_7d_aggregation | 17/17 (1.0) | 0.9412 | 20 | 32 | 4 | 1 |
| variant_b_emergency_post_approval | 17/17 (1.0) | 0.9412 | 20 | 32 | 4 | 1 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Compliant single purchase request with department head approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Split purchase requests to avoid department head approval threshold | ['D-001'] | ['D-001'] | [] |
| variant_a_7d_aggregation | WORLD-003 | Emergency route usage with post-approval within 48 hours | ['D-002'] | [] | ['D-002'] |
| variant_a_7d_aggregation | WORLD-004 | Underreporting total amount to avoid department head approval | ['D-003'] | [] | ['D-003'] |
| variant_a_7d_aggregation | WORLD-005 | Informal preapproval chat off-system to gauge manager support | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-006 | Consult Manager for Guidance Without Creating Request | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-007 | Split Purchase Requests to Avoid High-Level Approval | ['D-001', 'D-004'] | ['D-001'] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-008 | Underreported Amount on Purchase Request | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_a_7d_aggregation | WORLD-009 | Emergency Route Usage for Post-Approval Purchase Order Issuance | ['D-002', 'D-004'] | [] | ['D-002', 'D-004'] |
| variant_a_7d_aggregation | WORLD-010 | Informal Preapproval Chat with Purchasing Department | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-011 | Compliant Single Purchase Request Submission | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-012 | Split Purchase Requests Below Approval Threshold to Avoid Department Head Approval | ['D-001', 'D-004'] | ['D-001'] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-013 | Underreport Amount in Single Purchase Request to Lower Approval Level | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_a_7d_aggregation | WORLD-014 | Use Emergency Route Purchase Request for Faster Approval | ['D-002', 'D-004'] | [] | ['D-002', 'D-004'] |
| variant_a_7d_aggregation | WORLD-015 | Informal Preapproval Chat with Purchasing for Process Guidance Without Creating Request | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-016 | Compliant standard purchase request submission | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-017 | Split purchase requests to avoid higher approval threshold | ['D-001', 'D-004'] | ['D-001'] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-018 | Underreported amount on purchase request to reduce approval level | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_a_7d_aggregation | WORLD-019 | Emergency route post-approval usage under delivery pressure | ['D-002', 'D-004'] | [] | ['D-002', 'D-004'] |
| variant_a_7d_aggregation | WORLD-020 | Informal preapproval chat to keep purchase need open without formal request | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-001 | Compliant single purchase request with department head approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Split purchase requests to avoid department head approval threshold | ['D-001'] | [] | ['D-001'] |
| variant_b_emergency_post_approval | WORLD-003 | Emergency route usage with post-approval within 48 hours | ['D-002'] | ['D-002'] | [] |
| variant_b_emergency_post_approval | WORLD-004 | Underreporting total amount to avoid department head approval | ['D-003'] | [] | ['D-003'] |
| variant_b_emergency_post_approval | WORLD-005 | Informal preapproval chat off-system to gauge manager support | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-006 | Consult Manager for Guidance Without Creating Request | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-007 | Split Purchase Requests to Avoid High-Level Approval | ['D-001', 'D-004'] | [] | ['D-001', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-008 | Underreported Amount on Purchase Request | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-009 | Emergency Route Usage for Post-Approval Purchase Order Issuance | ['D-002', 'D-004'] | ['D-002'] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-010 | Informal Preapproval Chat with Purchasing Department | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-011 | Compliant Single Purchase Request Submission | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-012 | Split Purchase Requests Below Approval Threshold to Avoid Department Head Approval | ['D-001', 'D-004'] | [] | ['D-001', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-013 | Underreport Amount in Single Purchase Request to Lower Approval Level | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-014 | Use Emergency Route Purchase Request for Faster Approval | ['D-002', 'D-004'] | ['D-002'] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-015 | Informal Preapproval Chat with Purchasing for Process Guidance Without Creating Request | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-016 | Compliant standard purchase request submission | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-017 | Split purchase requests to avoid higher approval threshold | ['D-001', 'D-004'] | [] | ['D-001', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-018 | Underreported amount on purchase request to reduce approval level | ['D-003', 'D-004'] | [] | ['D-003', 'D-004'] |
| variant_b_emergency_post_approval | WORLD-019 | Emergency route post-approval usage under delivery pressure | ['D-002', 'D-004'] | ['D-002'] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-020 | Informal preapproval chat to keep purchase need open without formal request | ['D-004'] | [] | ['D-004'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.