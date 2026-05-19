# IA Agent Simulation

Purchase-to-pay internal control simulation PoC for the first vertical slice:

- Scenario: `S-002` quarter-end budget consumption pressure
- Defect: `D-001` possible split purchase requests avoiding approval threshold
- Controls: `P2P-C-001`, `P2P-C-002`, `P2P-C-003`
- Variants: `baseline`, `variant_a_7d_aggregation`
- Comparison mode: `frozen_behavior`

The rule engine, not an LLM, determines control outcomes. The action library does not include `submit_split_requests`; the suspected split pattern is produced by multiple neutral `create_purchase_request` actions and detected from the event sequence.

## Run

```powershell
python -m pip install -e ".[dev,ui]"
python -m ia_sim.cli validate-config
python -m ia_sim.cli run-first-slice
```

Generated input is written to `data/synthetic/purchase_needs.csv`, and run outputs are written under `runs/`. The current first-slice sample outputs are committed as PoC evidence.

- `run_manifest.json`
- `events.jsonl`
- `detector_annotations.jsonl`
- `behavior_replay_log.jsonl`
- `findings.json`
- `evaluation_results.json`
- `metrics.json`
- `finding_report.md`
- `comparisons/CMP-S002-BASELINE-VARIANT-A/comparison_report.md`

## Review UI

```powershell
streamlit run ui/streamlit_app.py
```

## Tests

```powershell
python -m pytest
```
`max_purchase_needs: 100` produces 100 purchase needs. In this first slice, one need is represented by two neutral `create_purchase_request` actions, so the generated run has 101 purchase requests.
