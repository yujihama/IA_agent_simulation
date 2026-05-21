import json
from datetime import date
from pathlib import Path

from ia_sim.branching import execute_branching_worlds
from ia_sim.config import load_control_cards, read_yaml, write_yaml
from ia_sim.detectors import detect_control_findings
from ia_sim.evidence import export_redacted_branching_evidence
from ia_sim.llm import ground_open_proposal, validate_action_selection_payload
from ia_sim.models import PlannedAction, PurchaseNeed
from ia_sim.orchestrator import (
    compare_runs,
    build_alias_residual_review,
    load_variant_policy,
    run_agent_stress_experiment,
    run_balanced_planning_hint_experiment,
    run_branching_alias_stability_experiment,
    run_branching_hint_ablation_experiment,
    run_branching_variant_comparison,
    run_branching_simulation,
    run_hint_pressure_matrix_experiment,
    run_prompt_ablation_experiment,
    run_pressure_condition_experiment,
    run_simulation,
)
from ia_sim.rule_engine import RuleEngine
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

    assert summary["generated_world_count"] == 20
    assert summary["completed_world_count"] == 20
    assert summary["multi_stage_enabled"] is True
    assert summary["max_depth"] == 3
    assert summary["max_total_worlds"] == 25
    assert summary["expanded_world_count"] == 3
    assert summary["max_depth_reached_count"] == 4
    assert summary["generated_depth_counts"] == {"1": 5, "2": 5, "3": 10}
    assert summary["duplicate_world_count"] == 0
    assert summary["unsupported_action_candidate_count"] == 0
    assert summary["misrepresentation_action_count"] == 4
    assert summary["detector_detection_rate"] == 1.0
    assert summary["lineage_detection_rate"] == 1.0
    assert summary["detector_detection_rate_numerator"] == 16
    assert summary["detector_detection_rate_denominator"] == 16
    assert summary["new_risk_detection_rate"] == 0.8125
    assert summary["new_risk_detection_rate_numerator"] == 13
    assert summary["new_risk_detection_rate_denominator"] == 16
    assert summary["current_world_detection_rate"] == 0.65
    assert summary["inherited_risk_count"] == 15
    assert summary["inherited_risk_world_count"] == 15
    assert summary["inherited_only_high_risk_world_count"] == 3
    assert summary["undetected_new_risk_world_count"] == 3
    assert summary["residual_risk_world_count"] == 3
    assert {world["world_id"] for world in worlds} == {f"WORLD-{index:03d}" for index in range(1, 21)}
    world_by_id = {world["world_id"]: world for world in worlds}
    assert world_by_id["WORLD-005"]["child_world_ids"] == [
        "WORLD-006",
        "WORLD-007",
        "WORLD-008",
        "WORLD-009",
        "WORLD-010",
    ]
    assert world_by_id["WORLD-006"]["child_world_ids"] == [
        "WORLD-016",
        "WORLD-017",
        "WORLD-018",
        "WORLD-019",
        "WORLD-020",
    ]
    assert world_by_id["WORLD-010"]["child_world_ids"] == [
        "WORLD-011",
        "WORLD-012",
        "WORLD-013",
        "WORLD-014",
        "WORLD-015",
    ]
    assert world_by_id["WORLD-010"]["terminal_reason"] == "expanded"
    assert world_by_id["WORLD-015"]["terminal_reason"] == "max_depth_reached"
    assert world_by_id["WORLD-020"]["terminal_reason"] == "max_depth_reached"
    assert world_by_id["WORLD-010"]["inherited_detected_findings"]
    assert world_by_id["WORLD-010"]["current_detected_findings"] == []
    assert world_by_id["WORLD-012"]["current_detected_findings"]
    assert world_by_id["WORLD-012"]["inherited_detected_findings"]
    assert all(event["world_id"] for event in events)
    assert all("lineage_action_depth" in event["metadata"] for event in events)
    assert {finding["defect_id"] for finding in findings} >= {"D-001", "D-002", "D-003", "D-004"}
    assert any(event["action_id"] == "informal_preapproval_chat" for event in events)
    assert (run_dir / "branching_report.md").exists()
    assert (run_dir / "residual_risk_report.md").exists()


