from __future__ import annotations

from datetime import datetime
from typing import Any

from ia_sim.models import APPROVER_RANK


SPLIT_ORDER_DETECTOR_ID = "split_order_detector"
AMOUNT_MISMATCH_DETECTOR_ID = "amount_mismatch_detector"
EMERGENCY_ROUTE_DETECTOR_ID = "emergency_route_detector"
INFORMAL_PREAPPROVAL_DETECTOR_ID = "informal_preapproval_detector"
FAST_TRACK_ROUTE_DETECTOR_ID = "fast_track_route_attempt_detector"
DEFECT_ID = "D-001"
UNDERREPORTED_AMOUNT_DEFECT_ID = "D-003"
EMERGENCY_ROUTE_DEFECT_ID = "D-002"
INFORMAL_PREAPPROVAL_DEFECT_ID = "D-004"
FAST_TRACK_ROUTE_DEFECT_ID = "D-CAND-FAST-TRACK"
DEPARTMENT_HEAD_THRESHOLD = 1_000_000
WINDOW_DAYS = 7


def _event_date(event: dict[str, Any]):
    return datetime.fromisoformat(event["timestamp"]).date()


def detect_split_orders(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    create_events = [event for event in events if event["action_id"] == "create_purchase_request"]
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for event in create_events:
        key = (event.get("world_id", ""), event["actor_user_id"], event["vendor_id"], event["project_id"])
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
                    "world_id": key[0],
                    "detector_id": SPLIT_ORDER_DETECTOR_ID,
                    "defect_id": DEFECT_ID,
                    "candidate_group_id": f"D001-{annotation_index:03d}",
                    "severity": "high",
                    "confidence": 0.92 if bypass_success else 0.74,
                    "bypass_success": bypass_success,
                    "mitigated_by_aggregation": mitigated_by_aggregation,
                    "evidence_event_ids": evidence_event_ids,
                    "grouping_key": {
                        "world_id": key[0],
                        "requester_user_id": key[1],
                        "vendor_id": key[2],
                        "project_id": key[3],
                    },
                    "observed_facts": [
                        f"\u540c\u4e00\u6761\u4ef6\u3067{WINDOW_DAYS}\u65e5\u4ee5\u5185\u306b{len(window)}\u4ef6\u306e\u8cfc\u8cb7\u7533\u8acb\u304c\u4f5c\u6210\u3055\u308c\u305f\u3002",
                        f"\u5404\u7533\u8acb\u91d1\u984d\u306f{DEPARTMENT_HEAD_THRESHOLD}\u672a\u6e80\u3067\u3042\u308b\u3002",
                        f"\u5408\u7b97\u91d1\u984d\u306f{total_amount}\u3067\u3042\u308a\u3001{DEPARTMENT_HEAD_THRESHOLD}\u3092\u8d85\u3048\u3066\u3044\u308b\u3002",
                    ],
                    "inference": (
                        "\u627f\u8a8d\u95be\u5024\u56de\u907f\u306e\u53ef\u80fd\u6027\u3068\u6574\u5408\u3059\u308b\u3002"
                        "\u3053\u308c\u306f\u4eba\u9593\u30ec\u30d3\u30e5\u30fc\u7528\u306e\u4e0d\u5099\u5019\u88dc\u3067\u3042\u308a\u3001"
                        "\u76e3\u67fb\u4e0a\u306e\u7d50\u8ad6\u3067\u306f\u306a\u3044\u3002"
                    ),
                    "related_controls": ["P2P-C-001", "P2P-C-002", "P2P-C-003"],
                    "proposal_flags_used": False,
                    "detection_basis": "events_only",
                }
            )
            annotation_index += 1
            break
    return annotations


