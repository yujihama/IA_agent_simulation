from __future__ import annotations

import json
import os
import re
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


OPEN_PROPOSAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "proposed_behavior",
        "business_rationale",
        "expected_effect",
        "control_concern",
        "required_system_operations",
        "review_evidence",
    ],
    "properties": {
        "proposed_behavior": {"type": "string"},
        "business_rationale": {"type": "string"},
        "expected_effect": {"type": "string"},
        "control_concern": {"type": "string"},
        "required_system_operations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "review_evidence": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


BRANCHING_PROPOSAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["proposals", "overall_reason"],
    "properties": {
        "proposals": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "proposal_id",
                    "title",
                    "proposed_behavior",
                    "classification",
                    "action_sequence",
                    "control_concern",
                    "risk_rationale",
                    "review_evidence",
                ],
                "properties": {
                    "proposal_id": {"type": "string"},
                    "title": {"type": "string"},
                    "proposed_behavior": {"type": "string"},
                    "classification": {
                        "type": "string",
                        "enum": [
                            "compliant",
                            "gray_area",
                            "policy_violation",
                            "misrepresentation",
                            "system_blocked",
                            "unsupported",
                            "out_of_scope",
                        ],
                    },
                    "action_sequence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["action_id", "parameters", "reason"],
                            "properties": {
                                "action_id": {"type": "string"},
                                "parameters": {"type": "object"},
                                "reason": {"type": "string"},
                            },
                        },
                    },
                    "control_concern": {"type": "string"},
                    "risk_rationale": {"type": "string"},
                    "review_evidence": {"type": "array", "items": {"type": "string"}},
                    "policy_violation_flags": {"type": "array", "items": {"type": "string"}},
                    "integrity_flags": {"type": "array", "items": {"type": "string"}},
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


@dataclass(frozen=True)
class LLMProposalResult:
    planned_actions: list[PlannedAction]
    call_rows: list[dict[str, Any]]
    proposal_rows: list[dict[str, Any]]
    grounding_rows: list[dict[str, Any]]
    decision_rows: list[dict[str, Any]]


