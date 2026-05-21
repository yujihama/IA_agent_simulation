from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from typing import Any

from ia_sim.models import PlannedAction, PurchaseNeed, PurchaseRequestRecord
from ia_sim.rule_engine import RuleEngine


JST = timezone(timedelta(hours=9))

APPROVER_DIRECTORY = {
    "manager": ("USER-MGR-001", "manager", 0.5),
    "department_head": ("USER-DHEAD-001", "department_head", 1.5),
    "division_head": ("USER-DIV-001", "division_head", 3.0),
}

FOLLOW_ON_ACTIONS = [
    ("issue_purchase_order", "purchasing", "USER-BUYER-001"),
    ("receive_goods", "receiver", "USER-RECEIVER-001"),
    ("receive_invoice", "ap_clerk", "USER-AP-001"),
    ("perform_three_way_match", "ap_clerk", "USER-AP-001"),
    ("approve_payment", "payment_approver", "USER-FIN-APP-001"),
    ("execute_payment", "payment_operator", "USER-FIN-OPS-001"),
]


def _lineage_metadata(action: PlannedAction) -> dict[str, Any]:
    return {
        "lineage_source_world_id": action.parameters.get("_lineage_source_world_id", action.world_id),
        "lineage_action_depth": int(action.parameters.get("_lineage_action_depth", action.depth)),
    }


def build_behavior_plan(needs: list[PurchaseNeed], max_purchase_needs: int) -> list[PlannedAction]:
    allowed_actions = [
        "create_purchase_request",
        "consult_manager",
        "consult_purchasing",
        "postpone_request",
    ]
    plan: list[PlannedAction] = []
    sequence = 1
    for need in needs[:max_purchase_needs]:
        if _uses_embedded_first_slice_split_pattern(need):
            amounts = [900_000, need.amount_total - 900_000]
            for offset, amount in enumerate(amounts):
                plan.append(
                    PlannedAction(
                        sequence=sequence,
                        purchase_need_id=need.purchase_need_id,
                        action_id="create_purchase_request",
                        parameters={
                            "amount": amount,
                            "request_date": (need.request_date + timedelta(days=offset)).isoformat(),
                            "vendor_id": need.vendor_id,
                            "project_id": need.project_id,
                            "route_type": "normal",
                        },
                        rationale="Quarter-end pressure creates multiple ordinary purchase requests for one purchase need.",
                        allowed_actions=allowed_actions,
                    )
                )
                sequence += 1
        else:
            plan.append(
                PlannedAction(
                    sequence=sequence,
                    purchase_need_id=need.purchase_need_id,
                    action_id="create_purchase_request",
                    parameters={
                        "amount": need.amount_total,
                        "request_date": need.request_date.isoformat(),
                        "vendor_id": need.vendor_id,
                        "project_id": need.project_id,
                        "route_type": "normal",
                    },
                    rationale="Ordinary single purchase request.",
                    allowed_actions=allowed_actions,
                )
            )
            sequence += 1
    return plan


def _uses_embedded_first_slice_split_pattern(need: PurchaseNeed) -> bool:
    return need.scenario_id == "S-002" and need.purchase_need_id == "NEED-001"


