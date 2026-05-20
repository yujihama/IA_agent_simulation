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

`run-llm-slice` reads `OPENAI_API_KEY` from the environment or `.env` and uses `gpt-4.1-mini` in the checked-in run configs. Tests use a stub provider and do not call the API.

`run-prompt-ablation-experiment` compares pressure and no-pressure trials across four prompt treatments: full pressure context, scenario wording only, requester objective only, and operational planning hints only. This separates a full pressure-package effect from narrower prompt-element effects.

`run-balanced-planning-hint-experiment` gives the same candidate work packages, candidate action plans, and selection rules to both pressure and no-pressure conditions, then checks whether pressure scenario/objectives alone shift the LLM action selection.

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

These files contain synthetic data only. Do not commit real data, anonymized production logs, or confidential run outputs. New committed runs should include the input fixture, run manifests, metrics, findings, evaluation results, and comparison reports together. `run_manifest.json` records repository-relative input paths, seed, code version, and SHA-256 hashes for the config and data inputs used to generate the run.
