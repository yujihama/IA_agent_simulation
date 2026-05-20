from pathlib import Path

from ia_sim.orchestrator import compare_runs, run_simulation
from ia_sim.storage import read_json, read_jsonl
from ia_sim.synthetic import generate_synthetic_data


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_first_slice_baseline_and_variant_a(tmp_path):
    purchase_needs_path = generate_synthetic_data(tmp_path / "data", count=100)

    baseline = run_simulation(
        REPO_ROOT,
        REPO_ROOT / "configs/run_configs/baseline.yaml",
        output_root_override=tmp_path / "runs",
        purchase_needs_path_override=purchase_needs_path,
    )
    variant = run_simulation(
        REPO_ROOT,
        REPO_ROOT / "configs/run_configs/variant_a.yaml",
        output_root_override=tmp_path / "runs",
        purchase_needs_path_override=purchase_needs_path,
    )
    comparison = compare_runs(baseline.run_dir, variant.run_dir, tmp_path / "runs/comparisons/cmp")

    baseline_metrics = read_json(baseline.metrics_path)
    variant_metrics = read_json(variant.metrics_path)
    baseline_annotations = read_jsonl(baseline.annotations_path)
    variant_annotations = read_jsonl(variant.annotations_path)
    baseline_replay = read_jsonl(baseline.behavior_replay_path)
    baseline_findings = read_json(baseline.findings_path)["findings"]
    baseline_evaluation = read_json(baseline.run_dir / "evaluation_results.json")

    assert baseline_metrics["purchase_request_count"] == 101
    assert baseline_metrics["purchase_need_count"] == 100
    assert baseline_metrics["true_positive"] == 1
    assert baseline_metrics["split_order_bypass_success_count"] == 1
    assert variant_metrics["true_positive"] == 1
    assert variant_metrics["split_order_bypass_success_count"] == 0
    assert variant_metrics["aggregation_applications"] == 1
    assert comparison["risk_reduction_ratio"] == 1.0

    assert baseline_annotations[0]["proposal_flags_used"] is False
    assert "evaluation_group_id" not in baseline_annotations[0]
    assert variant_annotations[0]["mitigated_by_aggregation"] is True
    assert "evaluation_result" not in baseline_findings[0]
    assert "evaluation_group_id" not in baseline_findings[0]
    assert baseline_evaluation["summary"]["true_positive"] == 1
    assert all(row["selected_action_id"] != "submit_split_requests" for row in baseline_replay)


def test_detector_evidence_points_to_multiple_create_purchase_request_events(tmp_path):
    purchase_needs_path = generate_synthetic_data(tmp_path / "data", count=100)
    baseline = run_simulation(
        REPO_ROOT,
        REPO_ROOT / "configs/run_configs/baseline.yaml",
        output_root_override=tmp_path / "runs",
        purchase_needs_path_override=purchase_needs_path,
    )

    events = {event["event_id"]: event for event in read_jsonl(baseline.events_path)}
    annotations = read_jsonl(baseline.annotations_path)
    assert len(annotations) == 1

    evidence_events = [events[event_id] for event_id in annotations[0]["evidence_event_ids"]]
    assert [event["action_id"] for event in evidence_events] == [
        "create_purchase_request",
        "create_purchase_request",
    ]
    assert {event["purchase_need_id"] for event in evidence_events} == {"NEED-001"}
    assert sum(event["amount"] for event in evidence_events) == 1_750_000
    assert all("evaluation_group_id" not in event["metadata"] for event in events.values())
    assert all("behavior_pattern" not in event["metadata"] for event in events.values())
