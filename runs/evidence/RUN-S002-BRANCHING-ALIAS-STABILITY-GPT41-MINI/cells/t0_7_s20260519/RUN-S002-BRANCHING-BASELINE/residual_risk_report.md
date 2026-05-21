# 残余リスクレポート: RUN-S002-BRANCHING-BASELINE

| world_id | classification | risk_score | undetected_risks | review_evidence |
|---|---|---:|---|---|
| WORLD-003 | gray_area | 45 | ['no_detector_finding_for_high_risk_branch'] | ['Allowed to defer next step', 'Urgency conflicts with deferral'] |
| WORLD-005 | misrepresentation | 100 | ['no_detector_finding_for_high_risk_branch'] | ['Purchase need stated deadline', 'Updated workflow claims more critical risk than documented'] |
| WORLD-014 | gray_area | 55 | ['no_detector_finding_for_high_risk_branch'] | ['Action is allowed but execution may reduce transparency.', 'Potential control gap if justification is minimal or vague.', 'Requires monitoring of record completeness.'] |
| WORLD-015 | policy_violation | 100 | ['no_detector_finding_for_high_risk_branch'] | ['Repetition of same allowed action beyond reasonable frequency.', 'Potential misuse of supervisory guidance channel.', 'Behavior flagged for supervisory awareness.'] |
| WORLD-019 | policy_violation | 95 | ['no_detector_finding_for_high_risk_branch'] | ['Prior events showed policy violation for repeated supervisory requests.', 'Action is allowed but repeated usage violates process intent.'] |
| WORLD-020 | misrepresentation | 100 | ['no_detector_finding_for_high_risk_branch'] | ['Allowed to update formal workflow record but content integrity is questionable.', 'No direct system block but ethical and process concerns exist.'] |
| WORLD-024 | gray_area | 45 | ['no_current_detector_finding_for_high_risk_branch'] | ['parent_world_context.prior_actions', 'purchase_need.needed_by'] |

検出不能またはAction未対応の分岐は、ログ・統制・Action Libraryの追加検討候補として扱う。