class SimulationEngine:
    def __init__(self, run_id: str, rule_engine: RuleEngine):
        self.run_id = run_id
        self.rule_engine = rule_engine
        self._event_counter = 1
        self._request_counter = 1
        self.purchase_requests: list[PurchaseRequestRecord] = []

    def run(self, needs: list[PurchaseNeed], plan: list[PlannedAction]) -> list[dict[str, Any]]:
        need_by_id = {need.purchase_need_id: need for need in needs}
        events: list[dict[str, Any]] = []
        for action in plan:
            need = need_by_id[action.purchase_need_id]
            if action.action_id == "create_purchase_request":
                events.extend(self._create_purchase_request_events(need, action))
            elif action.action_id in {
                "consult_manager",
                "consult_purchasing",
                "postpone_request",
                "informal_preapproval_chat",
            }:
                events.append(self._non_purchase_request_event(need, action))
        return events

    def record_system_blocked_attempt(self, need: PurchaseNeed, action: PlannedAction) -> dict[str, Any]:
        action_date = action.parameters.get("request_date") or need.request_date.isoformat()
        timestamp = datetime.combine(datetime.fromisoformat(action_date).date(), time(9, 0), tzinfo=JST)
        amount = int(action.parameters.get("reported_amount", action.parameters.get("amount", 0)))
        economic_amount = int(action.parameters.get("economic_amount", amount))
        return self._event(
            timestamp=timestamp,
            case_id=f"CASE-BLOCKED-{action.sequence:06d}",
            purchase_need_id=need.purchase_need_id,
            purchase_request_id="",
            actor_user_id=need.requester_user_id,
            actor_role="requester",
            action_id=action.action_id,
            amount=amount,
            vendor_id=str(action.parameters.get("vendor_id", need.vendor_id)),
            project_id=str(action.parameters.get("project_id", need.project_id)),
            route_type=str(action.parameters.get("route_type", "")),
            state_before=need.status,
            state_after="blocked_attempt",
            control_results={
                "SYSTEM-BLOCK": {
                    "status": "failed",
                    "control_name": "Synthetic system constraint",
                    "reason": action.branch_reason or action.rationale,
                }
            },
            metadata={
                "scenario_id": need.scenario_id,
                "planned_action_sequence": action.sequence,
                "item_description": need.item_description,
                "proposal_id": action.proposal_id,
                "reported_amount": amount,
                "economic_amount": economic_amount,
                "amount_mismatch": amount != economic_amount,
                "classification": action.classification,
                "policy_violation_flags": action.policy_violation_flags,
                "integrity_flags": action.integrity_flags,
                "risk_score": action.risk_score,
                "attempt_only": True,
                **_lineage_metadata(action),
            },
            world_id=action.world_id,
            parent_world_id=action.parent_world_id,
            branch_reason=action.branch_reason,
            classification=action.classification,
        )

    def _non_purchase_request_event(self, need: PurchaseNeed, action: PlannedAction) -> dict[str, Any]:
        action_date = action.parameters.get("request_date") or need.request_date.isoformat()
        timestamp = datetime.combine(datetime.fromisoformat(action_date).date(), time(9, 0), tzinfo=JST)
        if action.action_id == "consult_manager":
            actor_role = "requester"
            state_before = need.status
            state_after = need.status
            metadata = {"question": action.parameters.get("question", ""), "consulted_role": "manager"}
        elif action.action_id == "consult_purchasing":
            actor_role = "requester"
            state_before = need.status
            state_after = need.status
            metadata = {"question": action.parameters.get("question", ""), "consulted_role": "purchasing"}
        elif action.action_id == "informal_preapproval_chat":
            actor_role = "requester"
            state_before = need.status
            state_after = need.status
            metadata = {
                "channel": action.parameters.get("channel", "chat"),
                "counterpart_role": action.parameters.get("counterpart_role", "purchasing"),
                "message": action.parameters.get("message", ""),
                "system_of_record": False,
            }
        else:
            actor_role = "requester"
            state_before, state_after = need.apply_postpone()
            metadata = {"reason": action.parameters.get("reason", "")}
        case_id = f"CASE-ACT-{action.sequence:06d}"
        metadata.update(
            {
                "scenario_id": need.scenario_id,
                "planned_action_sequence": action.sequence,
                "item_description": need.item_description,
                "proposal_id": action.proposal_id,
                "policy_violation_flags": action.policy_violation_flags,
                "integrity_flags": action.integrity_flags,
                "risk_score": action.risk_score,
                **_lineage_metadata(action),
            }
        )
        return self._event(
            timestamp=timestamp,
            case_id=case_id,
            purchase_need_id=need.purchase_need_id,
            purchase_request_id="",
            actor_user_id=need.requester_user_id,
            actor_role=actor_role,
            action_id=action.action_id,
            amount=0,
            vendor_id=need.vendor_id,
            project_id=need.project_id,
            route_type=action.parameters.get("route_type", ""),
            state_before=state_before,
            state_after=state_after,
            control_results={},
            metadata=metadata,
            world_id=action.world_id,
            parent_world_id=action.parent_world_id,
            branch_reason=action.branch_reason,
            classification=action.classification,
        )

    def _create_purchase_request_events(self, need: PurchaseNeed, action: PlannedAction) -> list[dict[str, Any]]:
        amount = int(action.parameters.get("reported_amount", action.parameters["amount"]))
        economic_amount = int(action.parameters.get("economic_amount", amount))
        request_date = datetime.fromisoformat(action.parameters["request_date"]).date()
        route_type = action.parameters["route_type"]
        requested_route_type = action.parameters.get("requested_route_type", route_type)
        purchase_request_id = f"PR-{self._request_counter:06d}"
        case_id = f"CASE-{self._request_counter:06d}"
        self._request_counter += 1

        state_before, state_after = need.apply_request_amount(economic_amount)
        control_results = self.rule_engine.evaluate_create_request(
            request_date=request_date,
            requester_user_id=need.requester_user_id,
            department_id=need.department_id,
            vendor_id=need.vendor_id,
            project_id=need.project_id,
            amount=amount,
            route_type=route_type,
            prior_requests=self.purchase_requests,
            emergency_reason=str(action.parameters.get("emergency_reason", "")),
        )
        amount_control = control_results["P2P-C-001"]
        required_level = amount_control["effective_required_approver_level"]
        individual_level = amount_control["individual_required_approver_level"]
        aggregate_amount = amount_control["aggregate_amount"]
        aggregation_applied = amount_control["aggregation_applied"]

        request_record = PurchaseRequestRecord(
            purchase_request_id=purchase_request_id,
            purchase_need_id=need.purchase_need_id,
            request_date=request_date,
            requester_user_id=need.requester_user_id,
            department_id=need.department_id,
            vendor_id=need.vendor_id,
            project_id=need.project_id,
            amount=amount,
            route_type=route_type,
            required_approver_level=required_level,
            individual_required_approver_level=individual_level,
            aggregate_amount=aggregate_amount,
            aggregation_applied=aggregation_applied,
            control_results=control_results,
        )
        self.purchase_requests.append(request_record)

        base_timestamp = datetime.combine(request_date, time(9, 0), tzinfo=JST)
        create_event = self._event(
            timestamp=base_timestamp,
            case_id=case_id,
            purchase_need_id=need.purchase_need_id,
            purchase_request_id=purchase_request_id,
            actor_user_id=need.requester_user_id,
            actor_role="requester",
            action_id="create_purchase_request",
            amount=amount,
            vendor_id=need.vendor_id,
            project_id=need.project_id,
            route_type=route_type,
            state_before=state_before,
            state_after=state_after,
            control_results=control_results,
            metadata={
                "scenario_id": need.scenario_id,
                "planned_action_sequence": action.sequence,
                "item_description": need.item_description,
                "proposal_id": action.proposal_id,
                "reported_amount": amount,
                "economic_amount": economic_amount,
                "amount_mismatch": amount != economic_amount,
                "emergency_reason": action.parameters.get("emergency_reason", ""),
                "requested_route_type": requested_route_type,
                "classification": action.classification,
                "policy_violation_flags": action.policy_violation_flags,
                "integrity_flags": action.integrity_flags,
                "risk_score": action.risk_score,
                "required_approver_level": required_level,
                "individual_required_approver_level": individual_level,
                "aggregate_amount": aggregate_amount,
                "aggregation_applied": aggregation_applied,
                **_lineage_metadata(action),
            },
            world_id=action.world_id,
            parent_world_id=action.parent_world_id,
            branch_reason=action.branch_reason,
            classification=action.classification,
        )

        approver_user_id, approver_role, lead_days = APPROVER_DIRECTORY[required_level]
        approval_time = base_timestamp + timedelta(days=lead_days)
        approval_results = self.rule_engine.evaluate_approval(
            approver_user_id=approver_user_id,
            approver_level=approver_role,
            requester_user_id=need.requester_user_id,
            required_level=required_level,
        )
        events = [
            create_event,
            self._event(
                timestamp=approval_time,
                case_id=case_id,
                purchase_need_id=need.purchase_need_id,
                purchase_request_id=purchase_request_id,
                actor_user_id=approver_user_id,
                actor_role=approver_role,
                action_id="approve_purchase_request",
                amount=amount,
                vendor_id=need.vendor_id,
                project_id=need.project_id,
                route_type=route_type,
                state_before="submitted",
                state_after="approved",
                control_results=approval_results,
                metadata={
                    "proposal_id": action.proposal_id,
                    "reported_amount": amount,
                    "economic_amount": economic_amount,
                    "amount_mismatch": amount != economic_amount,
                    "emergency_reason": action.parameters.get("emergency_reason", ""),
                    "requested_route_type": requested_route_type,
                    "classification": action.classification,
                    "policy_violation_flags": action.policy_violation_flags,
                    "integrity_flags": action.integrity_flags,
                    "risk_score": action.risk_score,
                    "approval_lead_time_days": lead_days,
                    "required_approver_level": required_level,
                    **_lineage_metadata(action),
                },
                world_id=action.world_id,
                parent_world_id=action.parent_world_id,
                branch_reason=action.branch_reason,
                classification=action.classification,
            ),
        ]

        current_time = approval_time
        for offset, (action_id, role, user_id) in enumerate(FOLLOW_ON_ACTIONS, start=1):
            current_time = current_time + timedelta(hours=4)
            events.append(
                self._event(
                    timestamp=current_time,
                    case_id=case_id,
                    purchase_need_id=need.purchase_need_id,
                    purchase_request_id=purchase_request_id,
                    actor_user_id=user_id,
                    actor_role=role,
                    action_id=action_id,
                    amount=amount,
                    vendor_id=need.vendor_id,
                    project_id=need.project_id,
                    route_type=route_type,
                    state_before="approved" if offset == 1 else "in_process",
                    state_after="in_process" if offset < len(FOLLOW_ON_ACTIONS) else "paid",
                    control_results={},
                    metadata={
                        "proposal_id": action.proposal_id,
                        "reported_amount": amount,
                        "economic_amount": economic_amount,
                        "amount_mismatch": amount != economic_amount,
                        "emergency_reason": action.parameters.get("emergency_reason", ""),
                        "requested_route_type": requested_route_type,
                        "classification": action.classification,
                        "policy_violation_flags": action.policy_violation_flags,
                        "integrity_flags": action.integrity_flags,
                        "risk_score": action.risk_score,
                        "required_approver_level": required_level,
                        **_lineage_metadata(action),
                    },
                    world_id=action.world_id,
                    parent_world_id=action.parent_world_id,
                    branch_reason=action.branch_reason,
                    classification=action.classification,
                )
            )
        return events

    def _event(
        self,
        *,
        timestamp: datetime,
        case_id: str,
        purchase_need_id: str,
        purchase_request_id: str,
        actor_user_id: str,
        actor_role: str,
        action_id: str,
        amount: int,
        vendor_id: str,
        project_id: str,
        route_type: str,
        state_before: str,
        state_after: str,
        control_results: dict[str, Any],
        metadata: dict[str, Any],
        world_id: str = "",
        parent_world_id: str = "",
        branch_reason: str = "",
        classification: str = "compliant",
    ) -> dict[str, Any]:
        event = {
            "event_id": f"EVT-{self._event_counter:06d}",
            "run_id": self.run_id,
            "world_id": world_id,
            "parent_world_id": parent_world_id,
            "branch_reason": branch_reason,
            "timestamp": timestamp.isoformat(),
            "case_id": case_id,
            "purchase_need_id": purchase_need_id,
            "purchase_request_id": purchase_request_id,
            "actor_user_id": actor_user_id,
            "actor_role": actor_role,
            "action_id": action_id,
            "amount": amount,
            "vendor_id": vendor_id,
            "project_id": project_id,
            "route_type": route_type,
            "classification": classification,
            "state_before": state_before,
            "state_after": state_after,
            "control_results": control_results,
            "metadata": metadata,
        }
        self._event_counter += 1
        return event


def behavior_replay_rows(run_id: str, plan: list[PlannedAction], behavior_mode: str, comparison_mode: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for action in plan:
        rows.append(
            {
                "run_id": run_id,
                "sequence": action.sequence,
                "behavior_mode": behavior_mode,
                "comparison_mode": comparison_mode,
                "source": action.source,
                "allowed_actions_presented": action.allowed_actions,
                "selected_action_id": action.action_id,
                "selected_action_is_neutral": True,
                "parameters": action.parameters,
                "rationale": action.rationale,
                "classification": action.classification,
                "policy_violation_flags": action.policy_violation_flags,
                "integrity_flags": action.integrity_flags,
                "world_id": action.world_id,
                "parent_world_id": action.parent_world_id,
                "branch_reason": action.branch_reason,
                "proposal_id": action.proposal_id,
                "risk_score": action.risk_score,
                "depth": action.depth,
            }
        )
    return rows
