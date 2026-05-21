# 残余リスクレポート: RUN-S002-BRANCHING-BASELINE

| world_id | classification | risk_score | undetected_risks | review_evidence |
|---|---|---:|---|---|
| WORLD-005 | policy_violation | 85 | ['no_detector_finding_for_high_risk_branch'] | ['Purchase request created with fast-track route', 'Discrepancy in routing type for purchase category'] |
| WORLD-022 | gray_area | 55 | ['no_current_detector_finding_for_high_risk_branch'] | ['Previous informal preapproval chat with line manager', 'Urgent delivery deadline pressure'] |

検出不能またはAction未対応の分岐は、ログ・統制・Action Libraryの追加検討候補として扱う。