def detect_amount_mismatches(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotations: list[dict[str, Any]] = []
    index = 1
    for event in events:
        if event["action_id"] != "create_purchase_request":
            continue
        metadata = event.get("metadata", {})
        reported_amount = int(metadata.get("reported_amount", event.get("amount", 0)))
        economic_amount = int(metadata.get("economic_amount", reported_amount))
        if reported_amount >= economic_amount:
            continue
        annotations.append(
            {
                "annotation_id": f"ANN-AMT-{index:06d}",
                "run_id": event["run_id"],
                "world_id": event.get("world_id", ""),
                "detector_id": AMOUNT_MISMATCH_DETECTOR_ID,
                "defect_id": UNDERREPORTED_AMOUNT_DEFECT_ID,
                "candidate_group_id": f"D003-{index:03d}",
                "severity": "high",
                "confidence": 0.88,
                "bypass_success": True,
                "mitigated_by_aggregation": False,
                "evidence_event_ids": [event["event_id"]],
                "reported_amount": reported_amount,
                "economic_amount": economic_amount,
                "policy_violation_flags": metadata.get("policy_violation_flags", []),
                "integrity_flags": metadata.get("integrity_flags", []),
                "observed_facts": [
                    f"申請金額は{reported_amount}だが、実質金額は{economic_amount}として記録されている。",
                    "承認ルールは申請金額を入力として評価されている。",
                ],
                "inference": (
                    "申請金額と実質金額の不整合により、承認閾値判定が低い金額で実行された可能性がある。"
                    "これは人間レビュー用の不備候補であり、監査上の結論ではない。"
                ),
                "related_controls": ["P2P-C-001"],
                "proposal_flags_used": True,
                "detection_basis": "event_metadata",
            }
        )
        index += 1
    return annotations


def detect_emergency_route_usage(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotations: list[dict[str, Any]] = []
    index = 1
    for event in events:
        if event["action_id"] != "create_purchase_request" or event.get("route_type") != "emergency":
            continue
        emergency_control = event.get("control_results", {}).get("P2P-C-003", {})
        mitigated_by_emergency_control = bool(
            emergency_control.get("emergency_route_reason_required")
            and emergency_control.get("emergency_route_reason_present")
            and emergency_control.get("post_approval_required")
            and int(emergency_control.get("post_approval_hours") or 9999) <= 48
        )
        annotations.append(
            {
                "annotation_id": f"ANN-EMG-{index:06d}",
                "run_id": event["run_id"],
                "world_id": event.get("world_id", ""),
                "detector_id": EMERGENCY_ROUTE_DETECTOR_ID,
                "defect_id": EMERGENCY_ROUTE_DEFECT_ID,
                "candidate_group_id": f"D002-{index:03d}",
                "severity": "medium",
                "confidence": 0.72,
                "bypass_success": False,
                "mitigated_by_aggregation": False,
                "mitigated_by_variant": mitigated_by_emergency_control,
                "mitigated_by_emergency_control": mitigated_by_emergency_control,
                "evidence_event_ids": [event["event_id"]],
                "observed_facts": [
                    "購買申請が緊急ルートで作成された。",
                    "事前承認統制は緊急ルート例外として扱われている。",
                ],
                "inference": (
                    "緊急ルート利用は、理由証跡と事後承認が十分かを人間レビューで確認する候補である。"
                    "これは監査上の結論ではない。"
                ),
                "related_controls": ["P2P-C-003"],
                "proposal_flags_used": True,
                "detection_basis": "event_route_type",
            }
        )
        index += 1
    return annotations


def detect_informal_preapprovals(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotations: list[dict[str, Any]] = []
    index = 1
    for event in events:
        if event["action_id"] != "informal_preapproval_chat":
            continue
        metadata = event.get("metadata", {})
        annotations.append(
            {
                "annotation_id": f"ANN-INF-{index:06d}",
                "run_id": event["run_id"],
                "world_id": event.get("world_id", ""),
                "detector_id": INFORMAL_PREAPPROVAL_DETECTOR_ID,
                "defect_id": INFORMAL_PREAPPROVAL_DEFECT_ID,
                "candidate_group_id": f"D004-{index:03d}",
                "severity": "medium",
                "confidence": 0.68,
                "bypass_success": False,
                "mitigated_by_aggregation": False,
                "evidence_event_ids": [event["event_id"]],
                "channel": metadata.get("channel", ""),
                "counterpart_role": metadata.get("counterpart_role", ""),
                "observed_facts": [
                    "正式な購買申請前に、システム外の非公式事前相談が記録された。",
                    "このイベントは通常の承認ワークフロー上の承認証跡ではない。",
                ],
                "inference": (
                    "非公式事前承認は正式統制を形骸化させる可能性がある。"
                    "承認コメント、チャット証跡、ヒアリング手続で追加確認すべきレビュー候補である。"
                ),
                "related_controls": ["P2P-C-001", "P2P-C-003"],
                "proposal_flags_used": True,
                "detection_basis": "branching_action_event",
            }
        )
        index += 1
    return annotations


def detect_fast_track_route_attempts(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotations: list[dict[str, Any]] = []
    index = 1
    markers = ("fast-track", "fast track", "fast_track", "shortcut route", "fast-track routing")
    for event in events:
        if event["action_id"] != "create_purchase_request":
            continue
        metadata = event.get("metadata", {})
        requested_route_type = str(metadata.get("requested_route_type", event.get("route_type", ""))).lower()
        branch_reason = str(event.get("branch_reason", "")).lower()
        policy_flags = " ".join(str(flag).lower() for flag in metadata.get("policy_violation_flags", []))
        route_text = " ".join([requested_route_type, branch_reason, policy_flags])
        if not any(marker in route_text for marker in markers):
            continue
        if event.get("route_type") == "emergency":
            continue
        annotations.append(
            {
                "annotation_id": f"ANN-FTR-{index:06d}",
                "run_id": event["run_id"],
                "world_id": event.get("world_id", ""),
                "detector_id": FAST_TRACK_ROUTE_DETECTOR_ID,
                "defect_id": FAST_TRACK_ROUTE_DEFECT_ID,
                "candidate_group_id": f"DCAND-FAST-TRACK-{index:03d}",
                "severity": "medium",
                "confidence": 0.64,
                "bypass_success": False,
                "mitigated_by_aggregation": False,
                "evidence_event_ids": [event["event_id"]],
                "requested_route_type": requested_route_type,
                "observed_facts": [
                    "A purchase request event refers to a requester-specified fast-track or shortcut route.",
                    "The executable route was not a modeled emergency route, so the current route controls do not evaluate this as D-002.",
                ],
                "inference": (
                    "This is a detector/library design candidate: the process model can execute the request, "
                    "but the requested fast-track route is not represented as a first-class controlled route."
                ),
                "related_controls": ["P2P-C-001", "P2P-C-003"],
                "proposal_flags_used": True,
                "detection_basis": "event_metadata_and_branch_reason",
            }
        )
        index += 1
    return annotations


def detect_control_findings(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotations = detect_split_orders(events)
    annotations.extend(detect_amount_mismatches(events))
    annotations.extend(detect_emergency_route_usage(events))
    annotations.extend(detect_informal_preapprovals(events))
    annotations.extend(detect_fast_track_route_attempts(events))
    return annotations


def build_findings(annotations: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events_by_id = {event["event_id"]: event for event in events}
    findings: list[dict[str, Any]] = []
    for index, annotation in enumerate(annotations, start=1):
        evidence = [events_by_id[event_id] for event_id in annotation["evidence_event_ids"]]
        mitigated_by_variant = bool(annotation.get("mitigated_by_variant", False))
        status = (
            "candidate_mitigated"
            if annotation["mitigated_by_aggregation"] or mitigated_by_variant
            else "candidate_unmitigated"
        )
        defect_id = annotation.get("defect_id", DEFECT_ID)
        if defect_id == UNDERREPORTED_AMOUNT_DEFECT_ID:
            title = "申請金額と実質金額の不整合候補"
            recommended_review_steps = [
                "申請金額、契約金額、請求金額、発注金額の差分を確認する。",
                "実質金額が承認閾値判定に利用可能なログとして残っているか確認する。",
                "過少申請フラグの根拠を人間レビューで確認する。",
            ]
        elif defect_id == EMERGENCY_ROUTE_DEFECT_ID:
            title = "緊急購買ルート利用のレビュー候補"
            recommended_review_steps = [
                "緊急理由、証跡添付、事後承認の有無を確認する。",
                "緊急ルート利用が反復していないか確認する。",
                "通常ルートでは間に合わなかった合理的理由を確認する。",
            ]
        elif defect_id == INFORMAL_PREAPPROVAL_DEFECT_ID:
            title = "非公式事前承認・システム外相談のレビュー候補"
            recommended_review_steps = [
                "正式承認前の非公式な合意形成があったか確認する。",
                "承認コメント、チャット証跡、ヒアリング手続で根拠を確認する。",
                "非公式相談が正式承認を形骸化させていないか評価する。",
            ]
        elif defect_id == FAST_TRACK_ROUTE_DEFECT_ID:
            title = "Fast-track route attempt review candidate"
            recommended_review_steps = [
                "Confirm whether a requester-specified fast-track or shortcut route exists outside modeled normal/emergency routes.",
                "Check whether approval, reason evidence, and post-action review requirements are defined for that route.",
                "Decide whether this should become a first-class Action Library route or a dedicated Detector rule.",
            ]
        else:
            title = "\u627f\u8a8d\u95be\u5024\u56de\u907f\u306e\u53ef\u80fd\u6027\u304c\u3042\u308b\u5206\u5272\u8cfc\u8cb7\u7533\u8acb"
            recommended_review_steps = [
                "\u8907\u6570\u7533\u8acb\u304c\u540c\u4e00\u306e\u8cfc\u8cb7\u30cb\u30fc\u30ba\u306b\u5bfe\u5fdc\u3059\u308b\u304b\u78ba\u8a8d\u3059\u308b\u3002",
                "\u7533\u8acb\u7406\u7531\u3068\u627f\u8a8d\u5c65\u6b74\u3092\u78ba\u8a8d\u3059\u308b\u3002",
                "\u5408\u7b97\u7d71\u5236\u306e\u9069\u7528\u8981\u5426\u3092\u8a55\u4fa1\u3059\u308b\u3002",
            ]
        findings.append(
            {
                "finding_id": f"FND-{index:06d}",
                "run_id": annotation["run_id"],
                "world_id": annotation.get("world_id", ""),
                "defect_id": defect_id,
                "title": title,
                "severity": annotation["severity"],
                "status": status,
                "detector_id": annotation["detector_id"],
                "related_controls": annotation["related_controls"],
                "evidence_event_ids": annotation["evidence_event_ids"],
                "observed_facts": annotation["observed_facts"],
                "inference": annotation["inference"],
                "bypass_success": annotation["bypass_success"],
                "mitigated_by_aggregation": annotation["mitigated_by_aggregation"],
                "mitigated_by_variant": mitigated_by_variant,
                "mitigated_by_emergency_control": bool(annotation.get("mitigated_by_emergency_control", False)),
                "recommended_review_steps": recommended_review_steps,
                "evidence_summary": [
                    {
                        "event_id": event["event_id"],
                        "timestamp": event["timestamp"],
                        "world_id": event.get("world_id", ""),
                        "purchase_need_id": event["purchase_need_id"],
                        "purchase_request_id": event["purchase_request_id"],
                        "amount": event["amount"],
                        "reported_amount": event.get("metadata", {}).get("reported_amount", event["amount"]),
                        "economic_amount": event.get("metadata", {}).get("economic_amount", event["amount"]),
                        "requested_route_type": event.get("metadata", {}).get("requested_route_type", event.get("route_type", "")),
                        "required_approver_level": event.get("metadata", {}).get("required_approver_level", ""),
                        "aggregation_applied": event.get("metadata", {}).get("aggregation_applied", False),
                    }
                    for event in evidence
                ],
            }
        )
    return findings