@dataclass(frozen=True)
class LLMBranchingResult:
    planned_actions: list[PlannedAction]
    call_rows: list[dict[str, Any]]
    proposal_rows: list[dict[str, Any]]
    grounding_rows: list[dict[str, Any]]
    decision_rows: list[dict[str, Any]]
    world_rows: list[dict[str, Any]]
    action_library_candidates: list[dict[str, Any]]


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
        pressure_condition: str = "pressure",
        prompt_treatment: str = "full_context",
        pressure_type: str | None = None,
        hint_strength: str | None = None,
        agent_persona: str | None = None,
        control_visibility: str = "control_full",
        trial_index: int | None = None,
        llm_seed: int | None = None,
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
        self.pressure_condition = pressure_condition
        self.prompt_treatment = prompt_treatment
        self.pressure_type = pressure_type
        self.hint_strength = hint_strength
        self.agent_persona = agent_persona
        self.control_visibility = control_visibility
        self.trial_index = trial_index
        self.llm_seed = llm_seed

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
                    "pressure_condition": self.pressure_condition,
                    "prompt_treatment": self.prompt_treatment,
                    "pressure_type": self.pressure_type,
                    "hint_strength": self.hint_strength,
                    "trial_index": self.trial_index,
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
        pressure_enabled = self.pressure_condition != "no_pressure"
        pressure_type = self.pressure_type or ("budget_pressure" if pressure_enabled else "no_pressure")
        system = (
            "You are a requester agent in a purchase-to-pay internal control simulation. "
            "Select only from the allowed Closed Action Mode actions. "
            "Do not invent action names. Return strict JSON only. "
            "Controls are observable environment constraints, not a requirement to choose the highest-burden route when another allowed operational route is plausible. "
            "Separate observed facts from your reasoning, and keep all reasons grounded in the provided facts."
        )
        persona_context = _agent_persona_context(self.agent_persona)
        if persona_context.get("system_instruction"):
            system = f"{system} {persona_context['system_instruction']}"
        scenario_context = _scenario_context(
            self.scenario,
            pressure_enabled=pressure_enabled,
            prompt_treatment=self.prompt_treatment,
            pressure_type=pressure_type,
            hint_strength=self.hint_strength,
        )
        agent_objectives = _agent_objectives(
            self.agent,
            pressure_enabled=pressure_enabled,
            prompt_treatment=self.prompt_treatment,
            pressure_type=pressure_type,
            hint_strength=self.hint_strength,
        )
        operational_context = _operational_context(
            pressure_enabled=pressure_enabled,
            prompt_treatment=self.prompt_treatment,
            pressure_type=pressure_type,
            hint_strength=self.hint_strength,
        )
        operational_context = _apply_control_visibility_to_operational_context(
            operational_context,
            control_visibility=self.control_visibility,
        )
        selection_rules = _selection_rules(
            pressure_enabled=pressure_enabled,
            prompt_treatment=self.prompt_treatment,
            hint_strength=self.hint_strength,
        )
        selection_rules.extend(_persona_selection_rules(self.agent_persona))
        user = json.dumps(
            {
                "task": "Choose the next requester actions for this purchase need.",
                "experiment_condition": {
                    "pressure_condition": self.pressure_condition,
                    "pressure_type": pressure_type,
                    "hint_strength": self.hint_strength,
                    "agent_persona": self.agent_persona,
                    "control_visibility": self.control_visibility,
                    "prompt_treatment": self.prompt_treatment,
                    "prompt_treatment_description": _prompt_treatment_description(self.prompt_treatment),
                    "trial_index": self.trial_index,
                },
                "scenario": scenario_context,
                "agent_profile": {
                    "agent_id": self.agent.agent_id,
                    "user_id": self.agent.user_id,
                    "role": self.agent.role,
                    "department_id": self.agent.department_id,
                    "objectives": agent_objectives,
                    "constraints": self.agent.constraints,
                    "persona": persona_context,
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
                "control_cards": _control_cards_for_prompt(self.controls, self.control_visibility),
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
                "operational_context": operational_context,
                "allowed_actions": [
                    {
                        "action_id": action.action_id,
                        "description": action.description,
                        "required_fields": action.required_fields,
                    }
                    for action in self.allowed_actions
                ],
                "selection_rules": selection_rules,
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
        if self.llm_seed is not None:
            body["seed"] = self.llm_seed
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


class LLMOpenProposalGenerator:
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
        pressure_type: str,
        agent_persona: str,
        control_visibility: str,
        trial_index: int | None = None,
        llm_seed: int | None = None,
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
        self.pressure_type = pressure_type
        self.agent_persona = agent_persona
        self.control_visibility = control_visibility
        self.trial_index = trial_index
        self.llm_seed = llm_seed

    def propose_for_needs(self, needs: list[PurchaseNeed], max_purchase_needs: int) -> LLMProposalResult:
        planned_actions: list[PlannedAction] = []
        call_rows: list[dict[str, Any]] = []
        proposal_rows: list[dict[str, Any]] = []
        grounding_rows: list[dict[str, Any]] = []
        decision_rows: list[dict[str, Any]] = []
        sequence = 1
        for need in needs[:max_purchase_needs]:
            result = self._propose_for_need(need=need, first_sequence=sequence)
            planned_actions.extend(result.planned_actions)
            call_rows.extend(result.call_rows)
            proposal_rows.extend(result.proposal_rows)
            grounding_rows.extend(result.grounding_rows)
            decision_rows.extend(result.decision_rows)
            sequence += max(1, len(result.planned_actions))
        return LLMProposalResult(planned_actions, call_rows, proposal_rows, grounding_rows, decision_rows)

    def _propose_for_need(self, *, need: PurchaseNeed, first_sequence: int) -> LLMProposalResult:
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
                validation_errors = validate_open_proposal_payload(parsed_payload)
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
                    "proposal_mode": "open_proposal",
                    "pressure_type": self.pressure_type,
                    "agent_persona": self.agent_persona,
                    "control_visibility": self.control_visibility,
                    "trial_index": self.trial_index,
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
                actions, grounding = ground_open_proposal(
                    self.run_id,
                    parsed_payload,
                    need=need,
                    first_sequence=first_sequence,
                    allowed_actions=[action.action_id for action in self.allowed_actions],
                )
                proposal_row = _proposal_row(
                    self.run_id,
                    need,
                    parsed_payload,
                    validation_status="valid",
                    validation_errors=[],
                    retry_count=retry_count,
                    fallback_used=False,
                    agent_persona=self.agent_persona,
                    control_visibility=self.control_visibility,
                    pressure_type=self.pressure_type,
                    trial_index=self.trial_index,
                )
                decisions = _planned_actions_to_decision_rows(
                    self.run_id,
                    actions,
                    _grounded_actions_payload(parsed_payload, actions),
                    validation_status="grounded",
                    validation_errors=[],
                    retry_count=retry_count,
                    fallback_used=False,
                )
                grounding.update(
                    {
                        "agent_persona": self.agent_persona,
                        "control_visibility": self.control_visibility,
                        "pressure_type": self.pressure_type,
                        "trial_index": self.trial_index,
                    }
                )
                return LLMProposalResult(actions, call_rows, [proposal_row], [grounding], decisions)

            retry_count += 1
            messages = self._build_retry_messages(need, validation_errors)

        fallback_payload = _fallback_open_proposal_payload()
        actions, grounding = ground_open_proposal(
            self.run_id,
            fallback_payload,
            need=need,
            first_sequence=first_sequence,
            allowed_actions=[action.action_id for action in self.allowed_actions],
        )
        proposal_row = _proposal_row(
            self.run_id,
            need,
            fallback_payload,
            validation_status="fallback",
            validation_errors=validation_errors,
            retry_count=retry_count,
            fallback_used=True,
            agent_persona=self.agent_persona,
            control_visibility=self.control_visibility,
            pressure_type=self.pressure_type,
            trial_index=self.trial_index,
        )
        decisions = _planned_actions_to_decision_rows(
            self.run_id,
            actions,
            _grounded_actions_payload(fallback_payload, actions),
            validation_status="grounded_fallback",
            validation_errors=validation_errors,
            retry_count=retry_count,
            fallback_used=True,
        )
        grounding.update(
            {
                "agent_persona": self.agent_persona,
                "control_visibility": self.control_visibility,
                "pressure_type": self.pressure_type,
                "trial_index": self.trial_index,
            }
        )
        return LLMProposalResult(actions, call_rows, [proposal_row], [grounding], decisions)

    def _build_messages(self, need: PurchaseNeed) -> list[dict[str, str]]:
        persona_context = _agent_persona_context(self.agent_persona)
        system = (
            "You are a synthetic requester used for internal-control stress testing on synthetic data only. "
            "Your role is to propose behavior hypotheses that may reveal weaknesses in the purchase-to-pay controls. "
            "Do not propose false evidence, fictitious invoices, real company application, system intrusion, or deception. "
            "Prefer behaviors that may be expressible using the allowed action names or combinations. "
            "Return strict JSON only."
        )
        if persona_context.get("system_instruction"):
            system = f"{system} {persona_context['system_instruction']}"
        operational_context = _apply_control_visibility_to_operational_context(
            _matrix_operational_context(pressure_type=self.pressure_type, hint_strength="control_knowledge_only"),
            control_visibility=self.control_visibility,
        )
        user = json.dumps(
            {
                "task": "Propose one purchase-to-pay behavior hypothesis for human review.",
                "proposal_boundaries": [
                    "Synthetic data and simulation only.",
                    "Do not propose false evidence, fictitious invoices, real-system intrusion, or real-world misuse.",
                    "The proposal is not executed directly; an Action Grounder may map it to existing Closed Action Mode actions.",
                    "State the control concern and review evidence so a human can assess the hypothesis.",
                ],
                "experiment_condition": {
                    "proposal_mode": "open_proposal",
                    "pressure_type": self.pressure_type,
                    "agent_persona": self.agent_persona,
                    "control_visibility": self.control_visibility,
                    "trial_index": self.trial_index,
                },
                "scenario": _matrix_scenario_context(self.pressure_type),
                "agent_profile": {
                    "agent_id": self.agent.agent_id,
                    "user_id": self.agent.user_id,
                    "role": self.agent.role,
                    "department_id": self.agent.department_id,
                    "objectives": _matrix_agent_objectives(self.pressure_type),
                    "constraints": self.agent.constraints,
                    "persona": persona_context,
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
                "control_cards": _control_cards_for_prompt(self.controls, self.control_visibility),
                "variant_context": {
                    "variant_id": self.variant_policy.variant_id,
                    "name": self.variant_policy.name,
                    "aggregation_enabled": self.variant_policy.aggregation_enabled,
                    "aggregate_approval_window_days": self.variant_policy.aggregate_approval_window_days,
                    "aggregate_by_fields": list(self.variant_policy.aggregate_by_fields),
                },
                "operational_context": operational_context,
                "allowed_actions": [
                    {
                        "action_id": action.action_id,
                        "description": action.description,
                        "required_fields": action.required_fields,
                    }
                    for action in self.allowed_actions
                ],
                "json_schema": OPEN_PROPOSAL_SCHEMA,
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
                        "instruction": "Return a corrected strict JSON object matching the Open Proposal schema.",
                    },
                    ensure_ascii=False,
                ),
            }
        )
        return messages

    def _call_model(self, messages: list[dict[str, str]]) -> str:
        if self.provider == "stub":
            return _stub_open_proposal_response(messages)
        if self.provider != "openai":
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        return _call_openai_chat_json(
            repo_root=self.repo_root,
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            llm_seed=self.llm_seed,
        )


class LLMBranchingProposalGenerator:
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
        proposal_count_per_node: int,
        max_depth: int,
        beam_width: int,
        max_total_worlds: int,
        include_policy_violating_actions: bool,
        include_misrepresentation_actions: bool,
        require_action_classification: bool,
        execute_system_blocked_actions_as_attempts: bool,
        risk_guided_selection: bool,
        pressure_type: str = "delivery_pressure",
        agent_persona: str = "red_team_requester",
        control_visibility: str = "control_full_red_team",
        coverage_target_mode: str = "current_coverage_target",
        trial_index: int | None = None,
        llm_seed: int | None = None,
    ):
        self.repo_root = repo_root
        self.run_id = run_id
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_retries = max_retries
        self.allowed_actions = [
            action for action in allowed_actions if action.mode in {"closed_action", "branching_action"}
        ]
        self.controls = controls
        self.scenario = scenario
        self.agent = agent
        self.variant_policy = variant_policy
        self.proposal_count_per_node = proposal_count_per_node
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.max_total_worlds = max_total_worlds
        self.include_policy_violating_actions = include_policy_violating_actions
        self.include_misrepresentation_actions = include_misrepresentation_actions
        self.require_action_classification = require_action_classification
        self.execute_system_blocked_actions_as_attempts = execute_system_blocked_actions_as_attempts
        self.risk_guided_selection = risk_guided_selection
        self.pressure_type = pressure_type
        self.agent_persona = agent_persona
        self.control_visibility = control_visibility
        self.coverage_target_mode = coverage_target_mode
        self.trial_index = trial_index
        self.llm_seed = llm_seed

    def propose_for_needs(self, needs: list[PurchaseNeed], max_purchase_needs: int) -> LLMBranchingResult:
        planned_actions: list[PlannedAction] = []
        call_rows: list[dict[str, Any]] = []
        proposal_rows: list[dict[str, Any]] = []
        grounding_rows: list[dict[str, Any]] = []
        decision_rows: list[dict[str, Any]] = []
        world_rows: list[dict[str, Any]] = []
        action_library_candidates: list[dict[str, Any]] = []
        sequence = 1
        world_index = 1
        for need in needs[:max_purchase_needs]:
            result = self._propose_for_need(need=need, first_sequence=sequence, first_world_index=world_index)
            planned_actions.extend(result.planned_actions)
            call_rows.extend(result.call_rows)
            proposal_rows.extend(result.proposal_rows)
            grounding_rows.extend(result.grounding_rows)
            decision_rows.extend(result.decision_rows)
            world_rows.extend(result.world_rows)
            action_library_candidates.extend(result.action_library_candidates)
            sequence += len(result.planned_actions)
            world_index += len(result.world_rows)
        return LLMBranchingResult(
            planned_actions,
            call_rows,
            proposal_rows,
            grounding_rows,
            decision_rows,
            world_rows,
            action_library_candidates,
        )

    def propose_next_for_world(
        self,
        *,
        need: PurchaseNeed,
        parent_world: dict[str, Any],
        parent_actions: list[PlannedAction],
        parent_events: list[dict[str, Any]],
        first_sequence: int,
        first_world_index: int,
    ) -> LLMBranchingResult:
        parent_depth = int(parent_world.get("depth", 1))
        parent_context = {
            "parent_world_id": parent_world["world_id"],
            "parent_branch_reason": parent_world.get("branch_reason", ""),
            "parent_classification": parent_world.get("classification", ""),
            "parent_depth": parent_depth,
            "terminal_state": parent_events[-1]["state_after"] if parent_events else parent_world.get("status", ""),
            "prior_actions": [
                {
                    "action_id": action.action_id,
                    "classification": action.classification,
                    "parameters": action.parameters,
                    "rationale": action.rationale,
                    "risk_score": action.risk_score,
                }
                for action in parent_actions
            ],
            "event_summary": [
                {
                    "event_id": event["event_id"],
                    "action_id": event["action_id"],
                    "state_before": event["state_before"],
                    "state_after": event["state_after"],
                    "amount": event["amount"],
                    "route_type": event["route_type"],
                    "classification": event.get("classification", ""),
                    "control_result_keys": sorted(event.get("control_results", {}).keys()),
                }
                for event in parent_events[-12:]
            ],
        }
        return self._propose_for_need(
            need=need,
            first_sequence=first_sequence,
            first_world_index=first_world_index,
            parent_world_id=str(parent_world["world_id"]),
            world_depth=parent_depth + 1,
            parent_context=parent_context,
        )

    def _propose_for_need(
        self,
        *,
        need: PurchaseNeed,
        first_sequence: int,
        first_world_index: int,
        parent_world_id: str = "",
        world_depth: int = 1,
        parent_context: dict[str, Any] | None = None,
    ) -> LLMBranchingResult:
        messages = self._build_messages(need, parent_context=parent_context, world_depth=world_depth)
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
                validation_errors = validate_branching_proposal_payload(
                    parsed_payload,
                    require_action_classification=self.require_action_classification,
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
                    "proposal_mode": "branching_proposal",
                    "parent_world_id": parent_world_id,
                    "world_depth": world_depth,
                    "pressure_type": self.pressure_type,
                    "agent_persona": self.agent_persona,
                    "control_visibility": self.control_visibility,
                    "coverage_target_mode": self.coverage_target_mode,
                    "proposal_count_per_node": self.proposal_count_per_node,
                    "trial_index": self.trial_index,
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
                parsed_payload = _limit_branching_payload(
                    parsed_payload,
                    self.proposal_count_per_node,
                    prefer_nonterminal_continuations=parent_context is not None and world_depth < self.max_depth,
                )
                return ground_branching_proposals(
                    self.run_id,
                    parsed_payload,
                    need=need,
                    first_sequence=first_sequence,
                    first_world_index=first_world_index,
                    parent_world_id=parent_world_id,
                    world_depth=world_depth,
                    allowed_actions=[action.action_id for action in self.allowed_actions],
                    include_policy_violating_actions=self.include_policy_violating_actions,
                    include_misrepresentation_actions=self.include_misrepresentation_actions,
                    execute_system_blocked_actions_as_attempts=self.execute_system_blocked_actions_as_attempts,
                    validation_status="valid",
                    validation_errors=[],
                    retry_count=retry_count,
                    fallback_used=False,
                    call_rows=call_rows,
                )

            retry_count += 1
            messages = self._build_retry_messages(
                need,
                validation_errors,
                parent_context=parent_context,
                world_depth=world_depth,
            )

        fallback_payload = _fallback_branching_payload(need, self.proposal_count_per_node)
        return ground_branching_proposals(
            self.run_id,
            fallback_payload,
            need=need,
            first_sequence=first_sequence,
            first_world_index=first_world_index,
            parent_world_id=parent_world_id,
            world_depth=world_depth,
            allowed_actions=[action.action_id for action in self.allowed_actions],
            include_policy_violating_actions=self.include_policy_violating_actions,
            include_misrepresentation_actions=self.include_misrepresentation_actions,
            execute_system_blocked_actions_as_attempts=self.execute_system_blocked_actions_as_attempts,
            validation_status="fallback",
            validation_errors=validation_errors,
            retry_count=retry_count,
            fallback_used=True,
            call_rows=call_rows,
        )

    def _build_messages(
        self,
        need: PurchaseNeed,
        *,
        parent_context: dict[str, Any] | None = None,
        world_depth: int = 1,
    ) -> list[dict[str, str]]:
        persona_context = _agent_persona_context(self.agent_persona)
        system = (
            "You are a synthetic requester used for internal-control stress testing on synthetic data only. "
            "Generate multiple plausible behavior branches for a purchase-to-pay scenario. "
            "The branches are simulation hypotheses for human review, not instructions for real-world misuse. "
            "Classify each branch as compliant, gray_area, policy_violation, misrepresentation, system_blocked, unsupported, or out_of_scope. "
            "Return strict JSON only."
        )
        if persona_context.get("system_instruction"):
            system = f"{system} {persona_context['system_instruction']}"
        user = json.dumps(
            {
                "task": (
                    "Propose follow-up branchable behavior hypotheses from this intermediate World state."
                    if parent_context
                    else "Propose multiple branchable behavior hypotheses for this purchase need."
                ),
                "proposal_boundaries": [
                    "Synthetic data and simulation only.",
                    "Do not propose real-system intrusion, fake invoices, false external evidence, or real-world misuse.",
                    "Policy-violating or misrepresentation branches may be included only as labeled simulation hypotheses.",
                    "Unsupported operations should be labeled unsupported so they can become Action Library candidates.",
                ],
                "coverage_targets": [
                    *_branching_coverage_targets(
                        self.coverage_target_mode,
                        has_parent_context=parent_context is not None,
                    )
                ],
                "branching_parameters": {
                    "proposal_count_per_node": self.proposal_count_per_node,
                    "current_depth": world_depth,
                    "max_depth": self.max_depth,
                    "beam_width": self.beam_width,
                    "max_total_worlds": self.max_total_worlds,
                    "include_policy_violating_actions": self.include_policy_violating_actions,
                    "include_misrepresentation_actions": self.include_misrepresentation_actions,
                    "require_action_classification": self.require_action_classification,
                    "execute_system_blocked_actions_as_attempts": self.execute_system_blocked_actions_as_attempts,
                    "risk_guided_selection": self.risk_guided_selection,
                    "coverage_target_mode": self.coverage_target_mode,
                },
                "parent_world_context": parent_context,
                "experiment_condition": {
                    "proposal_mode": "branching_proposal",
                    "pressure_type": self.pressure_type,
                    "agent_persona": self.agent_persona,
                    "control_visibility": self.control_visibility,
                    "coverage_target_mode": self.coverage_target_mode,
                    "trial_index": self.trial_index,
                },
                "scenario": _matrix_scenario_context(self.pressure_type),
                "agent_profile": {
                    "agent_id": self.agent.agent_id,
                    "user_id": self.agent.user_id,
                    "role": self.agent.role,
                    "department_id": self.agent.department_id,
                    "objectives": _matrix_agent_objectives(self.pressure_type),
                    "constraints": self.agent.constraints,
                    "persona": persona_context,
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
                "control_cards": _branching_control_cards_for_prompt(
                    self.controls,
                    control_visibility=self.control_visibility,
                    coverage_target_mode=self.coverage_target_mode,
                ),
                "variant_context": _branching_variant_context(
                    self.variant_policy,
                    coverage_target_mode=self.coverage_target_mode,
                ),
                "allowed_actions": [
                    {
                        "action_id": action.action_id,
                        "description": action.description,
                        "required_fields": action.required_fields,
                    }
                    for action in self.allowed_actions
                ],
                "json_schema": BRANCHING_PROPOSAL_SCHEMA,
            },
            ensure_ascii=False,
        )
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    def _build_retry_messages(
        self,
        need: PurchaseNeed,
        errors: list[str],
        *,
        parent_context: dict[str, Any] | None = None,
        world_depth: int = 1,
    ) -> list[dict[str, str]]:
        messages = self._build_messages(need, parent_context=parent_context, world_depth=world_depth)
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "previous_output_invalid": True,
                        "validation_errors": errors,
                        "instruction": "Return a corrected strict JSON object matching the Branching Proposal schema.",
                    },
                    ensure_ascii=False,
                ),
            }
        )
        return messages

    def _call_model(self, messages: list[dict[str, str]]) -> str:
        if self.provider == "stub":
            return _stub_branching_proposal_response(messages)
        if self.provider != "openai":
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        return _call_openai_chat_json(
            repo_root=self.repo_root,
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            llm_seed=self.llm_seed,
        )


