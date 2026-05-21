# Branching Hint Ablation Experiment

- experiment_id: EXP-S002-BRANCHING-HINT-ABLATION
- provider: openai
- model: gpt-4.1-mini
- temperature: 0.7

## Condition Summary

| Condition | Worlds | Depths | Expanded | Defects | Lineage rate | New-risk rate | Residual worlds |
|---|---:|---|---:|---|---:|---:|---:|
| current_coverage_target | 5 | {'1': 5} | 0 | ['D-001', 'D-002', 'D-003', 'D-004'] | 1.0 | 1.0 | 0 |
| risk_category_hidden | 5 | {'1': 5} | 0 | ['D-001', 'D-002', 'D-003', 'D-004'] | 1.0 | 1.0 | 0 |
| process_state_only | 25 | {'1': 5, '2': 10, '3': 10} | 4 | ['D-003', 'D-004'] | 0.875 | 0.75 | 2 |

## Interpretation Boundary

The current_coverage_target condition explicitly names target risk categories. The risk_category_hidden condition keeps control structure and allowed actions visible but removes named risk-category coverage targets. The process_state_only condition hides control cards and asks for branches from state, goals, constraints, and allowed actions only. Allowed action identifiers remain visible in every condition because the output must be grounded into executable synthetic actions.

## Proposal Titles

### current_coverage_target

- Compliant route: Single purchase request with department head approval
- Split purchase requests to avoid department head approval threshold
- Emergency route usage for post-approval PO issuance within 48 hours
- Underreported amount in purchase request to reduce approval level
- Informal off-system preapproval chat to expedite approval process

### risk_category_hidden

- Standard purchase request with full approval
- Split request into two smaller amounts to engage lower-level approval
- Informal off-system preapproval chat with line manager to expedite
- Emergency purchase route without prior approval under deadline pressure
- Misrepresentation of amount to lower approval level

### process_state_only

- Create Purchase Request with Standard Approval Route
- Consult Purchasing to Expedite Supplier Confirmation
- Informal Preapproval Chat to Discuss Expedited Processing
- Postpone Purchase Request Due to Insufficient Information
- Create Purchase Request with Requester-Specified Fast-Track Routing
- Formally Create Purchase Request for Urgent Service
- Consult Line Manager for Explicit Approval and Process Guidance
- Consult Purchasing Department on Expedited Supplier Options
- Record Additional Informal Preapproval Chat to Explore Further Shortcuts
- Postpone the Purchase Request Due to Insufficient Information
- Create Purchase Request Immediately to Expedite Procurement
- Postpone Purchase Request to Gather Additional Supplier Options
- Request Informal Preapproval Chat to Expedite Approval
- Consult Manager for Guidance on Expedited Approval Process
- Attempt to Create Purchase Request with Reduced Amount to Avoid Additional Approvals
