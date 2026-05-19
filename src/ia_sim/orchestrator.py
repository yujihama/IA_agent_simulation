from __future__ import annotations

from pathlib import Path
from typing import Any

from ia_sim.config import (
    load_action_definitions,
    load_control_cards,
    load_run_config,
    read_yaml,
    validate_action_definitions,
    validate_config_tree,
)
from ia_sim.detectors import build_findings, detect_split_orders
from ia_sim.evaluation import evaluate_findings
from ia_sim.metrics import compare_metric_sets, compute_metrics
from ia_sim.models import RunResult, now_utc_iso
from ia_sim.reports import write_comparison_report, write_finding_report
from ia_sim.rule_engine import RuleEngine, VariantPolicy
from ia_sim.simulation import SimulationEngine, behavior_replay_rows, build_behavior_plan
from ia_sim.storage import read_json, write_json, write_jsonl
from ia_sim.synthetic import generate_synthetic_data, read_purchase_needs_csv


def load_variant_policy(repo_root: Path, variant_id: str) -> VariantPolicy:
    raw = read_yaml(repo_root / "configs/variants/p2p_control_variants.yaml")
    for item in raw["variants"]:
        if item["variant_id"] == variant_id:
            aggregate_days = item.get("rules", {}).get("aggregate_approval_window_days")
            return VariantPolicy(
                variant_id=item["variant_id"],
                name=item["name"],
                aggregate_approval_window_days=aggregate_days,
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
    plan = build_behavior_plan(needs, max_purchase_needs=max_purchase_needs)
    engine = SimulationEngine(run_config.run_id, rule_engine)
    events = engine.run(needs, plan)

    ground_truth = read_yaml(repo_root / run_config.evaluation_inputs["ground_truth_labels"])
    annotations = detect_split_orders(events)
    findings = build_findings(annotations, events)
    evaluation_results = evaluate_findings(findings=findings, events=events, ground_truth=ground_truth)
    metrics = compute_metrics(
        events=events,
        annotations=annotations,
        findings=findings,
        evaluation_results=evaluation_results,
        variant_id=run_config.variant_id,
    )

    run_dir = _resolve_run_dir(repo_root, run_config.outputs["dir"], run_config.run_id, output_root_override)
    manifest = {
        "run_id": run_config.run_id,
        "name": run_config.name,
        "created_at": now_utc_iso(),
        "process": run_config.process,
        "scenario_id": run_config.scenario_id,
        "variant_id": run_config.variant_id,
        "behavior_mode": run_config.behavior_mode,
        "comparison_mode": run_config.comparison_mode,
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
            "run_config": str(config_path),
            "purchase_needs": str(purchase_needs_path),
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
    comparison = compare_metric_sets(baseline_metrics, variant_metrics)
    comparison["baseline_run_id"] = read_json(baseline_run_dir / "run_manifest.json")["run_id"]
    comparison["variant_run_id"] = read_json(variant_run_dir / "run_manifest.json")["run_id"]
    comparison["comparison_mode"] = "frozen_behavior"

    write_json(output_dir / "comparison.json", comparison)
    write_comparison_report(output_dir / "comparison_report.md", comparison)
    return comparison


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


def _resolve_run_dir(repo_root: Path, template: str, run_id: str, output_root_override: Path | None) -> Path:
    if output_root_override is not None:
        return output_root_override / run_id
    return repo_root / template.replace("{run_id}", run_id)


def _max_purchase_needs(simulation_config: dict[str, Any]) -> int:
    return int(simulation_config["max_purchase_needs"])
