from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / "runs"

MODE_OPTIONS = {
    "\u30d6\u30e9\u30a4\u30f3\u30c9\u30ec\u30d3\u30e5\u30fc": "blind_review",
    "\u8a55\u4fa1\u7d50\u679c": "evaluation",
}

METRIC_LABELS = {
    "variant_id": "Variant",
    "event_count": "\u30a4\u30d9\u30f3\u30c8\u4ef6\u6570",
    "purchase_need_count": "\u8cfc\u8cb7\u30cb\u30fc\u30ba\u4ef6\u6570",
    "purchase_request_count": "\u8cfc\u8cb7\u7533\u8acb\u4ef6\u6570",
    "detector_annotation_count": "Detector Annotation\u4ef6\u6570",
    "finding_count": "\u4e0d\u5099\u5019\u88dc\u4ef6\u6570",
    "split_order_bypass_success_count": "\u672a\u7de9\u548c\u3059\u308a\u629c\u3051\u5019\u88dc\u4ef6\u6570",
    "split_order_mitigated_candidate_count": "\u7d71\u5236\u306b\u3088\u308a\u7de9\u548c\u3055\u308c\u305f\u5019\u88dc\u4ef6\u6570",
    "aggregation_applications": "\u5408\u7b97\u5224\u5b9a\u9069\u7528\u4ef6\u6570",
    "true_positive": "\u771f\u967d\u6027",
    "false_positive": "\u507d\u967d\u6027",
    "false_negative": "\u507d\u9670\u6027",
    "precision": "\u9069\u5408\u7387",
    "recall": "\u518d\u73fe\u7387",
    "approval_event_count": "\u627f\u8a8d\u30a4\u30d9\u30f3\u30c8\u4ef6\u6570",
    "department_head_approval_count": "\u90e8\u9580\u9577\u627f\u8a8d\u4ef6\u6570",
    "total_approval_lead_time_days": "\u627f\u8a8d\u30ea\u30fc\u30c9\u30bf\u30a4\u30e0\u5408\u8a08\uff08\u65e5\uff09",
}

ACTION_METRIC_LABELS = {
    "selected_action_distribution": "\u9078\u629eAction\u5206\u5e03",
    "amount_selection_distribution": "\u91d1\u984d\u9078\u629e\u5206\u5e03",
    "partial_request_rate": "\u90e8\u5206\u7533\u8acb\u7387",
    "consult_rate": "\u76f8\u8ac7\u7387",
    "postpone_rate": "\u5ef6\u671f\u7387",
    "invalid_action_rate": "\u7121\u52b9Action\u7387",
    "retry_rate": "Retry\u7387",
    "fallback_rate": "Fallback\u7387",
    "split_order_candidate_count": "\u5206\u5272\u8cfc\u8cb7\u5019\u88dc\u4ef6\u6570",
    "bypass_success_count": "\u672a\u7de9\u548c\u5019\u88dc\u4ef6\u6570",
    "aggregation_mitigation_count": "\u5408\u7b97\u7de9\u548c\u4ef6\u6570",
    "control_awareness": "\u7d71\u5236\u8a8d\u8b58",
    "reason_groundedness": "\u7406\u7531\u306e\u6839\u62e0\u6027",
    "fact_in_reason_error_rate": "\u7406\u7531\u5185\u306e\u4e8b\u5b9f\u8aa4\u308a\u7387",
    "human_plausibility_score": "\u4eba\u9593\u30ec\u30d3\u30e5\u30fc\u4e0a\u306e\u59a5\u5f53\u6027",
    "mapped_to_action_rate": "Action Grounding\u6210\u529f\u7387",
    "unsupported_action_proposal_count": "\u672a\u5bfe\u5fdcAction\u63d0\u6848\u6570",
    "emergency_proposal_rate": "\u7dca\u6025\u30fb\u4f8b\u5916\u63d0\u6848\u7387",
    "compliance_concern_coverage": "\u7d71\u5236\u61f8\u5ff5\u8a18\u8f09\u7387",
    "human_useful_hypothesis_rate": "\u4eba\u9593\u30ec\u30d3\u30e5\u30fc\u6709\u7528\u4eee\u8aac\u7387",
    "detector_candidate_generation_rate": "Detector\u5019\u88dc\u751f\u6210\u7387",
}

STATUS_LABELS = {
    "candidate_unmitigated": "\u5019\u88dc\uff08\u672a\u7de9\u548c\uff09",
    "candidate_mitigated": "\u5019\u88dc\uff08\u7d71\u5236\u306b\u3088\u308a\u7de9\u548c\uff09",
}


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


