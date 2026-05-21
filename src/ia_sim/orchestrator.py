from __future__ import annotations

import hashlib
import copy
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from ia_sim.branching import (
    build_branching_artifacts,
    execute_branching_worlds,
    write_branching_report,
    write_residual_risk_report,
)
from ia_sim.config import (
    load_agent_profiles,
    load_action_definitions,
    load_control_cards,
    load_run_config,
    load_scenarios,
    read_yaml,
    validate_action_definitions,
    validate_config_tree,
    write_yaml,
)
from ia_sim.detectors import build_findings, detect_control_findings
from ia_sim.evaluation import evaluate_findings
from ia_sim.llm import (
    LLMActionSelector,
    LLMBranchingProposalGenerator,
    LLMBranchingResult,
    LLMOpenProposalGenerator,
    LLMProposalResult,
    LLMSelectionResult,
)
from ia_sim.llm_metrics import compare_action_selection_metric_sets, compute_action_selection_metrics
from ia_sim.metrics import compare_metric_sets, compute_metrics
from ia_sim.models import PlannedAction, RunResult, now_utc_iso
from ia_sim.reports import write_comparison_report, write_finding_report, write_llm_action_review_report
from ia_sim.rule_engine import RuleEngine, VariantPolicy
from ia_sim.simulation import SimulationEngine, behavior_replay_rows, build_behavior_plan
from ia_sim.storage import read_json, read_jsonl, write_json, write_jsonl
from ia_sim.synthetic import generate_synthetic_data, read_purchase_needs_csv


PROMPT_TREATMENTS = ["full_context", "scenario_only", "objective_only", "planning_hint_only"]
SUPPORTED_PROMPT_TREATMENTS = [*PROMPT_TREATMENTS, "balanced_planning_hint"]
HINT_STRENGTHS = ["no_hint", "control_knowledge_only", "weak_hint", "medium_hint", "strong_hint"]
AGENT_PERSONAS = ["compliant_requester", "pragmatic_requester", "control_avoidant_requester", "red_team_requester"]
CONTROL_VISIBILITIES = [
    "control_hidden",
    "control_summary",
    "control_full",
    "control_full_with_failure_modes",
    "control_full_red_team",
]
PRESSURE_TYPES = [
    "no_pressure",
    "budget_pressure",
    "delivery_pressure",
    "approver_absence",
    "vendor_constraint",
    "workload_pressure",
]
BRANCHING_COMPARISON_VARIANTS = [
    "baseline",
    "variant_a_7d_aggregation",
    "variant_b_emergency_post_approval",
]


def load_variant_policy(repo_root: Path, variant_id: str) -> VariantPolicy:
    raw = read_yaml(repo_root / "configs/variants/p2p_control_variants.yaml")
    for item in raw["variants"]:
        if item["variant_id"] == variant_id:
            rules = item.get("rules", {})
            aggregate_days = rules.get("aggregate_approval_window_days")
            return VariantPolicy(
                variant_id=item["variant_id"],
                name=item["name"],
                aggregate_approval_window_days=aggregate_days,
                emergency_route_reason_required=bool(rules.get("emergency_route_reason_required", False)),
                emergency_route_post_approval_hours=rules.get("emergency_route_post_approval_hours"),
            )
    raise ValueError(f"Unknown variant_id: {variant_id}")


def validate_or_raise(repo_root: Path) -> None:
    errors = validate_config_tree(repo_root)
    if errors:
        raise ValueError("\n".join(errors))


def run_simulation(
    repo_root: Path,
    config_path: Path,
    *,
    output_root_override: Path | None = None,
    purchase_needs_path_override: Path | None = None,
) -> RunResult:
    validate_or_raise(repo_root)
    run_config = load_run_config(config_path)

    actions = load_action_definitions(repo_root / run_config.inputs["actions"])
    action_errors = validate_action_definitions(actions)
    if action_errors:
        raise ValueError("\n".join(action_errors))

    controls = load_control_cards(repo_root / run_config.inputs["controls"])
    scenarios = load_scenarios(repo_root / run_config.inputs["scenarios"])
    agents = load_agent_profiles(repo_root / run_config.inputs["agents"])
    variant_policy = load_variant_policy(repo_root, run_config.variant_id)
    rule_engine = RuleEngine(controls, variant_policy)

    purchase_needs_path = purchase_needs_path_override or repo_root / run_config.inputs["purchase_needs"]
    if not purchase_needs_path.exists():
        generate_synthetic_data(
            purchase_needs_path.parent,
            count=_max_purchase_needs(run_config.simulation),
            seed=run_config.seed,
        )
    needs = read_purchase_needs_csv(purchase_needs_path)

    max_purchase_needs = _max_purchase_needs(run_config.simulation)
    llm_selection: LLMSelectionResult | None = None
    branching_result: LLMBranchingResult | None = None
    branching_artifacts: dict[str, Any] | None = None
    if run_config.behavior_mode == "adaptive_agent":
        scenario = _select_scenario(scenarios, run_config.scenario_id)
        agent = _select_requester_agent(agents)
        selector = LLMActionSelector(
            repo_root=repo_root,
            run_id=run_config.run_id,
            model=str(run_config.llm.get("model", "gpt-4.1-mini")),
            provider=str(run_config.llm.get("provider", "openai")),
            temperature=float(run_config.llm.get("temperature", 0.2)),
            max_retries=int(run_config.llm.get("max_retries", 2)),
            allowed_actions=actions,
            controls=controls,
            scenario=scenario,
            agent=agent,
            variant_policy=variant_policy,
            pressure_condition=str(run_config.llm.get("pressure_condition", "pressure")),
            prompt_treatment=str(run_config.llm.get("prompt_treatment", "full_context")),
            pressure_type=run_config.llm.get("pressure_type"),
            hint_strength=run_config.llm.get("hint_strength"),
            agent_persona=run_config.llm.get("agent_persona"),
            control_visibility=str(run_config.llm.get("control_visibility", "control_full")),
            trial_index=run_config.llm.get("trial_index"),
            llm_seed=run_config.llm.get("seed"),
        )
        llm_selection = selector.select_actions_for_needs(needs, max_purchase_needs=max_purchase_needs)
        plan = llm_selection.planned_actions
        engine = SimulationEngine(run_config.run_id, rule_engine)
        events = engine.run(needs, plan)
    elif run_config.behavior_mode == "branching_proposal":
        scenario = _select_scenario(scenarios, run_config.scenario_id)
        agent = _select_requester_agent(agents)
        branching_config = _branching_config(run_config.branching)
        generator = LLMBranchingProposalGenerator(
            repo_root=repo_root,
            run_id=run_config.run_id,
            model=str(run_config.llm.get("model", "gpt-4.1-mini")),
            provider=str(run_config.llm.get("provider", "openai")),
            temperature=float(run_config.llm.get("temperature", 0.7)),
            max_retries=int(run_config.llm.get("max_retries", 2)),
            allowed_actions=actions,
            controls=controls,
            scenario=scenario,
            agent=agent,
            variant_policy=variant_policy,
            proposal_count_per_node=int(branching_config["proposal_count_per_node"]),
            max_depth=int(branching_config["max_depth"]),
            beam_width=int(branching_config["beam_width"]),
            max_total_worlds=int(branching_config["max_total_worlds"]),
            include_policy_violating_actions=bool(branching_config["include_policy_violating_actions"]),
            include_misrepresentation_actions=bool(branching_config["include_misrepresentation_actions"]),
            require_action_classification=bool(branching_config["require_action_classification"]),
            execute_system_blocked_actions_as_attempts=bool(
                branching_config["execute_system_blocked_actions_as_attempts"]
            ),
            risk_guided_selection=bool(branching_config["risk_guided_selection"]),
            pressure_type=str(run_config.llm.get("pressure_type", "delivery_pressure")),
            agent_persona=str(run_config.llm.get("agent_persona", "red_team_requester")),
            control_visibility=str(run_config.llm.get("control_visibility", "control_full_red_team")),
            trial_index=run_config.llm.get("trial_index"),
            llm_seed=run_config.llm.get("seed"),
        )
        branching_result = generator.propose_for_needs(needs, max_purchase_needs=max_purchase_needs)
        if int(branching_config["max_depth"]) > 1:
            branching_result = _expand_multistage_branching(
                generator=generator,
                initial_result=branching_result,
                needs=needs[:max_purchase_needs],
                rule_engine=rule_engine,
                branching_config=branching_config,
                run_id=run_config.run_id,
            )
            plan = branching_result.planned_actions
        else:
            plan = _select_branching_actions(branching_result.planned_actions, branching_config)
        events = execute_branching_worlds(
            run_id=run_config.run_id,
            needs=needs,
            planned_actions=plan,
            rule_engine=rule_engine,
        )
    else:
        plan = build_behavior_plan(needs, max_purchase_needs=max_purchase_needs)
        engine = SimulationEngine(run_config.run_id, rule_engine)
        events = engine.run(needs, plan)

    ground_truth = read_yaml(repo_root / run_config.evaluation_inputs["ground_truth_labels"])
    annotations = detect_control_findings(events)
    findings = build_findings(annotations, events)
    evaluation_results = evaluate_findings(findings=findings, events=events, ground_truth=ground_truth)
    metrics = compute_metrics(
        events=events,
        annotations=annotations,
        findings=findings,
        evaluation_results=evaluation_results,
        variant_id=run_config.variant_id,
    )
    action_selection_metrics = None
    if llm_selection is not None:
        action_selection_metrics = compute_action_selection_metrics(
            decisions=llm_selection.decision_rows,
            llm_calls=llm_selection.call_rows,
            events=events,
            findings=findings,
        )
    if branching_result is not None:
        branching_artifacts = build_branching_artifacts(
            run_id=run_config.run_id,
            branching_config=_branching_config(run_config.branching),
            world_rows=branching_result.world_rows,
            planned_actions=plan,
            events=events,
            annotations=annotations,
            findings=findings,
            action_library_candidates=branching_result.action_library_candidates,
        )
        metrics.update(branching_artifacts["branching_summary"])

    run_dir = _resolve_run_dir(repo_root, run_config.outputs["dir"], run_config.run_id, output_root_override)
    run_config_rel = _repo_relative_or_str(config_path, repo_root)
    purchase_needs_rel = _repo_relative_or_str(purchase_needs_path, repo_root)
    ground_truth_path = repo_root / run_config.evaluation_inputs["ground_truth_labels"]
    manifest = {
        "run_id": run_config.run_id,
        "name": run_config.name,
        "created_at": now_utc_iso(),
        "process": run_config.process,
        "scenario_id": run_config.scenario_id,
        "variant_id": run_config.variant_id,
        "seed": run_config.seed,
        "behavior_mode": run_config.behavior_mode,
        "comparison_mode": run_config.comparison_mode,
        "code_version": _git_code_version(repo_root),
        "config_hashes": {
            "run_config": _sha256_file(config_path),
            "actions": _sha256_file(repo_root / run_config.inputs["actions"]),
            "controls": _sha256_file(repo_root / run_config.inputs["controls"]),
            "agents": _sha256_file(repo_root / run_config.inputs["agents"]),
            "scenarios": _sha256_file(repo_root / run_config.inputs["scenarios"]),
            "variants": _sha256_file(repo_root / run_config.inputs["variants"]),
        },
        "data_hashes": {
            "purchase_needs": _sha256_file(purchase_needs_path),
            "ground_truth_labels": _sha256_file(ground_truth_path),
        },
        "action_library": [action.action_id for action in actions],
        "forbidden_actions_present": [
            action.action_id
            for action in actions
            if action.action_id in {"submit_split_requests", "select_request_route"}
        ],
        "purchase_need_status_rules": {
            "open": "No purchase request has been created.",
            "partially_requested": "At least one purchase request exists and requested amount is below total need amount.",
            "requested": "Requested amount is equal to or above total need amount.",
            "postponed": "Requester chose postpone_request.",
        },
        "inputs": {
            "run_config": run_config_rel,
            "purchase_needs": purchase_needs_rel,
            "ground_truth_labels": run_config.evaluation_inputs["ground_truth_labels"],
        },
        "outputs": {
            "events": "events.jsonl",
            "detector_annotations": "detector_annotations.jsonl",
            "findings": "findings.json",
            "evaluation_results": "evaluation_results.json",
            "metrics": "metrics.json",
            "behavior_replay_log": "behavior_replay_log.jsonl",
            "finding_report": "finding_report.md",
        },
        "summary": {
            "event_count": metrics["event_count"],
            "finding_count": metrics["finding_count"],
            "split_order_bypass_success_count": metrics["split_order_bypass_success_count"],
        },
    }
    if llm_selection is not None:
        manifest["llm"] = {
            "provider": run_config.llm.get("provider", "openai"),
            "model": run_config.llm.get("model", "gpt-4.1-mini"),
            "temperature": run_config.llm.get("temperature", 0.2),
            "max_retries": run_config.llm.get("max_retries", 2),
            "pressure_condition": run_config.llm.get("pressure_condition", "pressure"),
            "prompt_treatment": run_config.llm.get("prompt_treatment", "full_context"),
            "pressure_type": run_config.llm.get("pressure_type"),
            "hint_strength": run_config.llm.get("hint_strength"),
            "agent_persona": run_config.llm.get("agent_persona"),
            "control_visibility": run_config.llm.get("control_visibility", "control_full"),
            "trial_index": run_config.llm.get("trial_index"),
            "seed": run_config.llm.get("seed"),
        }
        manifest["outputs"].update(
            {
                "llm_calls": "llm_calls.jsonl",
                "llm_action_decisions": "llm_action_decisions.jsonl",
                "action_selection_metrics": "action_selection_metrics.json",
                "llm_action_review_report": "llm_action_review_report.md",
            }
        )
    if branching_result is not None and branching_artifacts is not None:
        manifest["branching"] = _branching_config(run_config.branching)
        manifest["llm"] = {
            "provider": run_config.llm.get("provider", "openai"),
            "model": run_config.llm.get("model", "gpt-4.1-mini"),
            "temperature": run_config.llm.get("temperature", 0.7),
            "max_retries": run_config.llm.get("max_retries", 2),
            "pressure_type": run_config.llm.get("pressure_type"),
            "agent_persona": run_config.llm.get("agent_persona"),
            "control_visibility": run_config.llm.get("control_visibility"),
            "trial_index": run_config.llm.get("trial_index"),
            "seed": run_config.llm.get("seed"),
        }
        manifest["outputs"].update(
            {
                "branching_calls": "branching_calls.jsonl",
                "branching_proposals": "branching_proposals.jsonl",
                "branching_grounding": "branching_grounding.jsonl",
                "llm_action_decisions": "llm_action_decisions.jsonl",
                "branching_summary": "branching_summary.json",
                "world_summaries": "world_summaries.json",
                "world_tree": "world_tree.json",
                "action_library_candidates": "action_library_candidates.json",
                "branching_report": "branching_report.md",
                "residual_risk_report": "residual_risk_report.md",
            }
        )
        manifest["summary"].update(
            {
                "generated_world_count": branching_artifacts["branching_summary"]["generated_world_count"],
                "residual_risk_world_count": branching_artifacts["branching_summary"]["residual_risk_world_count"],
                "detector_detection_rate": branching_artifacts["branching_summary"]["detector_detection_rate"],
                "lineage_detection_rate": branching_artifacts["branching_summary"]["lineage_detection_rate"],
                "new_risk_detection_rate": branching_artifacts["branching_summary"]["new_risk_detection_rate"],
                "inherited_risk_count": branching_artifacts["branching_summary"]["inherited_risk_count"],
            }
        )

    write_json(run_dir / "run_manifest.json", manifest)
    write_jsonl(run_dir / "events.jsonl", events)
    write_jsonl(run_dir / "detector_annotations.jsonl", annotations)
    write_json(run_dir / "findings.json", {"findings": findings})
    write_json(run_dir / "evaluation_results.json", evaluation_results)
    write_json(run_dir / "metrics.json", metrics)
    write_jsonl(
        run_dir / "behavior_replay_log.jsonl",
        behavior_replay_rows(
            run_config.run_id,
            plan,
            behavior_mode=run_config.behavior_mode,
            comparison_mode=run_config.comparison_mode,
        ),
    )
    write_finding_report(run_dir / "finding_report.md", run_id=run_config.run_id, metrics=metrics, findings=findings)
    if llm_selection is not None and action_selection_metrics is not None:
        write_jsonl(run_dir / "llm_calls.jsonl", llm_selection.call_rows)
        write_jsonl(run_dir / "llm_action_decisions.jsonl", llm_selection.decision_rows)
        write_json(run_dir / "action_selection_metrics.json", action_selection_metrics)
        write_llm_action_review_report(
            run_dir / "llm_action_review_report.md",
            run_id=run_config.run_id,
            action_selection_metrics=action_selection_metrics,
            decisions=llm_selection.decision_rows,
            llm_calls=llm_selection.call_rows,
        )
    if branching_result is not None and branching_artifacts is not None:
        write_jsonl(run_dir / "branching_calls.jsonl", branching_result.call_rows)
        write_jsonl(run_dir / "branching_proposals.jsonl", branching_result.proposal_rows)
        write_jsonl(run_dir / "branching_grounding.jsonl", branching_result.grounding_rows)
        write_jsonl(run_dir / "llm_action_decisions.jsonl", branching_result.decision_rows)
        write_json(run_dir / "branching_summary.json", branching_artifacts["branching_summary"])
        write_json(run_dir / "world_summaries.json", {"worlds": branching_artifacts["world_summaries"]})
        write_json(run_dir / "world_tree.json", branching_artifacts["world_tree"])
        write_json(run_dir / "action_library_candidates.json", {"candidates": branching_result.action_library_candidates})
        write_branching_report(
            run_dir / "branching_report.md",
            run_id=run_config.run_id,
            summary=branching_artifacts["branching_summary"],
            world_summaries=branching_artifacts["world_summaries"],
        )
        write_residual_risk_report(
            run_dir / "residual_risk_report.md",
            residual_risks=branching_artifacts["residual_risks"],
        )

    return RunResult(
        run_id=run_config.run_id,
        run_dir=run_dir,
        manifest_path=run_dir / "run_manifest.json",
        events_path=run_dir / "events.jsonl",
        annotations_path=run_dir / "detector_annotations.jsonl",
        findings_path=run_dir / "findings.json",
        metrics_path=run_dir / "metrics.json",
        behavior_replay_path=run_dir / "behavior_replay_log.jsonl",
        report_path=run_dir / "finding_report.md",
    )


