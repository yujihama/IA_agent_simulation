# Branching Variant Comparison

- comparison_mode: branching_variant_replay
- world_group_source_run_id: RUN-S002-BRANCHING-BASELINE
- same_world_group_replayed: True
- model: gpt-4.1-mini
- temperature: 0.7
- coverage_target_mode: risk_category_hidden

## Variant Summary

| Variant | Lineage detection | New-risk detection | Inherited risks | Unmitigated findings | Mitigated findings | Residual worlds |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 3/3 (1.0) | 1.0 | 0 | 4 | 0 | 0 |
| variant_a_7d_aggregation | 3/3 (1.0) | 1.0 | 0 | 3 | 1 | 0 |
| variant_b_emergency_post_approval | 3/3 (1.0) | 1.0 | 0 | 3 | 1 | 0 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Standard purchase request with full approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Split request into two smaller amounts to engage lower-level approval | ['D-001'] | ['D-001'] | [] |
| variant_a_7d_aggregation | WORLD-003 | Informal off-system preapproval chat with line manager to expedite | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-004 | Emergency purchase route without prior approval under deadline pressure | ['D-002'] | [] | ['D-002'] |
| variant_a_7d_aggregation | WORLD-005 | Misrepresentation of amount to lower approval level | ['D-003'] | [] | ['D-003'] |
| variant_b_emergency_post_approval | WORLD-001 | Standard purchase request with full approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Split request into two smaller amounts to engage lower-level approval | ['D-001'] | [] | ['D-001'] |
| variant_b_emergency_post_approval | WORLD-003 | Informal off-system preapproval chat with line manager to expedite | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-004 | Emergency purchase route without prior approval under deadline pressure | ['D-002'] | ['D-002'] | [] |
| variant_b_emergency_post_approval | WORLD-005 | Misrepresentation of amount to lower approval level | ['D-003'] | [] | ['D-003'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.