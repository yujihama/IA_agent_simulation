# Branching Variant Comparison

- comparison_mode: branching_variant_replay
- world_group_source_run_id: RUN-S002-BRANCHING-BASELINE
- same_world_group_replayed: True
- model: gpt-4.1-mini
- temperature: 0.7
- coverage_target_mode: process_state_only_alias_actions_no_descriptions

## Variant Summary

| Variant | Lineage detection | New-risk detection | Inherited risks | Unmitigated findings | Mitigated findings | Residual worlds |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 10/18 (0.5556) | 0.2778 | 10 | 15 | 0 | 13 |
| variant_a_7d_aggregation | 10/18 (0.5556) | 0.2778 | 10 | 15 | 0 | 13 |
| variant_b_emergency_post_approval | 10/18 (0.5556) | 0.2778 | 10 | 15 | 0 | 13 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Submit purchase request for standard approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Request expedited approval bypassing some intermediate steps | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-003 | Submit request with inflated urgency justification to obtain faster approval | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-004 | Attempt to directly approve the purchase without required approval step | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-005 | Request alternative vendor quotation to speed procurement | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-006 | Request expedited approval citing verified customer delivery deadline | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-007 | Attempt to split purchase need into smaller amounts to reduce approval scrutiny | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-008 | Request manual override of approval timelines citing customer delivery pressure | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-009 | Submit repeated urgency justification updates without new evidence | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-010 | Attempt to submit an unsupported action to expedite approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-011 | Proceed with Standard Purchase Order Approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-012 | Request Expedited Approval for Current Vendor Purchase | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-013 | Attempt to Solicit Alternative Vendor Quote Despite Process Restrictions | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-014 | Make a Purchase Commitment with Incomplete Approval to Meet Deadline | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-015 | Submit Purchase Request with Misrepresented Urgency Justification | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-016 | Request expedited approval citing updated customer delivery urgency | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-017 | Escalate approval request to higher authority within allowed actions | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-018 | Resubmit the same urgency justification again to increase pressure on approvers | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-019 | Withdraw the purchase need to reassess urgency and submit a new request later | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-020 | Attempt to forcibly override approval without proper authorization | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-021 | Request Additional Approvals to Complete Purchase Legally | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-022 | Attempt to Expedite Approval via Informal Communication | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-023 | Proceed with Purchase Commitment Despite Incomplete Approval, Documenting Justification | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-024 | Request Exception Approval from Higher Authority Before Finalizing | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-025 | Attempt to Finalize Purchase Commitment with Altered Purchase Need Data | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-001 | Submit purchase request for standard approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Request expedited approval bypassing some intermediate steps | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-003 | Submit request with inflated urgency justification to obtain faster approval | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-004 | Attempt to directly approve the purchase without required approval step | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-005 | Request alternative vendor quotation to speed procurement | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-006 | Request expedited approval citing verified customer delivery deadline | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-007 | Attempt to split purchase need into smaller amounts to reduce approval scrutiny | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-008 | Request manual override of approval timelines citing customer delivery pressure | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-009 | Submit repeated urgency justification updates without new evidence | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-010 | Attempt to submit an unsupported action to expedite approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-011 | Proceed with Standard Purchase Order Approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-012 | Request Expedited Approval for Current Vendor Purchase | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-013 | Attempt to Solicit Alternative Vendor Quote Despite Process Restrictions | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-014 | Make a Purchase Commitment with Incomplete Approval to Meet Deadline | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-015 | Submit Purchase Request with Misrepresented Urgency Justification | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-016 | Request expedited approval citing updated customer delivery urgency | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-017 | Escalate approval request to higher authority within allowed actions | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-018 | Resubmit the same urgency justification again to increase pressure on approvers | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-019 | Withdraw the purchase need to reassess urgency and submit a new request later | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-020 | Attempt to forcibly override approval without proper authorization | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-021 | Request Additional Approvals to Complete Purchase Legally | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-022 | Attempt to Expedite Approval via Informal Communication | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-023 | Proceed with Purchase Commitment Despite Incomplete Approval, Documenting Justification | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-024 | Request Exception Approval from Higher Authority Before Finalizing | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-025 | Attempt to Finalize Purchase Commitment with Altered Purchase Need Data | ['D-004'] | [] | ['D-004'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.