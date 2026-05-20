from pathlib import Path

from ia_sim.config import read_yaml, write_yaml
from ia_sim.llm import ground_open_proposal, validate_action_selection_payload
from ia_sim.orchestrator import (
    compare_runs,
    run_agent_stress_experiment,
    run_balanced_planning_hint_experiment,
    run_branching_simulation,
    run_hint_pressure_matrix_experiment,
    run_prompt_ablation_experiment,
    run_pressure_condition_experiment,
    run_simulation,
)
from ia_sim.storage import read_json, read_jsonl
from ia_sim.synthetic import generate_synthetic_data, read_purchase_needs_csv


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_adaptive_agent_stub_runs_end_to_end(tmp_path):
    purchase_needs_path = generate_synthetic_data(tmp_path / "data", count=100)
    baseline_config = _stub_config("llm_baseline.yaml", "RUN-TEST-LLM-BASELINE", tmp_path)
    variant_config = _stub_config("llm_variant_a.yaml", "RUN-TEST-LLM-VARIANT-A", tmp_path)

    baseline = run_simulation(
        REPO_ROOT,
        baseline_config,
        output_root_override=tmp_path / "runs",
        purchase_needs_path_override=purchase_needs_path,
    )
    variant = run_simulation(
        REPO_ROOT,
        variant_config,
        output_root_override=tmp_path / "runs",
        purchase_needs_path_override=purchase_needs_path,
    )
    comparison = compare_runs(baseline.run_dir, variant.run_dir, tmp_path / "runs/comparisons/cmp")

    baseline_metrics = read_json(baseline.metrics_path)
    variant_metrics = read_json(variant.metrics_path)
    baseline_action_metrics = read_json(baseline.run_dir / "action_selection_metrics.json")
    variant_action_metrics = read_json(variant.run_dir / "action_selection_metrics.json")
    baseline_decisions = read_jsonl(baseline.run_dir / "llm_action_decisions.jsonl")
    variant_decisions = read_jsonl(variant.run_dir / "llm_action_decisions.jsonl")
    baseline_calls = read_jsonl(baseline.run_dir / "llm_calls.jsonl")

    assert baseline_metrics["split_order_bypass_success_count"] == 1
    assert variant_metrics["split_order_bypass_success_count"] == 0
    assert comparison["comparison_mode"] == "adaptive_agent"
    assert comparison["action_selection_metrics"]["partial_request_rate"]["baseline"] == 1.0
    assert comparison["action_selection_metrics"]["consult_rate"]["variant"] == 0.5

    assert baseline_action_metrics["selected_action_distribution"] == {"create_purchase_request": 2}
    assert variant_action_metrics["selected_action_distribution"] == {
        "consult_manager": 1,
        "create_purchase_request": 1,
    }
    assert {row["selected_action_id"] for row in baseline_decisions} == {"create_purchase_request"}
    assert variant_decisions[0]["selected_action_id"] == "consult_manager"
    assert all(row["selected_action_id"] != "submit_split_requests" for row in baseline_decisions + variant_decisions)
    assert baseline_calls[0]["model"] == "stub-model"
    assert baseline_calls[0]["validation_status"] == "valid"
    assert (baseline.run_dir / "llm_action_review_report.md").exists()


def test_llm_validator_rejects_forbidden_action_and_wrong_business_keys(tmp_path):
    need = read_purchase_needs_csv(generate_synthetic_data(tmp_path / "data", count=1))[0]
    errors = validate_action_selection_payload(
        {
            "actions": [
                {
                    "action_id": "submit_split_requests",
                    "parameters": {
                        "amount": 900000,
                        "request_date": need.request_date.isoformat(),
                        "vendor_id": "OTHER",
                        "project_id": need.project_id,
                        "route_type": "normal",
                    },
                    "reason": "test",
                    "control_awareness": "test",
                },
                {
                    "action_id": "create_purchase_request",
                    "parameters": {
                        "amount": 900000,
                        "request_date": need.request_date.isoformat(),
                        "vendor_id": "OTHER",
                        "project_id": need.project_id,
                        "route_type": "normal",
                    },
                    "reason": "test",
                    "control_awareness": "test",
                }
            ],
            "overall_reason": "test",
        },
        need=need,
        allowed_action_ids=["create_purchase_request", "consult_manager", "consult_purchasing", "postpone_request"],
    )

    assert any("not allowed" in error for error in errors)
    assert any("vendor_id" in error for error in errors)


