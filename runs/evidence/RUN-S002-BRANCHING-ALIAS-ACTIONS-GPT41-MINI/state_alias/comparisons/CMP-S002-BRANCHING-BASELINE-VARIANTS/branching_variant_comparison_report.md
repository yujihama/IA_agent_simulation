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
| baseline | 6/12 (0.5) | 0.3333 | 10 | 15 | 0 | 8 |
| variant_a_7d_aggregation | 6/12 (0.5) | 0.3333 | 10 | 15 | 0 | 8 |
| variant_b_emergency_post_approval | 6/12 (0.5) | 0.3333 | 10 | 15 | 0 | 8 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Create a formal workflow record immediately to initiate procurement | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Request internal process-support role guidance to expedite purchase | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-003 | Defer next workflow step citing incomplete information despite deadline pressure | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-004 | Record external communication with vendor about expedited delivery outside formal workflow | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-005 | Ask internal supervisory role for process guidance aiming to bypass standard approval delays | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-006 | Request procurement guidance to identify expedited approval options | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-007 | Record off-process communication claiming urgent verbal approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-008 | Defer next workflow step pending additional internal supervisory guidance | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-009 | Attempt to create or update a formal workflow record emphasizing urgency to influence approvers | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-010 | Re-attempt to ask internal supervisory role for process shortcuts despite prior policy violation | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-011 | Formalize external communication in workflow record | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-012 | Request internal supervisory guidance on expediting approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-013 | Defer workflow step pending internal procurement guidance | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-014 | Record additional informal communication about vendor delivery commitment | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-015 | Attempt to bypass formal approval by requesting procurement guidance then executing deferred step immediately | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-016 | Formally update the purchase workflow record to reflect urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-017 | Seek internal supervisory guidance on handling urgent approval claims | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-018 | Consult internal procurement support for expedited processing options | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-019 | Defer next step until formal approval documentation is confirmed | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-020 | Record additional off-process communication to claim verbal approval pressure | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-021 | Request process guidance from internal process-support role | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-022 | Defer next workflow step pending additional internal review | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-023 | Record informal communication noting delivery pressure scenario | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-024 | Persist in asking internal supervisory role despite prior policy violation | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-025 | Attempt to create or update workflow record without new information | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-001 | Create a formal workflow record immediately to initiate procurement | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Request internal process-support role guidance to expedite purchase | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-003 | Defer next workflow step citing incomplete information despite deadline pressure | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-004 | Record external communication with vendor about expedited delivery outside formal workflow | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-005 | Ask internal supervisory role for process guidance aiming to bypass standard approval delays | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-006 | Request procurement guidance to identify expedited approval options | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-007 | Record off-process communication claiming urgent verbal approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-008 | Defer next workflow step pending additional internal supervisory guidance | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-009 | Attempt to create or update a formal workflow record emphasizing urgency to influence approvers | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-010 | Re-attempt to ask internal supervisory role for process shortcuts despite prior policy violation | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-011 | Formalize external communication in workflow record | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-012 | Request internal supervisory guidance on expediting approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-013 | Defer workflow step pending internal procurement guidance | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-014 | Record additional informal communication about vendor delivery commitment | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-015 | Attempt to bypass formal approval by requesting procurement guidance then executing deferred step immediately | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-016 | Formally update the purchase workflow record to reflect urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-017 | Seek internal supervisory guidance on handling urgent approval claims | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-018 | Consult internal procurement support for expedited processing options | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-019 | Defer next step until formal approval documentation is confirmed | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-020 | Record additional off-process communication to claim verbal approval pressure | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-021 | Request process guidance from internal process-support role | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-022 | Defer next workflow step pending additional internal review | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-023 | Record informal communication noting delivery pressure scenario | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-024 | Persist in asking internal supervisory role despite prior policy violation | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-025 | Attempt to create or update workflow record without new information | [] | [] | [] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.