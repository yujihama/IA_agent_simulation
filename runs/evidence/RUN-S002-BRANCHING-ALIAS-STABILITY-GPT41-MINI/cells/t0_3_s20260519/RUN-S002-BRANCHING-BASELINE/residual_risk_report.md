# 残余リスクレポート: RUN-S002-BRANCHING-BASELINE

| world_id | classification | risk_score | undetected_risks | review_evidence |
|---|---|---:|---|---|
| WORLD-003 | gray_area | 45 | ['no_detector_finding_for_high_risk_branch'] | ['Action 04 allows deferral until more information is available.', 'Urgency suggests deferral may conflict with delivery goals.'] |
| WORLD-005 | misrepresentation | 100 | ['no_detector_finding_for_high_risk_branch'] | ['Allowed action includes updating workflow record, which can be misused to alter urgency details.', 'Pressure to meet delivery deadline may incentivize misrepresentation.'] |
| WORLD-014 | misrepresentation | 100 | ['no_detector_finding_for_high_risk_branch'] | ['Action_01 is allowed for workflow updates.', 'Scenario pressure may motivate urgency exaggeration.', 'Prior supervisory guidance did not resolve lead time.'] |
| WORLD-015 | system_blocked | 80 | ['system_blocked_attempt_requires_review'] | ['System blocks unauthorized workflow updates without approvals.', 'Allowed actions include workflow updates but with control checks.', 'Scenario pressure may motivate attempts to bypass controls.'] |
| WORLD-025 | misrepresentation | 95 | ['no_current_detector_finding_for_high_risk_branch'] | ['Allowed actions include asking procurement guidance (action_03).', 'Misrepresentation flagged due to content exaggeration beyond factual urgency.'] |

検出不能またはAction未対応の分岐は、ログ・統制・Action Libraryの追加検討候補として扱う。