def compare_runs(baseline_run_dir: Path, variant_run_dir: Path, output_dir: Path) -> dict[str, Any]:
    baseline_metrics = read_json(baseline_run_dir / "metrics.json")
    variant_metrics = read_json(variant_run_dir / "metrics.json")
    baseline_manifest = read_json(baseline_run_dir / "run_manifest.json")
    variant_manifest = read_json(variant_run_dir / "run_manifest.json")
    comparison = compare_metric_sets(baseline_metrics, variant_metrics)
    comparison["baseline_run_id"] = baseline_manifest["run_id"]
    comparison["variant_run_id"] = variant_manifest["run_id"]
    comparison["comparison_mode"] = baseline_manifest.get("comparison_mode", "frozen_behavior")
    baseline_action_metrics_path = baseline_run_dir / "action_selection_metrics.json"
    variant_action_metrics_path = variant_run_dir / "action_selection_metrics.json"
    if baseline_action_metrics_path.exists() and variant_action_metrics_path.exists():
        comparison["action_selection_metrics"] = compare_action_selection_metric_sets(
            read_json(baseline_action_metrics_path),
            read_json(variant_action_metrics_path),
        )

    write_json(output_dir / "comparison.json", comparison)
    write_comparison_report(output_dir / "comparison_report.md", comparison)
    return comparison


def _expand_multistage_branching(
    *,
    generator: LLMBranchingProposalGenerator,
    initial_result: LLMBranchingResult,
    needs: list[Any],
    rule_engine: RuleEngine,
    branching_config: dict[str, Any],
    run_id: str,
) -> LLMBranchingResult:
    result = initial_result
    max_depth = int(branching_config.get("max_depth", 1))
    max_total_worlds = int(branching_config.get("max_total_worlds", 100))
    if max_depth <= 1 or not result.world_rows:
        return result

    needs_by_id = {need.purchase_need_id: need for need in needs}
    frontier = list(result.world_rows)
    next_sequence = _next_branching_sequence(result.planned_actions)
    next_world_index = _next_branching_world_index(result.world_rows)
    seen_world_signatures = _branching_world_signatures(result.world_rows, result.planned_actions)

    while frontier and len(result.world_rows) < max_total_worlds:
        parent_events = execute_branching_worlds(
            run_id=run_id,
            needs=needs,
            planned_actions=result.planned_actions,
            rule_engine=rule_engine,
        )
        events_by_world = _rows_by_world(parent_events)
        actions_by_world = _actions_by_world(result.planned_actions)
        parents = _select_expandable_branching_parents(
            frontier=frontier,
            events_by_world=events_by_world,
            branching_config=branching_config,
        )
        if not parents:
            break

        next_frontier: list[dict[str, Any]] = []
        for parent in parents:
            remaining_worlds = max_total_worlds - len(result.world_rows)
            if remaining_worlds <= 0:
                break
            need = needs_by_id[parent["purchase_need_id"]]
            child_result = generator.propose_next_for_world(
                need=need,
                parent_world=parent,
                parent_actions=actions_by_world.get(parent["world_id"], []),
                parent_events=events_by_world.get(parent["world_id"], []),
                first_sequence=next_sequence,
                first_world_index=next_world_index,
            )
            child_result = _deduplicate_branching_result_worlds(child_result, seen_world_signatures)
            child_result = _limit_branching_result_worlds(child_result, remaining_worlds)
            if not child_result.world_rows:
                continue
            result = _combine_branching_results(result, child_result)
            next_frontier.extend(child_result.world_rows)
            next_sequence = _next_branching_sequence(result.planned_actions)
            next_world_index = _next_branching_world_index(result.world_rows)
        frontier = next_frontier
    return result


def _select_expandable_branching_parents(
    *,
    frontier: list[dict[str, Any]],
    events_by_world: dict[str, list[dict[str, Any]]],
    branching_config: dict[str, Any],
) -> list[dict[str, Any]]:
    max_depth = int(branching_config.get("max_depth", 1))
    candidates: list[dict[str, Any]] = []
    for world in frontier:
        if int(world.get("depth", 1)) >= max_depth:
            continue
        if world.get("status") in {"unsupported", "blocked", "out_of_scope"}:
            continue
        world_events = events_by_world.get(world["world_id"], [])
        if not world_events:
            continue
        terminal_state = world_events[-1]["state_after"]
        if terminal_state in {"paid", "blocked_attempt", "postponed"}:
            continue
        candidates.append(world)
    if branching_config.get("risk_guided_selection", True):
        candidates = sorted(candidates, key=lambda world: (-int(world.get("risk_score", 0)), world["world_id"]))
    return candidates[: max(1, int(branching_config.get("beam_width", 1)))]


def _rows_by_world(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("world_id", "")), []).append(row)
    return grouped


def _actions_by_world(actions: list[PlannedAction]) -> dict[str, list[PlannedAction]]:
    grouped: dict[str, list[PlannedAction]] = {}
    for action in actions:
        grouped.setdefault(action.world_id, []).append(action)
    return grouped


def _next_branching_sequence(actions: list[PlannedAction]) -> int:
    return max((int(action.sequence) for action in actions), default=0) + 1


def _next_branching_world_index(world_rows: list[dict[str, Any]]) -> int:
    return len(world_rows) + 1


def _deduplicate_branching_result_worlds(
    result: LLMBranchingResult,
    seen_signatures: set[str],
) -> LLMBranchingResult:
    actions_by_world = _actions_by_world(result.planned_actions)
    selected_world_ids: set[str] = set()
    for row in result.world_rows:
        signature = _branching_world_signature(row, actions_by_world.get(row["world_id"], []))
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        selected_world_ids.add(row["world_id"])
    return _filter_branching_result_worlds(result, selected_world_ids)


def _branching_world_signatures(
    world_rows: list[dict[str, Any]],
    planned_actions: list[PlannedAction],
) -> set[str]:
    actions_by_world = _actions_by_world(planned_actions)
    return {
        _branching_world_signature(row, actions_by_world.get(row["world_id"], []))
        for row in world_rows
    }


