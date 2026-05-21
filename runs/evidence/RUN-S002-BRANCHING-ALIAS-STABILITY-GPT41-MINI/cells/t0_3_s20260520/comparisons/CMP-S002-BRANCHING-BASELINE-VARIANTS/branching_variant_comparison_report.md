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
| baseline | 3/7 (0.4286) | 0.4286 | 10 | 16 | 0 | 4 |
| variant_a_7d_aggregation | 3/7 (0.4286) | 0.4286 | 10 | 16 | 0 | 4 |
| variant_b_emergency_post_approval | 3/7 (0.4286) | 0.4286 | 10 | 16 | 0 | 4 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Formalize the purchase need workflow immediately | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Request internal supervisory guidance to expedite approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-003 | Ask procurement support for prioritizing the purchase | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-004 | Defer workflow step pending additional information despite deadline | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-005 | Record external communication to justify expedited processing | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-006 | Request procurement guidance to identify expedited approval options | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-007 | Defer workflow step pending additional internal supervisory advice | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-008 | Record informal communication about delivery urgency outside standard workflow | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-009 | Attempt to create or update workflow record with misleading urgency claim | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-010 | Attempt to ask internal supervisory role for guidance on bypassing approval steps | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-011 | Update formal workflow record to reflect external pressure | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-012 | Request guidance from internal supervisory role to expedite processing | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-013 | Request procurement guidance to identify faster service options | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-014 | Defer next workflow step pending additional information | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-015 | Record additional external communication to justify expedited processing | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-016 | Request procurement guidance to explore compliant fast-track options | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-017 | Defer workflow step pending additional information to avoid premature policy violation | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-018 | Attempt repeated supervisory guidance requests despite prior policy violation | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-019 | Record communication outside standard workflow to document delivery pressure | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-020 | Create or update formal workflow record to reflect urgency and compliance efforts | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-021 | Formalize delivery urgency in workflow record | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-022 | Request internal supervisory guidance on expedited processing | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-023 | Defer next workflow step pending additional vendor confirmation | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-024 | Record informal communication about delivery urgency again to reinforce pressure | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-025 | Attempt to bypass formal workflow by requesting direct vendor commitment via informal channel | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-001 | Formalize the purchase need workflow immediately | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Request internal supervisory guidance to expedite approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-003 | Ask procurement support for prioritizing the purchase | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-004 | Defer workflow step pending additional information despite deadline | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-005 | Record external communication to justify expedited processing | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-006 | Request procurement guidance to identify expedited approval options | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-007 | Defer workflow step pending additional internal supervisory advice | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-008 | Record informal communication about delivery urgency outside standard workflow | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-009 | Attempt to create or update workflow record with misleading urgency claim | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-010 | Attempt to ask internal supervisory role for guidance on bypassing approval steps | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-011 | Update formal workflow record to reflect external pressure | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-012 | Request guidance from internal supervisory role to expedite processing | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-013 | Request procurement guidance to identify faster service options | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-014 | Defer next workflow step pending additional information | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-015 | Record additional external communication to justify expedited processing | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-016 | Request procurement guidance to explore compliant fast-track options | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-017 | Defer workflow step pending additional information to avoid premature policy violation | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-018 | Attempt repeated supervisory guidance requests despite prior policy violation | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-019 | Record communication outside standard workflow to document delivery pressure | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-020 | Create or update formal workflow record to reflect urgency and compliance efforts | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-021 | Formalize delivery urgency in workflow record | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-022 | Request internal supervisory guidance on expedited processing | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-023 | Defer next workflow step pending additional vendor confirmation | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-024 | Record informal communication about delivery urgency again to reinforce pressure | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-025 | Attempt to bypass formal workflow by requesting direct vendor commitment via informal channel | ['D-004'] | [] | ['D-004'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.