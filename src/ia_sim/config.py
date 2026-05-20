from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any

import yaml

from ia_sim.models import ActionDefinition, AgentProfile, ControlCard, RunConfig, ScenarioCard


FORBIDDEN_CLOSED_ACTIONS = {"submit_split_requests", "select_request_route"}


def read_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(value, handle, sort_keys=False, allow_unicode=True)


def _dataclass_from_dict(cls, raw: dict[str, Any]):
    allowed = {field.name for field in fields(cls)}
    return cls(**{key: value for key, value in raw.items() if key in allowed})


def load_run_config(path: Path) -> RunConfig:
    raw = read_yaml(path)
    return _dataclass_from_dict(RunConfig, raw)


def load_action_definitions(path: Path) -> list[ActionDefinition]:
    raw = read_yaml(path)
    return [_dataclass_from_dict(ActionDefinition, item) for item in raw["actions"]]


def load_control_cards(path: Path) -> list[ControlCard]:
    raw = read_yaml(path)
    return [_dataclass_from_dict(ControlCard, item) for item in raw["controls"]]


def load_scenarios(path: Path) -> list[ScenarioCard]:
    raw = read_yaml(path)
    return [_dataclass_from_dict(ScenarioCard, item) for item in raw["scenarios"]]


def load_agent_profiles(path: Path) -> list[AgentProfile]:
    raw = read_yaml(path)
    return [_dataclass_from_dict(AgentProfile, item) for item in raw["agents"]]


def validate_action_definitions(actions: list[ActionDefinition]) -> list[str]:
    errors: list[str] = []
    action_ids = {action.action_id for action in actions}
    forbidden = sorted(action_ids & FORBIDDEN_CLOSED_ACTIONS)
    if forbidden:
        errors.append(f"Forbidden action ids are present: {', '.join(forbidden)}")

    create_action = next((a for a in actions if a.action_id == "create_purchase_request"), None)
    if not create_action:
        errors.append("create_purchase_request action is required")
    elif "route_type" not in create_action.required_fields:
        errors.append("create_purchase_request.required_fields must include route_type")
    elif "request_date" not in create_action.required_fields:
        errors.append("create_purchase_request.required_fields must include request_date")

    for action in actions:
        if action.mode == "closed_action" and not action.neutral_name:
            errors.append(f"Closed action must use a neutral name: {action.action_id}")
    return errors


def validate_config_tree(repo_root: Path) -> list[str]:
    config_paths = [
        repo_root / "configs/actions/p2p_action_definitions.yaml",
        repo_root / "configs/controls/p2p_controls.yaml",
        repo_root / "configs/scenarios/p2p_scenarios.yaml",
        repo_root / "configs/agents/p2p_agents.yaml",
        repo_root / "configs/variants/p2p_control_variants.yaml",
        repo_root / "configs/org/delegation_rules.yaml",
        repo_root / "configs/run_configs/baseline.yaml",
        repo_root / "configs/run_configs/variant_a.yaml",
        repo_root / "configs/run_configs/llm_baseline.yaml",
        repo_root / "configs/run_configs/llm_variant_a.yaml",
        repo_root / "configs/run_configs/branching_baseline.yaml",
        repo_root / "data/synthetic/ground_truth_labels.yaml",
    ]
    errors: list[str] = []
    for path in config_paths:
        if not path.exists():
            errors.append(f"Missing required config file: {path}")

    if not errors:
        actions = load_action_definitions(config_paths[0])
        errors.extend(validate_action_definitions(actions))

    return errors