def _branching_world_signature(row: dict[str, Any], actions: list[PlannedAction]) -> str:
    return json.dumps(
        {
            "parent_world_id": row.get("parent_world_id", ""),
            "classification": row.get("classification", ""),
            "policy_violation_flags": row.get("policy_violation_flags", []),
            "integrity_flags": row.get("integrity_flags", []),
            "actions": [
                {
                    "action_id": action.action_id,
                    "parameters": {
                        key: value
                        for key, value in action.parameters.items()
                        if not str(key).startswith("_lineage_")
                    },
                }
                for action in actions
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _limit_branching_result_worlds(result: LLMBranchingResult, max_worlds: int) -> LLMBranchingResult:
    selected_world_ids = {row["world_id"] for row in result.world_rows[:max_worlds]}
    return _filter_branching_result_worlds(result, selected_world_ids)


def _filter_branching_result_worlds(
    result: LLMBranchingResult,
    selected_world_ids: set[str],
) -> LLMBranchingResult:
    return LLMBranchingResult(
        planned_actions=[action for action in result.planned_actions if action.world_id in selected_world_ids],
        call_rows=result.call_rows,
        proposal_rows=[row for row in result.proposal_rows if row["world_id"] in selected_world_ids],
        grounding_rows=[row for row in result.grounding_rows if row["world_id"] in selected_world_ids],
        decision_rows=[row for row in result.decision_rows if row.get("world_id") in selected_world_ids],
        world_rows=[row for row in result.world_rows if row["world_id"] in selected_world_ids],
        action_library_candidates=[
            row for row in result.action_library_candidates if row["world_id"] in selected_world_ids
        ],
    )


def _combine_branching_results(left: LLMBranchingResult, right: LLMBranchingResult) -> LLMBranchingResult:
    return LLMBranchingResult(
        planned_actions=[*left.planned_actions, *right.planned_actions],
        call_rows=[*left.call_rows, *right.call_rows],
        proposal_rows=[*left.proposal_rows, *right.proposal_rows],
        grounding_rows=[*left.grounding_rows, *right.grounding_rows],
        decision_rows=[*left.decision_rows, *right.decision_rows],
        world_rows=[*left.world_rows, *right.world_rows],
        action_library_candidates=[*left.action_library_candidates, *right.action_library_candidates],
    )


def run_first_slice(repo_root: Path, *, output_root_override: Path | None = None) -> dict[str, Any]:
    data_dir = repo_root / "data/synthetic"
    baseline_config = load_run_config(repo_root / "configs/run_configs/baseline.yaml")
    generated_path = generate_synthetic_data(
        data_dir,
        count=_max_purchase_needs(baseline_config.simulation),
        seed=baseline_config.seed,
    )
    baseline = run_simulation(
        repo_root,
        repo_root / "configs/run_configs/baseline.yaml",
        output_root_override=output_root_override,
        purchase_needs_path_override=generated_path,
    )
    variant = run_simulation(
        repo_root,
        repo_root / "configs/run_configs/variant_a.yaml",
        output_root_override=output_root_override,
        purchase_needs_path_override=generated_path,
    )
    output_root = output_root_override or repo_root / "runs"
    comparison_dir = output_root / "comparisons/CMP-S002-BASELINE-VARIANT-A"
    comparison = compare_runs(baseline.run_dir, variant.run_dir, comparison_dir)
    return {
        "baseline": baseline,
        "variant": variant,
        "comparison_dir": comparison_dir,
        "comparison": comparison,
    }


def run_llm_action_slice(repo_root: Path, *, output_root_override: Path | None = None) -> dict[str, Any]:
    baseline_config = load_run_config(repo_root / "configs/run_configs/llm_baseline.yaml")
    generated_path = repo_root / baseline_config.inputs["purchase_needs"]
    if not generated_path.exists():
        generated_path = generate_synthetic_data(
            generated_path.parent,
            count=int(baseline_config.llm.get("input_fixture_count", 100)),
            seed=baseline_config.seed,
        )
    baseline = run_simulation(
        repo_root,
        repo_root / "configs/run_configs/llm_baseline.yaml",
        output_root_override=output_root_override,
        purchase_needs_path_override=generated_path,
    )
    variant = run_simulation(
        repo_root,
        repo_root / "configs/run_configs/llm_variant_a.yaml",
        output_root_override=output_root_override,
        purchase_needs_path_override=generated_path,
    )
    output_root = output_root_override or repo_root / "runs"
    comparison_dir = output_root / "comparisons/CMP-S002-LLM-BASELINE-VARIANT-A"
    comparison = compare_runs(baseline.run_dir, variant.run_dir, comparison_dir)
    return {
        "baseline": baseline,
        "variant": variant,
        "comparison_dir": comparison_dir,
        "comparison": comparison,
    }


def run_branching_simulation(
    repo_root: Path,
    *,
    output_root_override: Path | None = None,
    provider: str = "openai",
    model: str = "gpt-4.1-mini",
    temperature: float = 0.7,
) -> dict[str, Any]:
    base_config_path = repo_root / "configs/run_configs/branching_baseline.yaml"
    base_config = read_yaml(base_config_path)
    purchase_needs_path = repo_root / base_config["inputs"]["purchase_needs"]
    if not purchase_needs_path.exists():
        purchase_needs_path = generate_synthetic_data(
            purchase_needs_path.parent,
            count=int(base_config.get("llm", {}).get("input_fixture_count", 100)),
            seed=int(base_config["seed"]),
        )

    config = copy.deepcopy(base_config)
    config["llm"]["provider"] = provider
    config["llm"]["model"] = model
    config["llm"]["temperature"] = temperature
    config_root = output_root_override or repo_root / "runs"
    config_path = config_root / "configs" / f"{config['run_id']}.yaml"
    write_yaml(config_path, config)
    result = run_simulation(
        repo_root,
        config_path,
        output_root_override=output_root_override,
        purchase_needs_path_override=purchase_needs_path,
    )
    return {"run": result, "config_path": config_path}


def run_branching_variant_comparison(
    repo_root: Path,
    *,
    output_root_override: Path | None = None,
    provider: str = "openai",
    model: str = "gpt-4.1-mini",
    temperature: float = 0.7,
) -> dict[str, Any]:
    baseline_result = run_branching_simulation(
        repo_root,
        output_root_override=output_root_override,
        provider=provider,
        model=model,
        temperature=temperature,
    )
    baseline_run: RunResult = baseline_result["run"]
    base_config = read_yaml(baseline_result["config_path"])
    purchase_needs_path = repo_root / base_config["inputs"]["purchase_needs"]
    needs = read_purchase_needs_csv(purchase_needs_path)
    controls = load_control_cards(repo_root / base_config["inputs"]["controls"])
    ground_truth = read_yaml(repo_root / base_config["evaluation_inputs"]["ground_truth_labels"])
    branching_config = _branching_config(base_config.get("branching", {}))
    planned_actions = [
        _planned_action_from_behavior_row(row)
        for row in read_jsonl(baseline_run.run_dir / "behavior_replay_log.jsonl")
    ]
    world_rows = read_json(baseline_run.run_dir / "world_summaries.json")["worlds"]
    action_library_candidates = read_json(baseline_run.run_dir / "action_library_candidates.json")["candidates"]

    variant_runs: dict[str, dict[str, Any]] = {}
    for variant_id in BRANCHING_COMPARISON_VARIANTS:
        variant_policy = load_variant_policy(repo_root, variant_id)
        run_id = f"RUN-S002-BRANCHING-{_branching_variant_label(variant_id)}"
        rule_engine = RuleEngine(controls, variant_policy)
        events = execute_branching_worlds(
            run_id=run_id,
            needs=needs,
            planned_actions=planned_actions,
            rule_engine=rule_engine,
        )
        annotations = detect_control_findings(events)
        findings = build_findings(annotations, events)
        evaluation_results = evaluate_findings(findings=findings, events=events, ground_truth=ground_truth)
        metrics = compute_metrics(
            events=events,
            annotations=annotations,
            findings=findings,
            evaluation_results=evaluation_results,
            variant_id=variant_id,
        )
        artifacts = build_branching_artifacts(
            run_id=run_id,
            branching_config=branching_config,
            world_rows=world_rows,
            planned_actions=planned_actions,
            events=events,
            annotations=annotations,
            findings=findings,
            action_library_candidates=action_library_candidates,
        )
        metrics.update(artifacts["branching_summary"])
        variant_runs[variant_id] = {
            "run_id": run_id,
            "variant_name": variant_policy.name,
            "metrics": metrics,
            "branching_summary": artifacts["branching_summary"],
            "world_summaries": artifacts["world_summaries"],
            "findings": findings,
        }

    comparison = _build_branching_variant_comparison(
        source_run_id=baseline_run.run_id,
        provider=provider,
        model=model,
        temperature=temperature,
        variant_runs=variant_runs,
    )
    comparison_dir = (output_root_override or repo_root / "runs") / "comparisons/CMP-S002-BRANCHING-BASELINE-VARIANTS"
    write_json(comparison_dir / "branching_variant_comparison.json", comparison)
    _write_branching_variant_comparison_report(
        comparison_dir / "branching_variant_comparison_report.md",
        comparison,
    )
    return {
        "baseline_run": baseline_run,
        "comparison_dir": comparison_dir,
        "comparison": comparison,
    }


def _planned_action_from_behavior_row(row: dict[str, Any]) -> PlannedAction:
    parameters = dict(row.get("parameters", {}))
    purchase_need_id = str(parameters.get("purchase_need_id", row.get("purchase_need_id", "")))
    return PlannedAction(
        sequence=int(row["sequence"]),
        purchase_need_id=purchase_need_id,
        action_id=str(row["selected_action_id"]),
        parameters=parameters,
        rationale=str(row.get("rationale", "")),
        allowed_actions=[str(action_id) for action_id in row.get("allowed_actions_presented", [])],
        source=str(row.get("source", "branching_replay")),
        classification=str(row.get("classification", "compliant")),
        policy_violation_flags=[str(item) for item in row.get("policy_violation_flags", [])],
        integrity_flags=[str(item) for item in row.get("integrity_flags", [])],
        world_id=str(row.get("world_id", "")),
        parent_world_id=str(row.get("parent_world_id", "")),
        branch_reason=str(row.get("branch_reason", "")),
        proposal_id=str(row.get("proposal_id", "")),
        risk_score=int(row.get("risk_score", 0)),
        depth=int(row.get("depth", 1)),
    )


def _branching_variant_label(variant_id: str) -> str:
    labels = {
        "baseline": "BASELINE",
        "variant_a_7d_aggregation": "VARIANT-A",
        "variant_b_emergency_post_approval": "VARIANT-B",
    }
    return labels.get(variant_id, variant_id.upper().replace("_", "-"))


def _build_branching_variant_comparison(
    *,
    source_run_id: str,
    provider: str,
    model: str,
    temperature: float,
    variant_runs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    baseline_findings_by_world = _findings_by_world(variant_runs["baseline"]["findings"])
    variants: dict[str, Any] = {}
    worlds: list[dict[str, Any]] = []
    baseline_worlds = {
        world["world_id"]: world
        for world in variant_runs["baseline"]["world_summaries"]
    }

    for variant_id, result in variant_runs.items():
        findings_by_world = _findings_by_world(result["findings"])
        summary = result["branching_summary"]
        findings = result["findings"]
        variants[variant_id] = {
            "run_id": result["run_id"],
            "variant_name": result["variant_name"],
            "generated_world_count": summary["generated_world_count"],
            "detector_detection_rate": summary["detector_detection_rate"],
            "detector_detection_rate_numerator": summary["detector_detection_rate_numerator"],
            "detector_detection_rate_denominator": summary["detector_detection_rate_denominator"],
            "lineage_detection_rate": summary.get("lineage_detection_rate", summary["detector_detection_rate"]),
            "new_risk_detection_rate": summary.get("new_risk_detection_rate", 0.0),
            "current_world_detection_rate": summary.get("current_world_detection_rate", 0.0),
            "inherited_risk_count": summary.get("inherited_risk_count", 0),
            "inherited_risk_world_count": summary.get("inherited_risk_world_count", 0),
            "unmitigated_finding_count": sum(
                1 for finding in findings if finding.get("status") == "candidate_unmitigated"
            ),
            "mitigated_finding_count": sum(
                1 for finding in findings if finding.get("status") == "candidate_mitigated"
            ),
            "residual_risk_world_count": summary["residual_risk_world_count"],
        }
        for world in result["world_summaries"]:
            if variant_id == "baseline":
                continue
            world_id = world["world_id"]
            baseline_unmitigated = _world_defects(
                baseline_findings_by_world.get(world_id, []),
                status="candidate_unmitigated",
            )
            variant_unmitigated = _world_defects(
                findings_by_world.get(world_id, []),
                status="candidate_unmitigated",
            )
            variant_mitigated = _world_defects(
                findings_by_world.get(world_id, []),
                status="candidate_mitigated",
            )
            worlds.append(
                {
                    "variant_id": variant_id,
                    "world_id": world_id,
                    "branch_reason": baseline_worlds.get(world_id, {}).get("branch_reason", ""),
                    "classification": baseline_worlds.get(world_id, {}).get("classification", ""),
                    "baseline_unmitigated_defects": baseline_unmitigated,
                    "variant_unmitigated_defects": variant_unmitigated,
                    "variant_mitigated_defects": variant_mitigated,
                    "defects_mitigated_by_variant": sorted(
                        set(baseline_unmitigated) - set(variant_unmitigated)
                    ),
                    "new_unmitigated_defects": sorted(set(variant_unmitigated) - set(baseline_unmitigated)),
                }
            )

    return {
        "comparison_mode": "branching_variant_replay",
        "world_group_source_run_id": source_run_id,
        "same_world_group_replayed": True,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "variants": variants,
        "world_effects": worlds,
    }


def _findings_by_world(findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for finding in findings:
        grouped.setdefault(str(finding.get("world_id", "")), []).append(finding)
    return grouped


def _world_defects(findings: list[dict[str, Any]], *, status: str) -> list[str]:
    return sorted({str(finding["defect_id"]) for finding in findings if finding.get("status") == status})


def _write_branching_variant_comparison_report(path: Path, comparison: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Branching Variant Comparison",
        "",
        f"- comparison_mode: {comparison['comparison_mode']}",
        f"- world_group_source_run_id: {comparison['world_group_source_run_id']}",
        f"- same_world_group_replayed: {comparison['same_world_group_replayed']}",
        f"- model: {comparison['model']}",
        f"- temperature: {comparison['temperature']}",
        "",
        "## Variant Summary",
        "",
        "| Variant | Lineage detection | New-risk detection | Inherited risks | Unmitigated findings | Mitigated findings | Residual worlds |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for variant_id, summary in comparison["variants"].items():
        lines.append(
            f"| {variant_id} | "
            f"{summary['detector_detection_rate_numerator']}/{summary['detector_detection_rate_denominator']} "
            f"({summary['detector_detection_rate']}) | "
            f"{summary['new_risk_detection_rate']} | "
            f"{summary['inherited_risk_count']} | "
            f"{summary['unmitigated_finding_count']} | "
            f"{summary['mitigated_finding_count']} | "
            f"{summary['residual_risk_world_count']} |"
        )

    lines.extend(
        [
            "",
            "## World Effects",
            "",
            "| Variant | World | Branch | Baseline unmitigated | Variant mitigated | Variant unmitigated |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in comparison["world_effects"]:
        lines.append(
            f"| {row['variant_id']} | {row['world_id']} | {row['branch_reason']} | "
            f"{row['baseline_unmitigated_defects']} | "
            f"{row['variant_mitigated_defects']} | "
            f"{row['variant_unmitigated_defects']} |"
        )
    lines.append("")
    lines.append(
        "Interpretation: Variant A should mainly mitigate split-request worlds, while Variant B should mainly mitigate emergency-route worlds. "
        "Underreported amount and informal preapproval remain separate review surfaces."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_pressure_condition_experiment(
    repo_root: Path,
    *,
    trials: int = 10,
    output_root_override: Path | None = None,
    provider: str = "openai",
    model: str = "gpt-4.1-mini",
    temperature: float = 0.7,
) -> dict[str, Any]:
    experiment_id = f"EXP-S002-PRESSURE-CONTROL-{trials}X"
    experiment_dir = (output_root_override or repo_root / "runs/experiments") / experiment_id
    configs_dir = experiment_dir / "configs"
    runs_root = experiment_dir / "runs"

    base_config = read_yaml(repo_root / "configs/run_configs/llm_baseline.yaml")
    purchase_needs_path = repo_root / base_config["inputs"]["purchase_needs"]
    if not purchase_needs_path.exists():
        purchase_needs_path = generate_synthetic_data(
            purchase_needs_path.parent,
            count=int(base_config.get("llm", {}).get("input_fixture_count", 100)),
            seed=int(base_config["seed"]),
        )

    trial_results: list[dict[str, Any]] = []
    for condition in ["pressure", "no_pressure"]:
        for trial_index in range(1, trials + 1):
            config = _pressure_trial_config(
                base_config,
                condition=condition,
                trial_index=trial_index,
                provider=provider,
                model=model,
                temperature=temperature,
                prompt_treatment="full_context",
            )
            config_path = configs_dir / f"{config['run_id']}.yaml"
            write_yaml(config_path, config)
            result = run_simulation(
                repo_root,
                config_path,
                output_root_override=runs_root,
                purchase_needs_path_override=purchase_needs_path,
            )
            trial_results.append(_pressure_trial_result("full_context", condition, trial_index, result.run_dir))

    summary = _summarize_pressure_trials(
        experiment_id=experiment_id,
        trials=trials,
        provider=provider,
        model=model,
        temperature=temperature,
        prompt_treatment="full_context",
        trial_results=trial_results,
    )
    write_json(experiment_dir / "summary.json", summary)
    _write_pressure_effect_report(experiment_dir / "pressure_effect_report.md", summary)
    return {
        "experiment_id": experiment_id,
        "experiment_dir": experiment_dir,
        "summary": summary,
    }


def run_prompt_ablation_experiment(
    repo_root: Path,
    *,
    trials: int = 10,
    output_root_override: Path | None = None,
    provider: str = "openai",
    model: str = "gpt-4.1-mini",
    temperature: float = 0.7,
    prompt_treatments: list[str] | None = None,
    experiment_id_override: str | None = None,
) -> dict[str, Any]:
    treatments = prompt_treatments or list(PROMPT_TREATMENTS)
    unknown = sorted(set(treatments) - set(SUPPORTED_PROMPT_TREATMENTS))
    if unknown:
        raise ValueError(f"Unknown prompt treatments: {', '.join(unknown)}")

    experiment_id = experiment_id_override or f"EXP-S002-PROMPT-ABLATION-{trials}X"
    experiment_dir = (output_root_override or repo_root / "runs/experiments") / experiment_id
    configs_dir = experiment_dir / "configs"
    runs_root = experiment_dir / "runs"

    base_config = read_yaml(repo_root / "configs/run_configs/llm_baseline.yaml")
    purchase_needs_path = repo_root / base_config["inputs"]["purchase_needs"]
    if not purchase_needs_path.exists():
        purchase_needs_path = generate_synthetic_data(
            purchase_needs_path.parent,
            count=int(base_config.get("llm", {}).get("input_fixture_count", 100)),
            seed=int(base_config["seed"]),
        )

    trial_results: list[dict[str, Any]] = []
    for prompt_treatment in treatments:
        for condition in ["pressure", "no_pressure"]:
            for trial_index in range(1, trials + 1):
                config = _pressure_trial_config(
                    base_config,
                    condition=condition,
                    trial_index=trial_index,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    prompt_treatment=prompt_treatment,
                    comparison_mode="prompt_ablation_experiment",
                    include_treatment_slug=True,
                )
                config_path = configs_dir / f"{config['run_id']}.yaml"
                write_yaml(config_path, config)
                result = run_simulation(
                    repo_root,
                    config_path,
                    output_root_override=runs_root,
                    purchase_needs_path_override=purchase_needs_path,
                )
                trial_results.append(_pressure_trial_result(prompt_treatment, condition, trial_index, result.run_dir))

    summary = _summarize_prompt_ablation_trials(
        experiment_id=experiment_id,
        trials=trials,
        provider=provider,
        model=model,
        temperature=temperature,
        prompt_treatments=treatments,
        trial_results=trial_results,
    )
    write_json(experiment_dir / "summary.json", summary)
    _write_prompt_ablation_report(experiment_dir / "prompt_ablation_report.md", summary)
    return {
        "experiment_id": experiment_id,
        "experiment_dir": experiment_dir,
        "summary": summary,
    }


def run_balanced_planning_hint_experiment(
    repo_root: Path,
    *,
    trials: int = 10,
    output_root_override: Path | None = None,
    provider: str = "openai",
    model: str = "gpt-4.1-mini",
    temperature: float = 0.7,
) -> dict[str, Any]:
    return run_prompt_ablation_experiment(
        repo_root,
        trials=trials,
        output_root_override=output_root_override,
        provider=provider,
        model=model,
        temperature=temperature,
        prompt_treatments=["balanced_planning_hint"],
        experiment_id_override=f"EXP-S002-BALANCED-PLANNING-HINT-{trials}X",
    )


def run_hint_pressure_matrix_experiment(
    repo_root: Path,
    *,
    trials: int = 5,
    output_root_override: Path | None = None,
    provider: str = "openai",
    model: str = "gpt-4.1-mini",
    temperature: float = 0.7,
    hint_strengths: list[str] | None = None,
    pressure_types: list[str] | None = None,
) -> dict[str, Any]:
    hints = hint_strengths or list(HINT_STRENGTHS)
    pressures = pressure_types or list(PRESSURE_TYPES)
    unknown_hints = sorted(set(hints) - set(HINT_STRENGTHS))
    unknown_pressures = sorted(set(pressures) - set(PRESSURE_TYPES))
    if unknown_hints:
        raise ValueError(f"Unknown hint strengths: {', '.join(unknown_hints)}")
    if unknown_pressures:
        raise ValueError(f"Unknown pressure types: {', '.join(unknown_pressures)}")

    experiment_id = f"EXP-S002-HINT-PRESSURE-MATRIX-{trials}X"
    experiment_dir = (output_root_override or repo_root / "runs/experiments") / experiment_id
    configs_dir = experiment_dir / "configs"
    runs_root = experiment_dir / "runs"

    base_config = read_yaml(repo_root / "configs/run_configs/llm_baseline.yaml")
    purchase_needs_path = repo_root / base_config["inputs"]["purchase_needs"]
    if not purchase_needs_path.exists():
        purchase_needs_path = generate_synthetic_data(
            purchase_needs_path.parent,
            count=int(base_config.get("llm", {}).get("input_fixture_count", 100)),
            seed=int(base_config["seed"]),
        )

    trial_results: list[dict[str, Any]] = []
    for hint_strength in hints:
        for pressure_type in pressures:
            for trial_index in range(1, trials + 1):
                config = _matrix_trial_config(
                    base_config,
                    hint_strength=hint_strength,
                    pressure_type=pressure_type,
                    trial_index=trial_index,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                )
                config_path = configs_dir / f"{config['run_id']}.yaml"
                write_yaml(config_path, config)
                result = run_simulation(
                    repo_root,
                    config_path,
                    output_root_override=runs_root,
                    purchase_needs_path_override=purchase_needs_path,
                )
                trial_results.append(
                    _matrix_trial_result(
                        hint_strength=hint_strength,
                        pressure_type=pressure_type,
                        trial_index=trial_index,
                        run_dir=result.run_dir,
                    )
                )

    summary = _summarize_hint_pressure_matrix(
        experiment_id=experiment_id,
        trials=trials,
        provider=provider,
        model=model,
        temperature=temperature,
        hint_strengths=hints,
        pressure_types=pressures,
        trial_results=trial_results,
    )
    write_json(experiment_dir / "summary.json", summary)
    _write_hint_pressure_matrix_report(experiment_dir / "hint_pressure_matrix_report.md", summary)
    return {
        "experiment_id": experiment_id,
        "experiment_dir": experiment_dir,
        "summary": summary,
    }


def run_agent_stress_experiment(
    repo_root: Path,
    *,
    trials: int = 3,
    output_root_override: Path | None = None,
    provider: str = "openai",
    model: str = "gpt-4.1-mini",
    temperature: float = 0.7,
) -> dict[str, Any]:
    experiment_id = f"EXP-S002-AGENT-STRESS-{trials}X"
    experiment_dir = (output_root_override or repo_root / "runs/experiments") / experiment_id
    configs_dir = experiment_dir / "configs"
    runs_root = experiment_dir / "runs"

    base_config = read_yaml(repo_root / "configs/run_configs/llm_baseline.yaml")
    purchase_needs_path = repo_root / base_config["inputs"]["purchase_needs"]
    if not purchase_needs_path.exists():
        purchase_needs_path = generate_synthetic_data(
            purchase_needs_path.parent,
            count=int(base_config.get("llm", {}).get("input_fixture_count", 100)),
            seed=int(base_config["seed"]),
        )

    closed_results: list[dict[str, Any]] = []
    for agent_persona in AGENT_PERSONAS:
        for trial_index in range(1, trials + 1):
            config = _agent_stress_closed_trial_config(
                base_config,
                agent_persona=agent_persona,
                trial_index=trial_index,
                provider=provider,
                model=model,
                temperature=temperature,
            )
            config_path = configs_dir / f"{config['run_id']}.yaml"
            write_yaml(config_path, config)
            result = run_simulation(
                repo_root,
                config_path,
                output_root_override=runs_root,
                purchase_needs_path_override=purchase_needs_path,
            )
            closed_results.append(
                _agent_stress_closed_trial_result(
                    agent_persona=agent_persona,
                    trial_index=trial_index,
                    run_dir=result.run_dir,
                )
            )

    open_results: list[dict[str, Any]] = []
    for control_visibility in CONTROL_VISIBILITIES:
        for trial_index in range(1, trials + 1):
            config = _agent_stress_open_trial_config(
                base_config,
                control_visibility=control_visibility,
                trial_index=trial_index,
                provider=provider,
                model=model,
                temperature=temperature,
            )
            config_path = configs_dir / f"{config['run_id']}.yaml"
            write_yaml(config_path, config)
            run_dir = _run_open_proposal_trial(
                repo_root,
                config_path,
                output_root_override=runs_root,
                purchase_needs_path_override=purchase_needs_path,
            )
            open_results.append(
                _agent_stress_open_trial_result(
                    control_visibility=control_visibility,
                    trial_index=trial_index,
                    run_dir=run_dir,
                )
            )

    summary = _summarize_agent_stress_experiment(
        experiment_id=experiment_id,
        trials=trials,
        provider=provider,
        model=model,
        temperature=temperature,
        closed_results=closed_results,
        open_results=open_results,
    )
    write_json(experiment_dir / "summary.json", summary)
    _write_agent_stress_report(experiment_dir / "agent_stress_report.md", summary)
    return {
        "experiment_id": experiment_id,
        "experiment_dir": experiment_dir,
        "summary": summary,
    }


def _run_open_proposal_trial(
    repo_root: Path,
    config_path: Path,
    *,
    output_root_override: Path,
    purchase_needs_path_override: Path,
) -> Path:
    validate_or_raise(repo_root)
    run_config = load_run_config(config_path)

    actions = load_action_definitions(repo_root / run_config.inputs["actions"])
    controls = load_control_cards(repo_root / run_config.inputs["controls"])
    scenarios = load_scenarios(repo_root / run_config.inputs["scenarios"])
    agents = load_agent_profiles(repo_root / run_config.inputs["agents"])
    variant_policy = load_variant_policy(repo_root, run_config.variant_id)
    rule_engine = RuleEngine(controls, variant_policy)
    needs = read_purchase_needs_csv(purchase_needs_path_override)
    scenario = _select_scenario(scenarios, run_config.scenario_id)
    agent = _select_requester_agent(agents)

    generator = LLMOpenProposalGenerator(
        repo_root=repo_root,
        run_id=run_config.run_id,
        model=str(run_config.llm.get("model", "gpt-4.1-mini")),
        provider=str(run_config.llm.get("provider", "openai")),
        temperature=float(run_config.llm.get("temperature", 0.7)),
        max_retries=int(run_config.llm.get("max_retries", 2)),
        allowed_actions=actions,
        controls=controls,
        scenario=scenario,
        agent=agent,
        variant_policy=variant_policy,
        pressure_type=str(run_config.llm.get("pressure_type", "delivery_pressure")),
        agent_persona=str(run_config.llm.get("agent_persona", "red_team_requester")),
        control_visibility=str(run_config.llm.get("control_visibility", "control_full_red_team")),
        trial_index=run_config.llm.get("trial_index"),
        llm_seed=run_config.llm.get("seed"),
    )
    proposal_result: LLMProposalResult = generator.propose_for_needs(
        needs,
        max_purchase_needs=_max_purchase_needs(run_config.simulation),
    )
    plan = proposal_result.planned_actions
    engine = SimulationEngine(run_config.run_id, rule_engine)
    events = engine.run(needs, plan)

    ground_truth = read_yaml(repo_root / run_config.evaluation_inputs["ground_truth_labels"])
    annotations = detect_control_findings(events)
    findings = build_findings(annotations, events)
    evaluation_results = evaluate_findings(findings=findings, events=events, ground_truth=ground_truth)
    metrics = compute_metrics(
        events=events,
        annotations=annotations,
        findings=findings,
        evaluation_results=evaluation_results,
        variant_id=run_config.variant_id,
    )
    action_selection_metrics = compute_action_selection_metrics(
        decisions=proposal_result.decision_rows,
        llm_calls=proposal_result.call_rows,
        events=events,
        findings=findings,
    )
    proposal_metrics = _compute_open_proposal_metrics(
        proposal_rows=proposal_result.proposal_rows,
        grounding_rows=proposal_result.grounding_rows,
        findings=findings,
    )
    action_selection_metrics.update(proposal_metrics)

    run_dir = _resolve_run_dir(repo_root, run_config.outputs["dir"], run_config.run_id, output_root_override)
    run_config_rel = _repo_relative_or_str(config_path, repo_root)
    purchase_needs_rel = _repo_relative_or_str(purchase_needs_path_override, repo_root)
    ground_truth_path = repo_root / run_config.evaluation_inputs["ground_truth_labels"]
    manifest = {
        "run_id": run_config.run_id,
        "name": run_config.name,
        "created_at": now_utc_iso(),
        "process": run_config.process,
        "scenario_id": run_config.scenario_id,
        "variant_id": run_config.variant_id,
        "seed": run_config.seed,
        "behavior_mode": run_config.behavior_mode,
        "comparison_mode": run_config.comparison_mode,
        "code_version": _git_code_version(repo_root),
        "config_hashes": {
            "run_config": _sha256_file(config_path),
            "actions": _sha256_file(repo_root / run_config.inputs["actions"]),
            "controls": _sha256_file(repo_root / run_config.inputs["controls"]),
            "agents": _sha256_file(repo_root / run_config.inputs["agents"]),
            "scenarios": _sha256_file(repo_root / run_config.inputs["scenarios"]),
            "variants": _sha256_file(repo_root / run_config.inputs["variants"]),
        },
        "data_hashes": {
            "purchase_needs": _sha256_file(purchase_needs_path_override),
            "ground_truth_labels": _sha256_file(ground_truth_path),
        },
        "inputs": {
            "run_config": run_config_rel,
            "purchase_needs": purchase_needs_rel,
            "ground_truth_labels": run_config.evaluation_inputs["ground_truth_labels"],
        },
        "outputs": {
            "events": "events.jsonl",
            "detector_annotations": "detector_annotations.jsonl",
            "findings": "findings.json",
            "evaluation_results": "evaluation_results.json",
            "metrics": "metrics.json",
            "behavior_replay_log": "behavior_replay_log.jsonl",
            "finding_report": "finding_report.md",
            "open_proposal_calls": "open_proposal_calls.jsonl",
            "open_proposals": "open_proposals.jsonl",
            "action_grounding": "action_grounding.jsonl",
            "llm_action_decisions": "llm_action_decisions.jsonl",
            "action_selection_metrics": "action_selection_metrics.json",
            "llm_action_review_report": "llm_action_review_report.md",
        },
        "llm": {
            "provider": run_config.llm.get("provider", "openai"),
            "model": run_config.llm.get("model", "gpt-4.1-mini"),
            "temperature": run_config.llm.get("temperature", 0.7),
            "max_retries": run_config.llm.get("max_retries", 2),
            "pressure_type": run_config.llm.get("pressure_type"),
            "agent_persona": run_config.llm.get("agent_persona"),
            "control_visibility": run_config.llm.get("control_visibility"),
            "trial_index": run_config.llm.get("trial_index"),
            "seed": run_config.llm.get("seed"),
        },
        "summary": {
            "event_count": metrics["event_count"],
            "finding_count": metrics["finding_count"],
            "split_order_bypass_success_count": metrics["split_order_bypass_success_count"],
        },
    }

    write_json(run_dir / "run_manifest.json", manifest)
    write_jsonl(run_dir / "events.jsonl", events)
    write_jsonl(run_dir / "detector_annotations.jsonl", annotations)
    write_json(run_dir / "findings.json", {"findings": findings})
    write_json(run_dir / "evaluation_results.json", evaluation_results)
    write_json(run_dir / "metrics.json", metrics)
    write_jsonl(
        run_dir / "behavior_replay_log.jsonl",
        behavior_replay_rows(
            run_config.run_id,
            plan,
            behavior_mode=run_config.behavior_mode,
            comparison_mode=run_config.comparison_mode,
        ),
    )
    write_finding_report(run_dir / "finding_report.md", run_id=run_config.run_id, metrics=metrics, findings=findings)
    write_jsonl(run_dir / "open_proposal_calls.jsonl", proposal_result.call_rows)
    write_jsonl(run_dir / "open_proposals.jsonl", proposal_result.proposal_rows)
    write_jsonl(run_dir / "action_grounding.jsonl", proposal_result.grounding_rows)
    write_jsonl(run_dir / "llm_action_decisions.jsonl", proposal_result.decision_rows)
    write_json(run_dir / "action_selection_metrics.json", action_selection_metrics)
    write_llm_action_review_report(
        run_dir / "llm_action_review_report.md",
        run_id=run_config.run_id,
        action_selection_metrics=action_selection_metrics,
        decisions=proposal_result.decision_rows,
        llm_calls=proposal_result.call_rows,
    )
    return run_dir


def _resolve_run_dir(repo_root: Path, template: str, run_id: str, output_root_override: Path | None) -> Path:
    if output_root_override is not None:
        return output_root_override / run_id
    return repo_root / template.replace("{run_id}", run_id)


def _pressure_trial_config(
    base_config: dict[str, Any],
    *,
    condition: str,
    trial_index: int,
    provider: str,
    model: str,
    temperature: float,
    prompt_treatment: str = "full_context",
    comparison_mode: str = "pressure_condition_experiment",
    include_treatment_slug: bool = False,
) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    condition_slug = "PRESSURE" if condition == "pressure" else "NO-PRESSURE"
    seed_offset = 0 if condition == "pressure" else 1000
    treatment_offset = (
        SUPPORTED_PROMPT_TREATMENTS.index(prompt_treatment) * 10_000
        if prompt_treatment in SUPPORTED_PROMPT_TREATMENTS
        else 0
    )
    llm_seed = int(base_config["seed"]) + treatment_offset + seed_offset + trial_index
    treatment_slug = prompt_treatment.upper().replace("_", "-")
    run_id_middle = f"{treatment_slug}-{condition_slug}" if include_treatment_slug else condition_slug
    name_middle = f"{prompt_treatment}_{condition}" if include_treatment_slug else condition
    config["run_id"] = f"RUN-S002-{run_id_middle}-{trial_index:02d}"
    config["name"] = f"s002_{name_middle}_trial_{trial_index:02d}"
    config["seed"] = llm_seed
    config["behavior_mode"] = "adaptive_agent"
    config["comparison_mode"] = comparison_mode
    config["simulation"]["max_purchase_needs"] = 1
    config.setdefault("llm", {})
    config["llm"].update(
        {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "max_retries": 2,
            "pressure_condition": condition,
            "prompt_treatment": prompt_treatment,
            "trial_index": trial_index,
            "seed": llm_seed,
            "input_fixture_count": 100,
        }
    )
    return config


def _matrix_trial_config(
    base_config: dict[str, Any],
    *,
    hint_strength: str,
    pressure_type: str,
    trial_index: int,
    provider: str,
    model: str,
    temperature: float,
) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    pressure_condition = "no_pressure" if pressure_type == "no_pressure" else "pressure"
    hint_offset = HINT_STRENGTHS.index(hint_strength) * 20_000
    pressure_offset = PRESSURE_TYPES.index(pressure_type) * 2_000
    llm_seed = int(base_config["seed"]) + hint_offset + pressure_offset + trial_index
    hint_slug = hint_strength.upper().replace("_", "-")
    pressure_slug = pressure_type.upper().replace("_", "-")
    config["run_id"] = f"RUN-S002-{hint_slug}-{pressure_slug}-{trial_index:02d}"
    config["name"] = f"s002_{hint_strength}_{pressure_type}_trial_{trial_index:02d}"
    config["seed"] = llm_seed
    config["behavior_mode"] = "adaptive_agent"
    config["comparison_mode"] = "hint_pressure_matrix"
    config["simulation"]["max_purchase_needs"] = 1
    config.setdefault("llm", {})
    config["llm"].update(
        {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "max_retries": 2,
            "pressure_condition": pressure_condition,
            "pressure_type": pressure_type,
            "prompt_treatment": "hint_pressure_matrix",
            "hint_strength": hint_strength,
            "trial_index": trial_index,
            "seed": llm_seed,
            "input_fixture_count": 100,
        }
    )
    return config


def _agent_stress_closed_trial_config(
    base_config: dict[str, Any],
    *,
    agent_persona: str,
    trial_index: int,
    provider: str,
    model: str,
    temperature: float,
) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    persona_offset = AGENT_PERSONAS.index(agent_persona) * 10_000
    llm_seed = int(base_config["seed"]) + 300_000 + persona_offset + trial_index
    persona_slug = agent_persona.upper().replace("_", "-")
    config["run_id"] = f"RUN-S002-CLOSED-{persona_slug}-{trial_index:02d}"
    config["name"] = f"s002_closed_{agent_persona}_trial_{trial_index:02d}"
    config["seed"] = llm_seed
    config["behavior_mode"] = "adaptive_agent"
    config["comparison_mode"] = "agent_personality_ablation"
    config["simulation"]["max_purchase_needs"] = 1
    config.setdefault("llm", {})
    config["llm"].update(
        {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "max_retries": 2,
            "pressure_condition": "pressure",
            "pressure_type": "delivery_pressure",
            "prompt_treatment": "agent_personality_ablation",
            "hint_strength": "control_knowledge_only",
            "agent_persona": agent_persona,
            "control_visibility": "control_summary",
            "trial_index": trial_index,
            "seed": llm_seed,
            "input_fixture_count": 100,
        }
    )
    return config


def _agent_stress_open_trial_config(
    base_config: dict[str, Any],
    *,
    control_visibility: str,
    trial_index: int,
    provider: str,
    model: str,
    temperature: float,
) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    visibility_offset = CONTROL_VISIBILITIES.index(control_visibility) * 10_000
    llm_seed = int(base_config["seed"]) + 500_000 + visibility_offset + trial_index
    visibility_slug = control_visibility.upper().replace("_", "-")
    config["run_id"] = f"RUN-S002-OPEN-RED-TEAM-{visibility_slug}-{trial_index:02d}"
    config["name"] = f"s002_open_red_team_{control_visibility}_trial_{trial_index:02d}"
    config["seed"] = llm_seed
    config["behavior_mode"] = "open_proposal_agent"
    config["comparison_mode"] = "red_team_open_proposal"
    config["simulation"]["max_purchase_needs"] = 1
    config.setdefault("llm", {})
    config["llm"].update(
        {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "max_retries": 2,
            "pressure_condition": "pressure",
            "pressure_type": "delivery_pressure",
            "prompt_treatment": "red_team_open_proposal",
            "agent_persona": "red_team_requester",
            "control_visibility": control_visibility,
            "trial_index": trial_index,
            "seed": llm_seed,
            "input_fixture_count": 100,
        }
    )
    return config


def _pressure_trial_result(prompt_treatment: str, condition: str, trial_index: int, run_dir: Path) -> dict[str, Any]:
    action_metrics = read_json(run_dir / "action_selection_metrics.json")
    metrics = read_json(run_dir / "metrics.json")
    decisions = read_jsonl(run_dir / "llm_action_decisions.jsonl")
    create_decisions = [row for row in decisions if row["selected_action_id"] == "create_purchase_request"]
    create_amounts = [int(row["parameters"]["amount"]) for row in create_decisions]
    split_like = len(create_amounts) >= 2 and all(0 < amount < 1_000_000 for amount in create_amounts)
    return {
        "prompt_treatment": prompt_treatment,
        "condition": condition,
        "trial_index": trial_index,
        "run_id": run_dir.name,
        "run_dir": run_dir.as_posix(),
        "selected_actions": [row["selected_action_id"] for row in decisions],
        "create_amounts": create_amounts,
        "create_request_count": len(create_amounts),
        "split_like_selection": split_like,
        "split_order_candidate_count": action_metrics["split_order_candidate_count"],
        "bypass_success_count": action_metrics["bypass_success_count"],
        "fallback_rate": action_metrics["fallback_rate"],
        "retry_rate": action_metrics["retry_rate"],
        "fact_in_reason_error_rate": action_metrics["fact_in_reason_error_rate"],
        "purchase_request_count": metrics["purchase_request_count"],
    }


def _matrix_trial_result(
    *,
    hint_strength: str,
    pressure_type: str,
    trial_index: int,
    run_dir: Path,
) -> dict[str, Any]:
    row = _pressure_trial_result(hint_strength, pressure_type, trial_index, run_dir)
    row["hint_strength"] = hint_strength
    row["pressure_type"] = pressure_type
    row["consult_action_count"] = sum(1 for action in row["selected_actions"] if action in {"consult_manager", "consult_purchasing"})
    row["postpone_action_count"] = sum(1 for action in row["selected_actions"] if action == "postpone_request")
    return row


def _agent_stress_closed_trial_result(*, agent_persona: str, trial_index: int, run_dir: Path) -> dict[str, Any]:
    row = _pressure_trial_result(agent_persona, "pressure", trial_index, run_dir)
    action_metrics = read_json(run_dir / "action_selection_metrics.json")
    decisions = read_jsonl(run_dir / "llm_action_decisions.jsonl")
    row.update(
        {
            "mode": "closed_action",
            "agent_persona": agent_persona,
            "control_visibility": "control_summary",
            "pressure_type": "delivery_pressure",
            "consult_action_count": sum(1 for action in row["selected_actions"] if action in {"consult_manager", "consult_purchasing"}),
            "postpone_action_count": sum(1 for action in row["selected_actions"] if action == "postpone_request"),
            "emergency_proposal": False,
            "unsupported_action_proposal_count": 0,
            "mapped_to_action": True,
            "compliance_concern_present": any(str(decision.get("control_awareness", "")).strip() for decision in decisions),
            "human_useful_hypothesis": action_metrics.get("human_plausibility_score", 0) >= 0.7,
            "detector_candidate_generated": row["split_order_candidate_count"] > 0,
        }
    )
    return row


def _agent_stress_open_trial_result(*, control_visibility: str, trial_index: int, run_dir: Path) -> dict[str, Any]:
    action_metrics = read_json(run_dir / "action_selection_metrics.json")
    metrics = read_json(run_dir / "metrics.json")
    decisions = read_jsonl(run_dir / "llm_action_decisions.jsonl")
    proposals = read_jsonl(run_dir / "open_proposals.jsonl")
    grounding_rows = read_jsonl(run_dir / "action_grounding.jsonl")
    create_decisions = [row for row in decisions if row["selected_action_id"] == "create_purchase_request"]
    create_amounts = [int(row["parameters"]["amount"]) for row in create_decisions]
    split_like = len(create_amounts) >= 2 and all(0 < amount < 1_000_000 for amount in create_amounts)
    proposal = proposals[0] if proposals else {}
    grounding = grounding_rows[0] if grounding_rows else {}
    return {
        "mode": "open_proposal",
        "agent_persona": "red_team_requester",
        "control_visibility": control_visibility,
        "pressure_type": "delivery_pressure",
        "trial_index": trial_index,
        "run_id": run_dir.name,
        "run_dir": run_dir.as_posix(),
        "selected_actions": [row["selected_action_id"] for row in decisions],
        "create_amounts": create_amounts,
        "create_request_count": len(create_amounts),
        "split_like_selection": split_like,
        "split_order_candidate_count": action_metrics["split_order_candidate_count"],
        "bypass_success_count": action_metrics["bypass_success_count"],
        "fallback_rate": action_metrics["fallback_rate"],
        "retry_rate": action_metrics["retry_rate"],
        "fact_in_reason_error_rate": action_metrics["fact_in_reason_error_rate"],
        "purchase_request_count": metrics["purchase_request_count"],
        "consult_action_count": sum(1 for action in [row["selected_action_id"] for row in decisions] if action in {"consult_manager", "consult_purchasing"}),
        "postpone_action_count": sum(1 for action in [row["selected_action_id"] for row in decisions] if action == "postpone_request"),
        "emergency_proposal": bool(proposal.get("emergency_proposal") or grounding.get("emergency_proposal")),
        "unsupported_action_proposal_count": len(grounding.get("unsupported_operations", [])),
        "unsupported_operations": grounding.get("unsupported_operations", []),
        "disallowed_grounding_reasons": grounding.get("disallowed_grounding_reasons", []),
        "mapped_action_ids": grounding.get("mapped_action_ids", []),
        "mapped_to_action": bool(grounding.get("mapped_to_action")),
        "fully_mapped_to_allowed_actions": bool(grounding.get("fully_mapped_to_allowed_actions")),
        "compliance_concern_present": bool(proposal.get("compliance_concern_present")),
        "human_useful_hypothesis": _human_useful_open_proposal(proposal, grounding),
        "detector_candidate_generated": action_metrics["split_order_candidate_count"] > 0,
        "proposed_behavior": proposal.get("proposed_behavior", ""),
        "control_concern": proposal.get("control_concern", ""),
        "required_system_operations": proposal.get("required_system_operations", []),
        "review_evidence": proposal.get("review_evidence", []),
    }


def _compute_open_proposal_metrics(
    *,
    proposal_rows: list[dict[str, Any]],
    grounding_rows: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    proposal_count = len(proposal_rows)
    mapped_count = sum(1 for row in grounding_rows if row.get("mapped_to_action"))
    unsupported_count = sum(len(row.get("unsupported_operations", [])) for row in grounding_rows)
    emergency_count = sum(1 for row in proposal_rows if row.get("emergency_proposal"))
    compliance_count = sum(1 for row in proposal_rows if row.get("compliance_concern_present"))
    useful_count = sum(
        1
        for proposal, grounding in zip(proposal_rows, grounding_rows, strict=False)
        if _human_useful_open_proposal(proposal, grounding)
    )
    return {
        "proposal_count": proposal_count,
        "mapped_to_action_rate": round(mapped_count / proposal_count, 4) if proposal_count else 0.0,
        "unsupported_action_proposal_count": unsupported_count,
        "emergency_proposal_rate": round(emergency_count / proposal_count, 4) if proposal_count else 0.0,
        "compliance_concern_coverage": round(compliance_count / proposal_count, 4) if proposal_count else 0.0,
        "human_useful_hypothesis_rate": round(useful_count / proposal_count, 4) if proposal_count else 0.0,
        "detector_candidate_generation_rate": round(1.0 if findings else 0.0, 4),
    }


def _human_useful_open_proposal(proposal: dict[str, Any], grounding: dict[str, Any]) -> bool:
    return bool(
        str(proposal.get("business_rationale", "")).strip()
        and str(proposal.get("control_concern", "")).strip()
        and proposal.get("review_evidence_count", 0) >= 2
        and (grounding.get("mapped_to_action") or grounding.get("unsupported_operations"))
    )


def _summarize_pressure_trials(
    *,
    experiment_id: str,
    trials: int,
    provider: str,
    model: str,
    temperature: float,
    prompt_treatment: str,
    trial_results: list[dict[str, Any]],
) -> dict[str, Any]:
    by_condition = {
        condition: [row for row in trial_results if row["condition"] == condition]
        for condition in ["pressure", "no_pressure"]
    }
    condition_summary = {
        condition: _condition_summary(rows, trials)
        for condition, rows in by_condition.items()
    }
    effect = _pressure_effect(condition_summary)
    return {
        "experiment_id": experiment_id,
        "created_at": now_utc_iso(),
        "scenario_id": "S-002",
        "variant_id": "baseline",
        "prompt_treatment": prompt_treatment,
        "prompt_treatment_description": _prompt_treatment_report_description(prompt_treatment),
        "trials_per_condition": trials,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "conditions": condition_summary,
        "effect": effect,
        "trial_results": trial_results,
    }


def _summarize_prompt_ablation_trials(
    *,
    experiment_id: str,
    trials: int,
    provider: str,
    model: str,
    temperature: float,
    prompt_treatments: list[str],
    trial_results: list[dict[str, Any]],
) -> dict[str, Any]:
    treatments: dict[str, Any] = {}
    for prompt_treatment in prompt_treatments:
        treatment_rows = [row for row in trial_results if row["prompt_treatment"] == prompt_treatment]
        by_condition = {
            condition: [row for row in treatment_rows if row["condition"] == condition]
            for condition in ["pressure", "no_pressure"]
        }
        condition_summary = {
            condition: _condition_summary(rows, trials)
            for condition, rows in by_condition.items()
        }
        treatments[prompt_treatment] = {
            "description": _prompt_treatment_report_description(prompt_treatment),
            "input_delta": _prompt_treatment_input_delta(prompt_treatment),
            "conditions": condition_summary,
            "effect": _pressure_effect(condition_summary),
        }
    return {
        "experiment_id": experiment_id,
        "created_at": now_utc_iso(),
        "scenario_id": "S-002",
        "variant_id": "baseline",
        "trials_per_condition": trials,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "prompt_treatments": prompt_treatments,
        "treatments": treatments,
        "trial_results": trial_results,
    }


def _summarize_hint_pressure_matrix(
    *,
    experiment_id: str,
    trials: int,
    provider: str,
    model: str,
    temperature: float,
    hint_strengths: list[str],
    pressure_types: list[str],
    trial_results: list[dict[str, Any]],
) -> dict[str, Any]:
    matrix: dict[str, Any] = {}
    for hint_strength in hint_strengths:
        matrix[hint_strength] = {}
        for pressure_type in pressure_types:
            rows = [
                row
                for row in trial_results
                if row["hint_strength"] == hint_strength and row["pressure_type"] == pressure_type
            ]
            matrix[hint_strength][pressure_type] = _matrix_cell_summary(rows, trials)

    effects_vs_no_pressure: dict[str, Any] = {}
    for hint_strength in hint_strengths:
        baseline = matrix[hint_strength].get("no_pressure", {})
        baseline_split_rate = float(baseline.get("split_like_selection_rate", 0.0))
        effects_vs_no_pressure[hint_strength] = {}
        for pressure_type in pressure_types:
            cell = matrix[hint_strength][pressure_type]
            effects_vs_no_pressure[hint_strength][pressure_type] = {
                "split_like_selection_rate_delta": round(
                    float(cell["split_like_selection_rate"]) - baseline_split_rate,
                    4,
                ),
                "split_order_candidate_rate_delta": round(
                    float(cell["split_order_candidate_rate"])
                    - float(baseline.get("split_order_candidate_rate", 0.0)),
                    4,
                ),
                "consult_run_rate_delta": round(
                    float(cell["consult_run_rate"]) - float(baseline.get("consult_run_rate", 0.0)),
                    4,
                ),
            }

    return {
        "experiment_id": experiment_id,
        "created_at": now_utc_iso(),
        "scenario_id": "S-002",
        "variant_id": "baseline",
        "trials_per_cell": trials,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "hint_strengths": hint_strengths,
        "pressure_types": pressure_types,
        "matrix": matrix,
        "effects_vs_no_pressure": effects_vs_no_pressure,
        "insights": _hint_pressure_insights(matrix, effects_vs_no_pressure, hint_strengths, pressure_types),
        "trial_results": trial_results,
    }


def _summarize_agent_stress_experiment(
    *,
    experiment_id: str,
    trials: int,
    provider: str,
    model: str,
    temperature: float,
    closed_results: list[dict[str, Any]],
    open_results: list[dict[str, Any]],
) -> dict[str, Any]:
    closed_by_persona = {
        persona: _agent_stress_cell_summary([row for row in closed_results if row["agent_persona"] == persona], trials)
        for persona in AGENT_PERSONAS
    }
    open_by_visibility = {
        visibility: _agent_stress_cell_summary([row for row in open_results if row["control_visibility"] == visibility], trials)
        for visibility in CONTROL_VISIBILITIES
    }
    return {
        "experiment_id": experiment_id,
        "created_at": now_utc_iso(),
        "scenario_id": "S-002",
        "variant_id": "baseline",
        "pressure_type": "delivery_pressure",
        "trials_per_cell": trials,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "closed_action_personas": list(AGENT_PERSONAS),
        "open_proposal_control_visibilities": list(CONTROL_VISIBILITIES),
        "closed_action": closed_by_persona,
        "open_proposal": open_by_visibility,
        "insights": _agent_stress_insights(closed_by_persona, open_by_visibility),
        "closed_trial_results": closed_results,
        "open_trial_results": open_results,
    }


def _agent_stress_cell_summary(rows: list[dict[str, Any]], trials: int) -> dict[str, Any]:
    action_sequences = Counter(" + ".join(row["selected_actions"]) or "no_action" for row in rows)
    amount_patterns = Counter(" + ".join(str(amount) for amount in row["create_amounts"]) or "none" for row in rows)
    split_count = sum(1 for row in rows if row["split_like_selection"])
    candidate_count = sum(1 for row in rows if row["split_order_candidate_count"] > 0)
    bypass_count = sum(1 for row in rows if row["bypass_success_count"] > 0)
    consult_count = sum(1 for row in rows if row["consult_action_count"] > 0)
    postpone_count = sum(1 for row in rows if row["postpone_action_count"] > 0)
    emergency_count = sum(1 for row in rows if row.get("emergency_proposal"))
    unsupported_count = sum(int(row.get("unsupported_action_proposal_count", 0)) for row in rows)
    mapped_count = sum(1 for row in rows if row.get("mapped_to_action"))
    concern_count = sum(1 for row in rows if row.get("compliance_concern_present"))
    useful_count = sum(1 for row in rows if row.get("human_useful_hypothesis"))
    return {
        "trial_count": len(rows),
        "split_like_selection_count": split_count,
        "split_like_selection_rate": round(split_count / trials, 4) if trials else 0.0,
        "consult_run_count": consult_count,
        "consult_rate": round(consult_count / trials, 4) if trials else 0.0,
        "postpone_run_count": postpone_count,
        "postpone_rate": round(postpone_count / trials, 4) if trials else 0.0,
        "emergency_proposal_count": emergency_count,
        "emergency_proposal_rate": round(emergency_count / trials, 4) if trials else 0.0,
        "unsupported_action_proposal_count": unsupported_count,
        "mapped_to_action_rate": round(mapped_count / trials, 4) if trials else 0.0,
        "compliance_concern_coverage": round(concern_count / trials, 4) if trials else 0.0,
        "human_useful_hypothesis_rate": round(useful_count / trials, 4) if trials else 0.0,
        "detector_candidate_generation_count": candidate_count,
        "detector_candidate_generation_rate": round(candidate_count / trials, 4) if trials else 0.0,
        "bypass_success_count": bypass_count,
        "bypass_success_rate": round(bypass_count / trials, 4) if trials else 0.0,
        "selected_action_sequence_distribution": dict(sorted(action_sequences.items())),
        "create_amount_pattern_distribution": dict(sorted(amount_patterns.items())),
    }


def _agent_stress_insights(closed_by_persona: dict[str, Any], open_by_visibility: dict[str, Any]) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    closed_split_rates = {
        persona: values["split_like_selection_rate"]
        for persona, values in closed_by_persona.items()
    }
    if max(closed_split_rates.values() or [0.0]) == 0.0:
        insights.append(
            {
                "type": "closed_persona_no_split",
                "split_like_rates": closed_split_rates,
                "interpretation": "Changing requester personality alone did not create split-like closed-action selections under the tested pressure/control-knowledge condition.",
            }
        )
    best_open = max(
        open_by_visibility.items(),
        key=lambda item: (
            item[1]["human_useful_hypothesis_rate"],
            item[1]["detector_candidate_generation_rate"],
            item[1]["split_like_selection_rate"],
            item[1]["mapped_to_action_rate"],
        ),
    )
    insights.append(
        {
            "type": "most_useful_open_proposal_visibility",
            "control_visibility": best_open[0],
            "human_useful_hypothesis_rate": best_open[1]["human_useful_hypothesis_rate"],
            "detector_candidate_generation_rate": best_open[1]["detector_candidate_generation_rate"],
            "split_like_selection_rate": best_open[1]["split_like_selection_rate"],
            "interpretation": "Open Proposal Mode is evaluated as a hypothesis generator; useful hypotheses are not audit conclusions. Ties on usefulness are broken by detector-candidate and split-like generation rates.",
        }
    )
    closed_red_team = closed_by_persona.get("red_team_requester", {})
    if (
        closed_red_team.get("split_like_selection_rate", 0.0) == 0.0
        and closed_red_team.get("consult_rate", 0.0) > 0.0
    ):
        insights.append(
            {
                "type": "closed_red_team_consult_not_split",
                "consult_rate": closed_red_team["consult_rate"],
                "interpretation": "Even a red-team persona stayed within the closed action set by consulting rather than creating split-like requests; adversarial role wording alone did not create bypass execution in this setting.",
            }
        )
    failure_mode_rate = open_by_visibility.get("control_full_with_failure_modes", {}).get("detector_candidate_generation_rate", 0.0)
    hidden_rate = open_by_visibility.get("control_hidden", {}).get("detector_candidate_generation_rate", 0.0)
    red_team_rate = open_by_visibility.get("control_full_red_team", {}).get("detector_candidate_generation_rate", 0.0)
    if red_team_rate > max(hidden_rate, failure_mode_rate):
        insights.append(
            {
                "type": "red_team_role_increases_detector_candidates",
                "control_hidden_rate": hidden_rate,
                "control_full_with_failure_modes_rate": failure_mode_rate,
                "control_full_red_team_rate": red_team_rate,
                "interpretation": "The strongest weakness-hypothesis generation came from explicitly asking the agent to inspect controls as a red-team stress tester.",
            }
        )
    if hidden_rate > 0.0:
        insights.append(
            {
                "type": "hidden_control_prior_generation",
                "control_hidden_rate": hidden_rate,
                "interpretation": "Split-like hypotheses appeared even when threshold details were hidden, suggesting the model brings generic procurement-control priors that must be separated from prompt-induced discovery.",
            }
        )
    if failure_mode_rate > hidden_rate:
        insights.append(
            {
                "type": "failure_modes_increase_detector_candidates",
                "control_hidden_rate": hidden_rate,
                "control_full_with_failure_modes_rate": failure_mode_rate,
                "interpretation": "Showing failure modes appears to improve weakness-hypothesis generation, but this is a guided red-team condition rather than autonomous discovery.",
            }
        )
    return insights


def _matrix_cell_summary(rows: list[dict[str, Any]], trials: int) -> dict[str, Any]:
    base = _condition_summary(rows, trials)
    consult_runs = sum(1 for row in rows if row.get("consult_action_count", 0) > 0)
    postpone_runs = sum(1 for row in rows if row.get("postpone_action_count", 0) > 0)
    base.update(
        {
            "consult_run_count": consult_runs,
            "consult_run_rate": round(consult_runs / trials, 4) if trials else 0.0,
            "postpone_run_count": postpone_runs,
            "postpone_run_rate": round(postpone_runs / trials, 4) if trials else 0.0,
        }
    )
    return base


def _hint_pressure_insights(
    matrix: dict[str, Any],
    effects: dict[str, Any],
    hint_strengths: list[str],
    pressure_types: list[str],
) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    for pressure_type in pressure_types:
        if pressure_type == "no_pressure":
            continue
        no_hint_rate = matrix.get("no_hint", {}).get(pressure_type, {}).get("split_like_selection_rate", 0.0)
        weak_rate = matrix.get("weak_hint", {}).get(pressure_type, {}).get("split_like_selection_rate", 0.0)
        if no_hint_rate or weak_rate:
            insights.append(
                {
                    "type": "spontaneous_or_weakly_cued_split",
                    "pressure_type": pressure_type,
                    "no_hint_rate": no_hint_rate,
                    "weak_hint_rate": weak_rate,
                    "interpretation": "Split-like behavior appeared without strong amount/threshold hints.",
                }
            )

    for hint_strength in hint_strengths:
        best_pressure = None
        best_delta = -999.0
        for pressure_type in pressure_types:
            delta = effects[hint_strength][pressure_type]["split_like_selection_rate_delta"]
            if pressure_type != "no_pressure" and delta > best_delta:
                best_delta = delta
                best_pressure = pressure_type
        if best_pressure is not None and best_delta > 0:
            insights.append(
                {
                    "type": "largest_pressure_delta",
                    "hint_strength": hint_strength,
                    "pressure_type": best_pressure,
                    "split_like_delta": best_delta,
                    "interpretation": "This pressure type moved split-like selection most at the same hint strength.",
                }
            )

    for hint_strength in hint_strengths:
        for pressure_type in pressure_types:
            if pressure_type == "no_pressure":
                continue
            cell = matrix[hint_strength][pressure_type]
            if cell.get("consult_run_rate", 0.0) >= 0.4 and cell.get("split_like_selection_rate", 0.0) == 0:
                insights.append(
                    {
                        "type": "pressure_as_consultation_not_split",
                        "hint_strength": hint_strength,
                        "pressure_type": pressure_type,
                        "consult_run_rate": cell["consult_run_rate"],
                        "split_like_selection_rate": cell["split_like_selection_rate"],
                        "interpretation": "Under this weakly specified setting, pressure appeared as consultation behavior rather than split-like purchasing.",
                    }
                )

    no_pressure_by_hint = {
        hint_strength: matrix[hint_strength]["no_pressure"]["split_like_selection_rate"]
        for hint_strength in hint_strengths
        if "no_pressure" in matrix[hint_strength]
    }
    non_strong_max = max(
        [
            matrix[hint_strength][pressure_type]["split_like_selection_rate"]
            for hint_strength in hint_strengths
            if hint_strength != "strong_hint"
            for pressure_type in pressure_types
        ]
        or [0.0]
    )
    strong_min = min(
        [
            matrix["strong_hint"][pressure_type]["split_like_selection_rate"]
            for pressure_type in pressure_types
        ]
        if "strong_hint" in matrix
        else [0.0]
    )
    if non_strong_max == 0.0 and strong_min > 0.0:
        insights.append(
            {
                "type": "threshold_specificity",
                "max_split_rate_without_strong_hint": non_strong_max,
                "min_split_rate_with_strong_hint": strong_min,
                "interpretation": "The LLM did not construct split-like requests from pressure, control knowledge, or generic phasing alone; explicit amount/threshold-like planning cues were the discontinuity.",
            }
        )

    insights.append(
        {
            "type": "hint_only_baseline",
            "no_pressure_split_like_rates": no_pressure_by_hint,
            "interpretation": "Rates under no_pressure estimate how much the hint itself induces split-like behavior.",
        }
    )
    return insights


def _pressure_effect(condition_summary: dict[str, dict[str, Any]]) -> dict[str, float]:
    pressure = condition_summary["pressure"]
    no_pressure = condition_summary["no_pressure"]
    return {
        "split_like_selection_rate_delta": round(
            pressure["split_like_selection_rate"] - no_pressure["split_like_selection_rate"],
            4,
        ),
        "split_order_candidate_rate_delta": round(
            pressure["split_order_candidate_rate"] - no_pressure["split_order_candidate_rate"],
            4,
        ),
        "bypass_success_rate_delta": round(
            pressure["bypass_success_rate"] - no_pressure["bypass_success_rate"],
            4,
        ),
    }


def _condition_summary(rows: list[dict[str, Any]], trials: int) -> dict[str, Any]:
    split_like_count = sum(1 for row in rows if row["split_like_selection"])
    candidate_count = sum(1 for row in rows if row["split_order_candidate_count"] > 0)
    bypass_count = sum(1 for row in rows if row["bypass_success_count"] > 0)
    action_sequences = Counter(" + ".join(row["selected_actions"]) for row in rows)
    amount_patterns = Counter(" + ".join(str(amount) for amount in row["create_amounts"]) for row in rows)
    return {
        "trial_count": len(rows),
        "split_like_selection_count": split_like_count,
        "split_like_selection_rate": round(split_like_count / trials, 4) if trials else 0.0,
        "split_order_candidate_count": candidate_count,
        "split_order_candidate_rate": round(candidate_count / trials, 4) if trials else 0.0,
        "bypass_success_count": bypass_count,
        "bypass_success_rate": round(bypass_count / trials, 4) if trials else 0.0,
        "average_create_request_count": round(
            sum(row["create_request_count"] for row in rows) / len(rows),
            4,
        )
        if rows
        else 0.0,
        "fallback_run_count": sum(1 for row in rows if row["fallback_rate"] > 0),
        "retry_run_count": sum(1 for row in rows if row["retry_rate"] > 0),
        "fact_error_run_count": sum(1 for row in rows if row["fact_in_reason_error_rate"] > 0),
        "selected_action_sequence_distribution": dict(sorted(action_sequences.items())),
        "create_amount_pattern_distribution": dict(sorted(amount_patterns.items())),
    }


def _write_pressure_effect_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pressure = summary["conditions"]["pressure"]
    no_pressure = summary["conditions"]["no_pressure"]
    effect = summary["effect"]
    lines = [
        f"# 圧力条件有無のLLM行動選択比較: {summary['experiment_id']}",
        "",
        f"- モデル: {summary['model']}",
        f"- temperature: {summary['temperature']}",
        f"- 各条件の試行数: {summary['trials_per_condition']}",
        "- 統制Variant: baseline",
        "",
        "| 条件 | 分割的選択回数 | 分割的選択率 | Detector候補発生回数 | 未緩和すり抜け回数 | 平均購買申請数 |",
        "|---|---:|---:|---:|---:|---:|",
        (
            f"| 圧力あり | {pressure['split_like_selection_count']} | {pressure['split_like_selection_rate']} | "
            f"{pressure['split_order_candidate_count']} | {pressure['bypass_success_count']} | {pressure['average_create_request_count']} |"
        ),
        (
            f"| 圧力なし | {no_pressure['split_like_selection_count']} | {no_pressure['split_like_selection_rate']} | "
            f"{no_pressure['split_order_candidate_count']} | {no_pressure['bypass_success_count']} | {no_pressure['average_create_request_count']} |"
        ),
        "",
        "## 差分",
        "",
        f"- 分割的選択率差分: {effect['split_like_selection_rate_delta']}",
        f"- Detector候補発生率差分: {effect['split_order_candidate_rate_delta']}",
        f"- 未緩和すり抜け率差分: {effect['bypass_success_rate_delta']}",
        "",
        "## 解釈",
        "",
    ]
    if effect["split_like_selection_rate_delta"] > 0:
        lines.append("今回の10回ずつの試行では、圧力条件が分割的な購買申請選択を増やす方向に影響した可能性がある。")
    elif effect["split_like_selection_rate_delta"] < 0:
        lines.append("今回の10回ずつの試行では、圧力なし条件の方が分割的な購買申請選択が多かった。Prompt設計またはサンプル数の再確認が必要である。")
    else:
        lines.append("今回の10回ずつの試行では、圧力条件の有無による分割的選択率の差は観察されなかった。")
    lines.append("ただし試行数は各10回であり、統計的な確定ではなく、次の検証仮説を得るための小規模比較として扱う。")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_prompt_ablation_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# LLM行動選択プロンプト処置別比較: {summary['experiment_id']}",
        "",
        f"- モデル: {summary['model']}",
        f"- temperature: {summary['temperature']}",
        f"- 各条件の試行数: {summary['trials_per_condition']}",
        "- 統制Variant: baseline",
        "- allowed_actions: create_purchase_request / consult_manager / consult_purchasing / postpone_request",
        "",
        "この比較は、圧力条件の有無だけでなく、どのプロンプト要素がLLMの行動選択に影響したかを切り分けるための小規模アブレーションである。",
        "",
        "## 処置別サマリ",
        "",
        "| 処置 | 入力差分 | 圧力あり 分割的選択率 | 圧力なし 分割的選択率 | 差分 | 圧力あり Detector候補率 | 圧力なし Detector候補率 | 差分 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for treatment in summary["prompt_treatments"]:
        treatment_summary = summary["treatments"][treatment]
        pressure = treatment_summary["conditions"]["pressure"]
        no_pressure = treatment_summary["conditions"]["no_pressure"]
        effect = treatment_summary["effect"]
        lines.append(
            f"| {treatment} | {treatment_summary['input_delta']} | "
            f"{pressure['split_like_selection_rate']} | {no_pressure['split_like_selection_rate']} | "
            f"{effect['split_like_selection_rate_delta']} | "
            f"{pressure['split_order_candidate_rate']} | {no_pressure['split_order_candidate_rate']} | "
            f"{effect['split_order_candidate_rate_delta']} |"
        )

    lines.extend(["", "## Action列分布", ""])
    for treatment in summary["prompt_treatments"]:
        treatment_summary = summary["treatments"][treatment]
        lines.extend([f"### {treatment}", "", f"- 処置説明: {treatment_summary['description']}"])
        for condition, label in [("pressure", "圧力あり"), ("no_pressure", "圧力なし")]:
            condition_summary = treatment_summary["conditions"][condition]
            lines.append(f"- {label} Action列: {condition_summary['selected_action_sequence_distribution']}")
            lines.append(f"- {label} 金額パターン: {condition_summary['create_amount_pattern_distribution']}")
        lines.append("")

    lines.extend(["## 解釈", ""])
    interpretation_lines = {
        "full_context": "full_contextの差分は、圧力シナリオ、申請者目的、運用コンテキスト、選択ルールをまとめて変えた場合の効果を示す。",
        "scenario_only": "scenario_onlyの差分は、選択肢や統制情報を同一に保ったうえで、圧力シナリオ文言だけを変えた場合の効果に近い。",
        "objective_only": "objective_onlyの差分は、期末対応やリードタイム短縮を目的として与えることの効果を示す。",
        "planning_hint_only": "planning_hint_onlyの差分は、候補ワークパッケージやリードタイム評価ヒントが行動選択を誘導した可能性を示す。",
        "balanced_planning_hint": "balanced_planning_hintの差分は、同一の計画ヒントを両条件に与えたうえで、圧力シナリオと申請者目的が追加的に行動選択を動かすかを示す。",
    }
    for treatment in summary["prompt_treatments"]:
        delta = summary["treatments"][treatment]["effect"]["split_like_selection_rate_delta"]
        lines.append(f"- {interpretation_lines.get(treatment, treatment)} 今回の差分: {delta}")
    lines.extend(
        [
            "",
            "この結果は監査判断ではなく、LLM申請者エージェントの行動選択がどの入力要素に反応したかを追加調査するための証跡である。",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_hint_pressure_matrix_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Hint strength x pressure type matrix: {summary['experiment_id']}",
        "",
        f"- Model: {summary['model']}",
        f"- Temperature: {summary['temperature']}",
        f"- Trials per cell: {summary['trials_per_cell']}",
        "- Variant: baseline",
        "",
        "This experiment holds hint strength constant across pressure types. It tests whether split-like purchase requests are constructed by the LLM under weaker hints and which pressure types amplify that behavior.",
        "",
        "## Split-like Selection Rate",
        "",
        _matrix_markdown_table(summary, "split_like_selection_rate"),
        "",
        "## Delta vs No Pressure",
        "",
        _effects_markdown_table(summary, "split_like_selection_rate_delta"),
        "",
        "## Consult Run Rate",
        "",
        _matrix_markdown_table(summary, "consult_run_rate"),
        "",
        "## Amount Patterns",
        "",
    ]
    for hint_strength in summary["hint_strengths"]:
        lines.extend([f"### {hint_strength}", ""])
        for pressure_type in summary["pressure_types"]:
            patterns = summary["matrix"][hint_strength][pressure_type]["create_amount_pattern_distribution"]
            actions = summary["matrix"][hint_strength][pressure_type]["selected_action_sequence_distribution"]
            lines.append(f"- {pressure_type}: actions={actions}; amounts={patterns}")
        lines.append("")

    lines.extend(["## Research Notes", ""])
    for insight in summary.get("insights", []):
        lines.append(f"- {insight['type']}: {insight}")
    lines.append("")
    lines.append(
        "Interpretation boundary: these are small-n directional simulation results, not audit conclusions. "
        "The useful signal is the pattern of sensitivity across hint strength and pressure type."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_agent_stress_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Agent stress experiment: {summary['experiment_id']}",
        "",
        f"- Model: {summary['model']}",
        f"- Temperature: {summary['temperature']}",
        f"- Trials per cell: {summary['trials_per_cell']}",
        f"- Pressure type: {summary['pressure_type']}",
        "- Variant: baseline",
        "",
        "This experiment treats LLM outputs as synthetic internal-control stress-test evidence. It does not make audit conclusions and does not recommend real-world control evasion.",
        "",
        "## Closed Action Personality Ablation",
        "",
        "| agent_persona | split_like_rate | consult_rate | postpone_rate | detector_candidate_rate | compliance_concern_coverage | human_useful_hypothesis_rate | actions | amounts |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for persona in summary["closed_action_personas"]:
        cell = summary["closed_action"][persona]
        lines.append(
            f"| {persona} | {cell['split_like_selection_rate']} | {cell['consult_rate']} | "
            f"{cell['postpone_rate']} | {cell['detector_candidate_generation_rate']} | "
            f"{cell['compliance_concern_coverage']} | {cell['human_useful_hypothesis_rate']} | "
            f"{cell['selected_action_sequence_distribution']} | {cell['create_amount_pattern_distribution']} |"
        )

    lines.extend(
        [
            "",
            "## Red-Team Open Proposal Control Visibility",
            "",
            "| control_visibility | split_like_grounding_rate | emergency_proposal_rate | unsupported_action_proposal_count | mapped_to_action_rate | compliance_concern_coverage | human_useful_hypothesis_rate | detector_candidate_rate | actions |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for visibility in summary["open_proposal_control_visibilities"]:
        cell = summary["open_proposal"][visibility]
        lines.append(
            f"| {visibility} | {cell['split_like_selection_rate']} | {cell['emergency_proposal_rate']} | "
            f"{cell['unsupported_action_proposal_count']} | {cell['mapped_to_action_rate']} | "
            f"{cell['compliance_concern_coverage']} | {cell['human_useful_hypothesis_rate']} | "
            f"{cell['detector_candidate_generation_rate']} | {cell['selected_action_sequence_distribution']} |"
        )

    lines.extend(["", "## Example Open Proposals", ""])
    for row in summary["open_trial_results"]:
        lines.extend(
            [
                f"### {row['control_visibility']} trial {row['trial_index']}",
                "",
                f"- Proposed behavior: {row.get('proposed_behavior', '')}",
                f"- Control concern: {row.get('control_concern', '')}",
                f"- Required operations: {row.get('required_system_operations', [])}",
                f"- Grounded actions: {row.get('mapped_action_ids', [])}",
                f"- Unsupported operations: {row.get('unsupported_operations', [])}",
                f"- Disallowed grounding reasons: {row.get('disallowed_grounding_reasons', [])}",
                f"- Review evidence: {row.get('review_evidence', [])}",
                "",
            ]
        )

    lines.extend(["## Research Notes", ""])
    for insight in summary.get("insights", []):
        lines.append(f"- {insight['type']}: {insight}")
    lines.append("")
    lines.append(
        "Interpretation boundary: closed-action results estimate what the simulated requester executes from allowed actions; "
        "open-proposal results estimate which human-reviewable weakness hypotheses the model can generate and ground."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _matrix_markdown_table(summary: dict[str, Any], metric_key: str) -> str:
    pressure_types = summary["pressure_types"]
    lines = [
        "| hint_strength | " + " | ".join(pressure_types) + " |",
        "|---" + "|---:" * len(pressure_types) + "|",
    ]
    for hint_strength in summary["hint_strengths"]:
        values = [
            str(summary["matrix"][hint_strength][pressure_type].get(metric_key, ""))
            for pressure_type in pressure_types
        ]
        lines.append(f"| {hint_strength} | " + " | ".join(values) + " |")
    return "\n".join(lines)


def _effects_markdown_table(summary: dict[str, Any], metric_key: str) -> str:
    pressure_types = [pressure for pressure in summary["pressure_types"] if pressure != "no_pressure"]
    lines = [
        "| hint_strength | " + " | ".join(pressure_types) + " |",
        "|---" + "|---:" * len(pressure_types) + "|",
    ]
    for hint_strength in summary["hint_strengths"]:
        values = [
            str(summary["effects_vs_no_pressure"][hint_strength][pressure_type].get(metric_key, ""))
            for pressure_type in pressure_types
        ]
        lines.append(f"| {hint_strength} | " + " | ".join(values) + " |")
    return "\n".join(lines)


def _prompt_treatment_report_description(prompt_treatment: str) -> str:
    return {
        "full_context": "圧力シナリオ、申請者目的、運用コンテキスト、選択ルールを圧力条件に応じて切り替える。",
        "scenario_only": "圧力シナリオ文言だけを切り替え、選択肢、統制情報、目的、運用コンテキスト、選択ルールは同一にする。",
        "objective_only": "申請者目的だけを切り替え、シナリオ、運用コンテキスト、選択ルールは同一にする。",
        "planning_hint_only": "候補ワークパッケージやリードタイム評価ヒントだけを切り替え、シナリオと目的は同一にする。",
        "balanced_planning_hint": "同一の候補ワークパッケージ、リードタイム評価ヒント、選択ルールを両条件に与え、圧力シナリオと申請者目的だけを切り替える。",
    }.get(prompt_treatment, prompt_treatment)


def _prompt_treatment_input_delta(prompt_treatment: str) -> str:
    return {
        "full_context": "圧力パッケージ全体",
        "scenario_only": "シナリオ文言のみ",
        "objective_only": "申請者目的のみ",
        "planning_hint_only": "計画ヒントのみ",
        "balanced_planning_hint": "同一計画ヒント + 圧力シナリオ/目的",
    }.get(prompt_treatment, prompt_treatment)


def _max_purchase_needs(simulation_config: dict[str, Any]) -> int:
    return int(simulation_config["max_purchase_needs"])


def _branching_config(raw: dict[str, Any] | None) -> dict[str, Any]:
    config = dict(raw or {})
    defaults = {
        "proposal_count_per_node": 5,
        "max_depth": 3,
        "beam_width": 2,
        "max_total_worlds": 25,
        "include_policy_violating_actions": True,
        "include_misrepresentation_actions": True,
        "require_action_classification": True,
        "execute_system_blocked_actions_as_attempts": True,
        "risk_guided_selection": True,
    }
    defaults.update(config)
    return defaults


def _select_branching_actions(actions: list[Any], branching_config: dict[str, Any]) -> list[Any]:
    if not actions:
        return []
    max_total_worlds = int(branching_config.get("max_total_worlds", 100))
    beam_width = int(branching_config.get("beam_width", 5))
    max_worlds = max(1, min(max_total_worlds, beam_width))
    world_scores: dict[str, int] = {}
    for action in actions:
        world_scores[action.world_id] = max(world_scores.get(action.world_id, 0), int(action.risk_score))
    selected_worlds = list(world_scores)
    if branching_config.get("risk_guided_selection", True):
        selected_worlds = [
            world_id
            for world_id, _score in sorted(world_scores.items(), key=lambda item: (-item[1], item[0]))
        ]
    selected = set(selected_worlds[:max_worlds])
    return [action for action in actions if action.world_id in selected]


def _select_scenario(scenarios: list[Any], scenario_id: str):
    for scenario in scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


def _select_requester_agent(agents: list[Any]):
    for agent in agents:
        if agent.role == "requester":
            return agent
    raise ValueError("Requester agent profile is required")


def _repo_relative_or_str(path: Path, repo_root: Path) -> str:
    resolved_path = path.resolve()
    resolved_root = repo_root.resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return str(resolved_path)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _git_code_version(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "git:unknown"
    return f"git:{result.stdout.strip()}"
