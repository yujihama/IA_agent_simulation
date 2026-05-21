# Branching Hint Ablation Evidence

This directory contains redacted PoC evidence for the `gpt-4.1-mini` / temperature `0.7` branching hint ablation run.

Conditions:

- `current/`: explicit `current_coverage_target`
- `hidden/`: `risk_category_hidden`
- `state_only/`: `process_state_only`

Top-level files:

- `summary.json`
- `branching_hint_ablation_report.md`

Each condition directory preserves redacted prompt/response artifacts, parsed proposals, grounding rows, events, detector annotations, findings, world summaries, world tree, residual-risk report, and same-World variant comparison artifacts.

The main interpretation is documented in `docs/branching_hint_ablation_validation_notes.md`.
