from __future__ import annotations

from pathlib import Path
from typing import Any


def write_finding_report(path: Path, *, run_id: str, metrics: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Finding Report: {run_id}",
        "",
        "This report lists detector-generated candidates for human review. It is not an audit conclusion.",
        "",
        "## Metrics",
        "",
        f"- Variant: {metrics['variant_id']}",
        f"- Findings: {metrics['finding_count']}",
        f"- Split-order bypass success count: {metrics['split_order_bypass_success_count']}",
        f"- Proposal flags used for detector metrics: {not metrics['proposal_flags_excluded_from_detector_metrics']}",
        "",
    ]
    if not findings:
        lines.extend(["## Findings", "", "No findings were generated."])
    for finding in findings:
        lines.extend(
            [
                f"## {finding['finding_id']} - {finding['title']}",
                "",
                f"- Defect: {finding['defect_id']}",
                f"- Severity: {finding['severity']}",
                f"- Status: {finding['status']}",
                f"- Related controls: {', '.join(finding['related_controls'])}",
                f"- Evidence events: {', '.join(finding['evidence_event_ids'])}",
                "",
                "### Observed Facts",
                "",
            ]
        )
        lines.extend([f"- {fact}" for fact in finding["observed_facts"]])
        lines.extend(["", "### Inference", "", finding["inference"], "", "### Evidence Summary", ""])
        for evidence in finding["evidence_summary"]:
            lines.append(
                "- "
                f"{evidence['event_id']} / {evidence['purchase_request_id']} / "
                f"amount={evidence['amount']} / required={evidence['required_approver_level']} / "
                f"aggregation_applied={evidence['aggregation_applied']}"
            )
        lines.extend(["", "### Recommended Review Steps", ""])
        lines.extend([f"- {step}" for step in finding["recommended_review_steps"]])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_comparison_report(path: Path, comparison: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Baseline / Variant A Comparison",
        "",
        "Comparison mode: frozen_behavior. The same planned create_purchase_request actions are replayed; only control policy changes.",
        "",
        "| Metric | Baseline | Variant | Delta |",
        "|---|---:|---:|---:|",
    ]
    bypass = comparison["split_order_bypass_success_count"]
    lead = comparison["approval_lead_time_days"]
    dept = comparison["department_head_approval_count"]
    aggregation = comparison["aggregation_applications"]
    lines.extend(
        [
            f"| Split-order bypass success count | {bypass['baseline']} | {bypass['variant']} | {bypass['delta']} |",
            f"| Total approval lead time days | {lead['baseline']} | {lead['variant']} | {lead['delta']} |",
            f"| Department-head approvals | {dept['baseline']} | {dept['variant']} | {dept['delta']} |",
            f"| Aggregation applications | {aggregation['baseline']} | {aggregation['variant']} | {aggregation['delta']} |",
            "",
            f"Risk reduction ratio: {comparison['risk_reduction_ratio']}",
            "",
            "Interpretation: Variant A reduces unmitigated split-order bypass in this scenario, with additional approval workload and lead time.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
