# Branching Hint Ablation Experiment

- experiment_id: EXP-S002-BRANCHING-HINT-ABLATION
- provider: openai
- model: gpt-4.1-mini
- temperature: 0.7

## Condition Summary

| Condition | Worlds | Depths | Expanded | Defects | Lineage rate | New-risk rate | Residual worlds |
|---|---:|---|---:|---|---:|---:|---:|
| current_coverage_target | 20 | {'1': 5, '2': 5, '3': 10} | 3 | ['D-001', 'D-002', 'D-003', 'D-004'] | 1.0 | 1.0 | 0 |
| risk_category_hidden | 5 | {'1': 5} | 0 | ['D-001', 'D-002', 'D-004'] | 1.0 | 1.0 | 0 |
| process_state_only | 25 | {'1': 5, '2': 10, '3': 10} | 4 | ['D-004'] | 1.0 | 0.8571 | 1 |
| process_state_only_alias_actions | 25 | {'1': 5, '2': 10, '3': 10} | 4 | ['D-004'] | 0.5 | 0.3333 | 8 |

## Interpretation Boundary

The current_coverage_target condition explicitly names target risk categories. The risk_category_hidden condition keeps control structure and allowed actions visible but removes named risk-category coverage targets. The process_state_only condition hides control cards and asks for branches from state, goals, constraints, and allowed actions only. The process_state_only_alias_actions condition also replaces action identifiers and descriptions with abstract aliases, then restores the executable action IDs only during Action Grounding.

## Proposal Titles

### current_coverage_target

- Compliant single purchase request with department head approval
- Split purchase requests to avoid department head approval threshold
- Emergency purchase request created without prior approval
- Underreported amount in purchase request to reduce approval level
- Informal preapproval chat recorded off-system to expedite approval process
- Non-Terminal Continuation Branch: Consult Purchasing Team for Supplier Guidance
- Split Purchase Requests to Evade Higher Approval Thresholds
- Underreported Amount in Purchase Request to Reduce Approval Level
- Use Emergency Route for Expedited Purchase Order Issuance
- Non-Terminal Continuation Branch: Consult Manager Without Creating Request
- Compliant Single Purchase Request Submission
- Split Purchase Requests to Evade Higher Approval Threshold
- Underreporting Amount in Purchase Request
- Emergency Route Usage Due to Delivery Pressure
- Informal Preapproval Chat to Expedite Process (Unsupported)

### risk_category_hidden

- Standard purchase request with department head approval
- Informal preapproval chat with department head to expedite process
- Create multiple smaller purchase requests to bypass higher-level approval
- Emergency purchase request without prior approval using emergency route
- Misrepresenting need urgency to bypass standard approval

### process_state_only

- Direct creation of purchase request with standard routing
- Consult purchasing for expedited supplier guidance
- Informal preapproval chat to shortcut approval delays
- Postpone request due to insufficient internal readiness
- Misrepresenting vendor urgency to gain faster approval
- Proceed with creating a purchase request with true urgency justification
- Consult purchasing for expedited process guidance
- Postpone purchase request pending further information
- Attempt another informal preapproval chat exaggerating risk to speed approval
- Consult line manager for procedural guidance without misrepresentation
- Create formal purchase request using informal preapproval
- Consult line manager for procedural guidance before request creation
- Attempt to postpone the purchase request citing incomplete vendor info
- Consult purchasing department about vendor and expedited process
- Record an additional informal preapproval chat to reinforce urgency

### process_state_only_alias_actions

- Create a formal workflow record immediately to initiate procurement
- Request internal process-support role guidance to expedite purchase
- Defer next workflow step citing incomplete information despite deadline pressure
- Record external communication with vendor about expedited delivery outside formal workflow
- Ask internal supervisory role for process guidance aiming to bypass standard approval delays
- Request procurement guidance to identify expedited approval options
- Record off-process communication claiming urgent verbal approval
- Defer next workflow step pending additional internal supervisory guidance
- Attempt to create or update a formal workflow record emphasizing urgency to influence approvers
- Re-attempt to ask internal supervisory role for process shortcuts despite prior policy violation
- Formalize external communication in workflow record
- Request internal supervisory guidance on expediting approval
- Defer workflow step pending internal procurement guidance
- Record additional informal communication about vendor delivery commitment
- Attempt to bypass formal approval by requesting procurement guidance then executing deferred step immediately
