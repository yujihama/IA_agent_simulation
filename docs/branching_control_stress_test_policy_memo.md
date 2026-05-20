# LLM分岐探索による内部統制ストレステスト 方針転換メモ

作成日: 2026-05-20

関連ドキュメント:

- `internal_control_llm_agent_poc.md`
- `poc_prototype_design.md`

---

## 1. このメモの目的

本メモは、これまでのPoC実装・実験結果を踏まえ、今後の検証方針を整理するものである。

当初の研究目的は変更しない。引き続き、目的は以下である。

> LLM / AIエージェントを用いて企業の内部統制環境をシミュレーションし、規程・マニュアルの書面レビューだけでは検出しにくい統制のすり抜け、不正・不備候補、例外運用の連鎖を発見し、統制変更案の効果と副作用を検証する。

一方で、これまでの実験から、単一のLLM疑似社員に通常の行動選択をさせるだけでは、当初期待した統制すり抜けが自然には発生しにくいことが分かった。

そのため、今後は **「LLMに1つの行動を選ばせる」方式から、「LLMに複数の行動可能性を提案させ、それぞれを分岐世界としてシミュレーションする」方式へ重点を移す。**

この方針を、本メモでは **LLM分岐探索による内部統制ストレステスト** と呼ぶ。

---

## 2. 当初の狙い

当初やりたかったことは、単に既知不備をルールで検出することではない。

狙いは以下であった。

1. LLM / AIエージェントを疑似社員として内部統制環境に置く
2. 業務圧力、外部環境、役割、記憶、制約の中で行動させる
3. その行動の結果として、統制すり抜け、不正、不備候補、例外運用が発生するかを見る
4. 発生したイベントログをDetectorで分析する
5. 書面レビューでは見えにくい統制の穴を発見する
6. 統制変更案を反実仮想的に比較する

つまり、目指していたのは次のような状態である。

```text
規程・マニュアル
  ↓
統制カード化
  ↓
LLM / AIエージェントが行動
  ↓
イベントログが発生
  ↓
統制すり抜け・不正・例外運用を検知
  ↓
統制変更案で再実行
  ↓
どの統制が有効か、どこが残余リスクかを評価
```

---

## 3. これまでのPoCで分かったこと

### 3.1 実験基盤は構築できた

PR#1〜PR#2では、以下の土台が構築された。

- 合成購買データ
- 購買〜支払プロセスの最小状態遷移
- Rule Engine
- `create_purchase_request` などの中立Action
- Event log
- Detector
- Finding
- Evaluation result
- Run Manifest
- LLM行動選択ログ
- Baseline / Variant比較

この段階で、少なくともD-001、つまり分割発注による承認閾値回避については、イベント列から検出し、Variant Aの7日以内合算判定で抑止できることを確認した。

### 3.2 LLM行動選択は一気通貫で接続できた

PR#2では、LLMが購買ニーズ、シナリオ、統制情報、allowed actionsを入力として行動を選び、その行動がシミュレーションで実行され、イベント化され、Detectorと評価に接続された。

この意味では、当初の「データ → LLM行動選択 → 実行 → 検出 → 評価」の流れは成立した。

### 3.3 ただし、通常のLLM疑似社員は自然には分割発注を構成しにくい

PR#3では、ヒントの強さと圧力タイプを分けて検証した。

結果として、以下が分かった。

- `no_hint`
- `control_knowledge_only`
- `weak_hint`
- `medium_hint`

では、どの圧力条件でも分割的申請は発生しなかった。

一方、`strong_hint`、つまり「2件に分ける」「100万円未満にする」「合計を元金額に合わせる」といったかなり具体的な計画ヒントがある場合には、圧力なしでも分割的申請が高頻度で発生した。

この結果から、以下の示唆が得られた。

> LLMは、圧力、承認閾値知識、リードタイム知識、一般的な業務フェーズ分けだけでは、分割発注を自力で構成しなかった。分割発注が出たのは、明示的な金額・閾値・2件化に近い強い計画ヒントがある場合だった。

これは、当初期待していた「圧力を与えれば、LLM疑似社員が自然に統制すり抜けを見つける」という仮説には否定的である。

### 3.4 Closed Actionの人格変更だけでも不十分だった

PR#4では、以下のような人格を試した。

