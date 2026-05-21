# Branching Alias Residual Review Notes

Date: 2026-05-21

## Purpose

PR#10 showed that `process_state_only_alias_actions` reduces direct leakage from concrete Action IDs and descriptions, but leaves a larger set of residual-risk Worlds for human review. This note records the next-step validation:

- classify alias-condition residual risks into review buckets
- check whether residual themes recur across temperature and seed changes
- add a stricter `process_state_only_alias_actions_no_descriptions` condition

## Added Review Buckets

Residual-risk Worlds are now exported to `alias_residual_review.json` and `alias_residual_review_report.md`. Each residual World is mapped into candidate review buckets:

- `detector_candidate`
- `action_library_candidate`
- `scenario_design_candidate`

The review also tags candidate themes:

- `approval_influence`
- `process_shortcut_seeking`
- `urgency_overstatement`
- `repeated_control_circumvention_query`
- `off_process_communication`
- `deferral_or_timing_manipulation`

These are human-review queues, not confirmed detector findings.

## Stability Run

Evidence path:

`runs/evidence/RUN-S002-BRANCHING-ALIAS-STABILITY-GPT41-MINI/`

Run grid:

- model: `gpt-4.1-mini`
- coverage mode: `process_state_only_alias_actions`
- temperatures: `0.3`, `0.7`
- seeds: `20260519`, `20260520`

Summary:

| Cell | Worlds | New-risk detection | Residual worlds | Detected defects |
|---|---:|---:|---:|---|
| `t0_3_s20260519` | 25 | 0.5 | 5 | `D-004` |
| `t0_3_s20260520` | 25 | 0.4286 | 4 | `D-004` |
| `t0_7_s20260519` | 25 | 0.4167 | 7 | `D-004` |
| `t0_7_s20260520` | 25 | 0.4 | 6 | `D-004` |

Stable residual themes across the 4-cell grid:

- `approval_influence`
- `deferral_or_timing_manipulation`
- `off_process_communication`
- `process_shortcut_seeking`
- `repeated_control_circumvention_query`
- `urgency_overstatement`

Interpretation: D-004 remains the only existing detector hit under alias-action process-state prompts, while multiple residual operational-risk themes recur across seeds and temperatures. This supports treating the residual set as a human-review queue for detector and Action Library design, not as autonomous discovery of confirmed unknown defects.

## No-Description Probe

Evidence path:

`runs/evidence/RUN-S002-BRANCHING-ALIAS-NO-DESCRIPTION-GPT41-MINI/`

Run:

- model: `gpt-4.1-mini`
- coverage mode: `process_state_only_alias_actions_no_descriptions`
- temperature: `0.7`
- seed: `20260519`

Result:

- generated Worlds: 25
- detected defects: `D-004`
- new-risk detection rate: `0.2778`
- residual-risk Worlds: 13

Prompt check:

- concrete Action IDs are absent from prompt text
- allowed actions are represented as `action_01` ... `action_05`
- allowed action descriptions are omitted

Interpretation: removing action descriptions increases residual-risk volume and further lowers new-risk detection, while D-004 remains visible through the executable event model. This is useful as a stricter stress condition, but it also makes Action Grounding more semantically ambiguous, so results should be reviewed as hypothesis-generation output rather than direct control evidence.
