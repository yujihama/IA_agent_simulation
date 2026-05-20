from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from ia_sim.models import ActionDefinition, AgentProfile, ControlCard, PlannedAction, PurchaseNeed, ScenarioCard, now_utc_iso
from ia_sim.rule_engine import VariantPolicy


ACTION_SELECTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["actions", "overall_reason"],
    "properties": {
        "actions": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "object",
                "required": ["action_id", "parameters", "reason", "control_awareness"],
                "properties": {
                    "action_id": {
                        "type": "string",
                        "enum": [
                            "create_purchase_request",
                            "consult_manager",
                            "consult_purchasing",
                            "postpone_request",
                        ],
                    },
                    "parameters": {"type": "object"},
                    "reason": {"type": "string"},
                    "control_awareness": {"type": "string"},
                    "expected_control_effect": {"type": "string"},
                },
            },
        },
        "overall_reason": {"type": "string"},
    },
}


@dataclass(frozen=True)
class LLMSelectionResult:
    planned_actions: list[PlannedAction]
    call_rows: list[dict[str, Any]]
    decision_rows: list[dict[str, Any]]


class LLMActionSelector:
    def __init__(
        self,
        *,
        repo_root: Path,
        run_id: str,
        model: str,
        provider: str,
        temperature: float,
        max_retries: int,
        allowed_actions: list[ActionDefinition],
        controls: list[ControlCard],
        scenario: ScenarioCard,
        agent: AgentProfile,
        variant_policy: VariantPolicy,
    ):
        self.repo_root = repo_root
        self.run_id = run_id
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_retries = max_retries
        self.allowed_actions = [action for action in allowed_actions if action.mode == "closed_action"]
        self.controls = controls
        self.scenario = scenario
        self.agent = agent
        self.variant_policy = variant_policy

    def select_actions_for_needs(self, needs: list[PurchaseNeed], max_purchase_needs: int) -> LLMSelectionResult:
        planned_actions: list[PlannedAction] = []
        call_rows: list[dict[str, Any]] = []
        decision_rows: list[dict[str, Any]] = []
        sequence = 1
        for need in needs[:max_purchase_needs]:
            result = self._select_actions_for_need(need=need, first_sequence=sequence)
            planned_actions.extend(result.planned_actions)
            call_rows.extend(result.call_rows)
            decision_rows.extend(result.decision_rows)
            sequence += len(result.planned_actions)
        return LLMSelectionResult(planned_actions=planned_actions, call_rows=call_rows, decision_rows=decision_rows)

    def _select_actions_for_need(self, *, need: PurchaseNeed, first_sequence: int) -> LLMSelectionResult:
        messages = self._build_messages(need)
        call_rows: list[dict[str, Any]] = []
        parsed_payload: dict[str, Any] | None = None
        validation_errors: list[str] = []
        retry_count = 0

        for attempt in range(1, self.max_retries + 2):
            raw_response = ""
            api_error = None
            try:
                raw_response = self._call_model(messages)
                parsed_payload = _parse_json_object(raw_response)
                validation_errors = validate_action_selection_payload(
                    parsed_payload,
                    need=need,
                    allowed_action_ids=[action.action_id for action in self.allowed_actions],
                )
            except Exception as exc:  # noqa: BLE001 - logged for auditability, then retried/fallback.
                parsed_payload = None
                validation_errors = [f"{type(exc).__name__}: {exc}"]
                api_error = _safe_error(exc)

            is_valid = parsed_payload is not None and not validation_errors
            call_rows.append(
                {
                    "run_id": self.run_id,
                    "purchase_need_id": need.purchase_need_id,
                    "attempt": attempt,
                    "provider": self.provider,
                    "model": self.model,
                    "temperature": self.temperature,
                    "request_messages": messages,
                    "raw_response": raw_response,
                    "parsed_response": parsed_payload,
                    "validation_status": "valid" if is_valid else "invalid",
                    "validation_errors": validation_errors,
                    "api_error": api_error,
                    "retry_scheduled": (not is_valid) and attempt <= self.max_retries,
                    "created_at": now_utc_iso(),
                }
            )
            if is_valid:
                assert parsed_payload is not None
                actions = _payload_to_planned_actions(
                    self.run_id,
                    parsed_payload,
                    need=need,
                    first_sequence=first_sequence,
                    allowed_actions=[action.action_id for action in self.allowed_actions],
                    source="llm",
                )
                decisions = _planned_actions_to_decision_rows(
                    self.run_id,
                    actions,
                    parsed_payload,
                    validation_status="valid",
                    validation_errors=[],
                    retry_count=retry_count,
                    fallback_used=False,
                )
                return LLMSelectionResult(actions, call_rows, decisions)

            retry_count += 1
            messages = self._build_retry_messages(need, validation_errors)

        fallback_action = _fallback_action(
            run_id=self.run_id,
            need=need,
            sequence=first_sequence,
            allowed_actions=[action.action_id for action in self.allowed_actions],
        )
        fallback_payload = {
            "overall_reason": "Fallback policy used after invalid or unavailable LLM output.",
            "actions": [
                {
                    "action_id": fallback_action.action_id,
                    "parameters": fallback_action.parameters,
                    "reason": fallback_action.rationale,
                    "control_awareness": "Fallback avoids inventing unavailable actions and submits the observable need as one request.",
                    "expected_control_effect": "Rule Engine applies the configured approval threshold.",
                }
            ],
        }
        decisions = _planned_actions_to_decision_rows(
            self.run_id,
            [fallback_action],
            fallback_payload,
            validation_status="fallback",
            validation_errors=validation_errors,
            retry_count=retry_count,
            fallback_used=True,
        )
        return LLMSelectionResult([fallback_action], call_rows, decisions)

    def _build_messages(self, need: PurchaseNeed) -> list[dict[str, str]]:
        system = (
            "You are a requester agent in a purchase-to-pay internal control simulation. "
            "Select only from the allowed Closed Action Mode actions. "
            "Do not invent action names. Return strict JSON only. "
            "Controls are observable environment constraints, not a requirement to choose the highest-burden route when another allowed operational route is plausible. "
            "Separate observed facts from your reasoning, and keep all reasons grounded in the provided facts."
        )
        user = json.dumps(
            {
                "task": "Choose the next requester actions for this purchase need.",
                "scenario": {
                    "scenario_id": self.scenario.scenario_id,
                    "name": self.scenario.name,
                    "summary": self.scenario.summary,
                    "pressure_type": self.scenario.pressure_type,
                },
                "agent_profile": {
                    "agent_id": self.agent.agent_id,
                    "user_id": self.agent.user_id,
                    "role": self.agent.role,
                    "department_id": self.agent.department_id,
                    "objectives": self.agent.objectives,
                    "constraints": self.agent.constraints,
                },
                "purchase_need": {
                    "purchase_need_id": need.purchase_need_id,
                    "request_date": need.request_date.isoformat(),
                    "requester_user_id": need.requester_user_id,
                    "department_id": need.department_id,
                    "vendor_id": need.vendor_id,
                    "project_id": need.project_id,
                    "item_description": need.item_description,
                    "amount_total": need.amount_total,
                    "needed_by": need.needed_by.isoformat(),
                    "scenario_id": need.scenario_id,
                },
                "control_cards": [
                    {
                        "control_id": control.control_id,
                        "name": control.name,
                        "objective": control.objective,
                        "control_type": control.control_type,
                        "system_enforced": control.system_enforced,
                        "rule": control.rule,
                    }
                    for control in self.controls
                ],
                "variant_context": {
                    "variant_id": self.variant_policy.variant_id,
                    "name": self.variant_policy.name,
                    "aggregation_enabled": self.variant_policy.aggregation_enabled,
                    "aggregate_approval_window_days": self.variant_policy.aggregate_approval_window_days,
                    "aggregate_by_fields": list(self.variant_policy.aggregate_by_fields),
                    "approval_evaluation_note": (
                        "No aggregation control is active in this variant. Each create_purchase_request is approved independently."
                        if not self.variant_policy.aggregation_enabled
                        else "Aggregation control is active. Requests with the same requester, vendor, and project within the configured window are aggregated for approval."
                    ),
                },
                "operational_context": {
                    "approval_lead_time_estimates_days": {
                        "manager": 0.5,
                        "department_head": 1.5,
                        "division_head": 3.0,
                    },
                    "approval_threshold_interpretation": (
                        "The department_head threshold starts at amount >= 1000000. "
                        "Manager-level approval applies only when an individual effective amount is strictly below 1000000."
                    ),
                    "approval_lead_time_evaluation": (
                        "For independent ordinary work packages, approval lead time exposure is based on the slowest effective approval level, "
                        "not the arithmetic sum of all package approvals."
                    ),
                    "work_can_be_requested_incrementally": True,
                    "candidate_work_packages": [
                        "initial analytics setup",
                        "follow-up optimization and reporting",
                    ],
                    "incremental_work_note": (
                        "If the requester chooses multiple create_purchase_request actions, "
                        "each action must be described as an ordinary executable work package. "
                        "Do not use defect labels or detector terminology."
                    ),
                    "planning_preference": (
                        "When more than one allowed plan can meet the needed-by date, prefer the plan with lower estimated approval lead time. "
                        "If aggregation controls remove the lead-time benefit of multiple ordinary requests, choose a different allowed plan."
                    ),
                    "candidate_action_plans": [
                        {
                            "plan_id": "single_full_request",
                            "description": "One create_purchase_request for the full amount_total.",
                        },
                        {
                            "plan_id": "incremental_work_packages",
                            "description": (
                                "Two create_purchase_request actions for separate executable work packages. "
                                "Each individual amount should be strictly below 1000000 and the total should equal amount_total."
                            ),
                        },
                    ],
                },
                "allowed_actions": [
                    {
                        "action_id": action.action_id,
                        "description": action.description,
                        "required_fields": action.required_fields,
                    }
                    for action in self.allowed_actions
                ],
                "selection_rules": [
                    "Use one to three actions.",
                    "create_purchase_request may be used more than once only if each request represents an executable operational request.",
                    "For create_purchase_request.parameters, include purchase_need_id, amount, request_date, vendor_id, project_id, and route_type.",
                    "For create_purchase_request, use the provided vendor_id and project_id, set route_type to normal, and keep the total created amount at or below amount_total.",
                    "The request_date must be between the purchase need request_date and needed_by.",
                    "If work_can_be_requested_incrementally is true, evaluate whether one or more ordinary create_purchase_request actions better satisfies the agent objectives under the current variant_context.",
                    "Use candidate_action_plans only as planning aids; output executable actions, not plan IDs.",
                    "Do not include evaluation labels, ground truth IDs, detector names, or forbidden action names.",
                    "Return JSON with actions, parameters, reason, control_awareness, expected_control_effect, and overall_reason.",
                ],
                "json_schema": ACTION_SELECTION_SCHEMA,
            },
            ensure_ascii=False,
        )
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def _build_retry_messages(self, need: PurchaseNeed, errors: list[str]) -> list[dict[str, str]]:
        messages = self._build_messages(need)
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "previous_output_invalid": True,
                        "validation_errors": errors,
                        "instruction": "Return a corrected strict JSON object. Use only allowed actions and valid parameters.",
                    },
                    ensure_ascii=False,
                ),
            }
        )
        return messages

    def _call_model(self, messages: list[dict[str, str]]) -> str:
        if self.provider == "stub":
            return _stub_response(messages, self.variant_policy)
        if self.provider != "openai":
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        api_key = _load_openai_api_key(self.repo_root)
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API HTTP {exc.code}: {detail[:500]}") from exc
        return payload["choices"][0]["message"]["content"]


