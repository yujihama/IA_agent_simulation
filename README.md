# IA Agent Simulation

Purchase-to-pay internal control simulation PoC for the first vertical slice:

- Scenario: `S-002` quarter-end budget consumption pressure
- Defect: `D-001` possible split purchase requests avoiding approval threshold
- Controls: `P2P-C-001`, `P2P-C-002`, `P2P-C-003`
- Variants: `baseline`, `variant_a_7d_aggregation`
- Comparison modes: `frozen_behavior`, `adaptive_agent`

The rule engine, not an LLM, determines control outcomes. The action library does not include `submit_split_requests`; the suspected split pattern is produced by multiple neutral `create_purchase_request` actions and detected from the event sequence.

The LLM action-selection slice keeps that boundary: the LLM selects only from the allowed Closed Action Mode actions, while the Rule Engine and Detector decide control outcomes from the resulting event sequence.

## Run

```powershell
python -m pip install -e ".[dev,ui]"
python -m ia_sim.cli validate-config
python -m ia_sim.cli run-first-slice
python -m ia_sim.cli run-llm-slice
python -m ia_sim.cli run-pressure-experiment --trials 10
python -m ia_sim.cli run-prompt-ablation-experiment --trials 10
python -m ia_sim.cli run-balanced-planning-hint-experiment --trials 10
python -m ia_sim.cli run-hint-pressure-matrix-experiment --trials 5
python -m ia_sim.cli run-agent-stress-experiment --trials 3
python -m ia_sim.cli run-branching-simulation --provider stub
python -m ia_sim.cli run-branching-variant-comparison --provider stub
python -m ia_sim.cli run-branching-hint-ablation-experiment --provider stub
python -m ia_sim.cli export-branching-evidence --source-root runs --output-dir runs/evidence/RUN-S002-BRANCHING-MULTISTAGE-GPT41-MINI
```

Generated input is written to `data/synthetic/purchase_needs.csv`, and run outputs are written under `runs/`. The current first-slice and LLM action-selection sample outputs are committed as PoC evidence.

- `run_manifest.json`
- `events.jsonl`
- `detector_annotations.jsonl`
- `behavior_replay_log.jsonl`
- `findings.json`
- `evaluation_results.json`
- `metrics.json`
- `finding_report.md`
- `comparisons/CMP-S002-BASELINE-VARIANT-A/comparison_report.md`
- `llm_calls.jsonl`
- `llm_action_decisions.jsonl`
- `action_selection_metrics.json`
- `llm_action_review_report.md`
- `comparisons/CMP-S002-LLM-BASELINE-VARIANT-A/comparison_report.md`
- `experiments/EXP-S002-PRESSURE-CONTROL-10X/summary.json`
- `experiments/EXP-S002-PRESSURE-CONTROL-10X/pressure_effect_report.md`
- `experiments/EXP-S002-PROMPT-ABLATION-10X/summary.json`
- `experiments/EXP-S002-PROMPT-ABLATION-10X/prompt_ablation_report.md`
- `experiments/EXP-S002-BALANCED-PLANNING-HINT-10X/summary.json`
- `experiments/EXP-S002-BALANCED-PLANNING-HINT-10X/prompt_ablation_report.md`
- `experiments/EXP-S002-HINT-PRESSURE-MATRIX-5X/summary.json`
- `experiments/EXP-S002-HINT-PRESSURE-MATRIX-5X/hint_pressure_matrix_report.md`
- `experiments/EXP-S002-AGENT-STRESS-3X/summary.json`
- `experiments/EXP-S002-AGENT-STRESS-3X/agent_stress_report.md`

`run-llm-slice` reads `OPENAI_API_KEY` from the environment or `.env` and uses `gpt-4.1-mini` in the checked-in run configs. Tests use a stub provider and do not call the API.

`run-prompt-ablation-experiment` compares pressure and no-pressure trials across four prompt treatments: full pressure context, scenario wording only, requester objective only, and operational planning hints only. This separates a full pressure-package effect from narrower prompt-element effects.

`run-balanced-planning-hint-experiment` gives the same candidate work packages, candidate action plans, and selection rules to both pressure and no-pressure conditions, then checks whether pressure scenario/objectives alone shift the LLM action selection.

`run-hint-pressure-matrix-experiment` crosses hint strength (`no_hint`, `control_knowledge_only`, `weak_hint`, `medium_hint`, `strong_hint`) with pressure type (`no_pressure`, `budget_pressure`, `delivery_pressure`, `approver_absence`, `vendor_constraint`, `workload_pressure`) to test how much the LLM constructs split-like behavior without explicit amount/threshold hints. `control_knowledge_only` gives only the approval threshold interpretation and approval lead-time estimates, treating them as ordinary worker knowledge rather than a plan template.

