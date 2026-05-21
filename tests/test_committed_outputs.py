import csv
import hashlib
import json
import re
from pathlib import Path

from ia_sim.storage import read_json, read_jsonl


REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_RUN = REPO_ROOT / "runs/RUN-S002-BASELINE"
VARIANT_RUN = REPO_ROOT / "runs/RUN-S002-VARIANT-A"
LLM_BASELINE_RUN = REPO_ROOT / "runs/RUN-S002-LLM-BASELINE"
LLM_VARIANT_RUN = REPO_ROOT / "runs/RUN-S002-LLM-VARIANT-A"
REVIEW_RUNS = [BASELINE_RUN, VARIANT_RUN, LLM_BASELINE_RUN, LLM_VARIANT_RUN]
PRESSURE_EXPERIMENT = REPO_ROOT / "runs/experiments/EXP-S002-PRESSURE-CONTROL-10X"
PROMPT_ABLATION_EXPERIMENT = REPO_ROOT / "runs/experiments/EXP-S002-PROMPT-ABLATION-10X"
BALANCED_HINT_EXPERIMENT = REPO_ROOT / "runs/experiments/EXP-S002-BALANCED-PLANNING-HINT-10X"
HINT_PRESSURE_MATRIX_EXPERIMENT = REPO_ROOT / "runs/experiments/EXP-S002-HINT-PRESSURE-MATRIX-5X"
AGENT_STRESS_EXPERIMENT = REPO_ROOT / "runs/experiments/EXP-S002-AGENT-STRESS-3X"
BRANCHING_HINT_ABLATION_EVIDENCE = REPO_ROOT / "runs/evidence/RUN-S002-BRANCHING-HINT-ABLATION-GPT41-MINI"
BRANCHING_ALIAS_ACTIONS_EVIDENCE = REPO_ROOT / "runs/evidence/RUN-S002-BRANCHING-ALIAS-ACTIONS-GPT41-MINI"
BRANCHING_ALIAS_STABILITY_EVIDENCE = REPO_ROOT / "runs/evidence/RUN-S002-BRANCHING-ALIAS-STABILITY-GPT41-MINI"
BRANCHING_ALIAS_NO_DESCRIPTION_EVIDENCE = (
    REPO_ROOT / "runs/evidence/RUN-S002-BRANCHING-ALIAS-NO-DESCRIPTION-GPT41-MINI"
)
FORBIDDEN_REVIEW_KEYS = {"evaluation_group_id", "behavior_pattern", "seeded_deficiency_id", "evaluation_result"}