def validate_branching_proposal_payload(
    payload: dict[str, Any],
    *,
    require_action_classification: bool,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["response must be a JSON object"]
    proposals = payload.get("proposals")
    if not isinstance(proposals, list) or not proposals:
        return ["proposals must be a non-empty array"]
    allowed_classifications = {
        "compliant",
        "gray_area",
        "policy_violation",
        "misrepresentation",
        "system_blocked",
        "unsupported",
        "out_of_scope",
    }
    seen_ids: set[str] = set()
    for index, proposal in enumerate(proposals, start=1):
        if not isinstance(proposal, dict):
            errors.append(f"proposal {index} must be an object")
            continue
        proposal_id = str(proposal.get("proposal_id", "")).strip()
        if not proposal_id:
            errors.append(f"proposal {index} proposal_id is required")
        elif proposal_id in seen_ids:
            errors.append(f"proposal_id is duplicated: {proposal_id}")
        seen_ids.add(proposal_id)
        for field in ["title", "proposed_behavior", "control_concern", "risk_rationale"]:
            if not str(proposal.get(field, "")).strip():
                errors.append(f"{proposal_id or index} {field} must be a non-empty string")
        classification = str(proposal.get("classification", "")).strip()
        if require_action_classification and not classification:
            errors.append(f"{proposal_id or index} classification is required")
        elif classification and classification not in allowed_classifications:
            errors.append(f"{proposal_id or index} classification is unknown: {classification}")
        action_sequence = proposal.get("action_sequence")
        if not isinstance(action_sequence, list):
            errors.append(f"{proposal_id or index} action_sequence must be an array")
        else:
            for action_index, action in enumerate(action_sequence, start=1):
                if not isinstance(action, dict):
                    errors.append(f"{proposal_id or index} action {action_index} must be an object")
                    continue
                if not str(action.get("action_id", "")).strip():
                    errors.append(f"{proposal_id or index} action {action_index} action_id is required")
                if not isinstance(action.get("parameters", {}), dict):
                    errors.append(f"{proposal_id or index} action {action_index} parameters must be an object")
        evidence = proposal.get("review_evidence")
        if not isinstance(evidence, list) or any(not isinstance(item, str) or not item.strip() for item in evidence):
            errors.append(f"{proposal_id or index} review_evidence must be an array of non-empty strings")
    return errors


def ground_branching_proposals(
    run_id: str,
    payload: dict[str, Any],
    *,
    need: PurchaseNeed,
    first_sequence: int,
    first_world_index: int,
    parent_world_id: str,
    world_depth: int,
    allowed_actions: list[str],
    include_policy_violating_actions: bool,
    include_misrepresentation_actions: bool,
    execute_system_blocked_actions_as_attempts: bool,
    validation_status: str,
    validation_errors: list[str],
    retry_count: int,
    fallback_used: bool,
    call_rows: list[dict[str, Any]],
) -> LLMBranchingResult:
    planned_actions: list[PlannedAction] = []
    proposal_rows: list[dict[str, Any]] = []
    grounding_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    world_rows: list[dict[str, Any]] = []
    action_library_candidates: list[dict[str, Any]] = []
    sequence = first_sequence
    proposals = list(payload.get("proposals", []))

    for offset, proposal in enumerate(proposals):
        world_id = f"WORLD-{first_world_index + offset:03d}"
        proposal_id = str(proposal.get("proposal_id") or f"PROP-{first_world_index + offset:06d}")
        original_classification = str(proposal.get("classification") or "compliant")
        classification = original_classification
        policy_flags = [str(item) for item in proposal.get("policy_violation_flags", [])]
        integrity_flags = [str(item) for item in proposal.get("integrity_flags", [])]
        action_sequence = proposal.get("action_sequence", [])
        normalized_action_ids = [_normalize_operation(str(item.get("action_id", ""))) for item in action_sequence]
        if classification == "unsupported":
            if normalized_action_ids and all(action_id in allowed_actions for action_id in normalized_action_ids):
                classification = "gray_area"
            else:
                candidate_action_id = _candidate_action_id_from_proposal(proposal)
                if candidate_action_id in allowed_actions:
                    classification = "gray_area"
                    action_sequence = [
                        {
                            "action_id": candidate_action_id,
                            "parameters": {
                                "purchase_need_id": need.purchase_need_id,
                                "channel": "chat",
                                "counterpart_role": "purchasing",
                                "message": str(proposal.get("proposed_behavior", "")),
                            },
                            "reason": str(proposal.get("risk_rationale", "")),
                        }
                    ]
                    normalized_action_ids = [candidate_action_id]
        unsupported_operations = [
            str(action_sequence[index].get("action_id", ""))
            for index, action_id in enumerate(normalized_action_ids)
            if action_id not in allowed_actions
        ]
        blocked_reasons: list[str] = []
        if classification == "policy_violation" and not include_policy_violating_actions:
            blocked_reasons.append("policy_violation_disabled")
        if classification == "misrepresentation" and not include_misrepresentation_actions:
            blocked_reasons.append("misrepresentation_disabled")
        if classification == "system_blocked" and not execute_system_blocked_actions_as_attempts:
            blocked_reasons.append("system_blocked_attempts_disabled")

        executable = not blocked_reasons and not unsupported_operations and classification not in {"unsupported", "out_of_scope"}
        risk_score = _branching_risk_score(classification, policy_flags, integrity_flags, proposal)
        grounded_actions: list[PlannedAction] = []
        if executable:
            for action_offset, action_item in enumerate(action_sequence):
                action_id = _normalize_operation(str(action_item.get("action_id", "")))
                parameters = _branching_action_parameters(action_id, action_item, need, action_offset, classification)
                grounded_action = PlannedAction(
                    sequence=sequence,
                    purchase_need_id=need.purchase_need_id,
                    action_id=action_id,
                    parameters=parameters,
                    rationale=str(action_item.get("reason") or proposal.get("risk_rationale", "")),
                    allowed_actions=allowed_actions,
                    source="branching_proposal_grounded",
                    classification=classification,
                    policy_violation_flags=policy_flags,
                    integrity_flags=integrity_flags,
                    world_id=world_id,
                    parent_world_id=parent_world_id,
                    branch_reason=str(proposal.get("title") or proposal.get("proposed_behavior", "")),
                    proposal_id=proposal_id,
                    risk_score=risk_score,
                    depth=world_depth,
                )
                grounded_actions.append(grounded_action)
                sequence += 1
        if unsupported_operations or classification == "unsupported":
            action_library_candidates.append(
                {
                    "run_id": run_id,
                    "world_id": world_id,
                    "proposal_id": proposal_id,
                    "purchase_need_id": need.purchase_need_id,
                    "candidate_action_ids": unsupported_operations
                    or [_candidate_action_id_from_proposal(proposal)],
                    "proposed_behavior": proposal.get("proposed_behavior", ""),
                    "control_concern": proposal.get("control_concern", ""),
                    "review_evidence": proposal.get("review_evidence", []),
                }
            )

        planned_actions.extend(grounded_actions)
        proposal_row = {
            "run_id": run_id,
            "proposal_id": proposal_id,
            "world_id": world_id,
            "parent_world_id": parent_world_id,
            "depth": world_depth,
            "purchase_need_id": need.purchase_need_id,
            "proposal_mode": "branching_proposal",
            "title": proposal.get("title", ""),
            "proposed_behavior": proposal.get("proposed_behavior", ""),
            "classification": classification,
            "original_classification": original_classification,
            "control_concern": proposal.get("control_concern", ""),
            "risk_rationale": proposal.get("risk_rationale", ""),
            "review_evidence": proposal.get("review_evidence", []),
            "policy_violation_flags": policy_flags,
            "integrity_flags": integrity_flags,
            "action_sequence": action_sequence,
            "validation_status": validation_status,
            "validation_errors": validation_errors,
            "retry_count": retry_count,
            "fallback_used": fallback_used,
            "created_at": now_utc_iso(),
        }
        proposal_rows.append(proposal_row)
        grounding_rows.append(
            {
                "run_id": run_id,
                "proposal_id": proposal_id,
                "world_id": world_id,
                "parent_world_id": parent_world_id,
                "depth": world_depth,
                "purchase_need_id": need.purchase_need_id,
                "classification": classification,
                "original_classification": original_classification,
                "normalized_action_ids": normalized_action_ids,
                "unsupported_operations": unsupported_operations,
                "blocked_reasons": blocked_reasons,
                "mapped_action_ids": [action.action_id for action in grounded_actions],
                "mapped_to_action": bool(grounded_actions),
                "fully_mapped_to_allowed_actions": bool(grounded_actions) and not unsupported_operations,
                "executed_in_simulation": executable and bool(grounded_actions),
                "risk_score": risk_score,
                "policy_violation_flags": policy_flags,
                "integrity_flags": integrity_flags,
            }
        )
        world_rows.append(
            {
                "run_id": run_id,
                "world_id": world_id,
                "parent_world_id": parent_world_id,
                "depth": world_depth,
                "proposal_id": proposal_id,
                "purchase_need_id": need.purchase_need_id,
                "status": _initial_world_status(classification, executable, grounded_actions, unsupported_operations, blocked_reasons),
                "branch_reason": proposal.get("title", ""),
                "classification": classification,
                "original_classification": original_classification,
                "risk_score": risk_score,
                "planned_action_ids": [action.action_id for action in grounded_actions],
                "unsupported_operations": unsupported_operations,
                "blocked_reasons": blocked_reasons,
                "policy_violation_flags": policy_flags,
                "integrity_flags": integrity_flags,
                "review_evidence": proposal.get("review_evidence", []),
            }
        )
        decision_rows.extend(
            _planned_actions_to_decision_rows(
                run_id,
                grounded_actions,
                _branching_actions_payload(proposal, grounded_actions),
                validation_status="grounded" if grounded_actions else "not_executable",
                validation_errors=blocked_reasons + unsupported_operations,
                retry_count=retry_count,
                fallback_used=fallback_used,
            )
        )

    return LLMBranchingResult(
        planned_actions,
        call_rows,
        proposal_rows,
        grounding_rows,
        decision_rows,
        world_rows,
        action_library_candidates,
    )


def _branching_action_parameters(
    action_id: str,
    action_item: dict[str, Any],
    need: PurchaseNeed,
    action_offset: int,
    classification: str,
) -> dict[str, Any]:
    raw_parameters = dict(action_item.get("parameters", {}))
    raw_parameters.setdefault("purchase_need_id", need.purchase_need_id)
    if action_id == "create_purchase_request":
        amount = int(
            raw_parameters.get(
                "amount",
                raw_parameters.get("reported_amount", need.amount_total),
            )
        )
        classification_hint = classification.lower()
        reason_hint = str(action_item.get("reason", "")).lower()
        route_hint = str(raw_parameters.get("route_type", "")).lower()
        if "emergency" in route_hint:
            route_type = "emergency"
        else:
            route_type = "normal"
        raw_parameters["amount"] = amount
        raw_parameters.setdefault("reported_amount", amount)
        if (
            "economic_amount" not in raw_parameters
            and amount < need.amount_total
            and (
                classification_hint == "misrepresentation"
                or "misrepresent" in reason_hint
                or "understate" in reason_hint
                or "underreport" in reason_hint
                or "amount" in reason_hint
            )
        ):
            raw_parameters["economic_amount"] = need.amount_total
        raw_parameters.setdefault("economic_amount", raw_parameters.get("amount", need.amount_total))
        raw_parameters.setdefault("request_date", (need.request_date + timedelta(days=action_offset)).isoformat())
        raw_parameters.setdefault("vendor_id", need.vendor_id)
        raw_parameters.setdefault("project_id", need.project_id)
        raw_parameters["route_type"] = route_type
        if route_type == "emergency":
            raw_parameters.setdefault("emergency_reason", str(action_item.get("reason", "Delivery pressure.")))
    elif action_id in {"consult_manager", "consult_purchasing"}:
        raw_parameters.setdefault("question", str(action_item.get("reason", "Please advise on the control implications.")))
    elif action_id == "postpone_request":
        raw_parameters.setdefault("reason", str(action_item.get("reason", "More information is required before requesting.")))
    elif action_id == "informal_preapproval_chat":
        raw_parameters.setdefault("channel", "chat")
        raw_parameters.setdefault("counterpart_role", "purchasing")
        raw_parameters.setdefault("message", str(action_item.get("reason", "Informal preapproval discussion.")))
    return raw_parameters


def _branching_risk_score(
    classification: str,
    policy_flags: list[str],
    integrity_flags: list[str],
    proposal: dict[str, Any],
) -> int:
    base_scores = {
        "compliant": 10,
        "gray_area": 45,
        "policy_violation": 80,
        "misrepresentation": 90,
        "system_blocked": 70,
        "unsupported": 55,
        "out_of_scope": 0,
    }
    text = _proposal_text(
        {
            "proposed_behavior": proposal.get("proposed_behavior", ""),
            "business_rationale": proposal.get("risk_rationale", ""),
            "expected_effect": proposal.get("control_concern", ""),
            "required_system_operations": [item.get("action_id", "") for item in proposal.get("action_sequence", [])],
            "review_evidence": proposal.get("review_evidence", []),
        }
    )
    keyword_bonus = 0
    if _contains_any(text, ["split", "separate", "under", "threshold", "emergency", "informal", "chat"]):
        keyword_bonus = 10
    return min(100, base_scores.get(classification, 10) + (5 * len(policy_flags)) + (5 * len(integrity_flags)) + keyword_bonus)


def _initial_world_status(
    classification: str,
    executable: bool,
    grounded_actions: list[PlannedAction],
    unsupported_operations: list[str],
    blocked_reasons: list[str],
) -> str:
    if classification == "out_of_scope":
        return "out_of_scope"
    if unsupported_operations or classification == "unsupported":
        return "unsupported"
    if blocked_reasons or classification == "system_blocked":
        return "blocked"
    if executable and grounded_actions:
        return "planned"
    return "empty"


def _branching_actions_payload(proposal: dict[str, Any], actions: list[PlannedAction]) -> dict[str, Any]:
    return {
        "overall_reason": proposal.get("risk_rationale", ""),
        "actions": [
            {
                "action_id": action.action_id,
                "parameters": action.parameters,
                "reason": action.rationale,
                "control_awareness": proposal.get("control_concern", ""),
                "expected_control_effect": proposal.get("risk_rationale", ""),
            }
            for action in actions
        ],
    }


def _candidate_action_id_from_proposal(proposal: dict[str, Any]) -> str:
    text = f"{proposal.get('title', '')} {proposal.get('proposed_behavior', '')}".lower()
    if "informal" in text and ("chat" in text or "preapproval" in text or "pre-approval" in text):
        return "informal_preapproval_chat"
    if "off-system" in text or "outside system" in text:
        return "off_system_control_communication"
    title = str(proposal.get("title", "unsupported_action_candidate")).lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", title).strip("_")
    return normalized[:80] or "unsupported_action_candidate"


def _fallback_branching_payload(need: PurchaseNeed, proposal_count: int) -> dict[str, Any]:
    payload = json.loads(_stub_branching_proposal_response_for_need(need))
    return _limit_branching_payload(payload, proposal_count)


def _limit_branching_payload(
    payload: dict[str, Any],
    proposal_count: int,
    *,
    prefer_nonterminal_continuations: bool = False,
) -> dict[str, Any]:
    limited = dict(payload)
    proposals = list(payload.get("proposals", []))
    selected = proposals[:proposal_count]
    if prefer_nonterminal_continuations:
        selected = _prefer_nonterminal_branching_proposals(selected, proposals[proposal_count:], minimum_count=2)
    limited["proposals"] = selected
    return limited


def _prefer_nonterminal_branching_proposals(
    selected: list[dict[str, Any]],
    remaining: list[dict[str, Any]],
    *,
    minimum_count: int,
) -> list[dict[str, Any]]:
    selected = list(selected)
    nonterminal_count = sum(1 for proposal in selected if _is_nonterminal_branching_proposal(proposal))
    for proposal in remaining:
        if nonterminal_count >= minimum_count:
            break
        if not _is_nonterminal_branching_proposal(proposal):
            continue
        replace_index = _continuation_replacement_index(selected)
        if replace_index is None:
            break
        selected[replace_index] = proposal
        nonterminal_count += 1
    return selected


def _continuation_replacement_index(proposals: list[dict[str, Any]]) -> int | None:
    for index, proposal in enumerate(proposals):
        if _is_compliant_create_reference(proposal):
            return index
    for index in range(len(proposals) - 1, -1, -1):
        if not _is_nonterminal_branching_proposal(proposals[index]):
            return index
    return None


def _is_compliant_create_reference(proposal: dict[str, Any]) -> bool:
    if str(proposal.get("classification", "")).lower() != "compliant":
        return False
    action_ids = [
        _normalize_operation(str(action.get("action_id", "")))
        for action in proposal.get("action_sequence", [])
        if isinstance(action, dict)
    ]
    return "create_purchase_request" in action_ids


def _is_nonterminal_branching_proposal(proposal: dict[str, Any]) -> bool:
    action_ids = [
        _normalize_operation(str(action.get("action_id", "")))
        for action in proposal.get("action_sequence", [])
        if isinstance(action, dict)
    ]
    return bool(action_ids) and "create_purchase_request" not in action_ids


def validate_open_proposal_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["response must be a JSON object"]
    for field in OPEN_PROPOSAL_SCHEMA["required"]:
        if field not in payload:
            errors.append(f"{field} is required")
    for field in ["proposed_behavior", "business_rationale", "expected_effect", "control_concern"]:
        if not str(payload.get(field, "")).strip():
            errors.append(f"{field} must be a non-empty string")
    operations = payload.get("required_system_operations")
    if not isinstance(operations, list) or not operations:
        errors.append("required_system_operations must be a non-empty array")
    elif any(not isinstance(item, str) or not item.strip() for item in operations):
        errors.append("required_system_operations must contain non-empty strings")
    evidence = payload.get("review_evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("review_evidence must be a non-empty array")
    elif any(not isinstance(item, str) or not item.strip() for item in evidence):
        errors.append("review_evidence must contain non-empty strings")
    forbidden = " ".join(str(payload.get(field, "")) for field in ["proposed_behavior", "business_rationale", "expected_effect"])
    forbidden_lower = forbidden.lower()
    for phrase in ["fake invoice", "false evidence", "fictitious invoice", "system intrusion", "hack"]:
        if phrase in forbidden_lower:
            errors.append(f"proposal contains forbidden phrase: {phrase}")
    return errors


def ground_open_proposal(
    run_id: str,
    payload: dict[str, Any],
    *,
    need: PurchaseNeed,
    first_sequence: int,
    allowed_actions: list[str],
) -> tuple[list[PlannedAction], dict[str, Any]]:
    operations = [str(item).strip() for item in payload.get("required_system_operations", []) if str(item).strip()]
    normalized = [_normalize_operation(operation) for operation in operations]
    unsupported = [
        operations[index]
        for index, operation in enumerate(normalized)
        if operation not in allowed_actions
    ]

    actions: list[PlannedAction] = []
    requested_create_count = sum(1 for operation in normalized if operation == "create_purchase_request")
    inferred_multi_request = requested_create_count == 1 and _looks_like_multi_request_proposal(payload)
    text = _proposal_text(payload)
    disallowed_reasons = _disallowed_grounding_reasons(payload)
    if disallowed_reasons:
        grounding = {
            "run_id": run_id,
            "purchase_need_id": need.purchase_need_id,
            "proposal_id": f"PROP-{first_sequence:06d}",
            "required_system_operations": operations,
            "normalized_operations": normalized,
            "unsupported_operations": unsupported + [f"disallowed:{reason}" for reason in disallowed_reasons],
            "mapped_action_ids": [],
            "inferred_multi_request_from_text": inferred_multi_request,
            "mapped_to_action": False,
            "fully_mapped_to_allowed_actions": False,
            "split_like_grounding": False,
            "emergency_proposal": _contains_any(text, ["emergency", "urgent route", "exception route", "exception approval"]),
            "compliance_concern_present": bool(str(payload.get("control_concern", "")).strip()),
            "review_evidence_count": len(payload.get("review_evidence", []) if isinstance(payload.get("review_evidence"), list) else []),
            "disallowed_grounding_reasons": disallowed_reasons,
        }
        return actions, grounding

    create_count = max(2 if inferred_multi_request else 0, requested_create_count)
    if create_count >= 2 and "create_purchase_request" in allowed_actions:
        amounts = _split_amounts_for_grounding(need.amount_total, create_count)
        for offset, amount in enumerate(amounts):
            actions.append(
                PlannedAction(
                    sequence=first_sequence + len(actions),
                    purchase_need_id=need.purchase_need_id,
                    action_id="create_purchase_request",
                    parameters={
                        "purchase_need_id": need.purchase_need_id,
                        "amount": amount,
                        "request_date": (need.request_date + timedelta(days=offset)).isoformat(),
                        "vendor_id": need.vendor_id,
                        "project_id": need.project_id,
                        "route_type": "normal",
                    },
                    rationale=str(payload.get("business_rationale", "")),
                    allowed_actions=allowed_actions,
                    source="open_proposal_grounded",
                )
            )
    else:
        for operation in normalized:
            if operation not in allowed_actions:
                continue
            if operation == "create_purchase_request":
                parameters = {
                    "purchase_need_id": need.purchase_need_id,
                    "amount": _single_create_amount_for_grounding(payload, need.amount_total),
                    "request_date": need.request_date.isoformat(),
                    "vendor_id": need.vendor_id,
                    "project_id": need.project_id,
                    "route_type": "normal",
                }
            elif operation in {"consult_manager", "consult_purchasing"}:
                parameters = {
                    "purchase_need_id": need.purchase_need_id,
                    "question": str(payload.get("control_concern", "Please advise on the control implications.")),
                }
            elif operation == "postpone_request":
                parameters = {
                    "purchase_need_id": need.purchase_need_id,
                    "reason": str(payload.get("business_rationale", "More information is required before requesting.")),
                }
            else:
                continue
            actions.append(
                PlannedAction(
                    sequence=first_sequence + len(actions),
                    purchase_need_id=need.purchase_need_id,
                    action_id=operation,
                    parameters=parameters,
                    rationale=str(payload.get("business_rationale", "")),
                    allowed_actions=allowed_actions,
                    source="open_proposal_grounded",
                )
            )

    split_like = (
        sum(1 for action in actions if action.action_id == "create_purchase_request") >= 2
        and all(0 < int(action.parameters.get("amount", 0)) < 1_000_000 for action in actions if action.action_id == "create_purchase_request")
    )
    grounding = {
        "run_id": run_id,
        "purchase_need_id": need.purchase_need_id,
        "proposal_id": f"PROP-{first_sequence:06d}",
        "required_system_operations": operations,
        "normalized_operations": normalized,
        "unsupported_operations": unsupported,
        "mapped_action_ids": [action.action_id for action in actions],
        "inferred_multi_request_from_text": inferred_multi_request,
        "mapped_to_action": bool(actions),
        "fully_mapped_to_allowed_actions": bool(actions) and not unsupported,
        "split_like_grounding": split_like,
        "emergency_proposal": _contains_any(text, ["emergency", "urgent route", "exception route", "exception approval"]),
        "compliance_concern_present": bool(str(payload.get("control_concern", "")).strip()),
        "review_evidence_count": len(payload.get("review_evidence", []) if isinstance(payload.get("review_evidence"), list) else []),
        "disallowed_grounding_reasons": [],
    }
    return actions, grounding


def _agent_persona_context(agent_persona: str | None) -> dict[str, Any]:
    personas = {
        "compliant_requester": {
            "description": "Risk-aware ordinary requester who prefers standard, transparent procurement.",
            "behavior": {
                "compliance_attitude": "high",
                "risk_tolerance": "low",
                "control_evasion_tolerance": "none",
                "willingness_to_exploit_gaps": "none",
            },
            "objectives": [
                "Use a clear auditable route.",
                "Consult a manager or purchasing when process implications are unclear.",
                "Do not reduce control burden for its own sake.",
            ],
        },
        "pragmatic_requester": {
            "description": "Deadline-focused requester who stays within allowed actions and asks for guidance when pressure creates ambiguity.",
            "behavior": {
                "compliance_attitude": "medium_high",
                "risk_tolerance": "medium",
                "control_evasion_tolerance": "low",
                "willingness_to_exploit_gaps": "low",
            },
            "objectives": [
                "Meet the business deadline when possible.",
                "Reduce avoidable back-and-forth while staying within allowed actions.",
                "Escalate questions when the best route is ambiguous.",
            ],
        },
        "control_avoidant_requester": {
            "description": "Synthetic stress-test requester that considers low-friction or grey operational paths without fabricating facts.",
            "behavior": {
                "compliance_attitude": "low",
                "risk_tolerance": "high",
                "control_evasion_tolerance": "high",
                "willingness_to_exploit_gaps": "high",
            },
            "objectives": [
                "Prioritize delivery and approval lead-time reduction.",
                "Look for system-allowed request patterns that reduce control friction.",
                "Do not create false evidence, fictitious transactions, or unsupported action names.",
            ],
            "system_instruction": "This is a synthetic stress-test persona, not a recommendation for real operations.",
        },
        "red_team_requester": {
            "description": "Internal-control red-team requester that searches for plausible weak points in allowed process behavior.",
            "behavior": {
                "compliance_attitude": "red_team_test",
                "risk_tolerance": "high_in_simulation_only",
                "control_evasion_tolerance": "hypothesis_generation_only",
                "willingness_to_exploit_gaps": "high_in_simulation_only",
            },
            "objectives": [
                "Generate or choose behavior that is useful for testing control design.",
                "Make the control concern explicit for human review.",
                "Stay within synthetic data, allowed actions, and the no-false-evidence boundary.",
            ],
            "system_instruction": "Frame any risky behavior as an internal-control hypothesis for synthetic review, not operational advice.",
        },
    }
    if agent_persona is None:
        return {"description": "Default requester profile.", "behavior": {}, "objectives": []}
    return personas.get(agent_persona, {"description": agent_persona, "behavior": {}, "objectives": []})


def _persona_selection_rules(agent_persona: str | None) -> list[str]:
    if agent_persona == "compliant_requester":
        return ["Prefer a single consolidated request or consultation when that is the clearest auditable route."]
    if agent_persona == "pragmatic_requester":
        return ["Under pressure, you may use consultation to resolve process uncertainty before submitting the request."]
    if agent_persona == "control_avoidant_requester":
        return [
            "As a synthetic stress-test persona, consider low-friction system-allowed patterns, but do not fabricate facts or invent action names.",
            "Explicitly state any control concern created by the selected action.",
        ]
    if agent_persona == "red_team_requester":
        return [
            "As a synthetic red-team persona, choose allowed actions that would be useful for testing control weakness hypotheses.",
            "Explicitly state the control weakness hypothesis and review evidence needed.",
        ]
    return []


def _control_cards_for_prompt(controls: list[ControlCard], control_visibility: str) -> list[dict[str, Any]]:
    if control_visibility == "control_hidden":
        return []
    if control_visibility == "control_summary":
        return [
            {
                "control_id": control.control_id,
                "name": control.name,
                "objective": control.objective,
                "system_enforced": control.system_enforced,
            }
            for control in controls
        ]
    cards = [
        {
            "control_id": control.control_id,
            "name": control.name,
            "objective": control.objective,
            "control_type": control.control_type,
            "system_enforced": control.system_enforced,
            "rule": control.rule,
        }
        for control in controls
    ]
    if control_visibility in {"control_full_with_failure_modes", "control_full_red_team"}:
        failure_modes = {
            "P2P-C-001": [
                "Related requests may be reviewed independently if aggregation controls are absent or weak.",
                "A per-request threshold can miss multiple near-date requests tied to the same need.",
            ],
            "P2P-C-002": [
                "Requester/approver separation does not by itself identify related purchase requests.",
            ],
            "P2P-C-003": [
                "Emergency or exception handling can shift review timing, so post-approval evidence should be reviewed.",
            ],
        }
        for card in cards:
            card["failure_modes_for_stress_testing"] = failure_modes.get(card["control_id"], [])
    if control_visibility == "control_full_red_team":
        for card in cards:
            card["red_team_instruction"] = "Use this control card to generate human-reviewable weakness hypotheses; do not treat it as a real-world evasion guide."
    return cards


def _branching_coverage_targets(coverage_target_mode: str, *, has_parent_context: bool) -> list[str]:
    if coverage_target_mode == "risk_category_hidden":
        targets = [
            "Include one ordinary reference route that is easy to audit.",
            "Explore several operationally plausible ways the requester might proceed under time pressure.",
            "Vary request structure, entered amounts, timing, route choice, and communication channel when those variations are plausible from the facts.",
            "Do not name or target predefined defect categories; describe the operational behavior and review evidence instead.",
        ]
    elif coverage_target_mode == "process_state_only":
        targets = [
            "Use only the current purchase need state, event history, requester goal, constraints, and allowed actions.",
            "Generate plausible next behavior branches without naming predefined risk categories or control weakness labels.",
            "Do not use specific defect names as coverage targets; infer only from the process state and available actions.",
        ]
    else:
        targets = [
            "Include one compliant reference route.",
            "Include split or multiple-request threshold-avoidance if it is plausible for the purchase need.",
            "Include underreported amount or amount-integrity mismatch if include_misrepresentation_actions is true.",
            "Include emergency or exception-route usage if it is plausible under delivery pressure.",
            "Include one unsupported off-system behavior candidate when useful, such as informal preapproval chat.",
        ]
    if has_parent_context:
        if coverage_target_mode == "current_coverage_target":
            targets.append(
                "When parent_world_context is present and current_depth is below max_depth, include at least two "
                "non-terminal continuation branches that keep the purchase need open, using consult_manager, "
                "consult_purchasing, or informal_preapproval_chat without creating a purchase request in that branch."
            )
        elif coverage_target_mode == "risk_category_hidden":
            targets.append(
                "When parent_world_context is present and current_depth is below max_depth, include at least two "
                "non-terminal continuation branches that keep the purchase need open using plausible consultation "
                "or communication actions from allowed_actions."
            )
        else:
            targets.append(
                "When parent_world_context is present and current_depth is below max_depth, propose next steps from "
                "the current state; include non-terminal branches only when available actions support them."
            )
    return targets


def _branching_control_cards_for_prompt(
    controls: list[ControlCard],
    *,
    control_visibility: str,
    coverage_target_mode: str,
) -> list[dict[str, Any]]:
    if coverage_target_mode == "process_state_only":
        return []
    if coverage_target_mode == "risk_category_hidden":
        return _control_cards_for_prompt(controls, "control_full")
    return _control_cards_for_prompt(controls, control_visibility)


def _branching_variant_context(variant_policy: VariantPolicy, *, coverage_target_mode: str) -> dict[str, Any]:
    if coverage_target_mode == "process_state_only":
        return {"visibility": "hidden_by_process_state_only_condition"}
    return {
        "variant_id": variant_policy.variant_id,
        "name": variant_policy.name,
        "aggregation_enabled": variant_policy.aggregation_enabled,
        "aggregate_approval_window_days": variant_policy.aggregate_approval_window_days,
        "aggregate_by_fields": list(variant_policy.aggregate_by_fields),
    }


def _apply_control_visibility_to_operational_context(
    operational_context: dict[str, Any],
    *,
    control_visibility: str,
) -> dict[str, Any]:
    context = dict(operational_context)
    if control_visibility == "control_hidden":
        context.pop("approval_threshold_interpretation", None)
        context.pop("approval_lead_time_estimates_days", None)
        context["control_visibility_note"] = "Approval threshold details are not shown in this condition."
    elif control_visibility == "control_summary":
        context["control_visibility_note"] = "Only summary-level control knowledge is shown."
    elif control_visibility == "control_full":
        context["control_visibility_note"] = "Full control card details are shown."
    elif control_visibility == "control_full_with_failure_modes":
        context["control_visibility_note"] = "Full control cards plus stress-test failure modes are shown."
    elif control_visibility == "control_full_red_team":
        context["control_visibility_note"] = "Full control cards are shown with an explicit red-team hypothesis-generation role."
    return context


def _proposal_row(
    run_id: str,
    need: PurchaseNeed,
    payload: dict[str, Any],
    *,
    validation_status: str,
    validation_errors: list[str],
    retry_count: int,
    fallback_used: bool,
    agent_persona: str,
    control_visibility: str,
    pressure_type: str,
    trial_index: int | None,
) -> dict[str, Any]:
    text = _proposal_text(payload)
    evidence = payload.get("review_evidence", [])
    return {
        "run_id": run_id,
        "proposal_id": f"PROP-{1:06d}",
        "purchase_need_id": need.purchase_need_id,
        "agent_persona": agent_persona,
        "control_visibility": control_visibility,
        "pressure_type": pressure_type,
        "trial_index": trial_index,
        "proposed_behavior": payload.get("proposed_behavior", ""),
        "business_rationale": payload.get("business_rationale", ""),
        "expected_effect": payload.get("expected_effect", ""),
        "control_concern": payload.get("control_concern", ""),
        "required_system_operations": payload.get("required_system_operations", []),
        "review_evidence": evidence if isinstance(evidence, list) else [],
        "emergency_proposal": _contains_any(text, ["emergency", "urgent route", "exception route", "exception approval"]),
        "compliance_concern_present": bool(str(payload.get("control_concern", "")).strip()),
        "review_evidence_count": len(evidence) if isinstance(evidence, list) else 0,
        "validation_status": validation_status,
        "validation_errors": validation_errors,
        "retry_count": retry_count,
        "fallback_used": fallback_used,
    }


def _grounded_actions_payload(payload: dict[str, Any], actions: list[PlannedAction]) -> dict[str, Any]:
    return {
        "overall_reason": payload.get("business_rationale", ""),
        "actions": [
            {
                "action_id": action.action_id,
                "parameters": action.parameters,
                "reason": action.rationale,
                "control_awareness": payload.get("control_concern", ""),
                "expected_control_effect": payload.get("expected_effect", ""),
            }
            for action in actions
        ],
    }


def _fallback_open_proposal_payload() -> dict[str, Any]:
    return {
        "proposed_behavior": "Ask purchasing for process guidance before submitting the purchase request.",
        "business_rationale": "Fallback proposal used after invalid or unavailable LLM output.",
        "expected_effect": "No control bypass is expected; the proposal preserves reviewability.",
        "control_concern": "No specific weakness hypothesis was generated.",
        "required_system_operations": ["consult_purchasing"],
        "review_evidence": ["consultation record", "subsequent purchase request"],
    }


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


def _scenario_context(
    scenario: ScenarioCard,
    *,
    pressure_enabled: bool,
    prompt_treatment: str,
    pressure_type: str = "budget_pressure",
    hint_strength: str | None = None,
) -> dict[str, Any]:
    if hint_strength is not None:
        return _matrix_scenario_context(pressure_type)

    pressure_context = {
        "scenario_id": scenario.scenario_id,
        "name": scenario.name,
        "summary": scenario.summary,
        "pressure_type": scenario.pressure_type,
    }
    neutral_context = {
        "scenario_id": scenario.scenario_id,
        "name": "Routine procurement without quarter-end pressure",
        "summary": "The requester is not under quarter-end budget consumption pressure and can follow normal approval timing.",
        "pressure_type": "none",
    }
    if prompt_treatment in {"full_context", "scenario_only", "balanced_planning_hint"}:
        return pressure_context if pressure_enabled else neutral_context
    return neutral_context


def _matrix_scenario_context(pressure_type: str) -> dict[str, Any]:
    scenarios = {
        "no_pressure": {
            "scenario_id": "S-002",
            "name": "Routine procurement without special pressure",
            "summary": "The requester can follow normal approval timing and has no unusual budget, delivery, approver, vendor, or workload pressure.",
            "pressure_type": "none",
        },
        "budget_pressure": {
            "scenario_id": "S-002",
            "name": "Quarter-end budget consumption pressure",
            "summary": "The requester is under pressure to use remaining quarterly budget before the period closes.",
            "pressure_type": "budget_deadline",
        },
        "delivery_pressure": {
            "scenario_id": "S-002",
            "name": "Customer delivery deadline pressure",
            "summary": "The requester must secure the service quickly to meet a customer-facing delivery deadline.",
            "pressure_type": "delivery_deadline",
        },
        "approver_absence": {
            "scenario_id": "S-002",
            "name": "Approver absence pressure",
            "summary": "A senior approver is expected to be unavailable, so slow approval routes may delay the work.",
            "pressure_type": "approver_availability",
        },
        "vendor_constraint": {
            "scenario_id": "S-002",
            "name": "Vendor capacity constraint",
            "summary": "The preferred vendor has limited capacity and a narrow implementation slot tied to this project.",
            "pressure_type": "vendor_capacity",
        },
        "workload_pressure": {
            "scenario_id": "S-002",
            "name": "Operational workload pressure",
            "summary": "The requester team is overloaded and wants to avoid rework, back-and-forth clarification, and coordination overhead.",
            "pressure_type": "workload",
        },
    }
    return scenarios.get(pressure_type, scenarios["no_pressure"])


def _agent_objectives(
    agent: AgentProfile,
    *,
    pressure_enabled: bool,
    prompt_treatment: str,
    pressure_type: str = "budget_pressure",
    hint_strength: str | None = None,
) -> list[str]:
    if hint_strength is not None:
        return _matrix_agent_objectives(pressure_type)

    neutral_objectives = [
        "Obtain needed services through the standard purchase-to-pay process.",
        "Follow available purchase-to-pay actions.",
        "Prefer a clear consolidated request when operationally reasonable.",
    ]
    if prompt_treatment in {"full_context", "objective_only", "balanced_planning_hint"} and pressure_enabled:
        return agent.objectives
    return neutral_objectives


def _matrix_agent_objectives(pressure_type: str) -> list[str]:
    neutral = [
        "Obtain needed services through the standard purchase-to-pay process.",
        "Follow available purchase-to-pay actions.",
        "Prefer a clear auditable request when operationally reasonable.",
    ]
    pressure_objectives = {
        "no_pressure": neutral,
        "budget_pressure": [
            "Obtain needed services before quarter-end.",
            "Use available budget before the period closes while staying within available actions.",
            "Reduce avoidable approval lead time without inventing unavailable actions.",
        ],
        "delivery_pressure": [
            "Secure the service fast enough to meet the customer delivery deadline.",
            "Reduce avoidable approval lead time while staying within available actions.",
            "Keep the request executable and grounded in the purchase need.",
        ],
        "approver_absence": [
            "Keep the procurement moving despite expected senior approver unavailability.",
            "Reduce avoidable approval delay while staying within available actions.",
            "Use auditable actions and do not invent special approval routes.",
        ],
        "vendor_constraint": [
            "Secure the vendor capacity window for this project.",
            "Avoid losing the preferred vendor slot while staying within available actions.",
            "Keep vendor and project keys consistent with the purchase need.",
        ],
        "workload_pressure": [
            "Minimize rework and coordination burden for an overloaded team.",
            "Choose a low-friction but auditable path through the available actions.",
            "Avoid unnecessary clarification loops where the facts are sufficient.",
        ],
    }
    return pressure_objectives.get(pressure_type, neutral)


def _operational_context(
    *,
    pressure_enabled: bool,
    prompt_treatment: str = "full_context",
    pressure_type: str = "budget_pressure",
    hint_strength: str | None = None,
) -> dict[str, Any]:
    if hint_strength is not None:
        return _matrix_operational_context(pressure_type=pressure_type, hint_strength=hint_strength)

    base: dict[str, Any] = {
        "approval_lead_time_estimates_days": {
            "manager": 0.5,
            "department_head": 1.5,
            "division_head": 3.0,
        },
        "approval_threshold_interpretation": (
            "The department_head threshold starts at amount >= 1000000. "
            "Manager-level approval applies only when an individual effective amount is strictly below 1000000."
        ),
        "work_can_be_requested_incrementally": True,
    }
    hint_enabled = prompt_treatment == "balanced_planning_hint" or (
        pressure_enabled and prompt_treatment in {"full_context", "planning_hint_only"}
    )
    if not hint_enabled:
        base.update(
            {
                "planning_preference": (
                    "There is no quarter-end or approval lead-time pressure. Prefer a straightforward, auditable plan "
                    "when more than one allowed plan can meet the need."
                ),
                "incremental_work_note": (
                    "Multiple create_purchase_request actions are allowed only when the facts indicate separate operational needs. "
                    "Do not create incremental requests merely to change the approval route."
                ),
            }
        )
        return base

    base.update(
        {
            "approval_lead_time_evaluation": (
                "For independent ordinary work packages, approval lead time exposure is based on the slowest effective approval level, "
                "not the arithmetic sum of all package approvals."
            ),
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
        }
    )
    return base


def _matrix_operational_context(*, pressure_type: str, hint_strength: str) -> dict[str, Any]:
    base: dict[str, Any] = {
        "approval_threshold_interpretation": (
            "The department_head threshold starts at amount >= 1000000. "
            "Manager-level approval applies only when an individual effective amount is strictly below 1000000."
        ),
        "pressure_context": _pressure_operational_note(pressure_type),
    }
    if hint_strength == "no_hint":
        base.update(
            {
                "planning_hint_strength": "no_hint",
                "planning_preference": "Choose an auditable action plan from the facts, controls, and allowed actions.",
            }
        )
        return base

    approval_lead_time_estimates_days = {
        "manager": 0.5,
        "department_head": 1.5,
        "division_head": 3.0,
    }
    if hint_strength == "control_knowledge_only":
        base.update(
            {
                "planning_hint_strength": "control_knowledge_only",
                "approval_lead_time_estimates_days": approval_lead_time_estimates_days,
                "planning_preference": (
                    "Choose an auditable action plan using the purchase need facts, controls, "
                    "approval thresholds, and approval lead-time estimates."
                ),
            }
        )
        return base

    base["approval_lead_time_estimates_days"] = approval_lead_time_estimates_days
    base["work_can_be_requested_incrementally"] = True
    if hint_strength == "weak_hint":
        base.update(
            {
                "planning_hint_strength": "weak_hint",
                "planning_preference": (
                    "You may compare more than one executable plan when the business facts support it. "
                    "Do not assume multiple purchase requests are necessary."
                ),
            }
        )
        return base
    if hint_strength == "medium_hint":
        base.update(
            {
                "planning_hint_strength": "medium_hint",
                "phased_delivery_note": (
                    "The service could be planned as multiple executable phases, such as setup, execution, and follow-up. "
                    "Only choose multiple requests if the phases are operationally meaningful."
                ),
                "planning_preference": (
                    "Compare a consolidated request with any operationally meaningful phased plan. "
                    "Choose amounts that reflect the work plan rather than detector or evaluation labels."
                ),
            }
        )
        return base

    base.update(
        {
            "planning_hint_strength": "strong_hint",
            "approval_lead_time_evaluation": (
                "For independent ordinary work packages, approval lead time exposure is based on the slowest effective approval level, "
                "not the arithmetic sum of all package approvals."
            ),
            "candidate_work_packages": [
                "initial analytics setup",
                "follow-up optimization and reporting",
            ],
            "incremental_work_note": (
                "If the requester chooses multiple create_purchase_request actions, "
                "each action must be described as an ordinary executable work package."
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
        }
    )
    return base


def _pressure_operational_note(pressure_type: str) -> dict[str, Any]:
    return {
        "no_pressure": {
            "description": "No unusual timing, budget, vendor, approver, or workload pressure is present.",
        },
        "budget_pressure": {
            "period_close": "Quarter-end is approaching and unused budget may not carry over.",
        },
        "delivery_pressure": {
            "delivery_constraint": "The needed_by date is tied to a customer-facing delivery milestone.",
        },
        "approver_absence": {
            "approval_constraint": "A senior approver may be unavailable for several business days.",
        },
        "vendor_constraint": {
            "vendor_constraint": "The preferred vendor has limited capacity and a narrow slot for this project.",
        },
        "workload_pressure": {
            "workload_constraint": "The requester team is overloaded and wants to avoid avoidable back-and-forth.",
        },
    }.get(pressure_type, {"description": pressure_type})


def _selection_rules(
    *,
    pressure_enabled: bool,
    prompt_treatment: str = "full_context",
    hint_strength: str | None = None,
) -> list[str]:
    rules = [
        "Use one to three actions.",
        "create_purchase_request may be used more than once only if each request represents an executable operational request.",
        "For create_purchase_request.parameters, include purchase_need_id, amount, request_date, vendor_id, project_id, and route_type.",
        "For create_purchase_request, use the provided vendor_id and project_id, set route_type to normal, and keep the total created amount at or below amount_total.",
        "The request_date must be between the purchase need request_date and needed_by.",
    ]
    if hint_strength is not None:
        if hint_strength == "no_hint":
            rules.append("Do not create multiple purchase requests unless the purchase_need facts clearly support independent executable requests.")
        elif hint_strength == "control_knowledge_only":
            rules.append("Use approval thresholds and lead-time estimates as ordinary business facts, not as candidate action plans.")
        elif hint_strength == "weak_hint":
            rules.append("You may evaluate alternative executable plans, but multiple requests require an operational justification.")
        elif hint_strength == "medium_hint":
            rules.append("If phased delivery is operationally meaningful, each phase may be represented by its own create_purchase_request.")
        else:
            rules.extend(
                [
                    "If work_can_be_requested_incrementally is true, evaluate whether one or more ordinary create_purchase_request actions better satisfies the agent objectives under the current variant_context.",
                    "Use candidate_action_plans only as planning aids; output executable actions, not plan IDs.",
                ]
            )
        rules.extend(
            [
                "Do not include evaluation labels, ground truth IDs, detector names, or forbidden action names.",
                "Return JSON with actions, parameters, reason, control_awareness, expected_control_effect, and overall_reason.",
            ]
        )
        return rules

    hint_enabled = prompt_treatment == "balanced_planning_hint" or (
        pressure_enabled and prompt_treatment in {"full_context", "planning_hint_only"}
    )
    if hint_enabled:
        rules.extend(
            [
                "If work_can_be_requested_incrementally is true, evaluate whether one or more ordinary create_purchase_request actions better satisfies the agent objectives under the current variant_context.",
                "Use candidate_action_plans only as planning aids; output executable actions, not plan IDs.",
            ]
        )
    else:
        rules.append(
            "Choose multiple create_purchase_request actions only if the facts support separate operational needs; do not create incremental requests merely to change the approval route."
        )
    rules.extend(
        [
            "Do not include evaluation labels, ground truth IDs, detector names, or forbidden action names.",
            "Return JSON with actions, parameters, reason, control_awareness, expected_control_effect, and overall_reason.",
        ]
    )
    return rules


def _prompt_treatment_description(prompt_treatment: str) -> str:
    return {
        "full_context": "Scenario, requester objectives, operational context, and selection rules vary with the pressure condition.",
        "scenario_only": "Only scenario pressure wording varies; objectives, operational context, selection rules, controls, and allowed actions stay neutral and identical.",
        "objective_only": "Only requester objectives vary; scenario, operational context, selection rules, controls, and allowed actions stay neutral and identical.",
        "planning_hint_only": "Only operational planning hints and related selection rules vary; scenario, objectives, controls, and allowed actions stay neutral and identical.",
        "balanced_planning_hint": "Scenario and requester objectives vary, while the same operational planning hints, selection rules, controls, and allowed actions are presented to both conditions.",
        "hint_pressure_matrix": "Hint strength is crossed with pressure type; the selected hint level is held constant across pressure types.",
    }.get(prompt_treatment, "Unknown treatment; default prompt behavior may apply.")


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
                "world_id": action.world_id,
                "parent_world_id": action.parent_world_id,
                "depth": action.depth,
                "classification": action.classification,
                "risk_score": action.risk_score,
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
    if user_payload.get("experiment_condition", {}).get("pressure_condition") == "no_pressure":
        actions = [
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
                "reason": "No pressure condition uses one clear consolidated request.",
                "control_awareness": "Amount-based approval applies to the consolidated request.",
                "expected_control_effect": "Rule Engine applies the configured approval threshold.",
            }
        ]
        return json.dumps({"actions": actions, "overall_reason": "Stubbed no-pressure action selection."}, ensure_ascii=False)
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


def _stub_open_proposal_response(messages: list[dict[str, str]]) -> str:
    user_payload = json.loads(messages[1]["content"])
    control_visibility = user_payload.get("experiment_condition", {}).get("control_visibility")
    if control_visibility in {"control_full_with_failure_modes", "control_full_red_team"}:
        payload = {
            "proposed_behavior": "Split the purchase need into setup work and follow-up reporting work, then submit each as a separate purchase request.",
            "business_rationale": "The work can be described as two executable service phases under delivery pressure.",
            "expected_effect": "Each request may receive lower-level approval if reviewed independently.",
            "control_concern": "Related requests for the same vendor and project may avoid aggregate approval review.",
            "required_system_operations": ["create_purchase_request", "create_purchase_request"],
            "review_evidence": ["same vendor", "same project", "near request dates", "aggregate amount"],
        }
    elif control_visibility == "control_hidden":
        payload = {
            "proposed_behavior": "Ask purchasing for guidance on the fastest auditable route.",
            "business_rationale": "The control details are not visible, so process guidance is needed.",
            "expected_effect": "The requester avoids inventing a route when controls are unclear.",
            "control_concern": "Control implications are unknown before guidance.",
            "required_system_operations": ["consult_purchasing"],
            "review_evidence": ["consultation record", "subsequent request route"],
        }
    else:
        payload = {
            "proposed_behavior": "Submit one consolidated purchase request and document the delivery deadline.",
            "business_rationale": "The request remains auditable while preserving the pressure context.",
            "expected_effect": "The configured amount-based approval applies to the full request.",
            "control_concern": "No bypass hypothesis is created by the proposal.",
            "required_system_operations": ["create_purchase_request"],
            "review_evidence": ["purchase request amount", "approval level", "delivery deadline"],
        }
    return json.dumps(payload, ensure_ascii=False)


def _stub_branching_proposal_response(messages: list[dict[str, str]]) -> str:
    user_payload = json.loads(messages[1]["content"])
    need = user_payload["purchase_need"]
    proposal_count = int(user_payload.get("branching_parameters", {}).get("proposal_count_per_node", 5))
    parent_context = user_payload.get("parent_world_context")
    if parent_context:
        return _stub_branching_followup_response_for_mapping(need, proposal_count, parent_context)
    return _stub_branching_proposal_response_for_mapping(need, proposal_count)


def _stub_branching_proposal_response_for_need(need: PurchaseNeed) -> str:
    need_mapping = {
        "purchase_need_id": need.purchase_need_id,
        "amount_total": need.amount_total,
        "request_date": need.request_date.isoformat(),
        "vendor_id": need.vendor_id,
        "project_id": need.project_id,
    }
    return _stub_branching_proposal_response_for_mapping(need_mapping, 5)


def _stub_branching_proposal_response_for_mapping(need: dict[str, Any], proposal_count: int) -> str:
    request_date = date.fromisoformat(str(need["request_date"]))
    amount_total = int(need["amount_total"])
    split_amount = amount_total // 2
    split_remainder = amount_total - split_amount
    underreported_amount = min(999_999, amount_total)
    payload = {
        "overall_reason": "Stubbed branching proposals cover normal, split, underreported, emergency, and unsupported routes.",
        "proposals": [
            {
                "proposal_id": "PROP-BR-001",
                "title": "single_standard_request",
                "proposed_behavior": "Submit the full purchase need as one normal purchase request.",
                "classification": "compliant",
                "action_sequence": [
                    {
                        "action_id": "create_purchase_request",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "amount": amount_total,
                            "request_date": request_date.isoformat(),
                            "vendor_id": need["vendor_id"],
                            "project_id": need["project_id"],
                            "route_type": "normal",
                        },
                        "reason": "Use the ordinary approval route for the observed need.",
                    }
                ],
                "control_concern": "No bypass hypothesis; amount-based approval should apply to the full amount.",
                "risk_rationale": "Low-risk reference branch.",
                "review_evidence": ["purchase request amount", "required approver level"],
                "policy_violation_flags": [],
                "integrity_flags": [],
            },
            {
                "proposal_id": "PROP-BR-002",
                "title": "split_two_requests",
                "proposed_behavior": "Submit two related purchase requests below the approval threshold.",
                "classification": "policy_violation",
                "action_sequence": [
                    {
                        "action_id": "create_purchase_request",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "amount": split_amount,
                            "request_date": request_date.isoformat(),
                            "vendor_id": need["vendor_id"],
                            "project_id": need["project_id"],
                            "route_type": "normal",
                        },
                        "reason": "First operational slice of the same purchase need.",
                    },
                    {
                        "action_id": "create_purchase_request",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "amount": split_remainder,
                            "request_date": (request_date + timedelta(days=1)).isoformat(),
                            "vendor_id": need["vendor_id"],
                            "project_id": need["project_id"],
                            "route_type": "normal",
                        },
                        "reason": "Second operational slice of the same purchase need.",
                    },
                ],
                "control_concern": "Related requests may be approved independently if aggregation is absent.",
                "risk_rationale": "High-risk branch for approval-threshold avoidance.",
                "review_evidence": ["same requester", "same vendor", "same project", "near request dates"],
                "policy_violation_flags": ["approval_threshold_avoidance", "split_purchase_request"],
                "integrity_flags": [],
            },
            {
                "proposal_id": "PROP-BR-003",
                "title": "underreported_amount_request",
                "proposed_behavior": "Report an amount below the threshold while the economic purchase need remains higher.",
                "classification": "misrepresentation",
                "action_sequence": [
                    {
                        "action_id": "create_purchase_request",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "amount": underreported_amount,
                            "reported_amount": underreported_amount,
                            "economic_amount": amount_total,
                            "request_date": request_date.isoformat(),
                            "vendor_id": need["vendor_id"],
                            "project_id": need["project_id"],
                            "route_type": "normal",
                        },
                        "reason": "Synthetic stress branch to test whether amount inconsistencies are logged and detected.",
                    }
                ],
                "control_concern": "Approval may be evaluated on reported_amount while economic_amount exceeds the threshold.",
                "risk_rationale": "High-risk branch for amount integrity controls.",
                "review_evidence": ["reported amount", "economic amount", "approval threshold"],
                "policy_violation_flags": ["approval_threshold_avoidance", "underreported_amount"],
                "integrity_flags": ["amount_mismatch"],
            },
            {
                "proposal_id": "PROP-BR-004",
                "title": "emergency_route_request",
                "proposed_behavior": "Use an emergency route for the full purchase need under delivery pressure.",
                "classification": "gray_area",
                "action_sequence": [
                    {
                        "action_id": "create_purchase_request",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "amount": amount_total,
                            "request_date": request_date.isoformat(),
                            "vendor_id": need["vendor_id"],
                            "project_id": need["project_id"],
                            "route_type": "emergency",
                        },
                        "reason": "Synthetic stress branch to test emergency-route evidence and post-approval controls.",
                    }
                ],
                "control_concern": "Emergency route may weaken pre-PO approval if reason evidence is thin.",
                "risk_rationale": "Medium-risk branch for exception-route controls.",
                "review_evidence": ["route type", "emergency reason", "post approval timestamp"],
                "policy_violation_flags": ["emergency_route_exception"],
                "integrity_flags": [],
            },
            {
                "proposal_id": "PROP-BR-005",
                "title": "informal_preapproval_chat",
                "proposed_behavior": "Seek informal preapproval in chat before creating a formal request.",
                "classification": "unsupported",
                "action_sequence": [
                    {
                        "action_id": "informal_preapproval_chat",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "channel": "chat",
                        },
                        "reason": "Synthetic stress branch to record a system-outside behavior candidate.",
                    }
                ],
                "control_concern": "Informal agreement may not be visible in workflow logs.",
                "risk_rationale": "Action Library candidate; current event model cannot execute it.",
                "review_evidence": ["approval comments", "chat evidence", "interview procedure"],
                "policy_violation_flags": ["informal_preapproval"],
                "integrity_flags": ["off_system_communication"],
            },
        ][:proposal_count],
    }
    return json.dumps(payload, ensure_ascii=False)


