from __future__ import annotations

import hashlib
import copy
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

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
from ia_sim.detectors import build_findings, detect_split_orders
from ia_sim.evaluation import evaluate_findings
from ia_sim.llm import LLMActionSelector, LLMSelectionResult
from ia_sim.llm_metrics import compare_action_selection_metric_sets, compute_action_selection_metrics
from ia_sim.metrics import compare_metric_sets, compute_metrics
from ia_sim.models import RunResult, now_utc_iso
from ia_sim.reports import write_comparison_report, write_finding_report, write_llm_action_review_report
from ia_sim.rule_engine import RuleEngine, VariantPolicy
from ia_sim.simulation import SimulationEngine, behavior_replay_rows, build_behavior_plan
from ia_sim.storage import read_json, read_jsonl, write_json, write_jsonl
from ia_sim.synthetic import generate_synthetic_data, read_purchase_needs_csv


PROMPT_TREATMENTS = ["full_context", "scenario_only", "objective_only", "planning_hint_only"]
SUPPORTED_PROMPT_TREATMENTS = [*PROMPT_TREATMENTS, "balanced_planning_hint"]
HINT_STRENGTHS = ["no_hint", "weak_hint", "medium_hint", "strong_hint"]
PRESSURE_TYPES = [
    "no_pressure",
    "budget_pressure",
    "delivery_pressure",
    "approver_absence",
    "vendor_constraint",
    "workload_pressure",
]


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
            trial_index=run_config.llm.get("trial_index"),
            llm_seed=run_config.llm.get("seed"),
        )
        llm_selection = selector.select_actions_for_needs(needs, max_purchase_needs=max_purchase_needs)
        plan = llm_selection.planned_actions
    else:
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
    action_selection_metrics = None
    if llm_selection is not None:
        action_selection_metrics = compute_action_selection_metrics(
            decisions=llm_selection.decision_rows,
            llm_calls=llm_selection.call_rows,
            events=events,
            findings=findings,
        )

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
    weak_or_medium_max = max(
        [
            matrix[hint_strength][pressure_type]["split_like_selection_rate"]
            for hint_strength in hint_strengths
            if hint_strength in {"no_hint", "weak_hint", "medium_hint"}
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
    if weak_or_medium_max == 0.0 and strong_min > 0.0:
        insights.append(
            {
                "type": "threshold_specificity",
                "max_split_rate_without_strong_hint": weak_or_medium_max,
                "min_split_rate_with_strong_hint": strong_min,
                "interpretation": "The LLM did not construct split-like requests from pressure or generic phasing alone; explicit amount/threshold-like planning cues were the discontinuity.",
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