def test_system_blocked_branch_records_attempt_only():
    need = PurchaseNeed(
        purchase_need_id="NEED-TEST",
        request_date=date(2026, 6, 25),
        requester_user_id="USER-REQ-001",
        department_id="DEPT-001",
        vendor_id="VENDOR-014",
        project_id="PRJ-TEST",
        item_description="Test purchase",
        amount_total=1_750_000,
        needed_by=date(2026, 6, 30),
        scenario_id="S-002",
    )
    action = PlannedAction(
        sequence=1,
        purchase_need_id=need.purchase_need_id,
        action_id="create_purchase_request",
        parameters={
            "purchase_need_id": need.purchase_need_id,
            "amount": need.amount_total,
            "request_date": need.request_date.isoformat(),
            "vendor_id": need.vendor_id,
            "project_id": need.project_id,
            "route_type": "emergency",
        },
        rationale="Attempt blocked action.",
        allowed_actions=["create_purchase_request"],
        source="test",
        classification="system_blocked",
        world_id="WORLD-BLOCKED",
        branch_reason="blocked attempt",
    )
    rule_engine = RuleEngine(
        load_control_cards(REPO_ROOT / "configs/controls/p2p_controls.yaml"),
        load_variant_policy(REPO_ROOT, "baseline"),
    )

    events = execute_branching_worlds(
        run_id="RUN-BLOCKED-TEST",
        needs=[need],
        planned_actions=[action],
        rule_engine=rule_engine,
    )

    assert len(events) == 1
    assert events[0]["world_id"] == "WORLD-BLOCKED"
    assert events[0]["state_after"] == "blocked_attempt"
    assert events[0]["metadata"]["attempt_only"] is True
    assert events[0]["action_id"] == "create_purchase_request"


def test_branching_variant_comparison_replays_same_world_group(tmp_path):
    result = run_branching_variant_comparison(
        REPO_ROOT,
        output_root_override=tmp_path / "runs",
        provider="stub",
    )

    comparison = result["comparison"]
    assert comparison["same_world_group_replayed"] is True
    assert set(comparison["variants"]) == {
        "baseline",
        "variant_a_7d_aggregation",
        "variant_b_emergency_post_approval",
    }
    assert comparison["variants"]["baseline"]["generated_world_count"] == 20
    assert comparison["variants"]["baseline"]["unmitigated_finding_count"] == 28
    assert comparison["variants"]["baseline"]["lineage_detection_rate"] == 1.0
    assert comparison["variants"]["baseline"]["new_risk_detection_rate"] == 0.8125
    assert comparison["variants"]["baseline"]["inherited_risk_count"] == 15
    assert comparison["variants"]["variant_a_7d_aggregation"]["mitigated_finding_count"] == 4
    assert comparison["variants"]["variant_b_emergency_post_approval"]["mitigated_finding_count"] == 4

    variant_a_effects = [
        row for row in comparison["world_effects"] if row["variant_id"] == "variant_a_7d_aggregation"
    ]
    variant_b_effects = [
        row for row in comparison["world_effects"] if row["variant_id"] == "variant_b_emergency_post_approval"
    ]
    assert any(row["defects_mitigated_by_variant"] == ["D-001"] for row in variant_a_effects)
    assert any(row["defects_mitigated_by_variant"] == ["D-002"] for row in variant_b_effects)
    assert (result["comparison_dir"] / "branching_variant_comparison_report.md").exists()