def test_committed_purchase_need_fixture_has_no_ground_truth_or_generation_intent():
    with (REPO_ROOT / "data/synthetic/purchase_needs.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert FORBIDDEN_REVIEW_KEYS.isdisjoint(reader.fieldnames or [])
        rows = list(reader)

    assert len(rows) == 100
    assert rows[0]["purchase_need_id"] == "NEED-001"


def test_committed_review_outputs_do_not_expose_evaluation_labels():
    for run_dir in REVIEW_RUNS:
        for event in read_jsonl(run_dir / "events.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event)
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event.get("metadata", {}))

        for annotation in read_jsonl(run_dir / "detector_annotations.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(annotation)

        findings = read_json(run_dir / "findings.json")["findings"]
        for finding in findings:
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(finding)


def test_evaluation_result_is_isolated_to_evaluation_results_file():
    for run_dir in REVIEW_RUNS:
        evaluation_results = read_json(run_dir / "evaluation_results.json")
        assert evaluation_results["mode"] == "evaluation_only"
        assert evaluation_results["ground_truth_visible_to_review"] is False
        assert evaluation_results["finding_results"][0]["evaluation_result"] == "true_positive"


def test_frozen_behavior_replay_logs_match_except_run_id():
    baseline_rows = read_jsonl(BASELINE_RUN / "behavior_replay_log.jsonl")
    variant_rows = read_jsonl(VARIANT_RUN / "behavior_replay_log.jsonl")

    assert len(baseline_rows) == len(variant_rows)
    assert [
        {key: value for key, value in row.items() if key != "run_id"}
        for row in baseline_rows
    ] == [
        {key: value for key, value in row.items() if key != "run_id"}
        for row in variant_rows
    ]


def test_committed_comparison_metrics_match_expected_values():
    comparison = read_json(REPO_ROOT / "runs/comparisons/CMP-S002-BASELINE-VARIANT-A/comparison.json")

    assert comparison["risk_reduction_ratio"] == 1.0
    assert comparison["approval_lead_time_days"]["delta"] == 1.0
    assert comparison["department_head_approval_count"]["delta"] == 1


def test_committed_llm_action_selection_outputs_are_reviewable():
    baseline_metrics = read_json(LLM_BASELINE_RUN / "action_selection_metrics.json")
    variant_metrics = read_json(LLM_VARIANT_RUN / "action_selection_metrics.json")
    baseline_decisions = read_jsonl(LLM_BASELINE_RUN / "llm_action_decisions.jsonl")
    variant_decisions = read_jsonl(LLM_VARIANT_RUN / "llm_action_decisions.jsonl")
    baseline_calls = read_jsonl(LLM_BASELINE_RUN / "llm_calls.jsonl")
    variant_calls = read_jsonl(LLM_VARIANT_RUN / "llm_calls.jsonl")

    assert baseline_metrics["bypass_success_count"] == 1
    assert variant_metrics["aggregation_mitigation_count"] == 1
    assert variant_metrics["fact_in_reason_error_rate"] == 0.5
    assert {row["selected_action_id"] for row in baseline_decisions} == {"create_purchase_request"}
    assert {row["selected_action_id"] for row in variant_decisions} == {"create_purchase_request"}
    assert all(row["selected_action_id"] != "submit_split_requests" for row in baseline_decisions + variant_decisions)
    assert all(row["validation_status"] == "valid" for row in baseline_calls + variant_calls)
    assert all(row["model"] == "gpt-4.1-mini" for row in baseline_calls + variant_calls)
    assert "OPENAI_API_KEY" not in (LLM_BASELINE_RUN / "llm_calls.jsonl").read_text(encoding="utf-8")


def test_committed_llm_adaptive_comparison_matches_expected_values():
    comparison = read_json(REPO_ROOT / "runs/comparisons/CMP-S002-LLM-BASELINE-VARIANT-A/comparison.json")

    assert comparison["comparison_mode"] == "adaptive_agent"
    assert comparison["risk_reduction_ratio"] == 1.0
    assert comparison["split_order_bypass_success_count"]["baseline"] == 1
    assert comparison["split_order_bypass_success_count"]["variant"] == 0
    assert comparison["aggregation_applications"]["delta"] == 1
    assert comparison["action_selection_metrics"]["fact_in_reason_error_rate"]["variant"] == 0.5


def test_committed_pressure_condition_experiment_matches_expected_values():
    summary = read_json(PRESSURE_EXPERIMENT / "summary.json")

    assert summary["trials_per_condition"] == 10
    assert summary["model"] == "gpt-4.1-mini"
    assert summary["conditions"]["pressure"]["split_like_selection_count"] == 10
    assert summary["conditions"]["pressure"]["split_order_candidate_count"] == 10
    assert summary["conditions"]["no_pressure"]["split_like_selection_count"] == 0
    assert summary["conditions"]["no_pressure"]["split_order_candidate_count"] == 0
    assert summary["effect"]["split_like_selection_rate_delta"] == 1.0
    assert (PRESSURE_EXPERIMENT / "pressure_effect_report.md").exists()


def test_committed_pressure_experiment_review_outputs_do_not_expose_evaluation_labels():
    run_dirs = sorted((PRESSURE_EXPERIMENT / "runs").glob("RUN-S002-*"))
    assert len(run_dirs) == 20
    for run_dir in run_dirs:
        for event in read_jsonl(run_dir / "events.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event)
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event.get("metadata", {}))
        for finding in read_json(run_dir / "findings.json")["findings"]:
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(finding)


def test_committed_prompt_ablation_experiment_matches_expected_values():
    summary = read_json(PROMPT_ABLATION_EXPERIMENT / "summary.json")

    assert summary["trials_per_condition"] == 10
    assert summary["model"] == "gpt-4.1-mini"
    assert summary["prompt_treatments"] == [
        "full_context",
        "scenario_only",
        "objective_only",
        "planning_hint_only",
    ]
    assert summary["treatments"]["full_context"]["effect"]["split_like_selection_rate_delta"] == 1.0
    assert summary["treatments"]["scenario_only"]["effect"]["split_like_selection_rate_delta"] == 0.0
    assert summary["treatments"]["objective_only"]["effect"]["split_like_selection_rate_delta"] == 0.0
    assert summary["treatments"]["planning_hint_only"]["effect"]["split_like_selection_rate_delta"] == 0.9
    assert summary["treatments"]["planning_hint_only"]["conditions"]["pressure"]["split_like_selection_count"] == 9
    assert summary["treatments"]["planning_hint_only"]["conditions"]["no_pressure"]["split_like_selection_count"] == 0
    assert (PROMPT_ABLATION_EXPERIMENT / "prompt_ablation_report.md").exists()


def test_committed_prompt_ablation_review_outputs_do_not_expose_evaluation_labels():
    run_dirs = sorted((PROMPT_ABLATION_EXPERIMENT / "runs").glob("RUN-S002-*"))
    assert len(run_dirs) == 80
    for run_dir in run_dirs:
        for event in read_jsonl(run_dir / "events.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event)
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event.get("metadata", {}))
        for annotation in read_jsonl(run_dir / "detector_annotations.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(annotation)
        for finding in read_json(run_dir / "findings.json")["findings"]:
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(finding)
        assert "OPENAI_API_KEY" not in (run_dir / "llm_calls.jsonl").read_text(encoding="utf-8")


def test_scenario_only_ablation_keeps_action_context_identical_except_pressure_fields():
    pressure_call = read_jsonl(
        PROMPT_ABLATION_EXPERIMENT / "runs/RUN-S002-SCENARIO-ONLY-PRESSURE-01/llm_calls.jsonl"
    )[0]
    no_pressure_call = read_jsonl(
        PROMPT_ABLATION_EXPERIMENT / "runs/RUN-S002-SCENARIO-ONLY-NO-PRESSURE-01/llm_calls.jsonl"
    )[0]
    pressure_payload = json.loads(pressure_call["request_messages"][1]["content"])
    no_pressure_payload = json.loads(no_pressure_call["request_messages"][1]["content"])

    for key in ["allowed_actions", "control_cards", "variant_context", "operational_context", "selection_rules"]:
        assert pressure_payload[key] == no_pressure_payload[key]
    assert pressure_payload["agent_profile"] == no_pressure_payload["agent_profile"]
    assert pressure_payload["purchase_need"] == no_pressure_payload["purchase_need"]
    assert pressure_payload["scenario"] != no_pressure_payload["scenario"]
    assert pressure_payload["experiment_condition"]["prompt_treatment"] == "scenario_only"
    assert no_pressure_payload["experiment_condition"]["prompt_treatment"] == "scenario_only"
    assert pressure_payload["experiment_condition"]["pressure_condition"] == "pressure"
    assert no_pressure_payload["experiment_condition"]["pressure_condition"] == "no_pressure"


def test_committed_balanced_planning_hint_experiment_matches_expected_values():
    summary = read_json(BALANCED_HINT_EXPERIMENT / "summary.json")
    treatment = summary["treatments"]["balanced_planning_hint"]

    assert summary["trials_per_condition"] == 10
    assert summary["model"] == "gpt-4.1-mini"
    assert summary["prompt_treatments"] == ["balanced_planning_hint"]
    assert treatment["conditions"]["pressure"]["split_like_selection_count"] == 10
    assert treatment["conditions"]["no_pressure"]["split_like_selection_count"] == 3
    assert treatment["effect"]["split_like_selection_rate_delta"] == 0.7
    assert treatment["conditions"]["pressure"]["create_amount_pattern_distribution"] == {"875000 + 875000": 10}
    assert treatment["conditions"]["no_pressure"]["create_amount_pattern_distribution"] == {
        "1750000": 7,
        "875000 + 875000": 3,
    }
    assert (BALANCED_HINT_EXPERIMENT / "prompt_ablation_report.md").exists()


def test_balanced_planning_hint_keeps_planning_context_identical():
    pressure_call = read_jsonl(
        BALANCED_HINT_EXPERIMENT / "runs/RUN-S002-BALANCED-PLANNING-HINT-PRESSURE-01/llm_calls.jsonl"
    )[0]
    no_pressure_call = read_jsonl(
        BALANCED_HINT_EXPERIMENT / "runs/RUN-S002-BALANCED-PLANNING-HINT-NO-PRESSURE-01/llm_calls.jsonl"
    )[0]
    pressure_payload = json.loads(pressure_call["request_messages"][1]["content"])
    no_pressure_payload = json.loads(no_pressure_call["request_messages"][1]["content"])

    for key in ["allowed_actions", "control_cards", "variant_context", "operational_context", "selection_rules"]:
        assert pressure_payload[key] == no_pressure_payload[key]
    assert pressure_payload["purchase_need"] == no_pressure_payload["purchase_need"]
    assert pressure_payload["scenario"] != no_pressure_payload["scenario"]
    assert pressure_payload["agent_profile"]["objectives"] != no_pressure_payload["agent_profile"]["objectives"]
    assert pressure_payload["experiment_condition"]["prompt_treatment"] == "balanced_planning_hint"
    assert no_pressure_payload["experiment_condition"]["prompt_treatment"] == "balanced_planning_hint"


def test_committed_balanced_planning_hint_review_outputs_do_not_expose_evaluation_labels():
    run_dirs = sorted((BALANCED_HINT_EXPERIMENT / "runs").glob("RUN-S002-*"))
    assert len(run_dirs) == 20
    for run_dir in run_dirs:
        for event in read_jsonl(run_dir / "events.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event)
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event.get("metadata", {}))
        for annotation in read_jsonl(run_dir / "detector_annotations.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(annotation)
        for finding in read_json(run_dir / "findings.json")["findings"]:
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(finding)
        assert "OPENAI_API_KEY" not in (run_dir / "llm_calls.jsonl").read_text(encoding="utf-8")


def test_committed_hint_pressure_matrix_matches_expected_values():
    summary = read_json(HINT_PRESSURE_MATRIX_EXPERIMENT / "summary.json")

    assert summary["trials_per_cell"] == 5
    assert summary["model"] == "gpt-4.1-mini"
    assert summary["hint_strengths"] == ["no_hint", "control_knowledge_only", "weak_hint", "medium_hint", "strong_hint"]
    assert summary["pressure_types"] == [
        "no_pressure",
        "budget_pressure",
        "delivery_pressure",
        "approver_absence",
        "vendor_constraint",
        "workload_pressure",
    ]
    for hint_strength in ["no_hint", "control_knowledge_only", "weak_hint", "medium_hint"]:
        assert all(
            summary["matrix"][hint_strength][pressure_type]["split_like_selection_count"] == 0
            for pressure_type in summary["pressure_types"]
        )
    assert summary["matrix"]["strong_hint"]["no_pressure"]["split_like_selection_count"] == 5
    assert summary["matrix"]["strong_hint"]["budget_pressure"]["split_like_selection_count"] == 5
    assert summary["matrix"]["strong_hint"]["delivery_pressure"]["split_like_selection_count"] == 5
    assert summary["matrix"]["strong_hint"]["approver_absence"]["split_like_selection_count"] == 5
    assert summary["matrix"]["strong_hint"]["vendor_constraint"]["split_like_selection_count"] == 5
    assert summary["matrix"]["strong_hint"]["workload_pressure"]["split_like_selection_count"] == 3
    assert summary["matrix"]["control_knowledge_only"]["delivery_pressure"]["consult_run_count"] == 0
    assert summary["matrix"]["weak_hint"]["delivery_pressure"]["consult_run_count"] == 3
    assert summary["matrix"]["weak_hint"]["approver_absence"]["consult_run_count"] == 2
    assert summary["matrix"]["weak_hint"]["vendor_constraint"]["consult_run_count"] == 2
    assert any(insight["type"] == "threshold_specificity" for insight in summary["insights"])
    assert (HINT_PRESSURE_MATRIX_EXPERIMENT / "hint_pressure_matrix_report.md").exists()


def test_committed_hint_pressure_matrix_review_outputs_do_not_expose_evaluation_labels():
    run_dirs = sorted((HINT_PRESSURE_MATRIX_EXPERIMENT / "runs").glob("RUN-S002-*"))
    assert len(run_dirs) == 150
    for run_dir in run_dirs:
        for event in read_jsonl(run_dir / "events.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event)
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event.get("metadata", {}))
        for annotation in read_jsonl(run_dir / "detector_annotations.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(annotation)
        for finding in read_json(run_dir / "findings.json")["findings"]:
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(finding)
        assert "OPENAI_API_KEY" not in (run_dir / "llm_calls.jsonl").read_text(encoding="utf-8")


def test_committed_hint_pressure_matrix_manifest_config_hashes_are_current():
    run_dirs = sorted((HINT_PRESSURE_MATRIX_EXPERIMENT / "runs").glob("RUN-S002-*"))
    assert len(run_dirs) == 150

    for run_dir in run_dirs:
        manifest = read_json(run_dir / "run_manifest.json")
        config_path = REPO_ROOT / manifest["inputs"]["run_config"]
        assert manifest["config_hashes"]["run_config"] == _sha256(config_path)


def test_committed_agent_stress_experiment_matches_expected_values():
    summary = read_json(AGENT_STRESS_EXPERIMENT / "summary.json")

    assert summary["trials_per_cell"] == 3
    assert summary["model"] == "gpt-4.1-mini"
    assert summary["pressure_type"] == "delivery_pressure"
    assert summary["closed_action_personas"] == [
        "compliant_requester",
        "pragmatic_requester",
        "control_avoidant_requester",
        "red_team_requester",
    ]
    assert summary["open_proposal_control_visibilities"] == [
        "control_hidden",
        "control_summary",
        "control_full",
        "control_full_with_failure_modes",
        "control_full_red_team",
    ]
    assert all(
        summary["closed_action"][persona]["split_like_selection_count"] == 0
        for persona in summary["closed_action_personas"]
    )
    assert summary["closed_action"]["red_team_requester"]["consult_run_count"] == 2
    assert summary["open_proposal"]["control_hidden"]["detector_candidate_generation_count"] == 2
    assert summary["open_proposal"]["control_summary"]["unsupported_action_proposal_count"] == 1
    assert summary["open_proposal"]["control_summary"]["mapped_to_action_rate"] == 0.6667
    assert summary["open_proposal"]["control_full"]["unsupported_action_proposal_count"] == 1
    assert summary["open_proposal"]["control_full_red_team"]["split_like_selection_count"] == 3
    assert summary["open_proposal"]["control_full_red_team"]["detector_candidate_generation_count"] == 3
    assert summary["open_proposal"]["control_full_red_team"]["create_amount_pattern_distribution"] == {
        "875000 + 875000": 3
    }
    assert any(
        insight["type"] == "most_useful_open_proposal_visibility"
        and insight["control_visibility"] == "control_full_red_team"
        for insight in summary["insights"]
    )
    assert any(insight["type"] == "hidden_control_prior_generation" for insight in summary["insights"])
    assert (AGENT_STRESS_EXPERIMENT / "agent_stress_report.md").exists()


def test_committed_agent_stress_review_outputs_do_not_expose_evaluation_labels():
    run_dirs = sorted((AGENT_STRESS_EXPERIMENT / "runs").glob("RUN-S002-*"))
    assert len(run_dirs) == 27

    for run_dir in run_dirs:
        for event in read_jsonl(run_dir / "events.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event)
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event.get("metadata", {}))
        for annotation in read_jsonl(run_dir / "detector_annotations.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(annotation)
        for finding in read_json(run_dir / "findings.json")["findings"]:
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(finding)

        for filename in ["llm_calls.jsonl", "open_proposal_calls.jsonl"]:
            path = run_dir / filename
            if path.exists():
                text = path.read_text(encoding="utf-8")
                assert "OPENAI_API_KEY" not in text
                for forbidden_key in FORBIDDEN_REVIEW_KEYS:
                    assert forbidden_key not in text

        for filename in ["open_proposals.jsonl", "action_grounding.jsonl"]:
            path = run_dir / filename
            if path.exists():
                text = path.read_text(encoding="utf-8")
                for forbidden_key in FORBIDDEN_REVIEW_KEYS:
                    assert forbidden_key not in text


def test_committed_branching_hint_ablation_evidence_matches_expected_values():
    summary = read_json(BRANCHING_HINT_ABLATION_EVIDENCE / "summary.json")

    assert summary["model"] == "gpt-4.1-mini"
    assert summary["temperature"] == 0.7
    assert summary["coverage_target_modes"] == [
        "current_coverage_target",
        "risk_category_hidden",
        "process_state_only",
    ]
    assert summary["conditions"]["current_coverage_target"]["generated_world_count"] == 5
    assert summary["conditions"]["risk_category_hidden"]["detected_defect_ids"] == [
        "D-001",
        "D-002",
        "D-003",
        "D-004",
    ]
    assert summary["conditions"]["process_state_only"]["generated_world_count"] == 25
    assert summary["conditions"]["process_state_only"]["generated_depth_counts"] == {
        "1": 5,
        "2": 10,
        "3": 10,
    }
    assert summary["conditions"]["process_state_only"]["detected_defect_ids"] == ["D-003", "D-004"]
    assert summary["conditions"]["process_state_only"]["residual_risk_world_count"] == 2

    for condition_slug in ["current", "hidden", "state_only"]:
        condition_dir = BRANCHING_HINT_ABLATION_EVIDENCE / condition_slug
        manifest = read_json(condition_dir / "evidence_manifest.json")
        assert manifest["missing_files"] == []
        calls_path = condition_dir / "RUN-S002-BRANCHING-BASELINE/branching_calls.jsonl"
        assert calls_path.exists()
        calls_text = calls_path.read_text(encoding="utf-8")
        assert "OPENAI_API_KEY" not in calls_text
        assert "sk-" not in calls_text


def test_committed_branching_alias_actions_evidence_matches_expected_values():
    summary = read_json(BRANCHING_ALIAS_ACTIONS_EVIDENCE / "summary.json")

    assert summary["model"] == "gpt-4.1-mini"
    assert summary["temperature"] == 0.7
    assert summary["coverage_target_modes"] == [
        "current_coverage_target",
        "risk_category_hidden",
        "process_state_only",
        "process_state_only_alias_actions",
    ]
    assert summary["conditions"]["current_coverage_target"]["generated_world_count"] == 20
    assert summary["conditions"]["risk_category_hidden"]["detected_defect_ids"] == [
        "D-001",
        "D-002",
        "D-004",
    ]
    assert summary["conditions"]["process_state_only"]["residual_risk_world_count"] == 1
    assert summary["conditions"]["process_state_only_alias_actions"]["generated_world_count"] == 25
    assert summary["conditions"]["process_state_only_alias_actions"]["new_risk_detection_rate"] == 0.3333
    assert summary["conditions"]["process_state_only_alias_actions"]["residual_risk_world_count"] == 8
    assert summary["conditions"]["process_state_only_alias_actions"]["detected_defect_ids"] == ["D-004"]

    for condition_slug in ["current", "hidden", "state_only", "state_alias"]:
        condition_dir = BRANCHING_ALIAS_ACTIONS_EVIDENCE / condition_slug
        manifest = read_json(condition_dir / "evidence_manifest.json")
        assert manifest["missing_files"] == []
        calls_path = condition_dir / "RUN-S002-BRANCHING-BASELINE/branching_calls.jsonl"
        calls_text = calls_path.read_text(encoding="utf-8")
        assert "OPENAI_API_KEY" not in calls_text
        assert "sk-" not in calls_text

    concrete_action_ids = [
        "create_purchase_request",
        "consult_manager",
        "consult_purchasing",
        "postpone_request",
        "informal_preapproval_chat",
    ]
    alias_calls = read_jsonl(
        BRANCHING_ALIAS_ACTIONS_EVIDENCE / "state_alias/RUN-S002-BRANCHING-BASELINE/branching_calls.jsonl"
    )
    assert alias_calls[0]["action_aliasing_enabled"] is True
    assert alias_calls[0]["action_alias_map"]["action_01"] == "create_purchase_request"
    for call in alias_calls:
        prompt_text = "\n".join(message["content"] for message in call["request_messages"])
        raw_response = call["raw_response"]
        for action_id in concrete_action_ids:
            assert action_id not in prompt_text
            assert action_id not in raw_response


def test_committed_branching_alias_stability_evidence_matches_expected_values():
    summary = read_json(BRANCHING_ALIAS_STABILITY_EVIDENCE / "summary.json")
    manifest = read_json(BRANCHING_ALIAS_STABILITY_EVIDENCE / "evidence_manifest.json")

    assert summary["model"] == "gpt-4.1-mini"
    assert summary["coverage_target_mode"] == "process_state_only_alias_actions"
    assert summary["temperatures"] == [0.3, 0.7]
    assert summary["seeds"] == [20260519, 20260520]
    assert summary["stability"]["residual_world_count_by_cell"] == {
        "t0_3_s20260519": 5,
        "t0_3_s20260520": 4,
        "t0_7_s20260519": 7,
        "t0_7_s20260520": 6,
    }
    assert summary["stability"]["detected_defect_ids_by_cell"] == {
        "t0_3_s20260519": ["D-004"],
        "t0_3_s20260520": ["D-004"],
        "t0_7_s20260519": ["D-004"],
        "t0_7_s20260520": ["D-004"],
    }
    assert set(summary["stability"]["stable_themes"]) >= {
        "approval_influence",
        "process_shortcut_seeking",
        "urgency_overstatement",
    }

    assert len(manifest["cells"]) == 4
    for cell in manifest["cells"]:
        assert cell["cell_missing_files"] == []
        assert (BRANCHING_ALIAS_STABILITY_EVIDENCE / cell["alias_residual_review"]).exists()
        assert (BRANCHING_ALIAS_STABILITY_EVIDENCE / cell["alias_residual_review_report"]).exists()


def test_committed_branching_alias_no_description_evidence_hides_action_descriptions():
    summary = read_json(BRANCHING_ALIAS_NO_DESCRIPTION_EVIDENCE / "summary.json")
    manifest = read_json(BRANCHING_ALIAS_NO_DESCRIPTION_EVIDENCE / "evidence_manifest.json")

    assert summary["coverage_target_mode"] == "process_state_only_alias_actions_no_descriptions"
    assert summary["temperatures"] == [0.7]
    assert summary["seeds"] == [20260519]
    assert summary["cells"][0]["residual_review"]["residual_world_count"] == 13
    assert summary["cells"][0]["new_risk_detection_rate"] == 0.2778
    assert manifest["cells"][0]["cell_missing_files"] == []

    calls_path = (
        BRANCHING_ALIAS_NO_DESCRIPTION_EVIDENCE
        / "cells/t0_7_s20260519/RUN-S002-BRANCHING-BASELINE/branching_calls.jsonl"
    )
    concrete_action_ids = [
        "create_purchase_request",
        "consult_manager",
        "consult_purchasing",
        "postpone_request",
        "informal_preapproval_chat",
    ]
    for call in read_jsonl(calls_path):
        prompt_text = "\n".join(message["content"] for message in call["request_messages"])
        payload = json.loads(call["request_messages"][1]["content"])
        assert all("description" not in action for action in payload["allowed_actions"])
        for action_id in concrete_action_ids:
            assert action_id not in prompt_text


def test_run_manifests_use_relative_paths_and_include_provenance_hashes():
    for run_dir in REVIEW_RUNS:
        manifest = read_json(run_dir / "run_manifest.json")

        assert manifest["seed"] == 20260519
        assert re.fullmatch(r"git:[0-9a-f]{40}", manifest["code_version"])
        assert manifest["inputs"]["purchase_needs"] == "data/synthetic/purchase_needs.csv"
        assert manifest["inputs"]["ground_truth_labels"] == "data/synthetic/ground_truth_labels.yaml"
        assert not Path(manifest["inputs"]["run_config"]).is_absolute()
        assert not Path(manifest["inputs"]["purchase_needs"]).is_absolute()

        for digest in manifest["config_hashes"].values():
            assert re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
        for digest in manifest["data_hashes"].values():
            assert re.fullmatch(r"sha256:[0-9a-f]{64}", digest)

        assert manifest["data_hashes"]["purchase_needs"] == _sha256(REPO_ROOT / "data/synthetic/purchase_needs.csv")
        assert manifest["data_hashes"]["ground_truth_labels"] == _sha256(
            REPO_ROOT / "data/synthetic/ground_truth_labels.yaml"
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"