def label_dict(values: dict) -> dict:
    labels = {**METRIC_LABELS, **ACTION_METRIC_LABELS}
    return {labels.get(key, key): localize_value(key, value) for key, value in values.items()}


def localize_value(key: str, value):
    if isinstance(value, bool):
        return "\u306f\u3044" if value else "\u3044\u3044\u3048"
    if key == "status":
        return STATUS_LABELS.get(value, value)
    return value


st.set_page_config(page_title="P2P\u7d71\u5236\u30b7\u30df\u30e5\u30ec\u30fc\u30b7\u30e7\u30f3\u30ec\u30d3\u30e5\u30fc", layout="wide")
st.title("P2P\u7d71\u5236\u30b7\u30df\u30e5\u30ec\u30fc\u30b7\u30e7\u30f3\u30ec\u30d3\u30e5\u30fc")
st.caption("Detector\u306e\u51fa\u529b\u306f\u4eba\u9593\u30ec\u30d3\u30e5\u30fc\u7528\u306e\u4e0d\u5099\u5019\u88dc\u3067\u3042\u308a\u3001\u76e3\u67fb\u4e0a\u306e\u7d50\u8ad6\u3067\u306f\u3042\u308a\u307e\u305b\u3093\u3002")

runs = run_dirs()
if not runs:
    st.info("Run\u51fa\u529b\u304c\u898b\u3064\u304b\u308a\u307e\u305b\u3093\u3002`python -m ia_sim.cli run-first-slice` \u307e\u305f\u306f `python -m ia_sim.cli run-llm-slice` \u3092\u5b9f\u884c\u3057\u3066\u304f\u3060\u3055\u3044\u3002")
    st.stop()

selected_run = st.selectbox("Run\u9078\u629e", runs, format_func=lambda path: path.name)
manifest = read_json(selected_run / "run_manifest.json")
metrics = read_json(selected_run / "metrics.json")
findings = read_json(selected_run / "findings.json").get("findings", [])
events = read_jsonl(selected_run / "events.jsonl")
annotations = read_jsonl(selected_run / "detector_annotations.jsonl")
events_by_id = {event["event_id"]: event for event in events}
evaluation_results_path = selected_run / "evaluation_results.json"
evaluation_results = read_json(evaluation_results_path) if evaluation_results_path.exists() else None
action_metrics_path = selected_run / "action_selection_metrics.json"
action_metrics = read_json(action_metrics_path) if action_metrics_path.exists() else None
llm_decisions = read_jsonl(selected_run / "llm_action_decisions.jsonl")
llm_calls = read_jsonl(selected_run / "llm_calls.jsonl") or read_jsonl(selected_run / "open_proposal_calls.jsonl")
open_proposals = read_jsonl(selected_run / "open_proposals.jsonl")
action_grounding = read_jsonl(selected_run / "action_grounding.jsonl")

review_mode = MODE_OPTIONS[st.radio("\u30ec\u30d3\u30e5\u30fc\u7a2e\u5225", list(MODE_OPTIONS), horizontal=True)]

left, right = st.columns(2)
with left:
    st.subheader("Run\u6982\u8981")
    st.json(
        {
            "Run ID": manifest["run_id"],
            "Scenario": manifest["scenario_id"],
            "Variant": manifest["variant_id"],
            "Seed": manifest.get("seed"),
            "\u884c\u52d5\u30e2\u30fc\u30c9": manifest["behavior_mode"],
            "\u6bd4\u8f03\u30e2\u30fc\u30c9": manifest["comparison_mode"],
            "LLM": manifest.get("llm"),
            "\u7981\u6b62Action\u691c\u51fa": manifest["forbidden_actions_present"],
        }
    )
with right:
    st.subheader("\u6307\u6a19")
    blind_keys = [
        "variant_id",
        "event_count",
        "purchase_need_count",
        "purchase_request_count",
        "detector_annotation_count",
        "finding_count",
        "split_order_bypass_success_count",
        "split_order_mitigated_candidate_count",
        "aggregation_applications",
    ]
    st.json(label_dict({key: metrics[key] for key in blind_keys if key in metrics} if review_mode == "blind_review" else metrics))
    if review_mode == "evaluation" and evaluation_results:
        st.markdown("#### \u8a55\u4fa1\u7d50\u679c")
        st.json(evaluation_results)

