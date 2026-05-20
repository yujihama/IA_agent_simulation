from __future__ import annotations

from datetime import datetime
from typing import Any

from ia_sim.models import APPROVER_RANK


SPLIT_ORDER_DETECTOR_ID = "split_order_detector"
DEFECT_ID = "D-001"
DEPARTMENT_HEAD_THRESHOLD = 1_000_000
WINDOW_DAYS = 7


def _event_date(event: dict[str, Any]):
    return datetime.fromisoformat(event["timestamp"]).date()


def detect_split_orders(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    create_events = [event for event in events if event["action_id"] == "create_purchase_request"]
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for event in create_events:
        key = (event["actor_user_id"], event["vendor_id"], event["project_id"])
        groups.setdefault(key, []).append(event)

    annotations: list[dict[str, Any]] = []
    annotation_index = 1
    for key, grouped_events in groups.items():
        ordered = sorted(grouped_events, key=lambda event: event["timestamp"])
        if len(ordered) < 2:
            continue
        for start_index in range(len(ordered)):
            window = [ordered[start_index]]
            first_date = _event_date(ordered[start_index])
            for event in ordered[start_index + 1 :]:
                if (_event_date(event) - first_date).days <= WINDOW_DAYS:
                    window.append(event)
            if len(window) < 2:
                continue
            total_amount = sum(int(event["amount"]) for event in window)
            all_below_threshold = all(int(event["amount"]) < DEPARTMENT_HEAD_THRESHOLD for event in window)
            if not all_below_threshold or total_amount < DEPARTMENT_HEAD_THRESHOLD:
                continue
            evidence_event_ids = [event["event_id"] for event in window]
            if any(set(evidence_event_ids) == set(item["evidence_event_ids"]) for item in annotations):
                continue
            mitigated_by_aggregation = any(
                event.get("control_results", {})
                .get("P2P-C-001", {})
                .get("aggregation_applied", False)
                for event in window
            )
            effective_levels = [
                event.get("control_results", {})
                .get("P2P-C-001", {})
                .get("effective_required_approver_level", "manager")
                for event in window
            ]
            bypass_success = not any(
                APPROVER_RANK.get(level, 0) >= APPROVER_RANK["department_head"] for level in effective_levels
            )
            annotations.append(
                {
                    "annotation_id": f"ANN-{annotation_index:06d}",
                    "run_id": window[0]["run_id"],
                    "detector_id": SPLIT_ORDER_DETECTOR_ID,
                    "defect_id": DEFECT_ID,
                    "candidate_group_id": f"D001-{annotation_index:03d}",
                    "severity": "high",
                    "confidence": 0.92 if bypass_success else 0.74,
                    "bypass_success": bypass_success,
                    "mitigated_by_aggregation": mitigated_by_aggregation,
                    "evidence_event_ids": evidence_event_ids,
                    "grouping_key": {
                        "requester_user_id": key[0],
                        "vendor_id": key[1],
                        "project_id": key[2],
                    },
                    "observed_facts": [
                        f"同一申請者・同一取引先・同一プロジェクトに対して、{WINDOW_DAYS}日以内に{len(window)}件の購買申請が作成された。",
                        f"各申請金額はいずれも{DEPARTMENT_HEAD_THRESHOLD}未満である。",
                        f"合算金額は{total_amount}であり、{DEPARTMENT_HEAD_THRESHOLD}を超過している。",
                    ],
                    "inference": (
                        "このイベント列は、承認閾値回避の可能性と整合する。"
                        "これは人間レビュー用の不備候補であり、監査上の結論ではない。"
                    ),
                    "related_controls": ["P2P-C-001", "P2P-C-002", "P2P-C-003"],
                    "proposal_flags_used": False,
                    "detection_basis": "events_only",
                }
            )
            annotation_index += 1
            break
    return annotations


def build_findings(annotations: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events_by_id = {event["event_id"]: event for event in events}
    findings: list[dict[str, Any]] = []
    for index, annotation in enumerate(annotations, start=1):
        evidence = [events_by_id[event_id] for event_id in annotation["evidence_event_ids"]]
        status = "candidate_mitigated" if annotation["mitigated_by_aggregation"] else "candidate_unmitigated"
        findings.append(
            {
                "finding_id": f"FND-{index:06d}",
                "run_id": annotation["run_id"],
                "defect_id": DEFECT_ID,
                "title": "承認閾値回避の可能性がある分割購買申請",
                "severity": annotation["severity"],
                "status": status,
                "detector_id": annotation["detector_id"],
                "related_controls": annotation["related_controls"],
                "evidence_event_ids": annotation["evidence_event_ids"],
                "observed_facts": annotation["observed_facts"],
                "inference": annotation["inference"],
                "bypass_success": annotation["bypass_success"],
                "mitigated_by_aggregation": annotation["mitigated_by_aggregation"],
                "recommended_review_steps": [
                    "複数申請が同一の経済的購買ニーズに対応するか確認する。",
                    "申請理由と承認履歴を確認する。",
                    "申請者・取引先・プロジェクト・期間による合算統制の適用要否を評価する。",
                ],
                "evidence_summary": [
                    {
                        "event_id": event["event_id"],
                        "timestamp": event["timestamp"],
                        "purchase_need_id": event["purchase_need_id"],
                        "purchase_request_id": event["purchase_request_id"],
                        "amount": event["amount"],
                        "required_approver_level": event["metadata"]["required_approver_level"],
                        "aggregation_applied": event["metadata"]["aggregation_applied"],
                    }
                    for event in evidence
                ],
            }
        )
    return findings
