from pathlib import Path

from ia_sim.config import load_action_definitions, validate_action_definitions, validate_config_tree
from ia_sim.synthetic import PURCHASE_NEED_FIELDS


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_config_tree_is_valid():
    assert validate_config_tree(REPO_ROOT) == []


def test_closed_actions_are_neutral_and_no_split_action_is_exposed():
    actions = load_action_definitions(REPO_ROOT / "configs/actions/p2p_action_definitions.yaml")
    action_ids = {action.action_id for action in actions}

    assert "submit_split_requests" not in action_ids
    assert "select_request_route" not in action_ids
    assert validate_action_definitions(actions) == []

    create_action = next(action for action in actions if action.action_id == "create_purchase_request")
    assert "route_type" in create_action.required_fields
    assert "request_date" in create_action.required_fields


def test_purchase_need_fields_do_not_expose_evaluation_or_generation_intent():
    assert "evaluation_group_id" not in PURCHASE_NEED_FIELDS
    assert "behavior_pattern" not in PURCHASE_NEED_FIELDS