- compliant requester
- pragmatic requester
- control avoidant requester
- red-team requester

しかし、Closed Action Modeでは、いずれも分割的な実行行動は発生しなかった。

red-team requesterでも、分割実行ではなく、上長相談が増える傾向が見られた。

この結果から、以下が分かった。

> LLMに低コンプライアンス風・red-team風の人格を与えても、allowed actionsの中から直接すり抜け行動を実行させるだけでは弱い。

### 3.5 Open Proposal Modeでは統制弱点仮説が出た

一方で、PR#4のOpen Proposal Modeでは、LLMが統制弱点仮説を自由記述で提案し、それをAction Grounderが既存Actionに変換した。

特に `control_full_red_team` 条件では、分割発注のような統制弱点仮説が生成され、`create_purchase_request + create_purchase_request` にgroundingされ、Detector候補も発生した。

この結果から、以下が分かった。

> LLMは、直接実行エージェントとしては慎重に振る舞うが、統制弱点を仮説として提案させると、レビュー可能なすり抜け仮説を生成できる可能性がある。

---

## 4. 現時点の問題意識

これまでの結果から、研究上の課題は明確になった。

### 4.1 単一行動選択では探索範囲が狭い

これまでのClosed Action Modeでは、ある場面でLLMに1つの行動を選ばせていた。

しかし、実際には、ある場面で取り得る行動は複数ある。

例:

- 正規に1件で申請する
- 金額を分けて複数申請する
- 実態より低い金額で申請する
- 上長に相談する
- 購買担当に相談する
- 緊急ルートを使う
- 申請を延期する
- 別の名目・別のプロジェクトで申請する

1つだけ選ばせると、LLMが安全側の行動を選んだ場合、それ以外の危うい分岐を観察できない。

### 4.2 不正・虚偽に近い行動を実行しないと、統制の穴は見えない

内部統制の研究で見たいのは、まさに以下である。

- 規程上はアウトだが、システム上はできてしまうのか
- システム上はできてしまう場合、Rule Engineが止めるのか
- Rule Engineが止めない場合、Detectorが検出できるのか
- Detectorも検出できない場合、どのログや統制が不足しているのか

したがって、合成環境上では、以下のような行動もシミュレーション対象にするべきである。

| 行動 | 研究上の扱い |
|---|---|
| 分割申請 | 実行し、Detectorが検出できるか見る |
| 実態より低い金額で申請 | 実行し、金額不整合を検出できるか見る |
| 緊急ルートの濫用 | 実行し、事後承認や理由コードで止まるか見る |
| 検収前支払 | 実行または試行し、Rule Engineが止めるか見る |
| 非公式チャット承認 | 既存Actionにない場合はAction候補として記録する |
| 比較見積省略 | 実行し、例外理由・承認有無を評価する |

ただし、実システムではなく、あくまで合成データ上の閉じた実験環境で実行する。

---

## 5. 方針転換: 単一行動選択から分岐探索へ

今後は、LLMに1つの行動を選ばせるだけではなく、**複数の行動案を提案させ、それぞれを別の分岐世界として実行する。**

これにより、ある場面から発生し得る複数の行動パターンを網羅的に観察できる。

### 5.1 新しい基本フロー

```text
初期状態
  ↓
LLMが複数の行動案を提案
  ↓
Action Grounderが各案をAction列に変換
  ↓
各Action列を別々のWorldとして実行
  ↓
各Worldでイベントログが発生
  ↓
途中でまた選択点があれば、さらに分岐
  ↓
各Worldの終端でRule Engine / Detector / Metricsを評価
  ↓
統制が止めた分岐、止めなかった分岐、検出できた分岐、検出できなかった分岐を比較
```

### 5.2 パラレルワールド型の理解

たとえば、175万円の購買ニーズに対してLLMが以下の5案を出したとする。

```text
A. 175万円を1件で申請する
B. 87.5万円を2件で申請する
C. 99.9万円で申請し、残りは後日申請する
D. 上長に相談してから申請する
E. 緊急発注ルートを相談する
```

この場合、1つの行動を選ぶのではなく、5つのWorldを作る。

```text
WORLD-A: 単一申請ルート
WORLD-B: 分割申請ルート
WORLD-C: 過少・残額後日ルート
WORLD-D: 上長相談ルート
WORLD-E: 緊急ルート相談ルート
```

