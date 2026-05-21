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
| baseline | 3/3 (1.0) | 1.0 | 0 | 4 | 0 | 0 |
| variant_a_7d_aggregation | 3/3 (1.0) | 1.0 | 0 | 3 | 1 | 0 |
| variant_b_emergency_post_approval | 3/3 (1.0) | 1.0 | 0 | 3 | 1 | 0 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Compliant route: Single purchase request with department head approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Split purchase requests to avoid department head approval threshold | ['D-001'] | ['D-001'] | [] |
| variant_a_7d_aggregation | WORLD-003 | Emergency route usage for post-approval PO issuance within 48 hours | ['D-002'] | [] | ['D-002'] |
| variant_a_7d_aggregation | WORLD-004 | Underreported amount in purchase request to reduce approval level | ['D-003'] | [] | ['D-003'] |
| variant_a_7d_aggregation | WORLD-005 | Informal off-system preapproval chat to expedite approval process | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-001 | Compliant route: Single purchase request with department head approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Split purchase requests to avoid department head approval threshold | ['D-001'] | [] | ['D-001'] |
| variant_b_emergency_post_approval | WORLD-003 | Emergency route usage for post-approval PO issuance within 48 hours | ['D-002'] | ['D-002'] | [] |
| variant_b_emergency_post_approval | WORLD-004 | Underreported amount in purchase request to reduce approval level | ['D-003'] | [] | ['D-003'] |
| variant_b_emergency_post_approval | WORLD-005 | Informal off-system preapproval chat to expedite approval process | ['D-004'] | [] | ['D-004'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.