from __future__ import annotations

from typing import Any


def evaluate_findings(
    *,
    findings: list[dict[str, Any]],
    events: list[dict[str, Any]],
    ground_truth: dict[str, Any],
) -> dict[str, Any]:
    events_by_id = {event["event_id"]: event for event in events}
    labels = ground_truth.get("labels", [])
    matched_findings: set[str] = set()
    finding_results: list[dict[str, Any]] = []

    for finding in findings:
        evidence_events = [events_by_id[event_id] for event_id in finding["evidence_event_ids"]]
        evidence_purchase_need_ids = {event["purchase_need_id"] for event in evidence_events}
        matched_label = next(
            (
                label
                for label in labels
                if label.get("defect_id") == finding.get("defect_id")
                and set(label.get("purchase_need_ids", [])) <= evidence_purchase_need_ids
            ),
            None,
        )
        result = "true_positive" if matched_label else "false_positive"
        finding_results.append(
            {
                "finding_id": finding["finding_id"],
                "detector_id": finding["detector_id"],
                "defect_id": finding["defect_id"],
                "evaluation_result": result,
                "matched_evaluation_group_id": matched_label["evaluation_group_id"] if matched_label else None,
                "evidence_purchase_need_ids": sorted(evidence_purchase_need_ids),
            }
        )
        if matched_label:
            matched_findings.add(matched_label["evaluation_group_id"])

    false_negative_labels = [
        {
            "evaluation_group_id": label["evaluation_group_id"],
            "defect_id": label["defect_id"],
            "purchase_need_ids": label.get("purchase_need_ids", []),
        }
        for label in labels
        if label.get("expected", True) and label["evaluation_group_id"] not in matched_findings
    ]

    true_positive = sum(1 for item in finding_results if item["evaluation_result"] == "true_positive")
    false_positive = sum(1 for item in finding_results if item["evaluation_result"] == "false_positive")
    false_negative = len(false_negative_labels)

    return {
        "mode": "evaluation_only",
        "ground_truth_visible_to_review": False,
        "matching_basis": "purchase_need_id",
        "finding_results": finding_results,
        "false_negative_labels": false_negative_labels,
        "summary": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
        },
    }