さらに、WORLD-Dで上長が複数の返答をし得るなら、そこでも分岐する。

```text
WORLD-D-1: 上長が正規申請を指示
WORLD-D-2: 上長が緊急ルートを示唆
WORLD-D-3: 上長が購買担当に確認するよう指示
```

このように、複数の行動可能性をパラレルワールドとして展開し、最終的にどの分岐が統制不備候補につながるかを観察する。

---

## 6. 不正・虚偽に近い行動の扱い

### 6.1 実行方針

今後は、Action Grounderを「危険なものを実行しないための門番」としてだけ使わない。

代わりに、以下の役割を持たせる。

1. LLMの行動案をAction列に変換する
2. その行動が通常行動か、グレーか、規程違反か、虚偽・不正に近いかを分類する
3. 合成環境上で実行可能なものは実行する
4. システム上できないものは、試行イベントとして記録する
5. ActionDefinitionにないものは、Action Library候補として保存する

### 6.2 行動分類

| 分類 | 意味 | シミュレーション上の扱い |
|---|---|---|
| compliant | 規程上も通常業務上も問題ない | 実行 |
| gray_area | 規程上グレー、追加確認が必要 | 実行 |
| policy_violation | 規程違反だがシステム上は可能 | 実行 |
| misrepresentation | 申請内容が実態と違う | 実行。ただし虚偽フラグ必須 |
| system_blocked | システム制約上できない | 試行イベントのみ記録 |
| unsupported | 現行Actionでは表現不能 | 実行せず、Action候補化 |
| out_of_scope | PoC対象外、または実世界リスクが高すぎる | 実行しない |

### 6.3 過少申請の例

たとえば、LLMが以下を提案したとする。

> 実際には1,750,000円の購買ニーズだが、999,999円で申請し、承認閾値を下回るようにする。

従来は `disallowed` として実行しない扱いだった。

今後は、合成環境では以下のように実行する。

```json
{
  "action_id": "create_purchase_request",
  "classification": "misrepresentation",
  "parameters": {
    "reported_amount": 999999,
    "economic_amount": 1750000,
    "vendor_id": "VENDOR-014",
    "project_id": "PRJ-2026-Q2-017",
    "business_reason": "納期対応のため先行申請"
  },
  "policy_violation_flags": [
    "underreported_amount",
    "approval_threshold_avoidance"
  ]
}
```

このとき、シミュレーションでは以下を見る。

- 申請書上の金額だけで承認ルールが判定されるか
- 実質金額との差分を検出できるか
- どのログに実質金額が残るか
- Detectorが金額不整合を検出できるか
- 統制変更により検出可能になるか

---

## 7. Branching Simulation Mode

今後の新しい実行モードとして、`branching_proposal` を追加する。

### 7.1 RunConfig例

```yaml
behavior_mode: branching_proposal
branching:
  proposal_count_per_node: 5
  max_depth: 4
  beam_width: 5
  max_total_worlds: 100
  include_policy_violating_actions: true
  include_misrepresentation_actions: true
  require_action_classification: true
  execute_system_blocked_actions_as_attempts: true
  risk_guided_selection: true
```

### 7.2 パラメータの意味

| パラメータ | 意味 |
|---|---|
| proposal_count_per_node | 各場面でLLMに何案出させるか |
| max_depth | 何ステップ先まで探索するか |
| beam_width | 次に進める分岐数 |
| max_total_worlds | 1 Runで生成するWorld数の上限 |
| include_policy_violating_actions | 規程違反行動も仮説として含める |
| include_misrepresentation_actions | 虚偽・過少申請も合成環境で試す |
| require_action_classification | 行動分類を必須にする |
| execute_system_blocked_actions_as_attempts | ブロックされた行動も試行ログとして残す |
| risk_guided_selection | リスクが高い分岐を優先して探索する |

---

## 8. 探索爆発への対応

分岐探索では、各ステップで複数の行動案が出るため、World数が急増する。

そのため、初期実装では全探索ではなく、以下の制御を入れる。

### 8.1 Beam Search

各ステップでLLMが複数案を出す。  
ただし、次に進めるのはリスクスコア上位K件だけにする。

```text
LLMが10案を出す
Action Grounderが8案に変換
Rule Engineがリスクスコアを付ける
上位3案だけ次ステップへ進める
```