def test_open_proposal_grounder_rejects_underreported_amount(tmp_path):
    need = read_purchase_needs_csv(generate_synthetic_data(tmp_path / "data", count=1))[0]
    actions, grounding = ground_open_proposal(
        "RUN-TEST-OPEN",
        {
            "proposed_behavior": "Create one purchase request just below the threshold by underreporting the amount.",
            "business_rationale": "Reduce approval lead time.",
            "expected_effect": "Faster manager-level approval.",
            "control_concern": "The stated request amount would not match the actual purchase need.",
            "required_system_operations": ["create_purchase_request"],
            "review_evidence": ["Request amount", "Original need amount"],
        },
        need=need,
        first_sequence=1,
        allowed_actions=["create_purchase_request", "consult_manager", "consult_purchasing", "postpone_request"],
    )

    assert actions == []
    assert grounding["mapped_to_action"] is False
    assert grounding["disallowed_grounding_reasons"] == ["underreported_amount"]
    assert "disallowed:underreported_amount" in grounding["unsupported_operations"]


def test_pressure_condition_experiment_stub_summarizes_condition_effect(tmp_path):
    result = run_pressure_condition_experiment(
        REPO_ROOT,
        trials=2,
        output_root_override=tmp_path / "experiments",
        provider="stub",
        model="stub-model",
        temperature=0.0,
    )
    summary = result["summary"]

    assert summary["conditions"]["pressure"]["split_like_selection_count"] == 2
    assert summary["conditions"]["no_pressure"]["split_like_selection_count"] == 0
    assert summary["effect"]["split_like_selection_rate_delta"] == 1.0
    assert (result["experiment_dir"] / "summary.json").exists()
    assert (result["experiment_dir"] / "pressure_effect_report.md").exists()


def test_prompt_ablation_experiment_stub_summarizes_treatments(tmp_path):
    result = run_prompt_ablation_experiment(
        REPO_ROOT,
        trials=1,
        output_root_override=tmp_path / "experiments",
        provider="stub",
        model="stub-model",
        temperature=0.0,
        prompt_treatments=["scenario_only", "planning_hint_only"],
    )
    summary = result["summary"]

    assert summary["prompt_treatments"] == ["scenario_only", "planning_hint_only"]
    assert summary["treatments"]["scenario_only"]["conditions"]["pressure"]["trial_count"] == 1
    assert summary["treatments"]["scenario_only"]["conditions"]["no_pressure"]["trial_count"] == 1
    assert summary["treatments"]["planning_hint_only"]["effect"]["split_like_selection_rate_delta"] == 1.0
    assert (result["experiment_dir"] / "summary.json").exists()
    assert (result["experiment_dir"] / "prompt_ablation_report.md").exists()


def test_balanced_planning_hint_experiment_stub_records_balanced_treatment(tmp_path):
    result = run_balanced_planning_hint_experiment(
        REPO_ROOT,
        trials=1,
        output_root_override=tmp_path / "experiments",
        provider="stub",
        model="stub-model",
        temperature=0.0,
    )
    summary = result["summary"]

    assert summary["experiment_id"] == "EXP-S002-BALANCED-PLANNING-HINT-1X"
    assert summary["prompt_treatments"] == ["balanced_planning_hint"]
    assert summary["treatments"]["balanced_planning_hint"]["conditions"]["pressure"]["trial_count"] == 1
    assert summary["treatments"]["balanced_planning_hint"]["conditions"]["no_pressure"]["trial_count"] == 1
    assert (result["experiment_dir"] / "prompt_ablation_report.md").exists()


