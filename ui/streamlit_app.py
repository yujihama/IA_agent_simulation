from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / "runs"

MODE_OPTIONS = {
    "ブラインドレビュー": "blind_review",
    "評価結果": "evaluation",
}
SEVERITY_LABELS = {"high": "高", "medium": "中", "low": "低"}
STATUS_LABELS = {
    "candidate_unmitigated": "候補（未緩和）",
    "candidate_mitigated": "候補（統制により緩和）",
}
LEVEL_LABELS = {
    "manager": "課長",
    "department_head": "部門長",
    "division_head": "本部長",
}
RESULT_LABELS = {
    "true_positive": "真陽性",
    "false_positive": "偽陽性",
    "false_negative": "偽陰性",
}
METRIC_LABELS = {
    "variant_id": "Variant",
    "event_count": "イベント件数",
    "purchase_need_count": "購買ニーズ件数",
    "purchase_request_count": "購買申請件数",
    "detector_annotation_count": "Detector Annotation件数",
    "finding_count": "不備候補件数",
    "split_order_bypass_success_count": "分割購買による未緩和すり抜け件数",
    "split_order_mitigated_candidate_count": "合算統制で緩和された候補件数",
    "aggregation_applications": "合算判定適用件数",
    "true_positive": "真陽性",
    "false_positive": "偽陽性",
    "false_negative": "偽陰性",
    "precision": "適合率",
    "recall": "再現率",
    "high_recall": "High重要度再現率",
    "approval_event_count": "承認イベント件数",
    "department_head_approval_count": "部門長承認件数",
    "division_head_approval_count": "本部長承認件数",
    "total_approval_lead_time_days": "承認リードタイム合計（日）",
    "average_approval_lead_time_days": "平均承認リードタイム（日）",
    "proposal_flags_excluded_from_detector_metrics": "Proposal FlagをDetector指標から除外",
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
    return {METRIC_LABELS.get(key, key): localize_value(key, value) for key, value in values.items()}


def localize_value(key: str, value):
    if isinstance(value, bool):
        return "はい" if value else "いいえ"
    if key in {"severity"}:
        return SEVERITY_LABELS.get(value, value)
    if key in {"status"}:
        return STATUS_LABELS.get(value, value)
    if key in {"required_approver_level", "individual_required_approver_level", "aggregate_required_approver_level"}:
        return LEVEL_LABELS.get(value, value)
    if key == "evaluation_result":
        return RESULT_LABELS.get(value, value)
    return value


def localized_evaluation_results(value: dict) -> dict:
    return {
        "モード": "評価専用",
        "Ground Truthをレビュー画面に表示": "はい" if value.get("ground_truth_visible_to_review") else "いいえ",
        "照合キー": value.get("matching_basis"),
        "サマリ": label_dict(value.get("summary", {})),
        "Finding別評価": [
            {
                "Finding ID": item["finding_id"],
                "Detector": item["detector_id"],
                "不備ID": item["defect_id"],
                "評価結果": item.get("result_label", RESULT_LABELS.get(item["evaluation_result"], item["evaluation_result"])),
                "照合Ground Truth": item.get("matched_evaluation_group_id"),
                "根拠PurchaseNeed": ", ".join(item.get("evidence_purchase_need_ids", [])),
            }
            for item in value.get("finding_results", [])
        ],
        "未検出Ground Truth": value.get("false_negative_labels", []),
    }


def localized_events(event_ids: list[str], events_by_id: dict[str, dict]) -> list[dict]:
    rows = []
    for event_id in event_ids:
        event = events_by_id[event_id]
        rows.append(
            {
                "イベントID": event["event_id"],
                "日時": event["timestamp"],
                "Action": event["action_id"],
                "PurchaseNeed": event["purchase_need_id"],
                "PurchaseRequest": event["purchase_request_id"],
                "申請者/実行者": event["actor_user_id"],
                "役割": event["actor_role"],
                "金額": event["amount"],
                "取引先": event["vendor_id"],
                "プロジェクト": event["project_id"],
                "状態Before": event["state_before"],
                "状態After": event["state_after"],
            }
        )
    return rows


st.set_page_config(page_title="P2P統制シミュレーションレビュー", layout="wide")
st.title("P2P統制シミュレーションレビュー")
st.caption("Detectorの出力は人間レビュー用の不備候補であり、監査上の結論ではありません。")

runs = run_dirs()
if not runs:
    st.info("Run出力が見つかりません。先に `python -m ia_sim.cli run-first-slice` を実行してください。")
    st.stop()

selected_run = st.selectbox("Run選択", runs, format_func=lambda path: path.name)
manifest = read_json(selected_run / "run_manifest.json")
metrics = read_json(selected_run / "metrics.json")
findings = read_json(selected_run / "findings.json").get("findings", [])
evaluation_results_path = selected_run / "evaluation_results.json"
evaluation_results = read_json(evaluation_results_path) if evaluation_results_path.exists() else None
annotations = read_jsonl(selected_run / "detector_annotations.jsonl")
events = read_jsonl(selected_run / "events.jsonl")
events_by_id = {event["event_id"]: event for event in events}
selected_mode_label = st.radio("レビュー種別", list(MODE_OPTIONS), horizontal=True)
review_mode = MODE_OPTIONS[selected_mode_label]

left, right = st.columns(2)
with left:
    st.subheader("Run概要")
    st.json(
        {
            "Run ID": manifest["run_id"],
            "Scenario": manifest["scenario_id"],
            "Variant": manifest["variant_id"],
            "Seed": manifest.get("seed"),
            "行動モード": manifest["behavior_mode"],
            "比較モード": manifest["comparison_mode"],
            "禁止Action検出": manifest["forbidden_actions_present"],
            "コードバージョン": manifest.get("code_version"),
        }
    )
with right:
    st.subheader("指標")
    if review_mode == "blind_review":
        st.json(label_dict(
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
        ))
    else:
        st.json(label_dict(metrics))
        if evaluation_results:
            st.markdown("#### 評価結果")
            st.json(localized_evaluation_results(evaluation_results))

st.subheader("不備候補")
if not findings:
    st.write("不備候補はありません。")
else:
    finding = st.selectbox("不備候補", findings, format_func=lambda item: item["finding_id"])
    st.markdown(f"### {finding['title']}")
    st.json(
        {
            "重要度": SEVERITY_LABELS.get(finding["severity"], finding["severity"]),
            "ステータス": STATUS_LABELS.get(finding["status"], finding["status"]),
            "未緩和すり抜け": "はい" if finding["bypass_success"] else "いいえ",
            "合算統制により緩和": "はい" if finding["mitigated_by_aggregation"] else "いいえ",
        }
    )
    st.markdown("#### 観察事実")
    for fact in finding["observed_facts"]:
        st.write(f"- {fact}")
    st.markdown("#### 推論")
    st.write(finding["inference"])
    st.markdown("#### 推奨レビュー手順")
    for step in finding["recommended_review_steps"]:
        st.write(f"- {step}")
    st.markdown("#### 根拠イベント")
    st.dataframe(localized_events(finding["evidence_event_ids"], events_by_id), use_container_width=True)

st.subheader("Detector Annotation")
st.dataframe(annotations, use_container_width=True)

comparison_report = RUNS_DIR / "comparisons/CMP-S002-BASELINE-VARIANT-A/comparison_report.md"
if comparison_report.exists():
    st.subheader("Baseline / Variant A 比較")
    st.markdown(comparison_report.read_text(encoding="utf-8"))