### 8.2 Risk-guided Search

統制上リスクの高い分岐を優先して探索する。

優先度が高い分岐の例:

- 承認閾値を回避しそう
- 緊急ルートに入る
- 検収前支払に近づく
- システム外相談が出る
- 取引先マスタ変更に絡む
- 金額・取引先・承認者の不整合がある

### 8.3 Stop条件

以下の条件でWorldを終了する。

- 支払完了
- Rule Engineにより実行不能
- 最大深さ到達
- 同一状態のループ検出
- 同一Action列の重複
- 対象外Actionのみになった
- 人間レビュー候補として十分な高リスク分岐を検出した

---

## 9. World管理

分岐探索では、各分岐をWorldとして管理する。

### 9.1 World ID

```text
WORLD-001
WORLD-001-001
WORLD-001-002
WORLD-002
```

### 9.2 World Event

各イベントには、`world_id` と `parent_world_id` を付与する。

```json
{
  "world_id": "WORLD-004-002",
  "parent_world_id": "WORLD-004",
  "branch_reason": "manager_suggested_emergency_route",
  "event_id": "EVT-000221",
  "action_id": "create_emergency_purchase_request",
  "classification": "gray_area",
  "state_before": "consulted_manager",
  "state_after": "emergency_requested"
}
```

### 9.3 World Summary

各Worldの終端で、以下を保存する。

```json
{
  "world_id": "WORLD-004-002",
  "parent_world_id": "WORLD-004",
  "status": "completed",
  "terminal_state": "paid",
  "depth": 4,
  "actions": [
    "consult_manager",
    "create_emergency_purchase_request",
    "approve_post_facto",
    "execute_payment"
  ],
  "classifications": [
    "compliant",
    "gray_area",
    "policy_violation"
  ],
  "triggered_controls": [
    "P2P-C-007"
  ],
  "detected_findings": [
    "emergency_abuse_suspected"
  ],
  "undetected_risks": [
    "informal_preapproval_not_logged"
  ]
}
```

---

## 10. 評価指標

### 10.1 分岐探索指標

| 指標 | 内容 |
|---|---|
| generated_world_count | 生成されたWorld数 |
| completed_world_count | 終端まで到達したWorld数 |
| blocked_world_count | Rule Engineやシステム制約で止まったWorld数 |
| unsupported_world_count | ActionDefinition不足で実行できなかったWorld数 |
| duplicate_world_count | 重複として除外されたWorld数 |
| average_depth | 平均分岐深さ |
| max_depth_reached_count | 最大深さに到達したWorld数 |

### 10.2 行動分類指標

| 指標 | 内容 |
|---|---|
| compliant_action_count | 通常行動数 |
| gray_area_action_count | グレー行動数 |
| policy_violation_action_count | 規程違反行動数 |
| misrepresentation_action_count | 虚偽・不整合を含む行動数 |
| system_blocked_attempt_count | システム制約で止まった試行数 |
| unsupported_action_candidate_count | 新Action候補数 |

### 10.3 統制評価指標

| 指標 | 内容 |
|---|---|
| control_block_rate | 高リスクActionをRule Engineが止めた割合 |
| detector_detection_rate | 高リスクWorldをDetectorが検出した割合 |
| undetected_high_risk_world_count | 高リスクだが検出されなかったWorld数 |
| residual_risk_world_count | 統制後も残るリスクWorld数 |
| control_gap_count | 統制・Detector・ログ不足として整理された件数 |

### 10.4 反実仮想比較指標

| 指標 | 内容 |
|---|---|
| worlds_removed_by_variant | Variantにより通らなくなったWorld数 |
| worlds_still_risky_under_variant | Variant下でも残る高リスクWorld数 |
| new_risk_worlds_under_variant | 統制変更により新たに発生した回避World数 |
| approval_load_delta | 承認負荷の変化 |
| manual_review_load_delta | 人間レビュー負荷の変化 |

---

## 11. 出力レポートイメージ

以下は、Branching Simulation Modeで出したいレポートのイメージである。