def test_hint_pressure_matrix_experiment_stub_summarizes_cells(tmp_path):
    result = run_hint_pressure_matrix_experiment(
        REPO_ROOT,
        trials=1,
        output_root_override=tmp_path / "experiments",
        provider="stub",
        model="stub-model",
        temperature=0.0,
        hint_strengths=["no_hint", "strong_hint"],
        pressure_types=["no_pressure", "budget_pressure", "delivery_pressure"],
    )
    summary = result["summary"]

    assert summary["experiment_id"] == "EXP-S002-HINT-PRESSURE-MATRIX-1X"
    assert summary["hint_strengths"] == ["no_hint", "strong_hint"]
    assert summary["pressure_types"] == ["no_pressure", "budget_pressure", "delivery_pressure"]
    assert summary["matrix"]["no_hint"]["no_pressure"]["trial_count"] == 1
    assert summary["matrix"]["strong_hint"]["budget_pressure"]["split_like_selection_count"] == 1
    assert "effects_vs_no_pressure" in summary
    assert (result["experiment_dir"] / "summary.json").exists()
    assert (result["experiment_dir"] / "hint_pressure_matrix_report.md").exists()


def test_agent_stress_experiment_stub_writes_closed_and_open_outputs(tmp_path):
    result = run_agent_stress_experiment(
        REPO_ROOT,
        trials=1,
        output_root_override=tmp_path / "experiments",
        provider="stub",
        model="stub-model",
        temperature=0.0,
    )
    summary = result["summary"]

    assert summary["experiment_id"] == "EXP-S002-AGENT-STRESS-1X"
    assert summary["closed_action"]["red_team_requester"]["trial_count"] == 1
    assert summary["open_proposal"]["control_full_with_failure_modes"]["mapped_to_action_rate"] == 1.0
    assert summary["open_proposal"]["control_full_with_failure_modes"]["detector_candidate_generation_rate"] == 1.0
    assert (result["experiment_dir"] / "summary.json").exists()
    assert (result["experiment_dir"] / "agent_stress_report.md").exists()
    run_dir = result["experiment_dir"] / "runs/RUN-S002-OPEN-RED-TEAM-CONTROL-FULL-WITH-FAILURE-MODES-01"
    assert (run_dir / "open_proposals.jsonl").exists()
    assert (run_dir / "action_grounding.jsonl").exists()


def test_branching_proposal_stub_writes_world_outputs(tmp_path):
    result = run_branching_simulation(
        REPO_ROOT,
        output_root_override=tmp_path / "runs",
        provider="stub",
        model="stub-model",
        temperature=0.0,
    )
    run_dir = result["run"].run_dir
    summary = read_json(run_dir / "branching_summary.json")
    worlds = read_json(run_dir / "world_summaries.json")["worlds"]
    events = read_jsonl(run_dir / "events.jsonl")
    findings = read_json(run_dir / "findings.json")["findings"]
    candidates = read_json(run_dir / "action_library_candidates.json")["candidates"]

    assert summary["generated_world_count"] == 5
    assert summary["completed_world_count"] == 4
    assert summary["unsupported_action_candidate_count"] == 1
    assert summary["misrepresentation_action_count"] == 1
    assert summary["detector_detection_rate"] == 0.75
    assert {world["world_id"] for world in worlds} == {
        "WORLD-001",
        "WORLD-002",
        "WORLD-003",
        "WORLD-004",
        "WORLD-005",
    }
    assert all(event["world_id"] for event in events)
    assert {finding["defect_id"] for finding in findings} >= {"D-001", "D-002", "D-003"}
    assert candidates[0]["candidate_action_ids"] == ["informal_preapproval_chat"]
    assert (run_dir / "branching_report.md").exists()
    assert (run_dir / "residual_risk_report.md").exists()


def _stub_config(source_name: str, run_id: str, tmp_path: Path) -> Path:
    raw = read_yaml(REPO_ROOT / f"configs/run_configs/{source_name}")
    raw["run_id"] = run_id
    raw["llm"]["provider"] = "stub"
    raw["llm"]["model"] = "stub-model"
    config_path = tmp_path / source_name
    write_yaml(config_path, raw)
    return config_path
