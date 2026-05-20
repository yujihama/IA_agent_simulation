import csv
import hashlib
import re
from pathlib import Path

from ia_sim.storage import read_json, read_jsonl


REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_RUN = REPO_ROOT / "runs/RUN-S002-BASELINE"
VARIANT_RUN = REPO_ROOT / "runs/RUN-S002-VARIANT-A"
LLM_BASELINE_RUN = REPO_ROOT / "runs/RUN-S002-LLM-BASELINE"
LLM_VARIANT_RUN = REPO_ROOT / "runs/RUN-S002-LLM-VARIANT-A"
REVIEW_RUNS = [BASELINE_RUN, VARIANT_RUN, LLM_BASELINE_RUN, LLM_VARIANT_RUN]
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
