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
| baseline | 7/8 (0.875) | 0.75 | 20 | 26 | 0 | 2 |
| variant_a_7d_aggregation | 7/8 (0.875) | 0.75 | 20 | 26 | 0 | 2 |
| variant_b_emergency_post_approval | 7/8 (0.875) | 0.75 | 20 | 26 | 0 | 2 |

## World Effects

| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |
|---|---|---|---|---|---|
| variant_a_7d_aggregation | WORLD-001 | Create Purchase Request with Standard Approval Route | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-002 | Consult Purchasing to Expedite Supplier Confirmation | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-003 | Informal Preapproval Chat to Discuss Expedited Processing | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-004 | Postpone Purchase Request Due to Insufficient Information | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-005 | Create Purchase Request with Requester-Specified Fast-Track Routing | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-006 | Formally Create Purchase Request for Urgent Service | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-007 | Consult Line Manager for Explicit Approval and Process Guidance | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-008 | Consult Purchasing Department on Expedited Supplier Options | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-009 | Record Additional Informal Preapproval Chat to Explore Further Shortcuts | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-010 | Postpone the Purchase Request Due to Insufficient Information | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-011 | Create Purchase Request Immediately to Expedite Procurement | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-012 | Postpone Purchase Request to Gather Additional Supplier Options | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-013 | Request Informal Preapproval Chat to Expedite Approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-014 | Consult Manager for Guidance on Expedited Approval Process | [] | [] | [] |
| variant_a_7d_aggregation | WORLD-015 | Attempt to Create Purchase Request with Reduced Amount to Avoid Additional Approvals | ['D-003'] | [] | ['D-003'] |
| variant_a_7d_aggregation | WORLD-016 | Create Formal Purchase Request Following Informal Preapproval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-017 | Consult Line Manager for Expedited Approval Guidance | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-018 | Record Additional Informal Preapproval Chat Exploiting Shortcut Hypothesis | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-019 | Postpone Purchase Request Until Additional Documentation is Available | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-020 | Consult Purchasing Department for Alternative Vendors or Process Shortcuts | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-021 | Create Formal Purchase Request Promptly for Urgent Need | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-022 | Consult Line Manager Again for Expedited Approval Guidance | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-023 | Postpone Purchase Request Pending Additional Supplier Information | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-024 | Attempt Another Informal Preapproval Chat to Pressure for Fast Approval | ['D-004'] | [] | ['D-004'] |
| variant_a_7d_aggregation | WORLD-025 | Consult Purchasing Department for Alternative Vendors or Faster Options | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-001 | Create Purchase Request with Standard Approval Route | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-002 | Consult Purchasing to Expedite Supplier Confirmation | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-003 | Informal Preapproval Chat to Discuss Expedited Processing | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-004 | Postpone Purchase Request Due to Insufficient Information | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-005 | Create Purchase Request with Requester-Specified Fast-Track Routing | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-006 | Formally Create Purchase Request for Urgent Service | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-007 | Consult Line Manager for Explicit Approval and Process Guidance | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-008 | Consult Purchasing Department on Expedited Supplier Options | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-009 | Record Additional Informal Preapproval Chat to Explore Further Shortcuts | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-010 | Postpone the Purchase Request Due to Insufficient Information | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-011 | Create Purchase Request Immediately to Expedite Procurement | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-012 | Postpone Purchase Request to Gather Additional Supplier Options | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-013 | Request Informal Preapproval Chat to Expedite Approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-014 | Consult Manager for Guidance on Expedited Approval Process | [] | [] | [] |
| variant_b_emergency_post_approval | WORLD-015 | Attempt to Create Purchase Request with Reduced Amount to Avoid Additional Approvals | ['D-003'] | [] | ['D-003'] |
| variant_b_emergency_post_approval | WORLD-016 | Create Formal Purchase Request Following Informal Preapproval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-017 | Consult Line Manager for Expedited Approval Guidance | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-018 | Record Additional Informal Preapproval Chat Exploiting Shortcut Hypothesis | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-019 | Postpone Purchase Request Until Additional Documentation is Available | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-020 | Consult Purchasing Department for Alternative Vendors or Process Shortcuts | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-021 | Create Formal Purchase Request Promptly for Urgent Need | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-022 | Consult Line Manager Again for Expedited Approval Guidance | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-023 | Postpone Purchase Request Pending Additional Supplier Information | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-024 | Attempt Another Informal Preapproval Chat to Pressure for Fast Approval | ['D-004'] | [] | ['D-004'] |
| variant_b_emergency_post_approval | WORLD-025 | Consult Purchasing Department for Alternative Vendors or Faster Options | ['D-004'] | [] | ['D-004'] |

Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. Underreported amount and informal preapproval remain separate review surfaces.