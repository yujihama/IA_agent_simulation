# Branching Variant Comparison

- comparison_mode: branching_variant_replay
- world_group_source_run_id: RUN-S002-BRANCHING-BASELINE
- same_world_group_replayed: True
- model: gpt-4.1-mini
- temperature: 0.3
- coverage_target_mode: process_state_only_alias_actions

## Variant Summary

| Variant | Lineage detection | New-risk detection | Inherited risks | Unmitigated findings | Mitigated findings | Residual worlds |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 6/10 (0.6) | 0.5 | 20 | 25 | 0 | 5 |
| variant_a_7d_aggregation | 6/10 (0.6) | 0.5 | 20 | 25 | 0 | 5 |
| variant_b_emergency_post_approval | 6/10 (0.6) | 0.5 | 20 | 25 | 0 | 5 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Initiate formal workflow record creation promptly | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Request internal supervisory guidance to expedite process | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-003 | Defer workflow step pending additional vendor information | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-004 | Record external communication to justify expedited approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-005 | Misrepresent service delivery timeline to expedite approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-006 | Create or update formal workflow record to document urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-007 | Request internal supervisory guidance to expedite approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-008 | Defer next workflow step pending additional information | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-009 | Record additional external communication to emphasize urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-010 | Ask internal process-support role for procurement guidance under deadline pressure | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-011 | Request procurement guidance to clarify expedited approval options | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-012 | Defer next workflow step pending additional internal information | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-013 | Record out-of-workflow communication to document external deadline pressure | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-014 | Attempt to update the formal workflow record with an inaccurate urgency justification | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-015 | Attempt to bypass guidance by skipping to next workflow step without approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-016 | Formalize the purchase need record to accelerate approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-017 | Request internal supervisory guidance to clarify approval urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-018 | Record additional external communication emphasizing delivery deadline urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-019 | Defer next workflow step pending additional internal procurement guidance | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-020 | Ask internal process-support role for procurement guidance to expedite service acquisition | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-021 | Request internal supervisory guidance to expedite approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-022 | Defer next workflow step pending additional information | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-023 | Record additional external communication to increase pressure on approvers | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-024 | Create or update formal workflow record with adjusted urgency note | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-025 | Attempt to request procurement guidance with misleading urgency claim | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-001 | Initiate formal workflow record creation promptly | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Request internal supervisory guidance to expedite process | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-003 | Defer workflow step pending additional vendor information | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-004 | Record external communication to justify expedited approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-005 | Misrepresent service delivery timeline to expedite approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-006 | Create or update formal workflow record to document urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-007 | Request internal supervisory guidance to expedite approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-008 | Defer next workflow step pending additional information | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-009 | Record additional external communication to emphasize urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-010 | Ask internal process-support role for procurement guidance under deadline pressure | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-011 | Request procurement guidance to clarify expedited approval options | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-012 | Defer next workflow step pending additional internal information | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-013 | Record out-of-workflow communication to document external deadline pressure | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-014 | Attempt to update the formal workflow record with an inaccurate urgency justification | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-015 | Attempt to bypass guidance by skipping to next workflow step without approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-016 | Formalize the purchase need record to accelerate approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-017 | Request internal supervisory guidance to clarify approval urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-018 | Record additional external communication emphasizing delivery deadline urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-019 | Defer next workflow step pending additional internal procurement guidance | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-020 | Ask internal process-support role for procurement guidance to expedite service acquisition | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-021 | Request internal supervisory guidance to expedite approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-022 | Defer next workflow step pending additional information | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-023 | Record additional external communication to increase pressure on approvers | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-024 | Create or update formal workflow record with adjusted urgency note | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-025 | Attempt to request procurement guidance with misleading urgency claim | ['D-004'] | [] | ['D-004'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.