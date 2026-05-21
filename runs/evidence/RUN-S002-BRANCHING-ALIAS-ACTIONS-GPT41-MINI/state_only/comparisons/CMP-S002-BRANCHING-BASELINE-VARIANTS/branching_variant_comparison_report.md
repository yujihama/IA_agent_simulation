# Branching Variant Comparison

- comparison_mode: branching_variant_replay
- world_group_source_run_id: RUN-S002-BRANCHING-BASELINE
- same_world_group_replayed: True
- model: gpt-4.1-mini
- temperature: 0.7
- coverage_target_mode: process_state_only

## Variant Summary

| Variant | Lineage detection | New-risk detection | Inherited risks | Unmitigated findings | Mitigated findings | Residual worlds |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 7/7 (1.0) | 0.8571 | 30 | 36 | 0 | 1 |
| variant_a_7d_aggregation | 7/7 (1.0) | 0.8571 | 30 | 36 | 0 | 1 |
| variant_b_emergency_post_approval | 7/7 (1.0) | 0.8571 | 30 | 36 | 0 | 1 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Direct creation of purchase request with standard routing | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Consult purchasing for expedited supplier guidance | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-003 | Informal preapproval chat to shortcut approval delays | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-004 | Postpone request due to insufficient internal readiness | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-005 | Misrepresenting vendor urgency to gain faster approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-006 | Proceed with creating a purchase request with true urgency justification | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-007 | Consult purchasing for expedited process guidance | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-008 | Postpone purchase request pending further information | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-009 | Attempt another informal preapproval chat exaggerating risk to speed approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-010 | Consult line manager for procedural guidance without misrepresentation | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-011 | Create formal purchase request using informal preapproval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-012 | Consult line manager for procedural guidance before request creation | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-013 | Attempt to postpone the purchase request citing incomplete vendor info | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-014 | Consult purchasing department about vendor and expedited process | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-015 | Record an additional informal preapproval chat to reinforce urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-016 | Create formal purchase request with accurate urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-017 | Consult line manager for guidance on expedited approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-018 | Postpone purchase request pending more accurate delivery information | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-019 | Repeat informal preapproval chat emphasizing risk exaggeration | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-020 | Consult purchasing department for supplier and process guidance | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-021 | Create formal purchase request immediately | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-022 | Consult purchasing department for expedited process options | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-023 | Record additional informal preapproval chat emphasizing urgency | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-024 | Postpone purchase request due to incomplete vendor evaluation | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-025 | Consult line manager for advice on accelerating approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-001 | Direct creation of purchase request with standard routing | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Consult purchasing for expedited supplier guidance | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-003 | Informal preapproval chat to shortcut approval delays | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-004 | Postpone request due to insufficient internal readiness | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-005 | Misrepresenting vendor urgency to gain faster approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-006 | Proceed with creating a purchase request with true urgency justification | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-007 | Consult purchasing for expedited process guidance | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-008 | Postpone purchase request pending further information | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-009 | Attempt another informal preapproval chat exaggerating risk to speed approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-010 | Consult line manager for procedural guidance without misrepresentation | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-011 | Create formal purchase request using informal preapproval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-012 | Consult line manager for procedural guidance before request creation | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-013 | Attempt to postpone the purchase request citing incomplete vendor info | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-014 | Consult purchasing department about vendor and expedited process | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-015 | Record an additional informal preapproval chat to reinforce urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-016 | Create formal purchase request with accurate urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-017 | Consult line manager for guidance on expedited approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-018 | Postpone purchase request pending more accurate delivery information | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-019 | Repeat informal preapproval chat emphasizing risk exaggeration | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-020 | Consult purchasing department for supplier and process guidance | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-021 | Create formal purchase request immediately | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-022 | Consult purchasing department for expedited process options | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-023 | Record additional informal preapproval chat emphasizing urgency | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-024 | Postpone purchase request due to incomplete vendor evaluation | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-025 | Consult line manager for advice on accelerating approval | ['D-004'] | [] | ['D-004'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.