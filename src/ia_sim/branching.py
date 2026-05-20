from __future__ import annotations

import copy
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any

from ia_sim.models import PlannedAction, PurchaseNeed
from ia_sim.rule_engine import RuleEngine
from ia_sim.simulation import SimulationEngine


HIGH_RISK_CLASSIFICATIONS = {"gray_area", "policy_violation", "misrepresentation", "system_blocked", "unsupported"}


def execute_branching_worlds(
    *,
    run_id: str,
    needs: list[PurchaseNeed],
    planned_actions: list[PlannedAction],
    rule_engine: RuleEngine,
) -> list[dict[str, Any]]:
    actions_by_world: OrderedDict[str, list[PlannedAction]] = OrderedDict()
    for action in planned_actions:
        actions_by_world.setdefault(action.world_id or "WORLD-000", []).append(action)

    engine = SimulationEngine(run_id, rule_engine)
    events: list[dict[str, Any]] = []
    for actions in actions_by_world.values():
        engine.purchase_requests = []
        world_needs = copy.deepcopy(needs)
        executable_actions = [action for action in actions if action.classification != "system_blocked"]
        blocked_actions = [action for action in actions if action.classification == "system_blocked"]
        if executable_actions:
            events.extend(engine.run(world_needs, executable_actions))
        need_by_id = {need.purchase_need_id: need for need in world_needs}
        for action in blocked_actions:
            events.append(engine.record_system_blocked_attempt(need_by_id[action.purchase_need_id], action))
    return events


