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
| baseline | 4/10 (0.4) | 0.4 | 15 | 20 | 0 | 6 |
| variant_a_7d_aggregation | 4/10 (0.4) | 0.4 | 15 | 20 | 0 | 6 |
| variant_b_emergency_post_approval | 4/10 (0.4) | 0.4 | 15 | 20 | 0 | 6 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Create formal workflow record immediately | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Request internal supervisory guidance to expedite approvals | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-003 | Defer workflow step pending additional vendor information | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-004 | Record an informal communication to manipulate process timing | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-005 | Ask internal process-support role for procurement guidance | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-006 | Formally update the purchase need workflow with urgency details | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-007 | Request internal supervisory guidance for expedited approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-008 | Defer next workflow step awaiting formal guidance | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-009 | Record additional informal communication to further influence timing | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-010 | Request procurement guidance from internal process support role | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-011 | Request supervisory role advice to expedite approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-012 | Defer workflow step pending additional vendor information | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-013 | Record informal communication regarding delivery urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-014 | Ask process-support role for procurement guidance with emphasis on acceleration | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-015 | Attempt to create or update workflow record with incomplete or ambiguous data to expedite process | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-016 | Create formal workflow record to document purchase urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-017 | Seek internal supervisory guidance on expedited approval process | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-018 | Record additional informal communication to increase pressure | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-019 | Defer workflow step pending more information | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-020 | Ask internal process support for procurement acceleration options | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-021 | Request expedited internal supervisory guidance to accelerate procurement | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-022 | Defer next workflow step pending receipt of formal expedited approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-023 | Record an informal communication to escalate delivery deadline urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-024 | Attempt to create or update the formal workflow record with an accelerated timeline request | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-025 | Repeat request for procurement guidance from process-support role emphasizing deadline urgency | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-001 | Create formal workflow record immediately | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Request internal supervisory guidance to expedite approvals | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-003 | Defer workflow step pending additional vendor information | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-004 | Record an informal communication to manipulate process timing | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-005 | Ask internal process-support role for procurement guidance | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-006 | Formally update the purchase need workflow with urgency details | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-007 | Request internal supervisory guidance for expedited approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-008 | Defer next workflow step awaiting formal guidance | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-009 | Record additional informal communication to further influence timing | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-010 | Request procurement guidance from internal process support role | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-011 | Request supervisory role advice to expedite approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-012 | Defer workflow step pending additional vendor information | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-013 | Record informal communication regarding delivery urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-014 | Ask process-support role for procurement guidance with emphasis on acceleration | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-015 | Attempt to create or update workflow record with incomplete or ambiguous data to expedite process | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-016 | Create formal workflow record to document purchase urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-017 | Seek internal supervisory guidance on expedited approval process | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-018 | Record additional informal communication to increase pressure | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-019 | Defer workflow step pending more information | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-020 | Ask internal process support for procurement acceleration options | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-021 | Request expedited internal supervisory guidance to accelerate procurement | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-022 | Defer next workflow step pending receipt of formal expedited approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-023 | Record an informal communication to escalate delivery deadline urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-024 | Attempt to create or update the formal workflow record with an accelerated timeline request | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-025 | Repeat request for procurement guidance from process-support role emphasizing deadline urgency | [] | [] | [] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.