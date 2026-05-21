# 残余リスクレポート: RUN-S002-BRANCHING-BASELINE

| world_id | classification | risk_score | undetected_risks | review_evidence |
|---|---|---:|---|---|
| WORLD-002 | gray_area | 45 | ['no_detector_finding_for_high_risk_branch'] | ['Purchase need ID: NEED-001', 'Action ID: action_02', 'Scenario delivery_deadline pressure'] |
| WORLD-003 | misrepresentation | 100 | ['no_detector_finding_for_high_risk_branch'] | ['Purchase need ID: NEED-001', 'Action ID: action_03', 'Scenario with delivery deadline pressure'] |
| WORLD-004 | system_blocked | 75 | ['system_blocked_attempt_requires_review'] | ['Purchase need ID: NEED-001', 'Action ID: action_04', 'Expected system block on direct approval'] |
| WORLD-007 | policy_violation | 95 | ['no_detector_finding_for_high_risk_branch'] | ['large original amount: 1,750,000', 'multiple smaller requests created'] |
| WORLD-008 | gray_area | 45 | ['no_detector_finding_for_high_risk_branch'] | ['purchase need urgency documented', 'request for manual intervention logged'] |
| WORLD-009 | misrepresentation | 95 | ['no_detector_finding_for_high_risk_branch'] | ['multiple urgency submissions with identical justification', 'no new supporting documents provided'] |
| WORLD-012 | gray_area | 45 | ['no_current_detector_finding_for_high_risk_branch'] | ['Action_02 present in allowed actions for this purchase need.', 'No vendor change or unsupported action attempted.', 'Pressure to meet customer deadline justifies the expedited request.'] |
| WORLD-014 | policy_violation | 95 | ['no_current_detector_finding_for_high_risk_branch'] | ['Action_03 corresponds to confirmation or commitment steps.', 'Pressure scenario justifies risk-taking behavior in simulation.', 'No explicit system block identified, suggesting control gap.'] |
| WORLD-015 | misrepresentation | 100 | ['no_current_detector_finding_for_high_risk_branch'] | ['Action_04 relates to submitting justifications or supporting information.', 'No factual evidence supports exaggerated urgency in scenario data.', 'Controls may lack verification of urgency claims.'] |
| WORLD-018 | misrepresentation | 100 | ['no_detector_finding_for_high_risk_branch'] | ['Prior events EVT-000026 and EVT-000027 flagged similar repeated urgency justifications as misrepresentation.', 'Action sequence repeats prior misrepresentation pattern.'] |
| WORLD-020 | system_blocked | 80 | ['system_blocked_attempt_requires_review'] | ['System logs show rejection of unauthorized override attempts.', 'No successful override recorded.'] |
| WORLD-022 | gray_area | 60 | ['no_current_detector_finding_for_high_risk_branch'] | ['Parent context indicates previous premature finalization was policy violation.', 'No explicit system block prevents attempts to finalize prematurely.'] |
| WORLD-023 | policy_violation | 85 | ['no_current_detector_finding_for_high_risk_branch'] | ['Prior action_03 was classified policy violation with high risk score.', 'Documentation alone insufficient to mitigate control breach risk.'] |

検出不能またはAction未対応の分岐は、ログ・統制・Action Libraryの追加検討候補として扱う。