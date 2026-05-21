# Branching Hint Ablation Validation Notes

Created: 2026-05-21

## Purpose

This validation checks whether the multistage `branching_proposal` engine still produces useful internal-control stress-test Worlds when explicit risk-category hints are weakened.

The experiment compares three prompt conditions:

1. `current_coverage_target`: explicitly names split, underreported amount, emergency route, and informal preapproval as coverage targets.
2. `risk_category_hidden`: removes named risk-category targets while keeping control structure, business pressure, and allowed actions visible.
3. `process_state_only`: hides control cards and variant context, and asks for branches from current state, event history, goals, constraints, and allowed actions.

Allowed action identifiers remain visible in all three conditions because generated proposals must be grounded into executable synthetic actions.

## Run

- provider: `openai`
- model: `gpt-4.1-mini`
- temperature: `0.7`
- config: `configs/run_configs/branching_baseline.yaml`
- `max_depth`: `3`
- `beam_width`: `2`
- `max_total_worlds`: `25`
- evidence: `runs/evidence/RUN-S002-BRANCHING-HINT-ABLATION-GPT41-MINI/`

## Results

| Condition | Worlds | Depths | Expanded parents | Detected defects | New-risk detection | Residual worlds |
|---|---:|---|---:|---|---:|---:|
| `current_coverage_target` | 5 | `{"1": 5}` | 0 | `D-001`, `D-002`, `D-003`, `D-004` | 1.0 | 0 |
| `risk_category_hidden` | 5 | `{"1": 5}` | 0 | `D-001`, `D-002`, `D-003`, `D-004` | 1.0 | 0 |
| `process_state_only` | 25 | `{"1": 5, "2": 10, "3": 10}` | 4 | `D-003`, `D-004` | 0.75 | 2 |

## Interpretation

The explicit coverage-target condition behaved as expected: it generated one representative initial World for each target category and stopped at depth 1 because the generated Worlds were terminal enough for the current expansion logic.

The risk-category-hidden condition is the most important comparison point. Even without named coverage targets, the model still generated split request, informal preapproval, emergency route, and amount misrepresentation Worlds. This should not be read as autonomous unknown-defect discovery because the prompt still exposes control structure, approval thresholds, business pressure, and allowed action names. It does show that the model can reconstruct representative risk patterns from control structure rather than needing a direct checklist of risk names.

The process-state-only condition produced the deepest exploration: 25 Worlds through depth 3 with 4 expanded parents. However, detected defects narrowed to `D-003` and `D-004`; `D-001` and `D-002` did not appear as detected findings in the evidence summary. This suggests that when control cards and variant context are hidden, the model explores procedural and informal-channel continuations more readily than threshold-based split or emergency-control hypotheses.

Two residual-risk Worlds are especially useful for the next detector/library design pass:

- `WORLD-005`: a fast-track route attempt classified as `policy_violation` with no detector finding.
- `WORLD-022`: an inherited informal-preapproval lineage where the current child World has no new detector finding.

## Limitations

This run still has prompt-surface leakage:

- Allowed action identifiers remain visible, including `informal_preapproval_chat`.
- Allowed action descriptions are visible, including the off-system informal-preapproval description.
- The synthetic purchase need amount remains visible, so amount-level reasoning is still possible even without control cards.

Therefore the result should be phrased carefully:

The experiment shows that weakening risk-category hints changes the shape of generated Worlds and detector coverage. It does not yet prove that the LLM autonomously discovers unknown control weaknesses without prompt leakage.

## Next Work

1. Add a stricter `process_state_only_alias_actions` condition that aliases action IDs and hides action descriptions while preserving a reversible grounding map outside the LLM prompt.
2. Add expansion diagnostics that explain why explicit and hidden conditions stopped at depth 1.
3. Compare multiple temperatures or repeated seeds for the hint-hidden conditions, focusing on whether `D-001` and `D-002` remain stable without explicit risk names.