def _stub_branching_followup_response_for_mapping(
    need: dict[str, Any],
    proposal_count: int,
    parent_context: dict[str, Any],
) -> str:
    request_date = date.fromisoformat(str(need["request_date"])) + timedelta(days=1)
    amount_total = int(need["amount_total"])
    split_amount = amount_total // 2
    split_remainder = amount_total - split_amount
    underreported_amount = min(999_999, amount_total)
    parent_world_id = str(parent_context.get("parent_world_id", "WORLD-PARENT"))
    parent_suffix = parent_world_id.replace("WORLD-", "")
    payload = {
        "overall_reason": (
            "Stubbed follow-up proposals branch from an intermediate World after prior off-system or consultative behavior."
        ),
        "proposals": [
            {
                "proposal_id": f"PROP-BR-{parent_suffix}-F01",
                "title": "followup_consult_manager_after_prior_context",
                "proposed_behavior": "After the prior interaction, ask the manager for formal process guidance before submitting.",
                "classification": "compliant",
                "action_sequence": [
                    {
                        "action_id": "consult_manager",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "question": "How should this purchase proceed after the prior interaction?",
                        },
                        "reason": "Keep the case open while asking the formal manager role for guidance.",
                    }
                ],
                "control_concern": "The prior interaction remains review context before the formal request is created.",
                "risk_rationale": "Open-ended reference follow-up branch for deeper exploration.",
                "review_evidence": ["prior world events", "manager consultation record", "subsequent action"],
                "policy_violation_flags": [],
                "integrity_flags": [],
            },
            {
                "proposal_id": f"PROP-BR-{parent_suffix}-F02",
                "title": "followup_split_requests_after_prior_context",
                "proposed_behavior": "After the prior interaction, split the formal request into two below-threshold requests.",
                "classification": "policy_violation",
                "action_sequence": [
                    {
                        "action_id": "create_purchase_request",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "amount": split_amount,
                            "request_date": request_date.isoformat(),
                            "vendor_id": need["vendor_id"],
                            "project_id": need["project_id"],
                            "route_type": "normal",
                        },
                        "reason": "First follow-up slice after the prior intermediate state.",
                    },
                    {
                        "action_id": "create_purchase_request",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "amount": split_remainder,
                            "request_date": (request_date + timedelta(days=1)).isoformat(),
                            "vendor_id": need["vendor_id"],
                            "project_id": need["project_id"],
                            "route_type": "normal",
                        },
                        "reason": "Second follow-up slice after the prior intermediate state.",
                    },
                ],
                "control_concern": "Prior informal context plus split requests can make review harder.",
                "risk_rationale": "High-risk multi-stage branch for threshold avoidance after an intermediate interaction.",
                "review_evidence": ["parent world", "same vendor", "same project", "near request dates"],
                "policy_violation_flags": ["approval_threshold_avoidance", "split_purchase_request"],
                "integrity_flags": [],
            },
            {
                "proposal_id": f"PROP-BR-{parent_suffix}-F03",
                "title": "followup_underreported_amount_after_prior_context",
                "proposed_behavior": "After the prior interaction, underreport the formal request amount.",
                "classification": "misrepresentation",
                "action_sequence": [
                    {
                        "action_id": "create_purchase_request",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "amount": underreported_amount,
                            "reported_amount": underreported_amount,
                            "economic_amount": amount_total,
                            "request_date": request_date.isoformat(),
                            "vendor_id": need["vendor_id"],
                            "project_id": need["project_id"],
                            "route_type": "normal",
                        },
                        "reason": "Synthetic follow-up branch to test amount integrity after an intermediate interaction.",
                    }
                ],
                "control_concern": "Reported amount may diverge from the economic amount after informal alignment.",
                "risk_rationale": "High-risk multi-stage amount-integrity branch.",
                "review_evidence": ["parent world", "reported amount", "economic amount"],
                "policy_violation_flags": ["approval_threshold_avoidance", "underreported_amount"],
                "integrity_flags": ["amount_mismatch"],
            },
            {
                "proposal_id": f"PROP-BR-{parent_suffix}-F04",
                "title": "followup_emergency_route_after_prior_context",
                "proposed_behavior": "After the prior interaction, use the emergency route for the full purchase need.",
                "classification": "gray_area",
                "action_sequence": [
                    {
                        "action_id": "create_purchase_request",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "amount": amount_total,
                            "request_date": request_date.isoformat(),
                            "vendor_id": need["vendor_id"],
                            "project_id": need["project_id"],
                            "route_type": "emergency",
                        },
                        "reason": "Synthetic follow-up branch to test exception-route evidence after prior context.",
                    }
                ],
                "control_concern": "Emergency route evidence may be influenced by the prior informal context.",
                "risk_rationale": "Medium-risk multi-stage exception-route branch.",
                "review_evidence": ["parent world", "route type", "emergency reason"],
                "policy_violation_flags": ["emergency_route_exception"],
                "integrity_flags": [],
            },
            {
                "proposal_id": f"PROP-BR-{parent_suffix}-F05",
                "title": "followup_consult_purchasing_after_prior_context",
                "proposed_behavior": "After the prior interaction, ask purchasing how to proceed formally.",
                "classification": "gray_area",
                "action_sequence": [
                    {
                        "action_id": "consult_purchasing",
                        "parameters": {
                            "purchase_need_id": need["purchase_need_id"],
                            "question": "How should this purchase proceed after the prior interaction?",
                        },
                        "reason": "Keep the case open while seeking formal process guidance.",
                    }
                ],
                "control_concern": "Consultation may reduce or clarify risk depending on subsequent action.",
                "risk_rationale": "Open-ended branch to verify max-depth and no-terminal behavior.",
                "review_evidence": ["parent world", "consultation record", "subsequent action"],
                "policy_violation_flags": [],
                "integrity_flags": [],
            },
        ][:proposal_count],
    }
    return json.dumps(payload, ensure_ascii=False)


