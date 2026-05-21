from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


APPROVER_RANK = {
    "none": 0,
    "manager": 1,
    "department_head": 2,
    "division_head": 3,
}


@dataclass(frozen=True)
class ActionDefinition:
    action_id: str
    description: str
    mode: str
    required_fields: list[str]
    neutral_name: bool = True


@dataclass(frozen=True)
class ControlCard:
    control_id: str
    name: str
    objective: str
    control_type: str
    owner: str
    system_enforced: bool
    rule: dict[str, Any]
    related_defects: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScenarioCard:
    scenario_id: str
    name: str
    summary: str
    pressure_type: str
    target_defects: list[str]


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    user_id: str
    role: str
    department_id: str
    objectives: list[str]
    constraints: list[str]


@dataclass(frozen=True)
class RunConfig:
    run_id: str
    name: str
    process: str
    scenario_id: str
    variant_id: str
    seed: int
    behavior_mode: str
    comparison_mode: str
    simulation: dict[str, Any]
    inputs: dict[str, str]
    evaluation_inputs: dict[str, str]
    outputs: dict[str, str]
    llm: dict[str, Any] = field(default_factory=dict)
    branching: dict[str, Any] = field(default_factory=dict)


@dataclass
class PurchaseNeed:
    purchase_need_id: str
    request_date: date
    requester_user_id: str
    department_id: str
    vendor_id: str
    project_id: str
    item_description: str
    amount_total: int
    needed_by: date
    scenario_id: str
    status: str = "open"
    requested_amount: int = 0

    def apply_request_amount(self, amount: int) -> tuple[str, str]:
        before = self.status
        self.requested_amount += amount
        if self.requested_amount <= 0:
            self.status = "open"
        elif self.requested_amount < self.amount_total:
            self.status = "partially_requested"
        else:
            self.status = "requested"
        return before, self.status

    def apply_postpone(self) -> tuple[str, str]:
        before = self.status
        self.status = "postponed"
        return before, self.status


@dataclass(frozen=True)
class PlannedAction:
    sequence: int
    purchase_need_id: str
    action_id: str
    parameters: dict[str, Any]
    rationale: str
    allowed_actions: list[str]
    source: str = "deterministic_policy"
    classification: str = "compliant"
    policy_violation_flags: list[str] = field(default_factory=list)
    integrity_flags: list[str] = field(default_factory=list)
    world_id: str = ""
    parent_world_id: str = ""
    branch_reason: str = ""
    proposal_id: str = ""
    risk_score: int = 0
    depth: int = 1


@dataclass
class PurchaseRequestRecord:
    purchase_request_id: str
    purchase_need_id: str
    request_date: date
    requester_user_id: str
    department_id: str
    vendor_id: str
    project_id: str
    amount: int
    route_type: str
    required_approver_level: str
    individual_required_approver_level: str
    aggregate_amount: int
    aggregation_applied: bool
    control_results: dict[str, Any]


@dataclass(frozen=True)
class RunResult:
    run_id: str
    run_dir: Path
    manifest_path: Path
    events_path: Path
    annotations_path: Path
    findings_path: Path
    metrics_path: Path
    behavior_replay_path: Path
    report_path: Path


def approver_at_least(level: str, required_level: str) -> bool:
    return APPROVER_RANK.get(level, -1) >= APPROVER_RANK.get(required_level, 999)


def now_utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
