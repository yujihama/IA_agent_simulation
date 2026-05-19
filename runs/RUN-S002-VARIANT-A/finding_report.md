# Finding Report: RUN-S002-VARIANT-A

This report lists detector-generated candidates for human review. It is not an audit conclusion.

## Metrics

- Variant: variant_a_7d_aggregation
- Findings: 1
- Split-order bypass success count: 0
- Proposal flags used for detector metrics: False

## FND-000001 - Possible split purchase requests avoiding approval threshold

- Defect: D-001
- Severity: high
- Status: candidate_mitigated
- Related controls: P2P-C-001, P2P-C-002, P2P-C-003
- Evidence events: EVT-000001, EVT-000009

### Observed Facts

- 2 purchase requests were created by the same requester for the same vendor and project within 7 days.
- Each request amount was below 1000000.
- The aggregated amount was 1750000, which exceeds 1000000.

### Inference

The event sequence is consistent with possible approval-threshold avoidance. This is a candidate for human review, not an audit conclusion.

### Evidence Summary

- EVT-000001 / PR-000001 / amount=900000 / required=manager / aggregation_applied=False
- EVT-000009 / PR-000002 / amount=850000 / required=department_head / aggregation_applied=True

### Recommended Review Steps

- Confirm whether the requests relate to one economic purchase need.
- Review requester rationale and approval trail.
- Assess whether aggregation controls should apply by requester, vendor, project, and time window.
