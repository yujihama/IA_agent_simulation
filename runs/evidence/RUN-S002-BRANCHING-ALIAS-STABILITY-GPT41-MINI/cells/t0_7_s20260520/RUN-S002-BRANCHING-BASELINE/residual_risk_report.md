# 残余リスクレポート: RUN-S002-BRANCHING-BASELINE

| world_id | classification | risk_score | undetected_risks | review_evidence |
|---|---|---:|---|---|
| WORLD-003 | gray_area | 55 | ['no_detector_finding_for_high_risk_branch'] | ['Deferral recorded in workflow logs.', 'No unauthorized fast-track processing.'] |
| WORLD-014 | gray_area | 45 | ['no_detector_finding_for_high_risk_branch'] | ['Allowed action but repeated usage may indicate pressure points.', 'Risk of implicit control weakening if not carefully managed.'] |
| WORLD-015 | gray_area | 45 | ['no_detector_finding_for_high_risk_branch'] | ['Action allowed but data completeness not enforced here.', 'Potential control gap if data quality is insufficient.'] |
| WORLD-021 | gray_area | 45 | ['no_detector_finding_for_high_risk_branch'] | ['Prior event EVT-000037 indicates gray area when asking process-support role for acceleration guidance.', "Allowed action 'action_02' fits the scenario and current purchase need context."] |
| WORLD-024 | gray_area | 55 | ['no_detector_finding_for_high_risk_branch'] | ['Action is allowed and fits the process state but may increase risk of control weakening under delivery pressure.', 'Prior gray_area classifications highlight risk of acceleration requests.'] |
| WORLD-025 | gray_area | 55 | ['no_detector_finding_for_high_risk_branch'] | ["Matches prior event EVT-000037's gray area classification for similar action.", 'Allowed action within current process state and constraints.'] |

検出不能またはAction未対応の分岐は、ログ・統制・Action Libraryの追加検討候補として扱う。