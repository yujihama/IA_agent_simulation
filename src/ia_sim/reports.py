from __future__ import annotations

from pathlib import Path
from typing import Any


def write_finding_report(path: Path, *, run_id: str, metrics: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# 不備候補レポート: {run_id}",
        "",
        "このレポートはDetectorが生成した人間レビュー用の不備候補を示すものであり、監査上の結論ではない。",
        "",
        "## 指標",
        "",
        f"- Variant: {metrics['variant_id']}",
        f"- 不備候補件数: {metrics['finding_count']}",
        f"- 分割購買による未緩和すり抜け件数: {metrics['split_order_bypass_success_count']}",
        f"- Detector指標にProposal Flagを使用: {not metrics['proposal_flags_excluded_from_detector_metrics']}",
        "",
    ]
    if not findings:
        lines.extend(["## 不備候補", "", "不備候補は生成されなかった。"])
    for finding in findings:
        lines.extend(
            [
                f"## {finding['finding_id']} - {finding['title']}",
                "",
                f"- 不備ID: {finding['defect_id']}",
                f"- 重要度: {_jp_severity(finding['severity'])}",
                f"- ステータス: {_jp_status(finding['status'])}",
                f"- 関連統制: {', '.join(finding['related_controls'])}",
                f"- 根拠イベント: {', '.join(finding['evidence_event_ids'])}",
                "",
                "### 観察事実",
                "",
            ]
        )
        lines.extend([f"- {fact}" for fact in finding["observed_facts"]])
        lines.extend(["", "### 推論", "", finding["inference"], "", "### 根拠サマリ", ""])
        for evidence in finding["evidence_summary"]:
            lines.append(
                "- "
                f"{evidence['event_id']} / {evidence['purchase_request_id']} / "
                f"金額={evidence['amount']} / 必要承認レベル={_jp_level(evidence['required_approver_level'])} / "
                f"合算適用={_jp_bool(evidence['aggregation_applied'])}"
            )
        lines.extend(["", "### 推奨レビュー手順", ""])
        lines.extend([f"- {step}" for step in finding["recommended_review_steps"]])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_comparison_report(path: Path, comparison: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Baseline / Variant A 比較レポート",
        "",
        "比較モード: frozen_behavior。同一の計画済みcreate_purchase_request行動列を再生し、統制ポリシーのみを変更する。",
        "",
        "| 指標 | Baseline | Variant | 差分 |",
        "|---|---:|---:|---:|",
    ]
    bypass = comparison["split_order_bypass_success_count"]
    lead = comparison["approval_lead_time_days"]
    dept = comparison["department_head_approval_count"]
    aggregation = comparison["aggregation_applications"]
    lines.extend(
        [
            f"| 分割購買による未緩和すり抜け件数 | {bypass['baseline']} | {bypass['variant']} | {bypass['delta']} |",
            f"| 承認リードタイム合計（日） | {lead['baseline']} | {lead['variant']} | {lead['delta']} |",
            f"| 部門長承認件数 | {dept['baseline']} | {dept['variant']} | {dept['delta']} |",
            f"| 合算判定適用件数 | {aggregation['baseline']} | {aggregation['variant']} | {aggregation['delta']} |",
            "",
            f"リスク低減率: {comparison['risk_reduction_ratio']}",
            "",
            "解釈: Variant Aはこのシナリオで未緩和の分割購買すり抜けを低減する。一方で、承認負荷とリードタイムは増加する。",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _jp_bool(value: bool) -> str:
    return "はい" if value else "いいえ"


def _jp_level(value: str) -> str:
    return {
        "manager": "課長",
        "department_head": "部門長",
        "division_head": "本部長",
    }.get(value, value)


def _jp_severity(value: str) -> str:
    return {"high": "高", "medium": "中", "low": "低"}.get(value, value)


def _jp_status(value: str) -> str:
    return {
        "candidate_unmitigated": "候補（未緩和）",
        "candidate_mitigated": "候補（統制により緩和）",
    }.get(value, value)
