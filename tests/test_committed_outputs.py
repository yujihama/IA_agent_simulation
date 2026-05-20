import csv
import hashlib
import re
from pathlib import Path

from ia_sim.storage import read_json, read_jsonl


REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_RUN = REPO_ROOT / "runs/RUN-S002-BASELINE"
VARIANT_RUN = REPO_ROOT / "runs/RUN-S002-VARIANT-A"
FORBIDDEN_REVIEW_KEYS = {"evaluation_group_id", "behavior_pattern", "seeded_deficiency_id", "evaluation_result"}


def test_committed_purchase_need_fixture_has_no_ground_truth_or_generation_intent():
    with (REPO_ROOT / "data/synthetic/purchase_needs.csv").open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert FORBIDDEN_REVIEW_KEYS.isdisjoint(reader.fieldnames or [])
        rows = list(reader)

    assert len(rows) == 100
    assert rows[0]["purchase_need_id"] == "NEED-001"


def test_committed_review_outputs_do_not_expose_evaluation_labels():
    for run_dir in [BASELINE_RUN, VARIANT_RUN]:
        for event in read_jsonl(run_dir / "events.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event)
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(event.get("metadata", {}))

        for annotation in read_jsonl(run_dir / "detector_annotations.jsonl"):
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(annotation)

        findings = read_json(run_dir / "findings.json")["findings"]
        for finding in findings:
            assert FORBIDDEN_REVIEW_KEYS.isdisjoint(finding)


def test_evaluation_result_is_isolated_to_evaluation_results_file():
    for run_dir in [BASELINE_RUN, VARIANT_RUN]:
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


def test_run_manifests_use_relative_paths_and_include_provenance_hashes():
    for run_dir in [BASELINE_RUN, VARIANT_RUN]:
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