if action_metrics:
    st.subheader("LLM\u884c\u52d5\u9078\u629e")
    st.json(label_dict(action_metrics))
    if llm_decisions:
        st.markdown("#### \u9078\u629eAction")
        st.dataframe(
            [
                {
                    "Decision": row["decision_id"],
                    "PurchaseNeed": row["purchase_need_id"],
                    "Action": row["selected_action_id"],
                    "Source": row["source"],
                    "Retry": row["retry_count"],
                    "Fallback": "\u306f\u3044" if row["fallback_used"] else "\u3044\u3044\u3048",
                    "\u7406\u7531": row["reason"],
                    "\u7d71\u5236\u8a8d\u8b58": row["control_awareness"],
                    "Parameters": row["parameters"],
                }
                for row in llm_decisions
            ],
            use_container_width=True,
        )
    if review_mode == "evaluation" and llm_calls:
        st.markdown("#### LLM Call / Validation")
        st.dataframe(
            [
                {
                    "PurchaseNeed": row["purchase_need_id"],
                    "Attempt": row["attempt"],
                    "Model": row["model"],
                    "Status": row["validation_status"],
                    "Retry": "\u306f\u3044" if row["retry_scheduled"] else "\u3044\u3044\u3048",
                    "Errors": row["validation_errors"],
                }
                for row in llm_calls
            ],
            use_container_width=True,
        )
    if open_proposals:
        st.markdown("#### Open Proposal")
        st.dataframe(open_proposals, use_container_width=True)
    if action_grounding:
        st.markdown("#### Action Grounding")
        st.dataframe(action_grounding, use_container_width=True)

st.subheader("\u4e0d\u5099\u5019\u88dc")
if not findings:
    st.write("\u4e0d\u5099\u5019\u88dc\u306f\u3042\u308a\u307e\u305b\u3093\u3002")
else:
    finding = st.selectbox("\u4e0d\u5099\u5019\u88dc", findings, format_func=lambda item: item["finding_id"])
    st.markdown(f"### {finding['title']}")
    st.json(
        {
            "\u91cd\u8981\u5ea6": finding["severity"],
            "\u30b9\u30c6\u30fc\u30bf\u30b9": STATUS_LABELS.get(finding["status"], finding["status"]),
            "\u672a\u7de9\u548c\u3059\u308a\u629c\u3051": "\u306f\u3044" if finding["bypass_success"] else "\u3044\u3044\u3048",
            "\u5408\u7b97\u7d71\u5236\u306b\u3088\u308a\u7de9\u548c": "\u306f\u3044" if finding["mitigated_by_aggregation"] else "\u3044\u3044\u3048",
        }
    )
    st.markdown("#### \u89b3\u5bdf\u4e8b\u5b9f")
    for fact in finding["observed_facts"]:
        st.write(f"- {fact}")
    st.markdown("#### \u63a8\u8ad6")
    st.write(finding["inference"])
    st.markdown("#### \u63a8\u5968\u30ec\u30d3\u30e5\u30fc\u624b\u9806")
    for step in finding["recommended_review_steps"]:
        st.write(f"- {step}")
    st.markdown("#### \u6839\u62e0\u30a4\u30d9\u30f3\u30c8")
    st.dataframe([events_by_id[event_id] for event_id in finding["evidence_event_ids"]], use_container_width=True)

st.subheader("Detector Annotation")
st.dataframe(annotations, use_container_width=True)

for comparison_report in [
    RUNS_DIR / "comparisons/CMP-S002-BASELINE-VARIANT-A/comparison_report.md",
    RUNS_DIR / "comparisons/CMP-S002-LLM-BASELINE-VARIANT-A/comparison_report.md",
]:
    if comparison_report.exists():
        st.subheader(comparison_report.parent.name)
        st.markdown(comparison_report.read_text(encoding="utf-8"))

experiment_reports = []
if (RUNS_DIR / "experiments").exists():
    for pattern in [
        "*/pressure_effect_report.md",
        "*/prompt_ablation_report.md",
        "*/hint_pressure_matrix_report.md",
        "*/agent_stress_report.md",
    ]:
        experiment_reports.extend((RUNS_DIR / "experiments").glob(pattern))
experiment_reports = sorted(experiment_reports)
if experiment_reports:
    st.subheader("\u5727\u529b\u6761\u4ef6\u30fb\u30d7\u30ed\u30f3\u30d7\u30c8\u6bd4\u8f03\u5b9f\u9a13")
    selected_experiment_report = st.selectbox(
        "\u5b9f\u9a13\u30ec\u30dd\u30fc\u30c8",
        experiment_reports,
        format_func=lambda path: f"{path.parent.name} / {path.name}",
    )
    st.markdown(selected_experiment_report.read_text(encoding="utf-8"))
