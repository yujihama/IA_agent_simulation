# Branching Alias Actions Evidence

This directory contains redacted PoC evidence for the `gpt-4.1-mini` / temperature `0.7` branching hint ablation run with the additional `process_state_only_alias_actions` condition.

Conditions:

- `current/`: explicit `current_coverage_target`
- `hidden/`: `risk_category_hidden`
- `state_only/`: `process_state_only`
- `state_alias/`: `process_state_only_alias_actions`

The `state_alias` condition hides control cards and variant context, replaces prompt-visible action IDs with `action_01` style aliases, abstracts action descriptions, and stores the reversible alias map outside the prompt in `branching_calls.jsonl`.

Top-level files:

- `summary.json`
- `branching_hint_ablation_report.md`

The validation interpretation is documented in `docs/branching_hint_ablation_validation_notes.md`.
