from __future__ import annotations

from pathlib import Path
from typing import Any


def write_finding_report(path: Path, *, run_id: str, metrics: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# \u4e0d\u5099\u5019\u88dc\u30ec\u30d3\u30e5\u30fc: {run_id}",
        "",
        "\u3053\u306e\u30ec\u30dd\u30fc\u30c8\u306fDetector\u304c\u751f\u6210\u3057\u305f\u4eba\u9593\u30ec\u30d3\u30e5\u30fc\u7528\u306e\u4e0d\u5099\u5019\u88dc\u3067\u3059\u3002\u76e3\u67fb\u4e0a\u306e\u7d50\u8ad6\u3067\u306f\u3042\u308a\u307e\u305b\u3093\u3002",
        "",
        "## \u6307\u6a19",
        "",
        f"- Variant: {metrics['variant_id']}",
        f"- \u4e0d\u5099\u5019\u88dc\u4ef6\u6570: {metrics['finding_count']}",
        f"- \u672a\u7de9\u548c\u5019\u88dc\u4ef6\u6570: {metrics['split_order_bypass_success_count']}",
        f"- Detector\u6307\u6a19\u306bProposal Flag\u3092\u4f7f\u7528: {not metrics['proposal_flags_excluded_from_detector_metrics']}",
        "",
    ]
    if not findings:
        lines.extend(["## \u4e0d\u5099\u5019\u88dc", "", "\u4e0d\u5099\u5019\u88dc\u306f\u751f\u6210\u3055\u308c\u307e\u305b\u3093\u3067\u3057\u305f\u3002"])
    for finding in findings:
        lines.extend(
            [
                f"## {finding['finding_id']} - {finding['title']}",
                "",
                f"- \u4e0d\u5099ID: {finding['defect_id']}",
                f"- \u91cd\u8981\u5ea6: {_jp_severity(finding['severity'])}",
                f"- \u30b9\u30c6\u30fc\u30bf\u30b9: {_jp_status(finding['status'])}",
                f"- \u95a2\u9023\u7d71\u5236: {', '.join(finding['related_controls'])}",
                f"- \u6839\u62e0\u30a4\u30d9\u30f3\u30c8: {', '.join(finding['evidence_event_ids'])}",
                "",
                "### \u89b3\u5bdf\u4e8b\u5b9f",
                "",
            ]
        )
        lines.extend([f"- {fact}" for fact in finding["observed_facts"]])
        lines.extend(["", "### \u63a8\u8ad6", "", finding["inference"], "", "### \u6839\u62e0\u30b5\u30de\u30ea", ""])
        for evidence in finding["evidence_summary"]:
            lines.append(
                "- "
                f"{evidence['event_id']} / {evidence['purchase_request_id']} / "
                f"\u91d1\u984d={evidence['amount']} / "
                f"\u5fc5\u8981\u627f\u8a8d\u30ec\u30d9\u30eb={_jp_level(evidence['required_approver_level'])} / "
                f"\u5408\u7b97\u9069\u7528={_jp_bool(evidence['aggregation_applied'])}"
            )
        lines.extend(["", "### \u63a8\u5968\u30ec\u30d3\u30e5\u30fc\u624b\u9806", ""])
        lines.extend([f"- {step}" for step in finding["recommended_review_steps"]])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_comparison_report(path: Path, comparison: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    comparison_mode = comparison.get("comparison_mode", "frozen_behavior")
    mode_note = (
        "adaptive_agent: LLM\u7533\u8acb\u8005\u30a8\u30fc\u30b8\u30a7\u30f3\u30c8\u306b\u5404Variant\u306e\u7d71\u5236\u6761\u4ef6\u3092\u63d0\u793a\u3057\u3066\u6bd4\u8f03\u3059\u308b\u3002"
        if comparison_mode == "adaptive_agent"
        else "frozen_behavior: \u540c\u4e00\u306e\u884c\u52d5\u5217\u3092\u518d\u751f\u3057\u3001\u7d71\u5236\u30dd\u30ea\u30b7\u30fc\u306e\u307f\u3092\u5909\u66f4\u3059\u308b\u3002"
    )
    lines = [
        "# Baseline / Variant A \u6bd4\u8f03\u30ec\u30dd\u30fc\u30c8",
        "",
        f"\u6bd4\u8f03\u30e2\u30fc\u30c9: {mode_note}",
        "",
        "| \u6307\u6a19 | Baseline | Variant | \u5dee\u5206 |",
        "|---|---:|---:|---:|",
    ]
    bypass = comparison["split_order_bypass_success_count"]
    lead = comparison["approval_lead_time_days"]
    dept = comparison["department_head_approval_count"]
    aggregation = comparison["aggregation_applications"]
    lines.extend(
        [
            f"| \u672a\u7de9\u548c\u3059\u308a\u629c\u3051\u5019\u88dc\u4ef6\u6570 | {bypass['baseline']} | {bypass['variant']} | {bypass['delta']} |",
            f"| \u627f\u8a8d\u30ea\u30fc\u30c9\u30bf\u30a4\u30e0\u5408\u8a08\uff08\u65e5\uff09 | {lead['baseline']} | {lead['variant']} | {lead['delta']} |",
            f"| \u90e8\u9580\u9577\u627f\u8a8d\u4ef6\u6570 | {dept['baseline']} | {dept['variant']} | {dept['delta']} |",
            f"| \u5408\u7b97\u5224\u5b9a\u9069\u7528\u4ef6\u6570 | {aggregation['baseline']} | {aggregation['variant']} | {aggregation['delta']} |",
            "",
            f"\u30ea\u30b9\u30af\u4f4e\u6e1b\u7387: {comparison['risk_reduction_ratio']}",
            "",
        ]
    )
    if "action_selection_metrics" in comparison:
        lines.extend(["## LLM\u884c\u52d5\u9078\u629e\u5dee\u5206", "", "| \u6307\u6a19 | Baseline | Variant | \u5dee\u5206 |", "|---|---:|---:|---:|"])
        labels = {
            "partial_request_rate": "\u90e8\u5206\u7533\u8acb\u7387",
            "consult_rate": "\u76f8\u8ac7\u7387",
            "postpone_rate": "\u5ef6\u671f\u7387",
            "invalid_action_rate": "\u7121\u52b9Action\u7387",
            "retry_rate": "Retry\u7387",
            "fallback_rate": "Fallback\u7387",
            "split_order_candidate_count": "\u5206\u5272\u8cfc\u8cb7\u5019\u88dc\u4ef6\u6570",
            "bypass_success_count": "\u672a\u7de9\u548c\u5019\u88dc\u4ef6\u6570",
            "aggregation_mitigation_count": "\u5408\u7b97\u7de9\u548c\u4ef6\u6570",
            "control_awareness": "\u7d71\u5236\u8a8d\u8b58",
            "reason_groundedness": "\u7406\u7531\u306e\u6839\u62e0\u6027",
            "fact_in_reason_error_rate": "\u7406\u7531\u5185\u306e\u4e8b\u5b9f\u8aa4\u308a\u7387",
            "human_plausibility_score": "\u4eba\u9593\u30ec\u30d3\u30e5\u30fc\u4e0a\u306e\u59a5\u5f53\u6027",
        }
        for key, values in comparison["action_selection_metrics"].items():
            lines.append(f"| {labels.get(key, key)} | {values['baseline']} | {values['variant']} | {values['delta']} |")
        lines.append("")
    lines.append(
        "\u89e3\u91c8: Variant A\u306e\u5408\u7b97\u5224\u5b9a\u306b\u3088\u308a\u3001\u5206\u5272\u7684\u306a\u7533\u8acb\u884c\u52d5\u304c\u691c\u51fa\u3055\u308c\u3066\u3082\u672a\u7de9\u548c\u3059\u308a\u629c\u3051\u5019\u88dc\u306f\u6e1b\u5c11\u3059\u308b\u3002"
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_llm_action_review_report(
    path: Path,
    *,
    run_id: str,
    action_selection_metrics: dict[str, Any],
    decisions: list[dict[str, Any]],
    llm_calls: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# LLM\u884c\u52d5\u9078\u629e\u30ec\u30d3\u30e5\u30fc: {run_id}",
        "",
        "\u3053\u306e\u30ec\u30dd\u30fc\u30c8\u306fLLM\u7533\u8acb\u8005\u30a8\u30fc\u30b8\u30a7\u30f3\u30c8\u306e\u884c\u52d5\u7406\u7531\u3068\u691c\u8a3c\u7d50\u679c\u3092\u78ba\u8a8d\u3059\u308b\u305f\u3081\u306e\u3082\u306e\u3067\u3059\u3002",
        "",
        "## \u884c\u52d5\u9078\u629e\u6307\u6a19",
        "",
        f"- \u9078\u629eAction\u5206\u5e03: {action_selection_metrics['selected_action_distribution']}",
        f"- \u90e8\u5206\u7533\u8acb\u7387: {action_selection_metrics['partial_request_rate']}",
        f"- \u76f8\u8ac7\u7387: {action_selection_metrics['consult_rate']}",
        f"- Retry\u7387: {action_selection_metrics['retry_rate']}",
        f"- Fallback\u7387: {action_selection_metrics['fallback_rate']}",
        f"- \u7d71\u5236\u8a8d\u8b58: {action_selection_metrics['control_awareness']}",
        f"- \u7406\u7531\u306e\u6839\u62e0\u6027: {action_selection_metrics['reason_groundedness']}",
        "",
        "## \u9078\u629eAction",
        "",
    ]
    for row in decisions:
        lines.extend(
            [
                f"### {row['decision_id']} / {row['selected_action_id']}",
                "",
                f"- PurchaseNeed: {row['purchase_need_id']}",
                f"- Source: {row['source']}",
                f"- Retry: {row['retry_count']}",
                f"- Fallback: {_jp_bool(row['fallback_used'])}",
                f"- Parameters: `{row['parameters']}`",
                f"- \u7406\u7531: {row['reason']}",
                f"- \u7d71\u5236\u8a8d\u8b58: {row['control_awareness']}",
                f"- \u671f\u5f85\u3055\u308c\u308b\u7d71\u5236\u52b9\u679c: {row['expected_control_effect']}",
                "",
            ]
        )
    lines.extend(["## LLM Call\u691c\u8a3c", ""])
    for call in llm_calls:
        lines.append(
            f"- PurchaseNeed={call['purchase_need_id']} attempt={call['attempt']} "
            f"status={call['validation_status']} retry={_jp_bool(call['retry_scheduled'])}"
        )
        if call.get("validation_errors"):
            lines.append(f"  - validation_errors: {call['validation_errors']}")
    path.write_text("\n".join(lines), encoding="utf-8")


def _jp_bool(value: bool) -> str:
    return "\u306f\u3044" if value else "\u3044\u3044\u3048"


def _jp_level(value: str) -> str:
    return {
        "manager": "\u8ab2\u9577",
        "department_head": "\u90e8\u9580\u9577",
        "division_head": "\u672c\u90e8\u9577",
    }.get(value, value)


def _jp_severity(value: str) -> str:
    return {"high": "\u9ad8", "medium": "\u4e2d", "low": "\u4f4e"}.get(value, value)


def _jp_status(value: str) -> str:
    return {
        "candidate_unmitigated": "\u5019\u88dc\uff08\u672a\u7de9\u548c\uff09",
        "candidate_mitigated": "\u5019\u88dc\uff08\u7d71\u5236\u306b\u3088\u308a\u7de9\u548c\uff09",
    }.get(value, value)