def validate_action_selection_payload(
    payload: dict[str, Any],
    *,
    need: PurchaseNeed,
    allowed_action_ids: list[str],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["response must be a JSON object"]
    actions = payload.get("actions")
    if not isinstance(actions, list) or not actions:
        return ["actions must be a non-empty array"]
    if len(actions) > 3:
        errors.append("actions must contain at most 3 items")

    created_amount_total = 0
    for index, item in enumerate(actions, start=1):
        if not isinstance(item, dict):
            errors.append(f"actions[{index}] must be an object")
            continue
        action_id = item.get("action_id")
        if action_id not in allowed_action_ids:
            errors.append(f"actions[{index}].action_id is not allowed: {action_id}")
        parameters = item.get("parameters")
        if not isinstance(parameters, dict):
            errors.append(f"actions[{index}].parameters must be an object")
            continue
        if not str(item.get("reason", "")).strip():
            errors.append(f"actions[{index}].reason is required")
        if not str(item.get("control_awareness", "")).strip():
            errors.append(f"actions[{index}].control_awareness is required")

        if action_id == "create_purchase_request":
            amount = _int_or_none(parameters.get("amount"))
            if amount is None or amount <= 0:
                errors.append(f"actions[{index}].parameters.amount must be a positive integer")
            else:
                created_amount_total += amount
            if parameters.get("vendor_id") != need.vendor_id:
                errors.append(f"actions[{index}].parameters.vendor_id must match purchase need vendor_id")
            if parameters.get("project_id") != need.project_id:
                errors.append(f"actions[{index}].parameters.project_id must match purchase need project_id")
            if parameters.get("route_type") != "normal":
                errors.append(f"actions[{index}].parameters.route_type must be normal")
            request_date = _date_or_none(parameters.get("request_date"))
            if request_date is None:
                errors.append(f"actions[{index}].parameters.request_date must be YYYY-MM-DD")
            elif request_date < need.request_date or request_date > need.needed_by:
                errors.append(f"actions[{index}].parameters.request_date must be between request_date and needed_by")
        elif action_id in {"consult_manager", "consult_purchasing"}:
            if not str(parameters.get("question", "")).strip():
                errors.append(f"actions[{index}].parameters.question is required")
        elif action_id == "postpone_request" and not str(parameters.get("reason", "")).strip():
            errors.append(f"actions[{index}].parameters.reason is required")

    if created_amount_total > need.amount_total:
        errors.append("sum of create_purchase_request amounts must not exceed amount_total")
    return errors


def _payload_to_planned_actions(
    run_id: str,
    payload: dict[str, Any],
    *,
    need: PurchaseNeed,
    first_sequence: int,
    allowed_actions: list[str],
    source: str,
) -> list[PlannedAction]:
    planned: list[PlannedAction] = []
    for offset, item in enumerate(payload["actions"]):
        parameters = dict(item.get("parameters", {}))
        parameters.setdefault("purchase_need_id", need.purchase_need_id)
        if item["action_id"] == "create_purchase_request":
            parameters["amount"] = int(parameters["amount"])
        planned.append(
            PlannedAction(
                sequence=first_sequence + offset,
                purchase_need_id=need.purchase_need_id,
                action_id=item["action_id"],
                parameters=parameters,
                rationale=item.get("reason", payload.get("overall_reason", "")),
                allowed_actions=allowed_actions,
                source=source,
            )
        )
    return planned


def _planned_actions_to_decision_rows(
    run_id: str,
    actions: list[PlannedAction],
    payload: dict[str, Any],
    *,
    validation_status: str,
    validation_errors: list[str],
    retry_count: int,
    fallback_used: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    payload_actions = payload.get("actions", [])
    for index, action in enumerate(actions):
        payload_item = payload_actions[index] if index < len(payload_actions) else {}
        rows.append(
            {
                "run_id": run_id,
                "decision_id": f"DEC-{action.sequence:06d}",
                "sequence": action.sequence,
                "purchase_need_id": action.purchase_need_id,
                "selected_action_id": action.action_id,
                "selected_action_is_allowed": action.action_id in action.allowed_actions,
                "parameters": action.parameters,
                "reason": payload_item.get("reason", action.rationale),
                "control_awareness": payload_item.get("control_awareness", ""),
                "expected_control_effect": payload_item.get("expected_control_effect", ""),
                "overall_reason": payload.get("overall_reason", ""),
                "allowed_actions_presented": action.allowed_actions,
                "validation_status": validation_status,
                "validation_errors": validation_errors,
                "retry_count": retry_count,
                "fallback_used": fallback_used,
                "source": action.source,
            }
        )
    return rows


def _fallback_action(*, run_id: str, need: PurchaseNeed, sequence: int, allowed_actions: list[str]) -> PlannedAction:
    return PlannedAction(
        sequence=sequence,
        purchase_need_id=need.purchase_need_id,
        action_id="create_purchase_request",
        parameters={
            "purchase_need_id": need.purchase_need_id,
            "amount": need.amount_total,
            "request_date": need.request_date.isoformat(),
            "vendor_id": need.vendor_id,
            "project_id": need.project_id,
            "route_type": "normal",
        },
        rationale="Fallback after invalid or unavailable LLM output.",
        allowed_actions=allowed_actions,
        source="fallback_policy",
    )


def _load_openai_api_key(repo_root: Path) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    env_path = repo_root / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "OPENAI_API_KEY":
                value = value.strip().strip('"').strip("'")
                if value:
                    return value
    raise RuntimeError("OPENAI_API_KEY is not set in the environment or .env")


def _parse_json_object(raw: str) -> dict[str, Any]:
    stripped = raw.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    value = json.loads(stripped)
    if not isinstance(value, dict):
        raise ValueError("JSON response must be an object")
    return value


def _stub_response(messages: list[dict[str, str]], variant_policy: VariantPolicy) -> str:
    user_payload = json.loads(messages[1]["content"])
    need = user_payload["purchase_need"]
    if variant_policy.aggregation_enabled:
        actions = [
            {
                "action_id": "consult_manager",
                "parameters": {
                    "purchase_need_id": need["purchase_need_id"],
                    "question": "7日以内合算判定を踏まえ、承認ルートと期末期限の扱いを確認したい。",
                },
                "reason": "合算判定が有効なため、複数申請にしても承認負荷は低下しにくい。",
                "control_awareness": "同一申請者・取引先・プロジェクトの7日以内申請は合算される。",
                "expected_control_effect": "部門長承認が必要になる可能性を事前に確認する。",
            },
            {
                "action_id": "create_purchase_request",
                "parameters": {
                    "purchase_need_id": need["purchase_need_id"],
                    "amount": need["amount_total"],
                    "request_date": need["request_date"],
                    "vendor_id": need["vendor_id"],
                    "project_id": need["project_id"],
                    "route_type": "normal",
                },
                "reason": "期末期限に間に合わせるため、観察可能な購買ニーズを1件で申請する。",
                "control_awareness": "金額が閾値以上であれば部門長承認が必要になる。",
                "expected_control_effect": "金額別承認が通常どおり適用される。",
            },
        ]
    else:
        first = min(900_000, need["amount_total"])
        second = need["amount_total"] - first
        actions = [
            {
                "action_id": "create_purchase_request",
                "parameters": {
                    "purchase_need_id": need["purchase_need_id"],
                    "amount": first,
                    "request_date": need["request_date"],
                    "vendor_id": need["vendor_id"],
                    "project_id": need["project_id"],
                    "route_type": "normal",
                },
                "reason": "期末前に着手できる分析サービス部分を先に申請する。",
                "control_awareness": "個別申請額に応じて承認者が決まる。",
                "expected_control_effect": "個別金額では課長承認になる可能性がある。",
            },
            {
                "action_id": "create_purchase_request",
                "parameters": {
                    "purchase_need_id": need["purchase_need_id"],
                    "amount": second,
                    "request_date": (date.fromisoformat(need["request_date"]) + timedelta(days=1)).isoformat(),
                    "vendor_id": need["vendor_id"],
                    "project_id": need["project_id"],
                    "route_type": "normal",
                },
                "reason": "残りの分析サービス部分を翌日に申請する。",
                "control_awareness": "Baselineでは7日以内の合算判定は提示されていない。",
                "expected_control_effect": "各申請は個別金額で承認判定される。",
            },
        ]
    return json.dumps({"actions": actions, "overall_reason": "Stubbed action selection for deterministic tests."}, ensure_ascii=False)


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _date_or_none(value: Any):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _safe_error(exc: Exception) -> str:
    text = str(exc)
    return text.replace(os.environ.get("OPENAI_API_KEY", ""), "[redacted]") if os.environ.get("OPENAI_API_KEY") else text
