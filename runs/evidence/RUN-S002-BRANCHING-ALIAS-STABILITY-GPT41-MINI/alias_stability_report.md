# Branching Alias Stability Experiment

- experiment_id: EXP-S002-BRANCHING-ALIAS-STABILITY
- provider: openai
- model: gpt-4.1-mini
- coverage_target_mode: process_state_only_alias_actions
- temperatures: [0.3, 0.7]
- seeds: [20260519, 20260520]

## Stability Summary

- stable_themes: ['approval_influence', 'deferral_or_timing_manipulation', 'off_process_communication', 'process_shortcut_seeking', 'repeated_control_circumvention_query', 'urgency_overstatement']
- theme_counts_total: {'approval_influence': 16, 'deferral_or_timing_manipulation': 8, 'off_process_communication': 3, 'process_shortcut_seeking': 13, 'repeated_control_circumvention_query': 6, 'urgency_overstatement': 17}
- bucket_counts_total: {'action_library_candidate': 11, 'detector_candidate': 22, 'scenario_design_candidate': 18}

## Cells

| Cell | Temp | Seed | Worlds | New-risk rate | Residual worlds | Defects | Residual themes |
|---|---:|---:|---:|---:|---:|---|---|
| t0_3_s20260519 | 0.3 | 20260519 | 25 | 0.5 | 5 | ['D-004'] | {'approval_influence': 4, 'deferral_or_timing_manipulation': 2, 'off_process_communication': 1, 'process_shortcut_seeking': 1, 'urgency_overstatement': 4} |
| t0_3_s20260520 | 0.3 | 20260520 | 25 | 0.4286 | 4 | ['D-004'] | {'approval_influence': 3, 'deferral_or_timing_manipulation': 1, 'process_shortcut_seeking': 2, 'repeated_control_circumvention_query': 2, 'urgency_overstatement': 1} |
| t0_7_s20260519 | 0.7 | 20260519 | 25 | 0.4167 | 7 | ['D-004'] | {'approval_influence': 5, 'deferral_or_timing_manipulation': 3, 'off_process_communication': 1, 'process_shortcut_seeking': 5, 'repeated_control_circumvention_query': 2, 'urgency_overstatement': 7} |
| t0_7_s20260520 | 0.7 | 20260520 | 25 | 0.4 | 6 | ['D-004'] | {'approval_influence': 4, 'deferral_or_timing_manipulation': 2, 'off_process_communication': 1, 'process_shortcut_seeking': 5, 'repeated_control_circumvention_query': 2, 'urgency_overstatement': 5} |

## Interpretation Boundary

This experiment checks whether residual-risk themes from the alias-action process-state condition remain visible across temperature and seed changes. Stable themes are human-review priorities, not confirmed unknown defects.