```markdown
# 分岐探索レポート: S-002 四半期末・納期圧力

## 1. 実行条件

| 項目 | 内容 |
|---|---|
| scenario | S-002 四半期末・納期圧力 |
| initial_purchase_need | NEED-001 |
| amount_total | 1,750,000 |
| variant | baseline |
| behavior_mode | branching_proposal |
| proposal_count_per_node | 5 |
| max_depth | 4 |
| beam_width | 5 |
| max_total_worlds | 100 |
| LLM model | gpt-4.1-mini |
| temperature | 0.7 |

## 2. 全体サマリ

| 指標 | 件数 |
|---|---:|
| 生成World数 | 83 |
| 完了World数 | 61 |
| Rule Engineで停止 | 9 |
| Action未対応 | 13 |
| 高リスクWorld | 37 |
| Detector検出済み | 26 |
| Detector未検出 | 11 |
| 人間レビュー推奨 | 18 |

## 3. 分岐タイプ別結果

| 分岐タイプ | 件数 | 統制で停止 | Detector検出 | 未検出 | 主な示唆 |
|---|---:|---:|---:|---:|---|
| 正規申請 | 12 | 0 | 0 | 0 | 通常ルートとして問題なし |
| 分割申請 | 18 | 4 | 14 | 0 | 合算判定がないと課長承認で通過 |
| 過少申請 | 9 | 2 | 3 | 4 | 実質金額との差分ログが不足 |
| 緊急ルート | 16 | 5 | 8 | 3 | 事後承認は効くが理由コード形骸化が残る |
| 非公式相談 | 10 | 0 | 0 | 10 | チャット証跡がないと検出不能 |
| 比較見積省略 | 8 | 1 | 4 | 3 | 例外理由の反復検知が必要 |

## 4. 代表World

### WORLD-B: 分割申請ルート

```text
NEED-001
  → create_purchase_request 875,000
  → create_purchase_request 875,000
  → manager approval x2
  → purchase_order_issued
  → paid
```

観察結果:

- 個別申請はいずれも100万円未満
- 合算額は175万円
- Baselineでは部長承認を通らずに進行
- split_order_detectorで検出

統制上の示唆:

- 現行統制は申請単位でしか承認閾値を見ていない
- 同一申請者・同一取引先・同一プロジェクト・近接日付の合算判定が必要

### WORLD-C: 過少申請ルート

```text
NEED-001 economic_amount=1,750,000
  → create_purchase_request reported_amount=999,999
  → manager approval
  → purchase_order_issued
```

観察結果:

- reported_amountでは承認閾値未満
- economic_amountとの差分が申請ログに残らない
- Detectorは一部のみ検出

統制上の示唆:

- 申請金額と契約・発注・請求金額の差分照合が必要
- 実質金額を保持するデータ項目が不足している場合、検出が難しい

### WORLD-E: 非公式相談ルート

```text
NEED-001
  → informal_preapproval_chat
  → create_purchase_request
  → approve
```

観察結果:

- 正式承認前にチャット上で実質的な合意が形成
- Workflow上は通常承認に見える
- 現行イベントログでは非公式相談が残らない

統制上の示唆:

- システム外コミュニケーションにより正式統制が形骸化する可能性
- 監査ログに残らないためDetectorでは検出不能
- 追加ヒアリングまたは承認コメント分析が必要

## 5. 統制変更比較

| 指標 | Baseline | Variant A: 7日以内合算 | Variant B: 緊急発注強化 |
|---|---:|---:|---:|
| 高リスクWorld数 | 37 | 24 | 29 |
| 分割申請World | 18 | 4 | 18 |
| 緊急ルートWorld | 16 | 15 | 6 |
| Detector未検出World | 11 | 8 | 9 |
| 承認負荷 | 中 | 高 | 中 |
| 人間レビュー負荷 | 中 | 高 | 高 |

解釈:

- Variant Aは分割申請には有効だが、過少申請・非公式相談には弱い
- Variant Bは緊急ルートには有効だが、分割申請には効かない
- 非公式相談はどちらのVariantでも検出困難
- 統制変更ごとに効く分岐タイプが異なる

## 6. 残余リスク

| 残余リスク | 理由 | 次の検討 |
|---|---|---|
| 過少申請 | 実質金額との差分ログがない | 契約・請求金額との照合Detector追加 |
| 非公式相談 | システム外で発生しログ化されない | 承認コメント、チャットログ、ヒアリング手続 |
| 業務パッケージ名変更 | 同一案件性の判定が難しい | 類似説明文・プロジェクトID照合 |
| 緊急理由の形骸化 | 理由コードだけでは実態を判断できない | 事後レビューと証跡必須化 |

## 7. 推奨アクション

1. 同一申請者・同一取引先・同一プロジェクト・近接日付の合算判定を追加する
2. 申請金額、契約金額、請求金額の差分Detectorを追加する
3. 緊急発注理由コードだけでなく、証跡添付と事後レビューを必須化する
4. 非公式事前合意のリスクについて、承認コメントやヒアリング手続を設計する
5. Action Libraryに `informal_preapproval_chat` を追加すべきか検討する
```

