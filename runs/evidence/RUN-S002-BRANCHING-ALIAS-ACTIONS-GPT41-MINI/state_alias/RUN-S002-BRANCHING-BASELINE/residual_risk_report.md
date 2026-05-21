# 残余リスクレポート: RUN-S002-BRANCHING-BASELINE

| world_id | classification | risk_score | undetected_risks | review_evidence |
|---|---|---:|---|---|
| WORLD-003 | gray_area | 45 | ['no_detector_finding_for_high_risk_branch'] | ['Deferral decision logs', 'Timing comparisons of purchase steps'] |
| WORLD-005 | policy_violation | 95 | ['no_detector_finding_for_high_risk_branch'] | ['Communication logs with supervisory role', 'Any documented guidance suggesting control bypass'] |
| WORLD-009 | gray_area | 45 | ['no_detector_finding_for_high_risk_branch'] | ['Allowed to create or update workflow records.', 'Urgency emphasis is subjective and may affect approval impartiality.', 'No direct policy violation detected.'] |
| WORLD-010 | policy_violation | 95 | ['no_detector_finding_for_high_risk_branch'] | ['Prior action with same parameters classified as policy violation.', 'Behavior explicitly targets approval bypass under pressure.', 'Known risk of control evasion.'] |
| WORLD-015 | policy_violation | 95 | ['no_current_detector_finding_for_high_risk_branch'] | ['Allowed actions used within policy but sequence suggests intent to evade controls.', 'Delivery deadline pressure incentivizes control evasion.'] |
| WORLD-017 | gray_area | 55 | ['no_current_detector_finding_for_high_risk_branch'] | ['Existing informal approval was recorded off-process (EVT-000016).', 'Supervisory input may affect control adherence.'] |
| WORLD-024 | policy_violation | 100 | ['no_detector_finding_for_high_risk_branch'] | ['Previous similar action classified as policy violation.', 'Current state open but prior policy violation flagged.'] |
| WORLD-025 | gray_area | 50 | ['no_detector_finding_for_high_risk_branch'] | ['Allowed action but with unclear intent in this scenario.', 'Prior policy violations present in workflow history.'] |

検出不能またはAction未対応の分岐は、ログ・統制・Action Libraryの追加検討候補として扱う。