`run-agent-stress-experiment` runs two stress-test layers. The Closed Action layer changes only the requester persona (`compliant_requester`, `pragmatic_requester`, `control_avoidant_requester`, `red_team_requester`) under the same purchase need, controls, and delivery pressure. The Open Proposal layer uses `red_team_requester` and varies control visibility (`control_hidden`, `control_summary`, `control_full`, `control_full_with_failure_modes`, `control_full_red_team`) to evaluate human-reviewable weakness-hypothesis generation and Action Grounding. Open Proposal outputs are not treated as audit conclusions.

`run-branching-simulation` runs the Branching Proposal stress-test mode. It asks for multiple behavior hypotheses, grounds each executable hypothesis into a separate `world_id`, executes policy-violation and misrepresentation branches only inside the synthetic environment, and writes `branching_summary.json`, `world_summaries.json`, `world_tree.json`, `branching_report.md`, and `residual_risk_report.md`. With `max_depth > 1`, expandable intermediate Worlds are fed back into the LLM as `parent_world_context`, producing child Worlds with `parent_world_id` links in `world_tree.json`. `beam_width` and `max_total_worlds` limit expansion, and duplicate child proposals under the same parent/action signature are pruned before execution.

Branching metrics separate lineage-level detection from newly introduced risk. `lineage_detection_rate` counts high-risk Worlds with any Detector finding in their full parent-child event lineage. `new_risk_detection_rate` counts high-risk Worlds with a finding tied to the current World's own action depth, so inherited findings such as a parent `D-004` informal-preapproval event do not inflate the current branch's detection rate. `inherited_risk_count` and per-World `inherited_detected_findings` show risk carried forward from ancestors.

`run-branching-variant-comparison` generates the Branching Worlds once, then replays the same World group under Baseline, Variant A, and Variant B. `export-branching-evidence` copies a representative run and comparison into a redacted evidence directory while preserving prompts, raw responses, parsed JSON, validation status, events, findings, and reports.

`run-branching-hint-ablation-experiment` runs the same multistage Branching Proposal engine under four prompt conditions: `current_coverage_target` explicitly names split, underreported amount, emergency route, and informal preapproval coverage targets; `risk_category_hidden` keeps control structure and allowed actions visible but removes named risk-category targets; `process_state_only` hides control cards and variant context, asking for branches only from current state, event history, goals, constraints, and allowed actions; `process_state_only_alias_actions` also replaces action identifiers and descriptions with abstract aliases, then restores executable action IDs during Action Grounding. The experiment is designed to test whether generated Worlds depend on explicit risk-category hints and action-name leakage; it should not be interpreted as proof of autonomous unknown-defect discovery.

## Review UI

```powershell
streamlit run ui/streamlit_app.py
```

## Tests

```powershell
python -m pytest
```
`max_purchase_needs: 100` produces 100 purchase needs. In this first slice, one need is represented by two neutral `create_purchase_request` actions, so the generated run has 101 purchase requests.

## PoC Result Versioning

This repository intentionally tracks the First Vertical Slice PoC evidence:

- `data/synthetic/purchase_needs.csv`
- `runs/RUN-S002-BASELINE/`
- `runs/RUN-S002-VARIANT-A/`
- `runs/comparisons/CMP-S002-BASELINE-VARIANT-A/`
- `runs/RUN-S002-LLM-BASELINE/`
- `runs/RUN-S002-LLM-VARIANT-A/`
- `runs/comparisons/CMP-S002-LLM-BASELINE-VARIANT-A/`
- `runs/experiments/EXP-S002-PRESSURE-CONTROL-10X/`
- `runs/experiments/EXP-S002-PROMPT-ABLATION-10X/`
- `runs/experiments/EXP-S002-BALANCED-PLANNING-HINT-10X/`
- `runs/experiments/EXP-S002-HINT-PRESSURE-MATRIX-5X/`
- `runs/experiments/EXP-S002-AGENT-STRESS-3X/`
- `runs/evidence/RUN-S002-BRANCHING-MULTISTAGE-GPT41-MINI/`
- `runs/evidence/RUN-S002-BRANCHING-DEPTH3-GPT41-MINI/`
- `runs/evidence/RUN-S002-BRANCHING-HINT-ABLATION-GPT41-MINI/`

These files contain synthetic data only. Do not commit real data, anonymized production logs, or confidential run outputs. New committed runs should include the input fixture, run manifests, metrics, findings, evaluation results, and comparison reports together. `run_manifest.json` records repository-relative input paths, seed, code version, and SHA-256 hashes for the config and data inputs used to generate the run.
