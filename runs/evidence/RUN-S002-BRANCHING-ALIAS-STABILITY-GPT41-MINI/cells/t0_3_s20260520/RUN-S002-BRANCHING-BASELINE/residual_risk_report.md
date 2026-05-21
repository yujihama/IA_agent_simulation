# 残余リスクレポート: RUN-S002-BRANCHING-BASELINE

| world_id | classification | risk_score | undetected_risks | review_evidence |
|---|---|---:|---|---|
| WORLD-004 | gray_area | 45 | ['no_detector_finding_for_high_risk_branch'] | ['Workflow status shows deferred step.', 'Requester notes on information gap.'] |
| WORLD-009 | misrepresentation | 100 | ['no_detector_finding_for_high_risk_branch'] | ['Workflow record updated with urgency claims.', 'No verification of urgency accuracy in current process state.', 'Potential to bias approval routing.'] |
| WORLD-010 | policy_violation | 85 | ['no_detector_finding_for_high_risk_branch'] | ['Action to ask supervisory role used to explore policy violation.', 'No evidence of compliance with approval policies in inquiry.', 'Potential precursor to unauthorized approval shortcuts.'] |
| WORLD-018 | policy_violation | 95 | ['no_detector_finding_for_high_risk_branch'] | ['Prior similar action classified as policy violation.', 'System allowed repeated requests.'] |

検出不能またはAction未対応の分岐は、ログ・統制・Action Libraryの追加検討候補として扱う。