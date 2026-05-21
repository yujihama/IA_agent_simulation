from __future__ import annotations

import copy
from collections import Counter, OrderedDict
from dataclasses import replace
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
    parent_by_world: dict[str, str] = {}
    for action in planned_actions:
        world_id = action.world_id or "WORLD-000"
        actions_by_world.setdefault(world_id, []).append(action)
        parent_by_world.setdefault(world_id, action.parent_world_id)

    engine = SimulationEngine(run_id, rule_engine)
    events: list[dict[str, Any]] = []
    for world_id in actions_by_world:
        engine.purchase_requests = []
        world_needs = copy.deepcopy(needs)
        actions = _lineage_actions_for_world(world_id, actions_by_world, parent_by_world)
        executable_actions = [action for action in actions if action.classification != "system_blocked"]
        blocked_actions = [action for action in actions if action.classification == "system_blocked"]
        if executable_actions:
            events.extend(engine.run(world_needs, executable_actions))
        need_by_id = {need.purchase_need_id: need for need in world_needs}
        for action in blocked_actions:
            events.append(engine.record_system_blocked_attempt(need_by_id[action.purchase_need_id], action))
    return events


def _lineage_actions_for_world(
    world_id: str,
    actions_by_world: OrderedDict[str, list[PlannedAction]],
    parent_by_world: dict[str, str],
) -> list[PlannedAction]:
    lineage: list[str] = []
    current = world_id
    seen: set[str] = set()
    while current and current not in seen:
        lineage.append(current)
        seen.add(current)
        current = parent_by_world.get(current, "")
    lineage.reverse()

    actions: list[PlannedAction] = []
    parent_world_id = parent_by_world.get(world_id, "")
    for lineage_world_id in lineage:
        for action in actions_by_world.get(lineage_world_id, []):
            parameters = dict(action.parameters)
            parameters["_lineage_source_world_id"] = action.world_id
            parameters["_lineage_action_depth"] = action.depth
            actions.append(
                replace(
                    action,
                    parameters=parameters,
                    world_id=world_id,
                    parent_world_id=parent_world_id,
                )
            )
    return actions


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
    events_by_id = {event["event_id"]: event for event in events}
    annotations_by_world: dict[str, list[dict[str, Any]]] = {}
    for annotation in annotations:
        annotations_by_world.setdefault(annotation.get("world_id", ""), []).append(annotation)
    findings_by_world: dict[str, list[dict[str, Any]]] = {}
    for finding in findings:
        findings_by_world.setdefault(finding.get("world_id", ""), []).append(finding)
    children_by_parent: dict[str, list[str]] = {}
    for row in world_rows:
        parent_world_id = row.get("parent_world_id", "")
        if parent_world_id:
            children_by_parent.setdefault(parent_world_id, []).append(row["world_id"])

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
        depth = int(row.get("depth", len(world_actions)))
        triggered_controls = sorted(
            {
                control_id
                for event in world_events
                for control_id, result in event.get("control_results", {}).items()
                if result.get("status") in {"passed", "failed"}
            }
        )
        detected_findings = [finding["finding_id"] for finding in world_findings]
        finding_sources = {
            finding["finding_id"]: _finding_lineage_source(
                finding=finding,
                events_by_id=events_by_id,
                current_depth=depth,
            )
            for finding in world_findings
        }
        current_detected_findings = [
            finding_id for finding_id, source in finding_sources.items() if source in {"current", "mixed"}
        ]
        inherited_detected_findings = [
            finding_id for finding_id, source in finding_sources.items() if source == "inherited"
        ]
        mixed_lineage_detected_findings = [
            finding_id for finding_id, source in finding_sources.items() if source == "mixed"
        ]
        undetected_risks = _undetected_risks(row, world_findings, current_detected_findings)
        child_world_ids = children_by_parent.get(world_id, [])
        terminal_reason = _terminal_reason(
            row=row,
            world_events=world_events,
            world_actions=world_actions,
            branching_config=branching_config,
            child_world_ids=child_world_ids,
        )
        world_summaries.append(
            {
                "run_id": run_id,
                "world_id": world_id,
                "parent_world_id": row.get("parent_world_id", ""),
                "proposal_id": row.get("proposal_id", ""),
                "status": status,
                "terminal_state": terminal_state,
                "terminal_reason": terminal_reason,
                "depth": depth,
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
                "current_detected_findings": current_detected_findings,
                "inherited_detected_findings": inherited_detected_findings,
                "mixed_lineage_detected_findings": mixed_lineage_detected_findings,
                "finding_lineage_sources": finding_sources,
                "undetected_risks": undetected_risks,
                "unsupported_operations": row.get("unsupported_operations", []),
                "blocked_reasons": row.get("blocked_reasons", []),
                "review_evidence": row.get("review_evidence", []),
                "child_world_ids": child_world_ids,
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
                "terminal_reason": world["terminal_reason"],
                "depth": world["depth"],
                "classification": world["classification"],
                "risk_score": world["risk_score"],
                "detected_findings": world["detected_findings"],
                "current_detected_findings": world["current_detected_findings"],
                "inherited_detected_findings": world["inherited_detected_findings"],
                "children": world["child_world_ids"],
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
        "expanded_world_count",
        "leaf_world_count",
        "generated_depth_counts",
        "high_risk_world_count",
        "detected_high_risk_world_count",
        "undetected_high_risk_world_count",
        "detector_detection_rate_numerator",
        "detector_detection_rate_denominator",
        "lineage_detection_rate",
        "new_risk_detection_rate",
        "current_world_detection_rate",
        "inherited_risk_count",
        "inherited_risk_world_count",
        "inherited_only_high_risk_world_count",
        "undetected_new_risk_world_count",
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
                f"- depth: {world['depth']}",
                f"- terminal_reason: {world['terminal_reason']}",
                f"- actions: {world['actions']}",
                f"- children: {world['child_world_ids']}",
                f"- detected_findings: {world['detected_findings']}",
                f"- current_detected_findings: {world['current_detected_findings']}",
                f"- inherited_detected_findings: {world['inherited_detected_findings']}",
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


def _finding_lineage_source(
    *,
    finding: dict[str, Any],
    events_by_id: dict[str, dict[str, Any]],
    current_depth: int,
) -> str:
    evidence_depths = [
        int(events_by_id[event_id].get("metadata", {}).get("lineage_action_depth", current_depth))
        for event_id in finding.get("evidence_event_ids", [])
        if event_id in events_by_id
    ]
    if not evidence_depths:
        return "unknown"
    has_current = any(depth >= current_depth for depth in evidence_depths)
    has_inherited = any(depth < current_depth for depth in evidence_depths)
    if has_current and has_inherited:
        return "mixed"
    if has_current:
        return "current"
    return "inherited"


def _undetected_risks(
    row: dict[str, Any],
    findings: list[dict[str, Any]],
    current_findings: list[str],
) -> list[str]:
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
    if not current_findings:
        return ["no_current_detector_finding_for_high_risk_branch"]
    return []


def _terminal_reason(
    *,
    row: dict[str, Any],
    world_events: list[dict[str, Any]],
    world_actions: list[PlannedAction],
    branching_config: dict[str, Any],
    child_world_ids: list[str],
) -> str:
    if child_world_ids:
        return "expanded"
    if row.get("unsupported_operations") or row.get("status") == "unsupported":
        return "unsupported"
    if row.get("blocked_reasons") or row.get("classification") == "system_blocked":
        return "blocked_attempt"
    if not world_actions and not world_events:
        return "no_valid_action"
    terminal_state = world_events[-1]["state_after"] if world_events else row.get("status", "")
    if terminal_state == "paid":
        return "paid"
    if terminal_state == "blocked_attempt":
        return "blocked_attempt"
    if int(row.get("depth", 1)) >= int(branching_config.get("max_depth", 1)):
        return "max_depth_reached"
    return "open"


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
    lineage_detected_high_risk_worlds = [world for world in high_risk_worlds if world["detected_findings"]]
    current_detected_high_risk_worlds = [
        world for world in high_risk_worlds if world["current_detected_findings"]
    ]
    blocked_world_count = sum(1 for world in world_summaries if world["status"] == "blocked")
    unsupported_world_count = sum(1 for world in world_summaries if world["status"] == "unsupported")
    depths = [int(world["depth"]) for world in world_summaries]
    action_signatures = Counter(_world_summary_signature(world) for world in world_summaries)
    duplicate_world_count = sum(count - 1 for count in action_signatures.values() if count > 1)
    action_classification_counts = Counter(action.classification for action in planned_actions)
    for world in world_summaries:
        if not world["actions"]:
            action_classification_counts[world["classification"]] += 1
    residual_risk_world_count = sum(1 for world in world_summaries if world["undetected_risks"])
    high_risk_count = len(high_risk_worlds)
    depth_counts = Counter(str(world["depth"]) for world in world_summaries)
    current_detected_world_count = sum(1 for world in world_summaries if world["current_detected_findings"])
    inherited_risk_count = sum(len(world["inherited_detected_findings"]) for world in world_summaries)
    inherited_risk_world_count = sum(1 for world in world_summaries if world["inherited_detected_findings"])
    inherited_only_high_risk_count = sum(
        1
        for world in high_risk_worlds
        if world["inherited_detected_findings"] and not world["current_detected_findings"]
    )
    return {
        "proposal_count_per_node": int(branching_config.get("proposal_count_per_node", 0)),
        "max_depth": int(branching_config.get("max_depth", 0)),
        "beam_width": int(branching_config.get("beam_width", 0)),
        "max_total_worlds": int(branching_config.get("max_total_worlds", 0)),
        "multi_stage_enabled": int(branching_config.get("max_depth", 0)) > 1,
        "generated_world_count": len(world_summaries),
        "completed_world_count": sum(1 for world in world_summaries if world["status"] == "completed"),
        "blocked_world_count": blocked_world_count,
        "unsupported_world_count": unsupported_world_count,
        "duplicate_world_count": duplicate_world_count,
        "average_depth": round(sum(depths) / len(depths), 4) if depths else 0.0,
        "max_depth_reached_count": sum(
            1 for world in world_summaries if world["terminal_reason"] == "max_depth_reached"
        ),
        "expanded_world_count": sum(1 for world in world_summaries if world["child_world_ids"]),
        "leaf_world_count": sum(1 for world in world_summaries if not world["child_world_ids"]),
        "generated_depth_counts": dict(sorted(depth_counts.items())),
        "compliant_action_count": action_classification_counts.get("compliant", 0),
        "gray_area_action_count": action_classification_counts.get("gray_area", 0),
        "policy_violation_action_count": action_classification_counts.get("policy_violation", 0),
        "misrepresentation_action_count": action_classification_counts.get("misrepresentation", 0),
        "system_blocked_attempt_count": action_classification_counts.get("system_blocked", 0),
        "unsupported_action_candidate_count": len(action_library_candidates),
        "action_classification_counts": dict(sorted(action_classification_counts.items())),
        "high_risk_world_count": high_risk_count,
        "detected_high_risk_world_count": len(lineage_detected_high_risk_worlds),
        "detector_detection_rate_numerator": len(lineage_detected_high_risk_worlds),
        "detector_detection_rate_denominator": high_risk_count,
        "control_block_rate": round(blocked_world_count / high_risk_count, 4) if high_risk_count else 0.0,
        "detector_detection_rate": round(len(lineage_detected_high_risk_worlds) / high_risk_count, 4)
        if high_risk_count
        else 0.0,
        "lineage_detection_rate_numerator": len(lineage_detected_high_risk_worlds),
        "lineage_detection_rate_denominator": high_risk_count,
        "lineage_detection_rate": round(len(lineage_detected_high_risk_worlds) / high_risk_count, 4)
        if high_risk_count
        else 0.0,
        "current_world_detection_rate_numerator": current_detected_world_count,
        "current_world_detection_rate_denominator": len(world_summaries),
        "current_world_detection_rate": round(current_detected_world_count / len(world_summaries), 4)
        if world_summaries
        else 0.0,
        "new_risk_detection_rate_numerator": len(current_detected_high_risk_worlds),
        "new_risk_detection_rate_denominator": high_risk_count,
        "new_risk_detection_rate": round(len(current_detected_high_risk_worlds) / high_risk_count, 4)
        if high_risk_count
        else 0.0,
        "inherited_risk_count": inherited_risk_count,
        "inherited_risk_world_count": inherited_risk_world_count,
        "inherited_only_high_risk_world_count": inherited_only_high_risk_count,
        "undetected_high_risk_world_count": sum(
            1 for world in high_risk_worlds if not world["detected_findings"]
        ),
        "undetected_new_risk_world_count": sum(
            1 for world in high_risk_worlds if not world["current_detected_findings"]
        ),
        "residual_risk_world_count": residual_risk_world_count,
        "control_gap_count": residual_risk_world_count,
    }


def _world_summary_signature(world: dict[str, Any]) -> str:
    return "|".join(
        [
            str(world.get("parent_world_id", "")),
            str(world.get("classification", "")),
            " + ".join(str(action_id) for action_id in world.get("actions", [])),
            str(world.get("policy_violation_flags", [])),
            str(world.get("integrity_flags", [])),
            str(world.get("branch_reason", "")),
        ]
    )
