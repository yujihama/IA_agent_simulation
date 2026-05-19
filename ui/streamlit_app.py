from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / "runs"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_dirs() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted([path for path in RUNS_DIR.glob("RUN-*") if path.is_dir()])


st.set_page_config(page_title="P2P Control Simulation Review", layout="wide")
st.title("P2P Control Simulation Review")
st.caption("Detector outputs are review candidates, not audit conclusions.")

runs = run_dirs()
if not runs:
    st.info("No run outputs found. Run `python -m ia_sim.cli run-first-slice` first.")
    st.stop()

selected_run = st.selectbox("Run", runs, format_func=lambda path: path.name)
manifest = read_json(selected_run / "run_manifest.json")
metrics = read_json(selected_run / "metrics.json")
findings = read_json(selected_run / "findings.json").get("findings", [])
evaluation_results_path = selected_run / "evaluation_results.json"
evaluation_results = read_json(evaluation_results_path) if evaluation_results_path.exists() else None
annotations = read_jsonl(selected_run / "detector_annotations.jsonl")
events = read_jsonl(selected_run / "events.jsonl")
events_by_id = {event["event_id"]: event for event in events}
review_mode = st.radio("Review mode", ["blind_review", "evaluation"], horizontal=True)

left, right = st.columns(2)
with left:
    st.subheader("Run Summary")
    st.json(
        {
            "run_id": manifest["run_id"],
            "scenario_id": manifest["scenario_id"],
            "variant_id": manifest["variant_id"],
            "behavior_mode": manifest["behavior_mode"],
            "comparison_mode": manifest["comparison_mode"],
            "forbidden_actions_present": manifest["forbidden_actions_present"],
        }
    )
with right:
    st.subheader("Metrics")
    if review_mode == "blind_review":
        st.json(
            {
                "variant_id": metrics["variant_id"],
                "event_count": metrics["event_count"],
                "purchase_need_count": metrics["purchase_need_count"],
                "purchase_request_count": metrics["purchase_request_count"],
                "detector_annotation_count": metrics["detector_annotation_count"],
                "finding_count": metrics["finding_count"],
                "split_order_bypass_success_count": metrics["split_order_bypass_success_count"],
                "split_order_mitigated_candidate_count": metrics["split_order_mitigated_candidate_count"],
                "aggregation_applications": metrics["aggregation_applications"],
            }
        )
    else:
        st.json(metrics)
        if evaluation_results:
            st.markdown("#### Evaluation Results")
            st.json(evaluation_results)

st.subheader("Findings")
if not findings:
    st.write("No findings.")
else:
    finding = st.selectbox("Finding", findings, format_func=lambda item: item["finding_id"])
    st.markdown(f"### {finding['title']}")
    st.write(
        {
            "severity": finding["severity"],
            "status": finding["status"],
            "bypass_success": finding["bypass_success"],
            "mitigated_by_aggregation": finding["mitigated_by_aggregation"],
        }
    )
    st.markdown("#### Observed facts")
    for fact in finding["observed_facts"]:
        st.write(f"- {fact}")
    st.markdown("#### Inference")
    st.write(finding["inference"])
    st.markdown("#### Evidence events")
    st.dataframe([events_by_id[event_id] for event_id in finding["evidence_event_ids"]], use_container_width=True)

st.subheader("Detector Annotations")
st.dataframe(annotations, use_container_width=True)

comparison_report = RUNS_DIR / "comparisons/CMP-S002-BASELINE-VARIANT-A/comparison_report.md"
if comparison_report.exists():
    st.subheader("Baseline / Variant A Comparison")
    st.markdown(comparison_report.read_text(encoding="utf-8"))
