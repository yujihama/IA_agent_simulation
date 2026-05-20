from __future__ import annotations

import hashlib
import copy
import subprocess
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
            )
            config_path = configs_dir / f"{config['run_id']}.yaml"
            write_yaml(config_path, config)
            result = run_simulation(
                repo_root,
                config_path,
                output_root_override=runs_root,
                purchase_needs_path_override=purchase_needs_path,
            )
            trial_results.append(_pressure_trial_result(condition, trial_index, result.run_dir))

    summary = _summarize_pressure_trials(
        experiment_id=experiment_id,
        trials=trials,
        provider=provider,
        model=model,
        temperature=temperature,
        trial_results=trial_results,
    )
    write_json(experiment_dir / "summary.json", summary)
    _write_pressure_effect_report(experiment_dir / "pressure_effect_report.md", summary)
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
) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    condition_slug = "PRESSURE" if condition == "pressure" else "NO-PRESSURE"
    seed_offset = 0 if condition == "pressure" else 1000
    llm_seed = int(base_config["seed"]) + seed_offset + trial_index
    config["run_id"] = f"RUN-S002-{condition_slug}-{trial_index:02d}"
    config["name"] = f"s002_{condition}_trial_{trial_index:02d}"
    config["seed"] = llm_seed
    config["behavior_mode"] = "adaptive_agent"
    config["comparison_mode"] = "pressure_condition_experiment"
    config["simulation"]["max_purchase_needs"] = 1
    config.setdefault("llm", {})
    config["llm"].update(
        {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "max_retries": 2,
            "pressure_condition": condition,
            "trial_index": trial_index,
            "seed": llm_seed,
            "input_fixture_count": 100,
        }
    )
    return config


def _pressure_trial_result(condition: str, trial_index: int, run_dir: Path) -> dict[str, Any]:
    action_metrics = read_json(run_dir / "action_selection_metrics.json")
    metrics = read_json(run_dir / "metrics.json")
    decisions = read_jsonl(run_dir / "llm_action_decisions.jsonl")
    create_decisions = [row for row in decisions if row["selected_action_id"] == "create_purchase_request"]
    create_amounts = [int(row["parameters"]["amount"]) for row in create_decisions]
    split_like = len(create_amounts) >= 2 and all(0 < amount < 1_000_000 for amount in create_amounts)
    return {
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


def _summarize_pressure_trials(
    *,
    experiment_id: str,
    trials: int,
    provider: str,
    model: str,
    temperature: float,
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
    pressure_split_rate = condition_summary["pressure"]["split_like_selection_rate"]
    no_pressure_split_rate = condition_summary["no_pressure"]["split_like_selection_rate"]
    pressure_candidate_rate = condition_summary["pressure"]["split_order_candidate_rate"]
    no_pressure_candidate_rate = condition_summary["no_pressure"]["split_order_candidate_rate"]
    return {
        "experiment_id": experiment_id,
        "created_at": now_utc_iso(),
        "scenario_id": "S-002",
        "variant_id": "baseline",
        "trials_per_condition": trials,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "conditions": condition_summary,
        "effect": {
            "split_like_selection_rate_delta": round(pressure_split_rate - no_pressure_split_rate, 4),
            "split_order_candidate_rate_delta": round(pressure_candidate_rate - no_pressure_candidate_rate, 4),
            "bypass_success_rate_delta": round(
                condition_summary["pressure"]["bypass_success_rate"]
                - condition_summary["no_pressure"]["bypass_success_rate"],
                4,
            ),
        },
        "trial_results": trial_results,
    }


def _condition_summary(rows: list[dict[str, Any]], trials: int) -> dict[str, Any]:
    split_like_count = sum(1 for row in rows if row["split_like_selection"])
    candidate_count = sum(1 for row in rows if row["split_order_candidate_count"] > 0)
    bypass_count = sum(1 for row in rows if row["bypass_success_count"] > 0)
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
