from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from ia_sim.models import APPROVER_RANK, ControlCard, PurchaseRequestRecord, approver_at_least


@dataclass(frozen=True)
class VariantPolicy:
    variant_id: str
    name: str
    aggregate_approval_window_days: int | None = None
    aggregate_by_fields: tuple[str, ...] = ("requester_user_id", "vendor_id", "project_id")

    @property
    def aggregation_enabled(self) -> bool:
        return self.aggregate_approval_window_days is not None


class RuleEngine:
    def __init__(self, controls: list[ControlCard], variant_policy: VariantPolicy):
        self.controls = {control.control_id: control for control in controls}
        self.variant_policy = variant_policy
        approval_control = self.controls["P2P-C-001"]
        thresholds = approval_control.rule["thresholds"]
        self.thresholds = sorted(thresholds, key=lambda item: int(item["min_amount"]))

    def required_approver_level(self, amount: int) -> str:
        required_level = "manager"
        for threshold in self.thresholds:
            if amount >= int(threshold["min_amount"]):
                required_level = threshold["approver_level"]
        return required_level

    def evaluate_create_request(
        self,
        *,
        request_date: date,
        requester_user_id: str,
        department_id: str,
        vendor_id: str,
        project_id: str,
        amount: int,
        route_type: str,
        prior_requests: list[PurchaseRequestRecord],
    ) -> dict[str, Any]:
        individual_level = self.required_approver_level(amount)
        aggregate_amount = amount
        aggregate_event_count = 1
        aggregation_applied = False

        if self.variant_policy.aggregation_enabled:
            window_days = self.variant_policy.aggregate_approval_window_days or 0
            for prior in prior_requests:
                same_group = (
                    prior.requester_user_id == requester_user_id
                    and prior.vendor_id == vendor_id
                    and prior.project_id == project_id
                )
                within_window = abs((request_date - prior.request_date).days) <= window_days
                if same_group and within_window:
                    aggregate_amount += prior.amount
                    aggregate_event_count += 1
            aggregate_level = self.required_approver_level(aggregate_amount)
            aggregation_applied = APPROVER_RANK[aggregate_level] > APPROVER_RANK[individual_level]
            required_level = aggregate_level if aggregation_applied else individual_level
        else:
            aggregate_level = individual_level
            required_level = individual_level

        return {
            "P2P-C-001": {
                "status": "passed",
                "control_id": "P2P-C-001",
                "control_name": "Amount-based approval",
                "individual_amount": amount,
                "individual_required_approver_level": individual_level,
                "aggregate_amount": aggregate_amount,
                "aggregate_event_count": aggregate_event_count,
                "aggregate_required_approver_level": aggregate_level,
                "effective_required_approver_level": required_level,
                "aggregation_window_days": self.variant_policy.aggregate_approval_window_days,
                "aggregation_applied": aggregation_applied,
                "route_type": route_type,
            },
            "P2P-C-002": {
                "status": "passed",
                "control_id": "P2P-C-002",
                "control_name": "Segregation of duties",
                "requester_user_id": requester_user_id,
                "department_id": department_id,
                "rule": "Requester must not approve own purchase request",
            },
            "P2P-C-003": {
                "status": "passed",
                "control_id": "P2P-C-003",
                "control_name": "Pre-PO approval",
                "pre_po_approval_required": route_type != "emergency",
                "route_type": route_type,
            },
        }

    def evaluate_approval(
        self, *, approver_user_id: str, approver_level: str, requester_user_id: str, required_level: str
    ) -> dict[str, Any]:
        sod_passed = approver_user_id != requester_user_id
        authority_passed = approver_at_least(approver_level, required_level)
        return {
            "P2P-C-001": {
                "status": "passed" if authority_passed else "failed",
                "required_approver_level": required_level,
                "actual_approver_level": approver_level,
            },
            "P2P-C-002": {
                "status": "passed" if sod_passed else "failed",
                "requester_user_id": requester_user_id,
                "approver_user_id": approver_user_id,
            },
        }