def test_branching_hint_ablation_experiment_compares_prompt_conditions(tmp_path):
    result = run_branching_hint_ablation_experiment(
        REPO_ROOT,
        output_root_override=tmp_path / "runs",
        provider="stub",
        model="stub-model",
        temperature=0.0,
    )
    summary = result["summary"]
    experiment_dir = result["experiment_dir"]

    assert summary["coverage_target_modes"] == [
        "current_coverage_target",
        "risk_category_hidden",
        "process_state_only",
        "process_state_only_alias_actions",
    ]
    assert set(summary["conditions"]) == set(summary["coverage_target_modes"])
    assert summary["conditions"]["current_coverage_target"]["condition_slug"] == "current"
    assert summary["conditions"]["risk_category_hidden"]["condition_slug"] == "hidden"
    assert summary["conditions"]["process_state_only"]["condition_slug"] == "state_only"
    assert summary["conditions"]["process_state_only_alias_actions"]["condition_slug"] == "state_alias"
    assert summary["cross_condition"]["generated_world_count_by_condition"] == {
        "current_coverage_target": 20,
        "risk_category_hidden": 20,
        "process_state_only": 20,
        "process_state_only_alias_actions": 20,
    }

    current_payload = _first_branching_call_payload(
        experiment_dir / summary["conditions"]["current_coverage_target"]["baseline_run_dir"]
    )
    hidden_payload = _first_branching_call_payload(
        experiment_dir / summary["conditions"]["risk_category_hidden"]["baseline_run_dir"]
    )
    state_only_payload = _first_branching_call_payload(
        experiment_dir / summary["conditions"]["process_state_only"]["baseline_run_dir"]
    )
    state_alias_run_dir = experiment_dir / summary["conditions"]["process_state_only_alias_actions"]["baseline_run_dir"]
    state_alias_payload = _first_branching_call_payload(state_alias_run_dir)
    state_alias_call = read_jsonl(state_alias_run_dir / "branching_calls.jsonl")[0]
    state_alias_raw = state_alias_call["raw_response"]
    state_alias_proposal = read_jsonl(state_alias_run_dir / "branching_proposals.jsonl")[0]

    assert current_payload["branching_parameters"]["coverage_target_mode"] == "current_coverage_target"
    assert any("split" in target for target in current_payload["coverage_targets"])
    assert any("underreported" in target for target in current_payload["coverage_targets"])
    assert hidden_payload["branching_parameters"]["coverage_target_mode"] == "risk_category_hidden"
    assert not any("split" in target or "underreported" in target for target in hidden_payload["coverage_targets"])
    assert hidden_payload["control_cards"]
    assert all("red_team_instruction" not in card for card in hidden_payload["control_cards"])
    assert state_only_payload["branching_parameters"]["coverage_target_mode"] == "process_state_only"
    assert state_only_payload["control_cards"] == []
    assert state_only_payload["variant_context"] == {"visibility": "hidden_by_process_state_only_condition"}
    assert state_alias_payload["branching_parameters"]["coverage_target_mode"] == "process_state_only_alias_actions"
    assert state_alias_payload["control_cards"] == []
    assert state_alias_payload["variant_context"] == {"visibility": "hidden_by_process_state_only_condition"}
    assert [action["action_id"] for action in state_alias_payload["allowed_actions"]] == [
        "action_01",
        "action_02",
        "action_03",
        "action_04",
        "action_05",
    ]
    assert state_alias_call["action_aliasing_enabled"] is True
    assert state_alias_call["action_alias_map"]["action_01"] == "create_purchase_request"
    assert "create_purchase_request" not in json.dumps(state_alias_payload)
    assert "informal_preapproval_chat" not in json.dumps(state_alias_payload)
    assert "create_purchase_request" not in state_alias_raw
    assert "action_01" in state_alias_raw
    assert state_alias_proposal["prompt_action_ids"] == ["action_01"]
    assert state_alias_proposal["action_sequence"][0]["action_id"] == "create_purchase_request"
    for mode in ("risk_category_hidden", "process_state_only", "process_state_only_alias_actions"):
        run_dir = experiment_dir / summary["conditions"][mode]["baseline_run_dir"]
        all_targets = " ".join(
            target
            for payload in _branching_call_payloads(run_dir)
            for target in payload["coverage_targets"]
        )
        assert "split" not in all_targets
        assert "underreported" not in all_targets
        assert "emergency" not in all_targets
        assert "informal_preapproval" not in all_targets
    assert (experiment_dir / "branching_hint_ablation_report.md").exists()
    assert (experiment_dir / "alias_residual_review.json").exists()
    assert (experiment_dir / "alias_residual_review_report.md").exists()
    assert summary["alias_residual_review"]["residual_world_count"] >= 0
    assert "bucket_counts" in summary["alias_residual_review"]


def test_alias_residual_review_classifies_human_review_queue(tmp_path):
    result = run_branching_variant_comparison(
        REPO_ROOT,
        output_root_override=tmp_path / "runs",
        provider="stub",
        model="stub-model",
        temperature=0.0,
        coverage_target_mode="process_state_only_alias_actions",
    )
    review = build_alias_residual_review(result["baseline_run"].run_dir)

    assert review["review_type"] == "process_state_only_alias_actions_residual_risk_human_review"
    assert "bucket_counts" in review
    assert "theme_counts" in review
    for row in review["review_rows"]:
        assert row["candidate_buckets"]
        assert row["candidate_themes"]
        assert row["review_questions"]


def test_branching_alias_no_description_condition_hides_action_descriptions(tmp_path):
    result = run_branching_simulation(
        REPO_ROOT,
        output_root_override=tmp_path / "runs",
        provider="stub",
        model="stub-model",
        temperature=0.0,
        coverage_target_mode="process_state_only_alias_actions_no_descriptions",
    )
    run_dir = result["run"].run_dir
    payload = _first_branching_call_payload(run_dir)
    call = read_jsonl(run_dir / "branching_calls.jsonl")[0]

    assert payload["branching_parameters"]["coverage_target_mode"] == (
        "process_state_only_alias_actions_no_descriptions"
    )
    assert [action["action_id"] for action in payload["allowed_actions"]] == [
        "action_01",
        "action_02",
        "action_03",
        "action_04",
        "action_05",
    ]
    assert all("description" not in action for action in payload["allowed_actions"])
    assert call["action_aliasing_enabled"] is True
    assert "create_purchase_request" not in json.dumps(payload)
    assert "informal_preapproval_chat" not in json.dumps(payload)


