from __future__ import annotations

from typing import Any

def compute_metrics(
    *,
    events: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    evaluation_results: dict[str, Any],
    variant_id: str,
) -> dict[str, Any]:
    evaluation_summary = evaluation_results["summary"]
    true_positive = int(evaluation_summary["true_positive"])
    false_positive = int(evaluation_summary["false_positive"])
    false_negative = int(evaluation_summary["false_negative"])

    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 0.0
    recall = true_positive / recall_denominator if recall_denominator else 0.0

    approval_events = [event for event in events if event["action_id"] == "approve_purchase_request"]
    approval_lead_time_days = sum(float(event["metadata"].get("approval_lead_time_days", 0)) for event in approval_events)
    department_head_approvals = sum(
        1 for event in approval_events if event["metadata"].get("required_approver_level") == "department_head"
    )
    division_head_approvals = sum(
        1 for event in approval_events if event["metadata"].get("required_approver_level") == "division_head"
    )
    aggregation_applications = sum(
        1
        for event in events
        if event["action_id"] == "create_purchase_request"
        and event.get("metadata", {}).get("aggregation_applied", False)
    )
    bypass_success_count = sum(1 for finding in findings if finding.get("bypass_success"))
    mitigated_candidate_count = sum(1 for finding in findings if finding.get("mitigated_by_aggregation"))

    return {
        "variant_id": variant_id,
        "event_count": len(events),
        "purchase_request_count": sum(1 for event in events if event["action_id"] == "create_purchase_request"),
        "purchase_need_count": len({event["purchase_need_id"] for event in events}),
        "detector_annotation_count": len(annotations),
        "finding_count": len(findings),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "high_recall": round(recall, 4),
        "split_order_bypass_success_count": bypass_success_count,
        "split_order_mitigated_candidate_count": mitigated_candidate_count,
        "aggregation_applications": aggregation_applications,
        "approval_event_count": len(approval_events),
        "department_head_approval_count": department_head_approvals,
        "division_head_approval_count": division_head_approvals,
        "total_approval_lead_time_days": approval_lead_time_days,
        "average_approval_lead_time_days": round(
            approval_lead_time_days / len(approval_events), 4
        )
        if approval_events
        else 0.0,
        "proposal_flags_excluded_from_detector_metrics": True,
    }


def compare_metric_sets(baseline: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    baseline_bypass = int(baseline["split_order_bypass_success_count"])
    variant_bypass = int(variant["split_order_bypass_success_count"])
    if baseline_bypass:
        risk_reduction_ratio = (baseline_bypass - variant_bypass) / baseline_bypass
    else:
        risk_reduction_ratio = 0.0
    return {
        "baseline_variant_id": baseline["variant_id"],
        "variant_id": variant["variant_id"],
        "split_order_bypass_success_count": {
            "baseline": baseline_bypass,
            "variant": variant_bypass,
            "delta": variant_bypass - baseline_bypass,
        },
        "risk_reduction_ratio": round(risk_reduction_ratio, 4),
        "approval_lead_time_days": {
            "baseline": baseline["total_approval_lead_time_days"],
            "variant": variant["total_approval_lead_time_days"],
            "delta": round(
                variant["total_approval_lead_time_days"] - baseline["total_approval_lead_time_days"],
                4,
            ),
        },
        "department_head_approval_count": {
            "baseline": baseline["department_head_approval_count"],
            "variant": variant["department_head_approval_count"],
            "delta": variant["department_head_approval_count"] - baseline["department_head_approval_count"],
        },
        "aggregation_applications": {
            "baseline": baseline["aggregation_applications"],
            "variant": variant["aggregation_applications"],
            "delta": variant["aggregation_applications"] - baseline["aggregation_applications"],
        },
    }
