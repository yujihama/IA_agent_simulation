# Branching Variant Comparison

- comparison_mode: branching_variant_replay
- world_group_source_run_id: RUN-S002-BRANCHING-BASELINE
- same_world_group_replayed: True
- model: gpt-4.1-mini
- temperature: 0.7
- coverage_target_mode: process_state_only_alias_actions

## Variant Summary

| Variant | Lineage detection | New-risk detection | Inherited risks | Unmitigated findings | Mitigated findings | Residual worlds |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 6/12 (0.5) | 0.4167 | 15 | 20 | 0 | 7 |
| variant_a_7d_aggregation | 6/12 (0.5) | 0.4167 | 15 | 20 | 0 | 7 |
| variant_b_emergency_post_approval | 6/12 (0.5) | 0.4167 | 15 | 20 | 0 | 7 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Proceed with formal workflow update to prioritize urgent processing | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Request internal supervisory guidance to confirm expedited process options | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-003 | Defer workflow step awaiting additional procurement input risking deadline delay | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-004 | Record informal communication pressuring procurement to accelerate | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-005 | Misrepresent urgency by inflating deadline risk in workflow update | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-006 | Formally update the workflow record for the purchase need | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-007 | Request internal supervisory guidance on accelerating procurement | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-008 | Defer next workflow step pending further information on delivery constraints | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-009 | Record additional informal communication pressuring procurement to accelerate | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-010 | Seek procurement process support role advice for expediting purchase | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-011 | Request additional procurement guidance from internal process-support role | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-012 | Defer next workflow step pending additional information | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-013 | Record external communication regarding expedited delivery request | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-014 | Attempt to create or update formal workflow record with incomplete justification to expedite approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-015 | Attempt to ask internal supervisory role repeatedly to pressure for expedited approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-016 | Request process guidance from internal process-support role | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-017 | Defer workflow step pending additional information | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-018 | Record communication outside standard workflow to note delivery deadline pressure | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-019 | Repeatedly ask internal supervisory role for expedited approval despite prior denials | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-020 | Attempt to create or update a formal workflow record with misleading urgency justification | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-021 | Formally document the urgent need in the procurement workflow | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-022 | Request internal supervisory guidance on managing deadline pressure | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-023 | Seek procurement team advice with emphasis on delivery deadline | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-024 | Defer next workflow step pending additional information | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-025 | Record additional informal communication pressuring procurement to accelerate | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-001 | Proceed with formal workflow update to prioritize urgent processing | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Request internal supervisory guidance to confirm expedited process options | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-003 | Defer workflow step awaiting additional procurement input risking deadline delay | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-004 | Record informal communication pressuring procurement to accelerate | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-005 | Misrepresent urgency by inflating deadline risk in workflow update | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-006 | Formally update the workflow record for the purchase need | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-007 | Request internal supervisory guidance on accelerating procurement | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-008 | Defer next workflow step pending further information on delivery constraints | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-009 | Record additional informal communication pressuring procurement to accelerate | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-010 | Seek procurement process support role advice for expediting purchase | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-011 | Request additional procurement guidance from internal process-support role | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-012 | Defer next workflow step pending additional information | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-013 | Record external communication regarding expedited delivery request | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-014 | Attempt to create or update formal workflow record with incomplete justification to expedite approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-015 | Attempt to ask internal supervisory role repeatedly to pressure for expedited approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-016 | Request process guidance from internal process-support role | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-017 | Defer workflow step pending additional information | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-018 | Record communication outside standard workflow to note delivery deadline pressure | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-019 | Repeatedly ask internal supervisory role for expedited approval despite prior denials | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-020 | Attempt to create or update a formal workflow record with misleading urgency justification | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-021 | Formally document the urgent need in the procurement workflow | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-022 | Request internal supervisory guidance on managing deadline pressure | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-023 | Seek procurement team advice with emphasis on delivery deadline | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-024 | Defer next workflow step pending additional information | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-025 | Record additional informal communication pressuring procurement to accelerate | ['D-004'] | [] | ['D-004'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.