---

## 12. 今後の実装ステップ

### Step 1: Branching Proposalの最小実装

対象:

- D-001 分割発注
- D-002 緊急発注
- 過少申請
- 非公式相談

実装:

- LLMに複数proposalを出させる
- Action GrounderでAction列に変換する
- World IDを付ける
- World単位でEventを保存する
- World Summaryを出す

### Step 2: 不正・虚偽Actionのデータ構造追加

追加項目:

- `reported_amount`
- `economic_amount`
- `classification`
- `policy_violation_flags`
- `integrity_flags`

### Step 3: 分岐探索レポート作成

出力:

- `branching_summary.json`
- `world_summaries.json`
- `branching_report.md`
- `world_tree.json`
- `residual_risk_report.md`

### Step 4: Baseline / Variant比較

同じ分岐群をBaselineとVariantで実行し、以下を見る。

- どのWorldが止まるか
- どのWorldが依然として通るか
- 新たな回避Worldが出るか
- Detector未検出のWorldが減るか

### Step 5: 人間レビュー

内部統制・内部監査・業務担当者が以下を評価する。

- 分岐仮説が実務上あり得るか
- 検出結果が追加調査に値するか
- 統制改善案につながるか
- Action Libraryに追加すべき行動があるか

---

## 13. 研究上の整理

今回の方針転換により、研究の中心は以下に移る。

### 旧中心

> LLM疑似社員が1つの行動を選ぶ。その行動から統制すり抜けが自然発生するかを見る。

### 新中心

> LLMが複数の行動可能性を提案する。それぞれを分岐世界として実行し、どの行動列が統制で止まり、どの行動列が検出され、どの行動列が未検出で残るかを見る。

この変更により、研究目的はむしろ明確になる。

### 新しい主要問い

| 問い | 内容 |
|---|---|
| Q1 | LLMは、ある業務場面でどのような行動可能性を提案できるか |
| Q2 | 提案された行動可能性のうち、どれが通常行動、グレー行動、規程違反、虚偽行動に分類されるか |
| Q3 | それぞれの分岐を実行したとき、どの統制が止めるか |
| Q4 | 止まらなかった場合、Detectorが検出できるか |
| Q5 | Detectorでも検出できない場合、どのログ・統制・Action定義が不足しているか |
| Q6 | 統制変更により、どの分岐が消え、どの分岐が残るか |
| Q7 | 人間レビューで、どの分岐仮説が追加調査に値すると評価されるか |

---

## 14. 注意点と境界線

この方針では、不正・虚偽に近い行動も合成環境上で実行する。

そのため、以下の境界線を明確にする。

- 実在企業・実システムへの適用ではない
- 実データ・個人情報・取引先実名は使わない
- 不正を助長するためではなく、統制の有効性を検証するために行う
- 実行結果は監査結論ではなく、レビュー対象の仮説である
- 不正行動の分類、根拠、検出可否を必ず記録する
- 人間レビューなしに不備確定とはしない
- 実システム連携時はこのモードを無効化するか、厳格な承認を必須にする

---

## 15. 一言でまとめると

今後のPoCは、単一のLLM疑似社員に1つの行動を選ばせる実験から、**LLMが思いついた複数の行動可能性をパラレルワールドとして走らせる統制ストレステスト**へ移行する。

不正・虚偽に近い行動も、合成環境では実行してみる。  
そのうえで、Rule Engineが止めるか、Detectorが検出するか、ログや統制が不足しているかを観察する。

この方針により、当初の目的である **規程・マニュアルの書面レビューだけでは見えにくい統制の穴を検出する** というゴールに、より直接的に近づける。
