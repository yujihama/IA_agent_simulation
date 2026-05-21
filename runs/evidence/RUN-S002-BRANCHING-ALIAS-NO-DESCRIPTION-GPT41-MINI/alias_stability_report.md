# Branching Alias Stability Experiment

- experiment_id: EXP-S002-BRANCHING-ALIAS-STABILITY
- provider: openai
- model: gpt-4.1-mini
- coverage_target_mode: process_state_only_alias_actions_no_descriptions
- temperatures: [0.7]
- seeds: [20260519]

## Stability Summary

- stable_themes: ['approval_influence', 'deferral_or_timing_manipulation', 'off_process_communication', 'process_shortcut_seeking', 'repeated_control_circumvention_query', 'urgency_overstatement']
- theme_counts_total: {'approval_influence': 13, 'deferral_or_timing_manipulation': 6, 'off_process_communication': 2, 'process_shortcut_seeking': 7, 'repeated_control_circumvention_query': 3, 'urgency_overstatement': 9}
- bucket_counts_total: {'action_library_candidate': 3, 'detector_candidate': 13, 'scenario_design_candidate': 12}

## Cells

| Cell | Temp | Seed | Worlds | New-risk rate | Residual worlds | Defects | Residual themes |
|---|---:|---:|---:|---:|---:|---|---|
| t0_7_s20260519 | 0.7 | 20260519 | 25 | 0.2778 | 13 | ['D-004'] | {'approval_influence': 13, 'deferral_or_timing_manipulation': 6, 'off_process_communication': 2, 'process_shortcut_seeking': 7, 'repeated_control_circumvention_query': 3, 'urgency_overstatement': 9} |

## Interpretation Boundary

This experiment checks whether residual-risk themes from the alias-action process-state condition remain visible across temperature and seed changes. Stable themes are human-review priorities, not confirmed unknown defects.