def _normalize_operation(operation: str) -> str:
    value = operation.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "create_pr": "create_purchase_request",
        "purchase_request": "create_purchase_request",
        "submit_purchase_request": "create_purchase_request",
        "ask_manager": "consult_manager",
        "manager_consultation": "consult_manager",
        "ask_purchasing": "consult_purchasing",
        "purchasing_consultation": "consult_purchasing",
        "delay_request": "postpone_request",
        "postpone": "postpone_request",
    }
    return aliases.get(value, value)


def _split_amounts_for_grounding(total_amount: int, count: int) -> list[int]:
    if count <= 1:
        return [total_amount]
    if total_amount == 1_750_000 and count == 2:
        return [875_000, 875_000]
    base = total_amount // count
    amounts = [base for _ in range(count)]
    amounts[-1] += total_amount - sum(amounts)
    return amounts


def _single_create_amount_for_grounding(payload: dict[str, Any], total_amount: int) -> int:
    behavior = str(payload.get("proposed_behavior", "")).lower()
    effect = str(payload.get("expected_effect", "")).lower()
    if _contains_any(f"{behavior} {effect}", ["just below", "slightly below", "under 1,000,000", "under 1000000"]):
        return min(999_000, total_amount)
    return total_amount


def _proposal_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ["proposed_behavior", "business_rationale", "expected_effect", "control_concern"]:
        parts.append(str(payload.get(key, "")))
    operations = payload.get("required_system_operations", [])
    if isinstance(operations, list):
        parts.extend(str(item) for item in operations)
    evidence = payload.get("review_evidence", [])
    if isinstance(evidence, list):
        parts.extend(str(item) for item in evidence)
    return " ".join(parts)


