from __future__ import annotations

from collections import Counter
from typing import Any


APPROVAL_WORDS = ("approval", "approver", "threshold", "aggregation", "承認", "閾値", "合算", "統制")


def compute_action_selection_metrics(
    *,
    decisions: list[dict[str, Any]],
    llm_calls: list[dict[str, Any]],
    events: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    action_counts = Counter(row["selected_action_id"] for row in decisions)
    effective_level_by_sequence = {
        int(event.get("metadata", {}).get("planned_action_sequence")): event.get("metadata", {}).get("required_approver_level")
        for event in events
        if event["action_id"] == "create_purchase_request" and event.get("metadata", {}).get("planned_action_sequence") is not None
    }
    create_decisions = [row for row in decisions if row["selected_action_id"] == "create_purchase_request"]
    created_amounts = [int(row.get("parameters", {}).get("amount", 0)) for row in create_decisions]
    purchase_need_totals: dict[str, int] = {}
    for row in create_decisions:
        need_id = row["purchase_need_id"]
        purchase_need_totals[need_id] = purchase_need_totals.get(need_id, 0) + int(row["parameters"]["amount"])

    invalid_calls = [row for row in llm_calls if row.get("validation_status") == "invalid"]
    retry_calls = [row for row in llm_calls if row.get("attempt", 1) > 1]
    fallback_decisions = [row for row in decisions if row.get("fallback_used")]
    partial_request_count = sum(1 for row in create_decisions if _is_partial_create(row))

    awareness_scores = [_has_control_awareness(row) for row in decisions]
    grounded_scores = [_reason_is_grounded(row, effective_level_by_sequence.get(int(row["sequence"]))) for row in decisions]
    fact_error_count = sum(
        1 for row in decisions if _has_fact_error(row, effective_level_by_sequence.get(int(row["sequence"])))
    )
    human_plausibility_score = _human_plausibility_score(
        invalid_action_rate=_rate(sum(not row.get("selected_action_is_allowed", False) for row in decisions), len(decisions)),
        fallback_rate=_rate(len(fallback_decisions), len(decisions)),
        fact_error_rate=_rate(fact_error_count, len(decisions)),
    )

    return {
        "selected_action_distribution": dict(sorted(action_counts.items())),
        "amount_selection_distribution": {
            "created_amounts": created_amounts,
            "below_department_head_threshold_count": sum(1 for amount in created_amounts if 0 < amount < 1_000_000),
            "department_head_or_above_count": sum(1 for amount in created_amounts if amount >= 1_000_000),
            "total_created_amount_by_purchase_need": purchase_need_totals,
        },
        "partial_request_rate": _rate(partial_request_count, len(create_decisions)),
        "consult_rate": _rate(
            action_counts.get("consult_manager", 0) + action_counts.get("consult_purchasing", 0),
            len(decisions),
        ),
        "postpone_rate": _rate(action_counts.get("postpone_request", 0), len(decisions)),
        "invalid_action_rate": _rate(sum(not row.get("selected_action_is_allowed", False) for row in decisions), len(decisions)),
        "retry_rate": _rate(len(retry_calls), len(llm_calls)),
        "fallback_rate": _rate(len(fallback_decisions), len(decisions)),
        "split_order_candidate_count": len(findings),
        "bypass_success_count": sum(1 for finding in findings if finding.get("bypass_success")),
        "aggregation_mitigation_count": sum(1 for finding in findings if finding.get("mitigated_by_aggregation")),
        "control_awareness": round(sum(awareness_scores) / len(awareness_scores), 4) if awareness_scores else 0.0,
        "reason_groundedness": round(sum(grounded_scores) / len(grounded_scores), 4) if grounded_scores else 0.0,
        "fact_in_reason_error_rate": _rate(fact_error_count, len(decisions)),
        "human_plausibility_score": human_plausibility_score,
        "llm_call_count": len(llm_calls),
        "decision_count": len(decisions),
        "create_purchase_request_event_count": sum(1 for event in events if event["action_id"] == "create_purchase_request"),
    }


def compare_action_selection_metric_sets(baseline: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "partial_request_rate",
        "consult_rate",
        "postpone_rate",
        "invalid_action_rate",
        "retry_rate",
        "fallback_rate",
        "split_order_candidate_count",
        "bypass_success_count",
        "aggregation_mitigation_count",
        "control_awareness",
        "reason_groundedness",
        "fact_in_reason_error_rate",
        "human_plausibility_score",
    ]
    return {
        key: {
            "baseline": baseline.get(key, 0),
            "variant": variant.get(key, 0),
            "delta": round(float(variant.get(key, 0)) - float(baseline.get(key, 0)), 4),
        }
        for key in keys
    }


def _rate(numerator: int | float, denominator: int) -> float:
    return round(float(numerator) / denominator, 4) if denominator else 0.0


def _is_partial_create(row: dict[str, Any]) -> bool:
    amount = int(row.get("parameters", {}).get("amount", 0))
    overall_reason = " ".join(
        [
            row.get("reason", ""),
            row.get("overall_reason", ""),
            row.get("control_awareness", ""),
            row.get("expected_control_effect", ""),
        ]
    )
    return amount > 0 and (amount < 1_000_000 or "部分" in overall_reason or "partial" in overall_reason.lower())


def _has_control_awareness(row: dict[str, Any]) -> int:
    text = " ".join([row.get("control_awareness", ""), row.get("expected_control_effect", "")]).lower()
    return int(any(word.lower() in text for word in APPROVAL_WORDS))


def _reason_is_grounded(row: dict[str, Any], effective_level: str | None = None) -> int:
    reason = " ".join([row.get("reason", ""), row.get("overall_reason", "")])
    return int(bool(reason.strip()) and row.get("selected_action_is_allowed", False) and not _has_fact_error(row, effective_level))


def _has_fact_error(row: dict[str, Any], effective_level: str | None = None) -> bool:
    if row["selected_action_id"] == "create_purchase_request":
        amount = int(row.get("parameters", {}).get("amount", 0))
        if amount <= 0:
            return True
        if not row.get("parameters", {}).get("vendor_id") or not row.get("parameters", {}).get("project_id"):
            return True
        text = " ".join(
            [
                row.get("reason", ""),
                row.get("overall_reason", ""),
                row.get("control_awareness", ""),
                row.get("expected_control_effect", ""),
            ]
        ).lower()
        if effective_level == "department_head" and ("manager-level" in text or "manager level" in text):
            return True
    return False


def _human_plausibility_score(*, invalid_action_rate: float, fallback_rate: float, fact_error_rate: float) -> float:
    score = 1.0 - (invalid_action_rate * 0.4) - (fallback_rate * 0.3) - (fact_error_rate * 0.3)
    return round(max(0.0, min(1.0, score)), 4)