def test_branching_alias_stability_experiment_summarizes_seed_temperature_grid(tmp_path):
    result = run_branching_alias_stability_experiment(
        REPO_ROOT,
        output_root_override=tmp_path / "runs",
        provider="stub",
        model="stub-model",
        temperatures=[0.0, 0.2],
        seeds=[101, 102],
    )
    summary = result["summary"]
    experiment_dir = result["experiment_dir"]

    assert summary["coverage_target_mode"] == "process_state_only_alias_actions"
    assert summary["temperatures"] == [0.0, 0.2]
    assert summary["seeds"] == [101, 102]
    assert len(summary["cells"]) == 4
    assert summary["stability"]["cell_count"] == 4
    assert "residual_world_count_by_cell" in summary["stability"]
    assert (experiment_dir / "summary.json").exists()
    assert (experiment_dir / "alias_stability_report.md").exists()
    for cell in summary["cells"]:
        assert cell["coverage_target_mode"] == "process_state_only_alias_actions"
        assert cell["seed"] in {101, 102}
        assert (experiment_dir / cell["alias_residual_review_path"]).exists()
        assert (experiment_dir / cell["alias_residual_review_report_path"]).exists()


def test_fast_track_route_attempt_detector_records_candidate():
    need = PurchaseNeed(
        purchase_need_id="NEED-FAST",
        request_date=date(2026, 6, 25),
        requester_user_id="USER-REQ-001",
        department_id="DEPT-001",
        vendor_id="VENDOR-014",
        project_id="PRJ-FAST",
        item_description="Fast track purchase",
        amount_total=1_750_000,
        needed_by=date(2026, 6, 30),
        scenario_id="S-002",
    )
    action = PlannedAction(
        sequence=1,
        purchase_need_id=need.purchase_need_id,
        action_id="create_purchase_request",
        parameters={
            "purchase_need_id": need.purchase_need_id,
            "amount": need.amount_total,
            "request_date": need.request_date.isoformat(),
            "vendor_id": need.vendor_id,
            "project_id": need.project_id,
            "route_type": "normal",
            "requested_route_type": "fast-track",
        },
        rationale="Attempt a requester-specified fast-track route.",
        allowed_actions=["create_purchase_request"],
        source="test",
        classification="policy_violation",
        world_id="WORLD-FAST",
        branch_reason="Requester-specified fast-track routing",
        risk_score=85,
    )
    rule_engine = RuleEngine(
        load_control_cards(REPO_ROOT / "configs/controls/p2p_controls.yaml"),
        load_variant_policy(REPO_ROOT, "baseline"),
    )
    events = execute_branching_worlds(
        run_id="RUN-FAST-TEST",
        needs=[need],
        planned_actions=[action],
        rule_engine=rule_engine,
    )

    annotations = detect_control_findings(events)

    fast_track = [item for item in annotations if item["detector_id"] == "fast_track_route_attempt_detector"]
    assert len(fast_track) == 1
    assert fast_track[0]["defect_id"] == "D-CAND-FAST-TRACK"
    assert fast_track[0]["world_id"] == "WORLD-FAST"


def test_export_redacted_branching_evidence_writes_reviewable_artifacts(tmp_path):
    result = run_branching_variant_comparison(
        REPO_ROOT,
        output_root_override=tmp_path / "runs",
        provider="stub",
    )
    evidence_dir = tmp_path / "evidence"

    manifest = export_redacted_branching_evidence(
        source_root=tmp_path / "runs",
        output_dir=evidence_dir,
    )

    assert not manifest["missing_files"]
    calls_path = evidence_dir / "RUN-S002-BRANCHING-BASELINE/branching_calls.jsonl"
    comparison_path = (
        evidence_dir
        / "comparisons/CMP-S002-BRANCHING-BASELINE-VARIANTS/branching_variant_comparison.json"
    )
    calls_text = calls_path.read_text(encoding="utf-8")
    assert calls_path.exists()
    assert comparison_path.exists()
    assert "request_messages" in calls_text
    assert "raw_response" in calls_text
    assert "sk-" not in calls_text
    assert (evidence_dir / "redaction_policy.json").exists()
    assert result["comparison"]["same_world_group_replayed"] is True


def _stub_config(source_name: str, run_id: str, tmp_path: Path) -> Path:
    raw = read_yaml(REPO_ROOT / f"configs/run_configs/{source_name}")
    raw["run_id"] = run_id
    raw["llm"]["provider"] = "stub"
    raw["llm"]["model"] = "stub-model"
    config_path = tmp_path / source_name
    write_yaml(config_path, raw)
    return config_path


def _first_branching_call_payload(run_dir: Path) -> dict:
    return _branching_call_payloads(run_dir)[0]


def _branching_call_payloads(run_dir: Path) -> list[dict]:
    return [
        json.loads(row["request_messages"][1]["content"])
        for row in read_jsonl(run_dir / "branching_calls.jsonl")
    ]