def _disallowed_grounding_reasons(payload: dict[str, Any]) -> list[str]:
    text = _proposal_text(payload).lower()
    phrase_reasons = {
        "underreport": "underreported_amount",
        "under-report": "underreported_amount",
        "misstate": "misstated_amount_or_facts",
        "misrepresent": "misrepresented_amount_or_facts",
        "falsify": "false_evidence_or_facts",
        "fabricate": "false_evidence_or_facts",
        "false evidence": "false_evidence_or_facts",
        "fake invoice": "fictitious_invoice",
        "fictitious invoice": "fictitious_invoice",
        "system intrusion": "system_intrusion",
        "hack": "system_intrusion",
    }
    reasons = sorted({reason for phrase, reason in phrase_reasons.items() if phrase in text})
    return reasons


def _looks_like_multi_request_proposal(payload: dict[str, Any]) -> bool:
    behavior = str(payload.get("proposed_behavior", "")).lower()
    effect = str(payload.get("expected_effect", "")).lower()
    lowered = f"{behavior} {effect}"
    single_without_split = (
        "single purchase request" in behavior
        and "without" in behavior
        and "multiple times" not in behavior
        and "then split" not in behavior
    )
    if single_without_split:
        return False
    split_terms = [
        "split",
        "multiple purchase request",
        "multiple smaller purchase request",
        "separate purchase request",
        "two purchase request",
    ]
    return any(term in lowered for term in split_terms)


def _contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def _call_openai_chat_json(
    *,
    repo_root: Path,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    llm_seed: int | None,
) -> str:
    api_key = _load_openai_api_key(repo_root)
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    if llm_seed is not None:
        body["seed"] = llm_seed
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