def build_branching_artifacts(
    *,
    run_id: str,
    branching_config: dict[str, Any],
    world_rows: list[dict[str, Any]],
    planned_actions: list[PlannedAction],
    events: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    action_library_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    actions_by_world: dict[str, list[PlannedAction]] = {}
    for action in planned_actions:
        actions_by_world.setdefault(action.world_id, []).append(action)
    events_by_world: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        events_by_world.setdefault(event.get("world_id", ""), []).append(event)
    annotations_by_world: dict[str, list[dict[str, Any]]] = {}
    for annotation in annotations:
        annotations_by_world.setdefault(annotation.get("world_id", ""), []).append(annotation)
    findings_by_world: dict[str, list[dict[str, Any]]] = {}
    for finding in findings:
        findings_by_world.setdefault(finding.get("world_id", ""), []).append(finding)

    world_summaries: list[dict[str, Any]] = []
    for row in world_rows:
        world_id = row["world_id"]
        world_events = events_by_world.get(world_id, [])
        world_actions = actions_by_world.get(world_id, [])
        world_findings = findings_by_world.get(world_id, [])
        world_annotations = annotations_by_world.get(world_id, [])
        initial_status = row["status"]
        status = "completed" if initial_status == "planned" and world_events else initial_status
        terminal_state = world_events[-1]["state_after"] if world_events else status
        triggered_controls = sorted(
            {
                control_id
                for event in world_events
                for control_id, result in event.get("control_results", {}).items()
                if result.get("status") in {"passed", "failed"}
            }
        )
        detected_findings = [finding["finding_id"] for finding in world_findings]
        undetected_risks = _undetected_risks(row, world_findings)
        world_summaries.append(
            {
                "run_id": run_id,
                "world_id": world_id,
                "parent_world_id": row.get("parent_world_id", ""),
                "proposal_id": row.get("proposal_id", ""),
                "status": status,
                "terminal_state": terminal_state,
                "depth": len(world_actions),
                "branch_reason": row.get("branch_reason", ""),
                "classification": row.get("classification", "compliant"),
                "risk_score": row.get("risk_score", 0),
                "actions": [action.action_id for action in world_actions],
                "classifications": [action.classification for action in world_actions]
                or [row.get("classification", "unsupported")],
                "policy_violation_flags": row.get("policy_violation_flags", []),
                "integrity_flags": row.get("integrity_flags", []),
                "triggered_controls": triggered_controls,
                "detected_annotations": [annotation["annotation_id"] for annotation in world_annotations],
                "detected_findings": detected_findings,
                "undetected_risks": undetected_risks,
                "unsupported_operations": row.get("unsupported_operations", []),
                "blocked_reasons": row.get("blocked_reasons", []),
                "review_evidence": row.get("review_evidence", []),
            }
        )

    branching_summary = _branching_summary(
        branching_config=branching_config,
        world_summaries=world_summaries,
        planned_actions=planned_actions,
        action_library_candidates=action_library_candidates,
    )
    world_tree = {
        "run_id": run_id,
        "nodes": [
            {
                "world_id": world["world_id"],
                "parent_world_id": world["parent_world_id"],
                "proposal_id": world["proposal_id"],
                "status": world["status"],
                "classification": world["classification"],
                "risk_score": world["risk_score"],
                "children": [],
            }
            for world in world_summaries
        ],
    }
    residual_risks = [
        {
            "world_id": world["world_id"],
            "classification": world["classification"],
            "risk_score": world["risk_score"],
            "undetected_risks": world["undetected_risks"],
            "review_evidence": world["review_evidence"],
        }
        for world in world_summaries
        if world["undetected_risks"]
    ]
    return {
        "branching_summary": branching_summary,
        "world_summaries": world_summaries,
        "world_tree": world_tree,
        "residual_risks": {"run_id": run_id, "residual_risks": residual_risks},
    }


def write_branching_report(path: Path, *, run_id: str, summary: dict[str, Any], world_summaries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# 分岐探索レポート: {run_id}",
        "",
        "## 実行条件",
        "",
        f"- behavior_mode: branching_proposal",
        f"- proposal_count_per_node: {summary['proposal_count_per_node']}",
        f"- max_depth: {summary['max_depth']}",
        f"- beam_width: {summary['beam_width']}",
        f"- max_total_worlds: {summary['max_total_worlds']}",
        "",
        "## 全体サマリ",
        "",
        "| 指標 | 件数 |",
        "|---|---:|",
    ]
    for key in [
        "generated_world_count",
        "completed_world_count",
        "blocked_world_count",
        "unsupported_world_count",
        "duplicate_world_count",
        "high_risk_world_count",
        "detected_high_risk_world_count",
        "undetected_high_risk_world_count",
        "detector_detection_rate_numerator",
        "detector_detection_rate_denominator",
        "residual_risk_world_count",
        "control_gap_count",
    ]:
        lines.append(f"| {key} | {summary[key]} |")

    lines.extend(
        [
            "",
            "## 行動分類",
            "",
            "| 分類 | Action数 |",
            "|---|---:|",
        ]
    )
    for classification, count in summary["action_classification_counts"].items():
        lines.append(f"| {classification} | {count} |")

    lines.extend(["", "## 代表World", ""])
    for world in world_summaries:
        lines.extend(
            [
                f"### {world['world_id']}: {world['branch_reason']}",
                "",
                f"- status: {world['status']}",
                f"- classification: {world['classification']}",
                f"- risk_score: {world['risk_score']}",
                f"- actions: {world['actions']}",
                f"- detected_findings: {world['detected_findings']}",
                f"- undetected_risks: {world['undetected_risks']}",
                "",
            ]
        )
    lines.append("このレポートは合成環境上のレビュー仮説であり、監査上の結論ではない。")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_residual_risk_report(path: Path, *, residual_risks: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# 残余リスクレポート: {residual_risks['run_id']}",
        "",
        "| world_id | classification | risk_score | undetected_risks | review_evidence |",
        "|---|---|---:|---|---|",
    ]
    for item in residual_risks["residual_risks"]:
        lines.append(
            f"| {item['world_id']} | {item['classification']} | {item['risk_score']} | "
            f"{item['undetected_risks']} | {item['review_evidence']} |"
        )
    if not residual_risks["residual_risks"]:
        lines.append("| - | - | 0 | [] | [] |")
    lines.append("")
    lines.append("検出不能またはAction未対応の分岐は、ログ・統制・Action Libraryの追加検討候補として扱う。")
    path.write_text("\n".join(lines), encoding="utf-8")


def _undetected_risks(row: dict[str, Any], findings: list[dict[str, Any]]) -> list[str]:
    classification = row.get("classification", "compliant")
    if classification not in HIGH_RISK_CLASSIFICATIONS:
        return []
    if row.get("unsupported_operations"):
        return ["unsupported_action_not_logged"]
    if classification == "unsupported":
        return ["unsupported_action_not_logged"]
    if classification == "system_blocked":
        return ["system_blocked_attempt_requires_review"]
    if not findings:
        return ["no_detector_finding_for_high_risk_branch"]
    return []


def _branching_summary(
    *,
    branching_config: dict[str, Any],
    world_summaries: list[dict[str, Any]],
    planned_actions: list[PlannedAction],
    action_library_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    high_risk_worlds = [
        world for world in world_summaries if world["classification"] in HIGH_RISK_CLASSIFICATIONS
    ]
    detected_high_risk_worlds = [world for world in high_risk_worlds if world["detected_findings"]]
    blocked_world_count = sum(1 for world in world_summaries if world["status"] == "blocked")
    unsupported_world_count = sum(1 for world in world_summaries if world["status"] == "unsupported")
    depths = [int(world["depth"]) for world in world_summaries]
    action_signatures = Counter(
        " + ".join(world["actions"]) + "|" + str(world.get("policy_violation_flags", []))
        for world in world_summaries
    )
    duplicate_world_count = sum(count - 1 for count in action_signatures.values() if count > 1)
    action_classification_counts = Counter(action.classification for action in planned_actions)
    for world in world_summaries:
        if not world["actions"]:
            action_classification_counts[world["classification"]] += 1
    residual_risk_world_count = sum(1 for world in world_summaries if world["undetected_risks"])
    high_risk_count = len(high_risk_worlds)
    return {
        "proposal_count_per_node": int(branching_config.get("proposal_count_per_node", 0)),
        "max_depth": int(branching_config.get("max_depth", 0)),
        "beam_width": int(branching_config.get("beam_width", 0)),
        "max_total_worlds": int(branching_config.get("max_total_worlds", 0)),
        "generated_world_count": len(world_summaries),
        "completed_world_count": sum(1 for world in world_summaries if world["status"] == "completed"),
        "blocked_world_count": blocked_world_count,
        "unsupported_world_count": unsupported_world_count,
        "duplicate_world_count": duplicate_world_count,
        "average_depth": round(sum(depths) / len(depths), 4) if depths else 0.0,
        "max_depth_reached_count": sum(
            1 for depth in depths if depth >= int(branching_config.get("max_depth", 0))
        ),
        "compliant_action_count": action_classification_counts.get("compliant", 0),
        "gray_area_action_count": action_classification_counts.get("gray_area", 0),
        "policy_violation_action_count": action_classification_counts.get("policy_violation", 0),
        "misrepresentation_action_count": action_classification_counts.get("misrepresentation", 0),
        "system_blocked_attempt_count": action_classification_counts.get("system_blocked", 0),
        "unsupported_action_candidate_count": len(action_library_candidates),
        "action_classification_counts": dict(sorted(action_classification_counts.items())),
        "high_risk_world_count": high_risk_count,
        "detected_high_risk_world_count": len(detected_high_risk_worlds),
        "detector_detection_rate_numerator": len(detected_high_risk_worlds),
        "detector_detection_rate_denominator": high_risk_count,
        "control_block_rate": round(blocked_world_count / high_risk_count, 4) if high_risk_count else 0.0,
        "detector_detection_rate": round(len(detected_high_risk_worlds) / high_risk_count, 4)
        if high_risk_count
        else 0.0,
        "undetected_high_risk_world_count": sum(
            1 for world in high_risk_worlds if not world["detected_findings"]
        ),
        "residual_risk_world_count": residual_risk_world_count,
        "control_gap_count": residual_risk_world_count,
    }
