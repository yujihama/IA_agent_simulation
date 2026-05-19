# 内部統制LLMエージェント PoCプロトタイプ設計書

作成日: 2026-05-19

関連ドキュメント: [internal_control_llm_agent_poc.md](./internal_control_llm_agent_poc.md)

---

## 1. 目的

本書は、`internal_control_llm_agent_poc.md` の構想をもとに、PoCで実際に使用するプロトタイプの設計を具体化するものである。

プロトタイプの目的は、購買〜支払プロセスを対象に、以下を人間がレビュー可能な証跡付きで検証できる最小システムを作ることである。

- 現行統制下での購買〜支払イベントの再現
- 既知不備の検出
- 未知の統制すり抜け仮説の生成
- 統制変更案の反実仮想比較
- LLMエージェント利用時の再現性・説明可能性・限界の確認

このプロトタイプは監査判断を自動化するものではない。AI出力は、追加調査・統制見直し・専門家レビューのための仮説として扱う。

---

## 2. プロトタイプの設計方針

### 2.1 最小構成で検証する

最初のPoCでは、会社全体のデジタルツインを作らない。購買〜支払プロセスのうち、統制論点が明確で、イベントログ化しやすい範囲に限定する。

対象範囲:

- 購買依頼
- 金額別承認
- 発注
- 検収
- 請求書受領
- 3点照合
- 支払承認
- 支払実行
- 取引先マスタ変更
- 緊急発注・例外処理

対象外:

- 実ERPとの連携
- 実口座情報・個人情報の投入
- 複数国・複数会計基準対応
- 外部ニュースや市場データのリアルタイム連携
- AIによる内部統制評価・監査意見の自動確定

### 2.2 LLMを統制判定の唯一の根拠にしない

統制ルール、状態遷移、金額閾値、職務分掌、システム制約は、プロトタイプのルールエンジン側で明示的に管理する。

LLMの主な役割は以下に限定する。

- エージェントの行動選択
- 行動理由の生成
- ログからの不備候補説明
- 既存ルールでは拾いにくいすり抜け仮説の生成
- レポート文面の下書き

LLMが存在しない規程・統制ID・証跡を作らないように、参照可能な統制カードとイベントログを入力として制限する。

### 2.3 再現性を優先する

PoCでは、結果の完全な現実再現よりも、比較可能性とレビュー可能性を重視する。

- 乱数種を固定できる
- 実行条件をRunConfigとして保存する
- LLMプロンプト、モデル、温度、出力JSONを保存する
- 同一条件で再実行できる
- 統制変更案の比較では、統制条件以外を固定する

### 2.4 実装は「CLI + 軽量レビューUI」を推奨する

PoCの最小実装は、シミュレーションをCLIで実行し、結果を軽量なWeb UIで確認する構成とする。

推奨構成:

- シミュレーション・分析コア: Python
- 設定ファイル: YAML / JSON
- イベントログ: JSONL
- 集計・比較: Python + pandas
- 保存先: ローカルファイル + SQLite
- レビューUI: Streamlit
- 将来拡張時: FastAPI + Reactなどに置き換え可能

この構成により、PoC期間中は実験を素早く回しつつ、あとから本格アプリケーションへ分離しやすくする。

---

## 3. 想定ユーザーと利用シーン

| ユーザー | 主な目的 | プロトタイプ上の操作 |
|---|---|---|
| 内部統制担当者 | 統制不備候補と改善案を確認する | シナリオ実行、検出結果レビュー、統制変更比較 |
| 内部監査担当者 | 追加監査手続の仮説を得る | 不備候補の根拠イベント確認、レポート出力 |
| 業務担当者 | シミュレーションが実務に近いか確認する | イベントログ、承認リードタイム、例外処理の妥当性確認 |
| PoC運用者 | 実験条件を管理し、結果を再実行する | 設定ファイル編集、CLI実行、結果保存 |
| 技術担当者 | LLM・ルール・データ処理の品質を管理する | プロンプト、JSONスキーマ、モデル設定、テスト確認 |

---

## 4. ユースケース

### UC-001: 平常時プロセスを再現する

目的:

購買依頼から支払までの基本イベントが、統制ルールに沿って流れることを確認する。

入力:

- 平常時シナリオカード
- 合成購買申請データ
- 統制カード
- エージェントプロファイル

出力:

- イベントログ
- プロセスKPI
- 業務担当者レビュー用サマリ

受入条件:

- 申請、承認、発注、検収、請求、支払の主要イベントが欠落しない
- 金額別承認と発注前承認がルール通りに適用される
- 例外がないケースでは重大な統制違反が発生しない

### UC-002: 既知不備を検出する

目的:

埋め込み済みの不備を検出し、根拠イベントと関連統制を示せるか確認する。

対象不備:

- 分割発注による承認閾値回避
- 緊急発注ルートの濫用
- 取引先口座変更の確認不足
- 代理承認者の不適切設定
- 検収未了での支払
- 比較見積の省略
- 請求書重複支払

出力:

- 不備候補一覧
- 関連イベント
- 関連統制ID
- 重要度
- 追加確認事項

受入条件:

- 重要度Highの埋め込み不備を優先的に検出できる
- 不備候補ごとに少なくとも1つ以上の根拠イベントを提示する
- 「なぜ不備候補なのか」が統制カードにひも付いている

### UC-003: 未知のすり抜け仮説を生成する

目的:

外部環境や業務圧力により発生し得る統制迂回パターンを、追加調査仮説として提示する。

入力:

- 四半期末
- 重要顧客の納期前倒し
- 主要部材の供給不足
- 上長不在
- 支払期限直前の請求書到着

出力:

- すり抜け仮説
- 想定発生条件
- 関連統制
- 追加で確認すべきログ・証跡
- 想定される統制改善案

受入条件:

- 出力が「事実」ではなく「仮説」として明示される
- イベントログ上の観察事実と、LLMの推論部分が分離される
- 内部統制担当者が追加調査に使える粒度になっている

### UC-004: 統制変更案を比較する

目的:

現行統制と変更案を同一条件で比較し、リスク低減と業務副作用を確認する。

比較対象:

- Baseline: 現行統制
- Variant A: 同一申請者・同一取引先・7日以内の合算判定
- Variant B: 緊急発注の48時間以内事後承認と理由コード必須化

Variant C: 支払先口座変更の二者承認とコールバック確認、Variant D: 代理承認時の職務分掌チェックは次フェーズ候補とし、初回PoCではBaseline、Variant A、Variant Bを優先する。

出力:

- リスク指標比較
- 業務影響指標比較
- 統制変更ごとの解釈
- 推奨判断材料

受入条件:

- 同じ初期条件・同じ取引データ・同じシナリオで比較できる
- すり抜け成功率、統制違反件数、承認リードタイム、差戻し率を出せる
- 統制強化の副作用を明示できる

---

## 5. 全体アーキテクチャ

```mermaid
flowchart LR
    A["設定ファイル<br/>actions / controls / agents / scenarios / variants"] --> B["Run Orchestrator"]
    C["合成データ<br/>cases / vendors / org / invoices"] --> B
    B --> D["Simulation Engine"]
    D --> E["Rule Engine"]
    D --> F["LLM Agent Adapter"]
    F --> M["Action Grounder"]
    M --> D
    A --> M
    D --> G["Event Store<br/>JSONL + SQLite"]
    G --> H["Audit Analyzer"]
    E --> H
    H --> I["Findings Store"]
    G --> J["Metrics Aggregator"]
    I --> J
    J --> K["Comparison Reporter"]
    G --> L["Review UI"]
    I --> L
    K --> L
```

### 5.1 構成要素

| コンポーネント | 役割 |
|---|---|
| Run Orchestrator | 実行条件を読み込み、シミュレーション、監査分析、比較集計を順に呼び出す |
| Simulation Engine | 購買〜支払プロセスの状態遷移を管理する |
| Rule Engine | 統制カード、ActionDefinition、権限・職務分掌マスタに基づき、承認権限、職務分掌、発注前承認、3点照合などを判定する |
| LLM Agent Adapter | エージェントの行動選択と理由生成をLLMに依頼する |
| Action Grounder | Open Proposal Modeの行動案を既存Actionにマッピングできるか判定する |
| Event Store | すべてのイベント、LLM入出力、統制判定結果を保存する |
| Audit Analyzer | イベントログと統制カードを照合し、不備候補を抽出する |
| Metrics Aggregator | リスク指標、業務影響指標、AI信頼性指標を集計する |
| Comparison Reporter | BaselineとVariantの差分をレポート化する |
| Review UI | 実行結果、イベントログ、不備候補、比較結果を人間が確認する |

---

## 6. 推奨ディレクトリ構成

PoC開始時点では、以下の構成を推奨する。

```text
IA_agent_simulation/
  docs/
    internal_control_llm_agent_poc.md
    poc_prototype_design.md
  configs/
    actions/
      p2p_action_definitions.yaml
    controls/
      p2p_controls.yaml
    org/
      user_master.yaml
      approval_matrix.yaml
      delegation_rules.yaml
      sod_policies.yaml
    agents/
      p2p_agents.yaml
    scenarios/
      p2p_scenarios.yaml
    variants/
      p2p_control_variants.yaml
    run_configs/
      baseline.yaml
      counterfactual_split_order.yaml
  data/
    synthetic/
      org_units.csv
      approval_matrix.csv
      vendors.csv
      purchase_needs.csv
      invoices.csv
      ground_truth_labels.yaml
  src/
    ia_sim/
      __init__.py
      cli.py
      orchestrator.py
      simulation/
        engine.py
        state_machine.py
        actions.py
      controls/
        rule_engine.py
        models.py
      agents/
        llm_adapter.py
        prompt_builder.py
        schemas.py
      audit/
        detectors.py
        analyzer.py
        report_writer.py
      metrics/
        aggregator.py
        comparison.py
      storage/
        event_store.py
        run_store.py
  ui/
    streamlit_app.py
  runs/
    .gitkeep
    RUN-*/
      run_manifest.json
      events.jsonl
      findings.json
      metrics.json
  tests/
    test_state_machine.py
    test_rule_engine.py
    test_detectors.py
```

PoC段階では、`runs/` 配下に実行結果を保存する。機密データや実データを使う場合は、リポジトリ管理対象外にする。

---

## 7. データ設計

### 7.1 RunConfig

実行条件を固定し、再実行可能にするための設定である。

```yaml
run_id: auto
name: baseline_s002_budget_pressure
process: p2p
scenario_id: S-002
variant_id: baseline
seed: 20260519
behavior_mode: closed_action
comparison_mode: frozen_behavior
control_visibility:
  mode: summary
  include_thresholds: true
  include_prior_memory: true
  include_failure_modes: false
simulation:
  max_cases: 100
  max_steps_per_case: 30
  start_date: 2026-04-01
  end_date: 2026-06-30
llm:
  provider: openai
  model: configurable
  temperature: 0.2
  max_retries: 2
  structured_output: true
llm_logging:
  store_prompt_text: true
  store_response_text: true
  mask_personal_data: true
  mask_vendor_data: true
  mask_bank_account: true
inputs:
  actions: configs/actions/p2p_action_definitions.yaml
  controls: configs/controls/p2p_controls.yaml
  org_masters: configs/org/
  agents: configs/agents/p2p_agents.yaml
  scenarios: configs/scenarios/p2p_scenarios.yaml
  variants: configs/variants/p2p_control_variants.yaml
  purchase_needs: data/synthetic/purchase_needs.csv
evaluation_inputs:
  ground_truth_labels: data/synthetic/ground_truth_labels.yaml
outputs:
  dir: runs/{run_id}
```

`behavior_mode` のenum値は `closed_action` / `open_proposal`、`comparison_mode` のenum値は `frozen_behavior` / `adaptive_agent` に固定する。

### 7.2 ControlCard

統制カードは、人間が読める説明と、機械判定に使うパラメータを分けて保持する。

```yaml
control_id: P2P-C-001
name: 金額別承認
objective: 一定金額以上の購買について、適切な権限者の承認を得る
policy_ref:
  - 購買規程 第X条
  - 承認権限表 Ver.2026-01
trigger: purchase_request_submitted
control_type: preventive
owner: 申請部門
system_enforced: true
rule:
  type: approval_threshold
  thresholds:
    - min_amount: 0
      approver_level: manager
    - min_amount: 1000000
      approver_level: department_head
    - min_amount: 5000000
      approver_level: division_head
evidence:
  - workflow_approval_log
exception_allowed: true
exception_rule:
  type: emergency_post_approval
  due_hours: 48
failure_modes:
  - 発注金額の分割
  - 代理承認者の不適切設定
  - 緊急発注理由の形骸化
```

### 7.3 AgentProfile

エージェントの行動傾向は、プロファイルとして設定する。AgentProfileは意思決定傾向を表す設定であり、正式な権限判定・職務分掌判定の根拠にはしない。Rule Engineは後述の権限・職務分掌マスタを参照する。

```yaml
agent_id: AGENT-REQUESTER-001
user_id: USER-001
role: requester
display_name: 申請者A
department_id: DEPT-SALES
authority_level: none
objectives:
  - 顧客納期を守る
  - 予算を期限内に消化する
constraints:
  - 購買規程に従う必要がある
  - 100万円以上は部長承認が必要
behavior:
  compliance_attitude: normal
  risk_tolerance: medium
  workload: high
  deadline_pressure: high
memory:
  - 過去に90万円台の申請は課長承認で早く通った
  - 部長承認は平均3日かかる
allowed_action_set: requester_default
```

AgentProfileは、必ずUserMasterの `user_id` に紐づける。PurchaseNeed、PurchaseCase、Event、ApprovalMatrix、SoDPolicyでは、正式な権限判定に使うIDとして `user_id` を使用する。`agent_id` は、LLMエージェントの行動傾向、プロンプト、LLMログ管理のためのIDとする。

### 7.4 権限・職務分掌マスタ

Rule Engineは、金額別承認、職務分掌、代理承認、支払承認の判定時に、AgentProfileではなく以下のマスタを参照する。

UserMaster:

```yaml
user_id: USER-001
display_name: 申請者A
department_id: DEPT-SALES
role_ids:
  - requester
job_title: staff
active_from: 2026-04-01
active_to: null
```

ApprovalMatrix:

```yaml
approval_matrix_id: AM-001
department_id: DEPT-SALES
amount_min: 0
amount_max: 999999
required_approver_level: manager
effective_from: 2026-04-01
effective_to: null
```

DelegationRule:

```yaml
delegation_id: DEL-001
principal_user_id: USER-MGR-001
delegate_user_id: USER-MGR-002
valid_from: 2026-06-01
valid_to: 2026-06-15
allowed_amount_max: 999999
restricted_controls:
  - P2P-C-001
  - P2P-C-002
```

SoDPolicy:

```yaml
sod_policy_id: SOD-P2P-001
description: 申請、承認、支払実行は同一人物が兼務できない
incompatible_role_sets:
  - ["requester", "approver"]
  - ["requester", "payment_executor"]
  - ["approver", "payment_executor"]
scope:
  - same_case
  - related_cases
```

### 7.5 ScenarioCard

外部環境や業務圧力は、固定のシナリオカードとして定義する。

```yaml
scenario_id: S-002
name: 四半期末の予算消化
summary: 四半期末に未消化予算を使い切る必要があり、申請者と承認者の期限圧力が高い
pressure:
  deadline: high
  budget_consumption: high
  supplier_constraint: normal
  workload: high
behavioral_effects:
  requester:
    action_bias:
      - action_id: create_purchase_request
        bias: 0.0
      - action_id: select_request_route
        parameter_conditions:
          route_type: emergency
        bias: 0.2
      - action_id: consult_manager
        bias: -0.1
      - action_id: postpone_request
        bias: -0.3
  approver:
    action_bias:
      - action_id: approve
        bias: 0.2
      - action_id: request_revision
        bias: -0.2
      - action_id: request_additional_evidence
        bias: -0.1
  purchasing:
    action_bias:
      - action_id: request_quotes
        bias: -0.1
      - action_id: approve_quote_exception
        bias: 0.2
expected_risks:
  - P2P-R-001
  - P2P-R-002
```

`behavioral_effects` は、LLMへの自然文入力に加え、決定的PolicyやAction選択時の重みとしても利用する。Eventには、LLMが選んだAction、ScenarioCard上のAction Bias、最終採用Action、採用理由、Rule Engineによる許可・拒否結果を保存する。

### 7.6 PurchaseNeed

分割発注を中立Actionから自然に発生させるため、購買の元ニーズを表す `PurchaseNeed` と、実際の申請単位である `PurchaseCase` を分離する。PurchaseNeedはシミュレーションの入力単位である。

```yaml
purchase_need_id: NEED-001
requester_user_id: USER-001
department_id: DEPT-SALES
total_required_amount: 1800000
project_id: PRJ-2026-Q2-017
preferred_vendor_id: VENDOR-014
business_reason: 四半期末キャンペーンで必要
requested_delivery_date: 2026-06-20
remaining_amount: 1800000
status: open
```

`create_purchase_request` は、PurchaseNeedからPurchaseCaseを1件作成するActionとする。PurchaseNeedの `remaining_amount` が残っている場合、同じPurchaseNeedから追加のPurchaseCaseを作成できる。これにより、LLMに `submit_split_requests` を提示しなくても、複数の `create_purchase_request` が同一PurchaseNeedに紐づくことで、結果として分割発注疑いが発生する。

PurchaseNeed State:

| state | 意味 |
|---|---|
| open | まだ申請化されていない金額が残っている |
| partially_requested | 一部金額がPurchaseCase化されている |
| fully_requested | 必要金額がすべてPurchaseCase化された |
| cancelled | 購買ニーズ自体が取り消された |
| closed | 関連するPurchaseCaseが完了または終了した |

### 7.7 PurchaseCase

PurchaseCaseは、実際の購買申請単位である。1つのPurchaseNeedから複数のPurchaseCaseが作成される場合がある。

```yaml
case_id: PO-CASE-001
purchase_need_id: NEED-001
requester_user_id: USER-001
department_id: DEPT-SALES
item_category: marketing_service
item_description: 展示会向け販促制作の制作費
amount: 900000
vendor_id: VENDOR-014
requested_delivery_date: 2026-06-20
business_reason: 四半期末キャンペーンで必要
project_id: PRJ-2026-Q2-017
state: pending_approval
```

PurchaseCase State:

| state | 意味 |
|---|---|
| draft | 申請作成中 |
| pending_approval | 承認待ち |
| returned | 差戻し |
| rejected | 却下 |
| approved | 承認済み |
| emergency_ordered | 緊急発注済み |
| post_approval_pending | 事後承認待ち |
| purchase_order_issued | 発注済み |
| goods_received | 検収済み |
| invoice_received | 請求書受領済み |
| matched | 3点照合完了 |
| match_exception | 3点照合差異 |
| payment_blocked | 支払停止 |
| payment_approved | 支払承認済み |
| paid | 支払済み |

`create_purchase_request` は、PurchaseNeedから新しいPurchaseCaseを作成し、そのPurchaseCaseを `route_type=normal` では `pending_approval`、`route_type=emergency` では `emergency_ordered` に遷移させるActionとする。

PurchaseNeedの `remaining_amount` が0になった場合、PurchaseNeedは `fully_requested` になる。PurchaseNeedの `remaining_amount` が残っている場合、同じPurchaseNeedから追加のPurchaseCaseを作成できる。

合成データに埋め込んだ不備の正解ラベルは、PurchaseCaseには含めない。正解ラベルは評価時のみ参照する `ground_truth_labels.yaml` に分離する。

### 7.8 Event

イベントログは、すべての分析の基礎になる。Raw Eventには、原則として観察事実のみを1イベント1行のJSONLで保存する。`possible_split_order` のようなリスク推定ラベルは、Detector実行後のAnnotationまたはFindingに保存する。

```json
{
  "event_id": "EVT-000102",
  "run_id": "RUN-20260519-001",
  "case_id": "PO-CASE-001",
  "purchase_need_id": "NEED-001",
  "timestamp": "2026-05-19T10:30:00+09:00",
  "step": 4,
  "actor_agent_id": "AGENT-REQUESTER-001",
  "actor_user_id": "USER-001",
  "actor_role": "requester",
  "action_id": "create_purchase_request",
  "action_label": "購買申請を登録",
  "llm_call_id": "LLM-CALL-000045",
  "input_snapshot_hash": "sha256:...",
  "amount": 900000,
  "vendor_id": "VENDOR-014",
  "related_case_ids": ["PO-CASE-002"],
  "state_before": "draft",
  "state_after": "pending_approval",
  "llm_reason": "部長承認では納期に間に合わない可能性があるため、先に制作費の申請を進める",
  "action_validation": {
    "status": "passed",
    "schema_version": "action_schema_v1",
    "retry_count": 0
  },
  "rule_evaluation_ids": ["RULE-EVAL-000201"],
  "deterministic_policy_used": false,
  "control_results": [
    {
      "control_id": "P2P-C-001",
      "result": "passed",
      "reason": "個別申請金額が100万円未満のため課長承認対象"
    }
  ],
  "rule_warning_flags": [],
  "evidence_refs": ["workflow_log:WF-00088"]
}
```

`llm_reason` は説明であり、統制判定の根拠にはしない。統制判定の根拠は `control_results` と `rule_evaluation_ids` に保持する。LLMへの入力全文はLLMログに保存し、Eventには `llm_call_id` と `input_snapshot_hash` を持たせる。

Detector Annotation:

```json
{
  "annotation_id": "ANN-0001",
  "run_id": "RUN-20260519-001",
  "event_ids": ["EVT-000102", "EVT-000115"],
  "detector_id": "split_order_detector",
  "risk_flag": "possible_split_order",
  "confidence": "medium"
}
```

運用ルール:

- DetectorはRaw Event、PurchaseNeed、PurchaseCase、ControlCard、Masterのみを入力とする
- DetectorはGround Truth Labelや事後Annotationを参照しない
- リスク推定ラベルはFinding生成後の説明・UI表示用に使う
- Eventに入れる場合は、`rule_warning_flags` と `detector_flags` を分離する

### 7.9 Finding

不備候補は、機械検出結果とLLMによる説明を分離して保持する。

```yaml
finding_id: FIND-0001
run_id: RUN-20260519-001
title: 分割発注による承認閾値回避の疑い
finding_type: split_order_suspected
severity: high
confidence: medium
evidence_strength: high
status: needs_human_review
related_controls:
  - P2P-C-001
related_cases:
  - PO-CASE-001
  - PO-CASE-002
detected_by:
  deterministic_rules:
    - split_order_detector
  llm_analysis:
    - audit_synthesis_agent
evidence_events:
  - EVT-000102
  - EVT-000115
observed_facts:
  - 同一申請者が同一取引先へ同日に90万円と85万円の申請を登録
  - 合算額は175万円で部長承認閾値を超える
deterministic_basis:
  detector_id: split_order_detector
  rule_version: split_order_detector@v1
  matched_conditions:
    - same_requester
    - same_vendor
    - same_project
    - within_7_days
    - combined_amount_exceeds_threshold
llm_interpretation:
  summary: 申請単位の金額別承認のみで合算判定がないため、承認権限回避の可能性がある
  limitations:
    - 申請者の意図はログのみでは断定できない
    - 正当な分割発注の可能性がある
human_review:
  review_status: needs_more_evidence
  reviewer_id: null
  reviewer_comment: null
  reviewed_at: null
```

`observed_facts` にはイベントログで確認できる事実のみを書く。推論、解釈、仮説は `llm_interpretation` に分離する。`human_review.review_status` が `accepted` になるまでは、不備確定として扱わない。

### 7.10 Ground Truth Label

合成データに埋め込んだ不備の正解ラベルは、シミュレーション入力や監査分析入力には含めない。評価時のみ参照する別ファイルとして管理する。

```yaml
case_id: PO-CASE-001
purchase_need_id: NEED-001
related_case_ids:
  - PO-CASE-002
seeded_deficiency_id: D-001
expected_detector:
  - split_order_detector
expected_related_controls:
  - P2P-C-001
severity_label: high
evaluation_group_id: GT-D001-0001
```

運用ルール:

- `purchase_needs.csv` および生成後のPurchaseCaseには `seeded_deficiency_id` を含めない
- 正解ラベルは `data/synthetic/ground_truth_labels.yaml` に保存する
- Detector、LLM Agent、Audit Analyzerから正解ラベルを参照できないようにする
- 評価時にのみ、FindingとGround Truthを照合する
- 分割発注のように複数Caseにまたがる不備は、`evaluation_group_id` 単位で評価する

### 7.11 Run Manifest

各Runの開始時に `run_manifest.json` を生成し、Run単位の再現性を担保する。

```json
{
  "run_id": "RUN-20260519-001",
  "created_at": "2026-05-19T10:00:00+09:00",
  "scenario_id": "S-002",
  "variant_id": "baseline",
  "seed": 20260519,
  "behavior_mode": "closed_action",
  "comparison_mode": "frozen_behavior",
  "code_version": "git:abcdef123456",
  "config_hashes": {
    "actions": "sha256:...",
    "controls": "sha256:...",
    "agents": "sha256:...",
    "scenarios": "sha256:...",
    "variants": "sha256:...",
    "run_config": "sha256:..."
  },
  "data_hashes": {
    "purchase_needs": "sha256:...",
    "vendors": "sha256:...",
    "approval_matrix": "sha256:...",
    "invoices": "sha256:..."
  },
  "llm": {
    "provider": "openai",
    "model": "configurable",
    "temperature": 0.2,
    "structured_output": true,
    "logging": {
      "store_prompt_text": true,
      "mask_personal_data": true,
      "mask_vendor_data": true,
      "mask_bank_account": true
    }
  },
  "outputs": {
    "events_jsonl": "runs/RUN-20260519-001/events.jsonl",
    "findings_json": "runs/RUN-20260519-001/findings.json",
    "metrics_json": "runs/RUN-20260519-001/metrics.json"
  }
}
```

Run Manifestは、比較レポート、レビューUI、Markdown出力に必ず表示する。

---

## 8. 状態遷移設計

### 8.1 State Enum

状態名はすべてsnake_caseの内部enumで統一する。

| 表示名 | 内部enum |
|---|---|
| Draft | draft |
| Pending Approval | pending_approval |
| Returned | returned |
| Rejected | rejected |
| Approved | approved |
| Emergency Ordered | emergency_ordered |
| Post Approval Pending | post_approval_pending |
| Purchase Order Issued | purchase_order_issued |
| Goods Received | goods_received |
| Invoice Received | invoice_received |
| Matched | matched |
| Match Exception | match_exception |
| Exception Escalated | exception_escalated |
| Payment Blocked | payment_blocked |
| Payment Approved | payment_approved |
| Paid | paid |
| Deadlocked | deadlocked |
| Agent Action Failed | agent_action_failed |
| Max Steps Reached | max_steps_reached |

Event、ActionDefinition、State Machine、テストでは、上記の内部enumのみを使用する。

購買案件は、以下の状態を持つ。

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> pending_approval: create_purchase_request(route_type=normal)
    draft --> emergency_ordered: create_purchase_request(route_type=emergency)
    pending_approval --> emergency_ordered: select_request_route(route_type=emergency)
    pending_approval --> rejected: reject
    pending_approval --> returned: request_revision
    returned --> draft: revise
    pending_approval --> approved: approve
    approved --> purchase_order_issued: issue_purchase_order
    emergency_ordered --> post_approval_pending: require_post_approval
    post_approval_pending --> purchase_order_issued: approve_post_facto
    post_approval_pending --> exception_escalated: post_approval_overdue
    purchase_order_issued --> goods_received: receive_goods
    purchase_order_issued --> invoice_received: receive_invoice_before_goods
    goods_received --> invoice_received: receive_invoice
    invoice_received --> matched: three_way_match_passed
    invoice_received --> match_exception: three_way_match_failed
    match_exception --> matched: resolve_exception
    match_exception --> payment_blocked: unresolved_exception
    matched --> payment_approved: approve_payment
    payment_approved --> paid: execute_payment
    paid --> [*]
```

例外状態:

| 状態 | 意味 | 主なリスク |
|---|---|---|
| returned | 差戻し | リードタイム増加、再申請時の分割 |
| rejected | 却下 | 代替ルート・緊急発注への移行 |
| emergency_ordered | 緊急発注 | 事前統制の省略、例外の常態化 |
| post_approval_pending | 事後承認待ち | 48時間超過、形式的承認 |
| match_exception | 3点照合差異 | 過大請求、重複請求、検収不足 |
| exception_escalated | 事後承認期限超過などにより上位者確認が必要 | 例外処理の滞留、形式的承認 |
| payment_blocked | 3点照合差異や検収不足により支払停止 | 支払遅延、支払例外処理への迂回 |
| agent_action_failed | LLMまたはAction検証失敗により処理不能 | 再現性不足、ActionDefinition不足 |
| deadlocked | 実行可能なActionがなく、案件が進まない | 状態遷移設計漏れ |
| max_steps_reached | 最大Step数に到達し、強制終了 | ループ、例外処理滞留 |

First Vertical Sliceでは、申請ルート選択を `create_purchase_request` の `route_type` パラメータとして扱う。`route_type=normal` の場合は `pending_approval`、`route_type=emergency` の場合は `emergency_ordered` へ進み、緊急発注では事後承認を要求する。

`select_request_route` は、次フェーズまたは緊急ルート詳細化時に、既存PurchaseCaseのルート変更Actionとして扱う。`select_request_route` の `route_type` は `normal` / `emergency` に限定する。

### 8.2 Simulation Step の定義

Simulation Engineは、各購買案件について、以下の順序で1 stepを処理する。

1. 現在の案件状態、担当エージェント、ScenarioCard、ControlCard、AgentProfileを読み込む
2. State MachineとRule Engineに基づき、現在状態で実行可能な `allowed_actions` を生成する
3. `allowed_actions` が空の場合は、案件を `deadlocked` として記録し、処理を終了する
4. Closed Action Modeでは、LLM Agent Adapterまたは決定的Policyにより、実行するActionを1つ選択する
5. Open Proposal Modeでは、LLMが行動案を提案し、Action Grounderが既存Actionへの変換可否を判定する
6. Action Schemaに基づき、必須パラメータ、型、値域、参照IDの存在を検証する
7. Rule Engineが、Actionの実行可否、統制判定、警告、違反候補を評価する
8. Actionの副作用として、案件状態、金額、取引先、承認者、関連案件などを更新する
9. Event Storeに、Action、状態遷移、統制判定結果、LLM call_id、Raw Eventの観察事実を保存する
10. 終了状態に到達した場合は、案件を `completed` とする
11. `max_steps_per_case` に到達した場合は、案件を `max_steps_reached` として終了する

Detectorは原則としてRun終了後に実行する。ただし、将来的にリアルタイム検知を検証する場合は、stepごとに一部Detectorを実行できる拡張余地を残す。

---

## 9. 行動設計

### 9.1 行動空間の設計方針

LLMエージェントの行動空間は、目的に応じて以下の2種類に分ける。

#### Closed Action Mode

Closed Action Modeでは、LLMエージェントは環境が提示する `allowed_actions` からのみ行動を選択する。

このモードの目的は以下である。

- 業務プロセスの安定した再現
- 既知不備の検出評価
- BaselineとVariantの反実仮想比較
- 統制ルール、状態遷移、イベントログの検証
- 再現性と比較可能性の確保

Closed Action Modeでは、エージェントが自由に新しいActionを作成することは許可しない。また、Action名は監査上の不備パターンを直接示さないようにする。

`submit_split_requests` のような行動名は、分割発注という不備仮説をエージェントに明示してしまうため、通常の行動選択では使用しない。代わりに、`create_purchase_request` などの中立的な業務操作を定義し、複数の購買申請が作成された結果として、Detectorが分割発注の疑いを判定する。

#### Open Proposal Mode

Open Proposal Modeでは、LLMエージェントに、実行Actionとは別に、自由記述で「意図する行動案」を提案させる。

このモードの目的は以下である。

- 未知のすり抜け仮説の探索
- 現行のActionDefinitionで表現できない現場行動の発見
- Action Libraryの不足点の洗い出し
- 次フェーズのシナリオ・Detector設計への入力作成

Open Proposal Modeで提案された行動は、直ちに実行しない。環境側のAction Grounderが、既存のActionDefinitionに変換できるかを判定する。

- 変換できる場合: 既存Actionにマッピングして実行する
- 変換できない場合: `unsupported_action_candidate` としてログに残し、人間レビュー対象にする

これにより、PoCでは再現性と監査可能性を保ちつつ、未知の行動仮説も収集できる。

### 9.2 行動候補

LLMエージェントは、Closed Action Modeでは自由記述で行動を作らない。環境が提示する `allowed_actions` から選択する。

申請者:

| action_id | 内容 | 主なパラメータ | 備考 |
|---|---|---|---|
| create_purchase_request | 購買申請を1件作成する | amount, vendor_id, project_id, item_description, business_reason, requested_delivery_date, route_type | 分割かどうかはDetectorが後から判定する |
| select_request_route | 通常・緊急などの申請ルートを選ぶ | route_type, reason | 既存PurchaseCaseのルート変更Action。First Vertical Sliceでは原則使わない |
| edit_purchase_request | 申請内容を修正する | amount, vendor_id, project_id, reason | 差戻し後の再申請にも使う |
| consult_manager | 上長に相談する | question | 自然な業務行動 |
| consult_purchasing | 購買担当に相談する | question | 例外処理や取引先選定に使う |
| postpone_request | 申請を延期する | reason | 業務影響を見るために残す |
| propose_behavior | 実行前に自由記述で行動案を提案する | intended_goal, proposed_behavior, expected_effect | Open Proposal Mode専用 |

`propose_behavior` はOpen Proposal Mode専用であり、Closed Action Modeの `allowed_actions` には含めない。

`submit_split_requests` は、Ground Truth生成用またはシナリオ注入用の内部Actionとしては利用可能とする。ただし、LLMエージェントに提示する通常の `allowed_actions` には含めない。

分割発注は、LLMが `submit_split_requests` を選ぶことで発生させるのではなく、複数の `create_purchase_request` が同一申請者・同一取引先・近接日付・同一プロジェクトで作成された結果として、Detectorが `split_order_suspected` と判定する。

承認者:

| action_id | 内容 | 主なパラメータ |
|---|---|---|
| approve | 承認する | comment |
| reject | 却下する | reason |
| request_revision | 差戻す | required_revision |
| request_additional_evidence | 追加資料を求める | evidence_type |
| delegate_approval | 代理承認者へ回す | delegate_id |
| ask_purchasing_review | 購買担当確認へ回す | review_reason |

購買担当:

| action_id | 内容 | 主なパラメータ |
|---|---|---|
| request_quotes | 見積を依頼する | vendor_ids |
| select_vendor | 取引先を選定する | vendor_id, selection_reason |
| issue_purchase_order | 発注する | po_id |
| approve_quote_exception | 比較見積省略を認める | exception_reason |
| request_vendor_master_change | 取引先マスタ変更を依頼する | change_type |

経理担当:

| action_id | 内容 | 主なパラメータ |
|---|---|---|
| perform_three_way_match | 3点照合する | invoice_id |
| reject_invoice | 請求書を差戻す | reason |
| approve_payment | 支払承認する | payment_id |
| create_payment_exception_request | 支払例外処理を申請する | exception_reason, due_date, evidence_refs |
| approve_payment_exception | 支払例外処理を承認する | approver_id, approval_comment |
| verify_bank_account_change | 口座変更を確認する | verification_method |

支払例外処理が不備かどうかは、Action名ではなく、検収有無、3点照合結果、承認者権限、証跡有無からDetectorが判定する。

取引先:

| action_id | 内容 | 主なパラメータ |
|---|---|---|
| submit_quote | 見積を提示する | amount, delivery_date |
| deliver_goods | 納品する | delivery_date, quantity |
| submit_invoice | 請求書を送付する | invoice_id, amount |
| request_bank_change | 支払口座変更を依頼する | new_bank_account_id |

### 9.3 ActionDefinition

LLMエージェントが選択できるActionは、以下のActionDefinitionとして定義する。LLMは自由記述で新しいActionを作成できない。

```yaml
action_id: create_purchase_request
actor_role: requester
description: 購買申請を1件作成する
allowed_states:
  - draft
required_parameters:
  purchase_need_id:
    type: string
  amount:
    type: integer
    min: 1
  vendor_id:
    type: string
  project_id:
    type: string
  item_description:
    type: string
  business_reason:
    type: string
  requested_delivery_date:
    type: date
  route_type:
    type: string
    enum:
      - normal
      - emergency
preconditions:
  - actor.role == requester
  - purchase_need.status == open
  - purchase_need.remaining_amount >= amount
state_transition:
  from: draft
  to:
    when:
      route_type=normal: pending_approval
      route_type=emergency: emergency_ordered
side_effects:
  - create_purchase_case
  - link_case_to_purchase_need
  - decrease_purchase_need_remaining_amount
  - set_route_type
  - set_request_amount
  - set_vendor_id
  - set_project_id
control_checks:
  - P2P-C-001
  - P2P-C-003
validation_failure_action: reject_and_retry
```

ActionDefinitionには、少なくとも以下を含める。

| 項目 | 内容 |
|---|---|
| action_id | Actionの一意ID |
| actor_role | 実行可能なロール |
| allowed_states | 実行可能な案件状態 |
| required_parameters | 必須パラメータと型 |
| preconditions | 実行前条件 |
| state_transition | 状態遷移 |
| side_effects | PurchaseNeed、PurchaseCase、関連案件、イベントへの影響 |
| control_checks | 当該Actionで評価する統制ID |
| validation_failure_action | 検証失敗時の扱い |

LLMが `allowed_actions` に含まれないActionを返した場合、または必須パラメータが欠ける場合は、再試行する。再試行上限を超えた場合は `no_valid_action` Eventを記録し、案件を `agent_action_failed` として処理する。

### 9.4 LLM行動選択の入出力

LLMへの入力は、行動選択に必要な情報だけに制限する。

入力:

```json
{
  "agent": {
    "agent_id": "AGENT-REQUESTER-001",
    "user_id": "USER-001",
    "role": "requester",
    "objectives": ["顧客納期を守る", "予算を期限内に消化する"],
    "behavior": {
      "compliance_attitude": "normal",
      "risk_tolerance": "medium",
      "deadline_pressure": "high"
    }
  },
  "purchase_need": {
    "purchase_need_id": "NEED-001",
    "total_required_amount": 1800000,
    "remaining_amount": 1800000,
    "requested_delivery_date": "2026-06-20",
    "preferred_vendor_id": "VENDOR-014",
    "project_id": "PRJ-2026-Q2-017"
  },
  "current_state": "draft",
  "scenario": {
    "scenario_id": "S-002",
    "name": "四半期末の予算消化",
    "pressure": {
      "deadline": "high",
      "budget_consumption": "high"
    }
  },
  "available_controls": [
    {
      "control_id": "P2P-C-001",
      "summary": "100万円以上は部長承認が必要"
    }
  ],
  "control_visibility": {
    "mode": "summary",
    "include_thresholds": true,
    "include_prior_memory": true,
    "include_failure_modes": false
  },
  "allowed_actions": [
    "create_purchase_request",
    "consult_manager",
    "consult_purchasing",
    "postpone_request"
  ],
  "memory": [
    "過去に90万円台の申請は課長承認で早く通った"
  ]
}
```

出力:

```json
{
  "selected_action": "create_purchase_request",
  "parameters": {
    "purchase_need_id": "NEED-001",
    "amount": 900000,
    "vendor_id": "VENDOR-014",
    "project_id": "PRJ-2026-Q2-017",
    "item_description": "展示会向け販促制作の制作費",
    "business_reason": "四半期末キャンペーンで必要",
    "requested_delivery_date": "2026-06-20",
    "route_type": "normal"
  },
  "reason": "納期圧力が高く、先に制作費の申請を進めるため",
  "known_control_consideration": "100万円以上は部長承認が必要であることを認識している",
  "confidence": 0.72
}
```

バリデーション:

- `selected_action` が `allowed_actions` に含まれない場合は拒否する
- 必須パラメータが欠ける場合は再試行する
- 再試行上限を超えた場合は `no_valid_action` イベントを記録する
- LLMの理由はログに残すが、統制判定はRule Engineで行う

### 9.5 Open Proposal Modeの出力スキーマ

Open Proposal Modeでは、LLMエージェントは実行Actionを直接返すのではなく、以下の形式で行動案を提案する。

```json
{
  "intended_goal": "納期に間に合わせつつ、承認を早く通したい",
  "proposed_behavior": "同じプロジェクトの費用を、制作費と運営費として別々に申請する",
  "expected_effect": "それぞれの申請が通常の課長承認で進む可能性がある",
  "required_system_operations": [
    "購買申請を2件作成する",
    "同じ取引先を指定する",
    "異なる費目説明を付ける"
  ],
  "compliance_concern": "実質的には同一案件の合算判定を避けている可能性がある"
}
```

環境側のAction Grounderは、この提案を既存Actionに変換できるか判定する。

変換できる場合:

```yaml
proposal_status: mapped_to_existing_actions
mapped_actions:
  - create_purchase_request
  - create_purchase_request
proposal_flags:
  - possible_split_order
review_required: true
```

変換できない場合:

```yaml
proposal_status: unsupported_action_candidate
reason: 現在のActionDefinitionではチャット上の非公式合意を表現できない
candidate_new_action:
  action_id: informal_pre_approval_chat
  description: 正式申請前に上長または購買担当からチャットで非公式了承を得る
review_required: true
```

Open Proposal Modeの提案は、未知仮説探索の材料であり、統制不備の確定結果として扱わない。

Action Grounderは、Open Proposal Modeで提案された行動案を、以下の基準で判定する。

| 判定 | 意味 | 処理 |
|---|---|---|
| mapped | 既存ActionDefinitionの組み合わせで表現できる | `mapped_actions` を生成し、Simulation Engineへ渡す |
| partially_mapped | 一部は既存Actionで表現できるが、一部が未対応 | 実行可能部分のみ候補化し、未対応部分をunsupportedとして記録 |
| unsupported | 既存ActionDefinitionでは表現できない | `candidate_new_action` として保存し、人間レビュー対象にする |
| rejected | 規程上・システム上・安全上、実行対象にしない | `rejected_proposal` として保存する |

Action Grounderは、以下を必ず記録する。

```yaml
proposal_id: PROP-0001
proposal_status: partially_mapped
mapped_actions:
  - create_purchase_request
  - create_purchase_request
unsupported_elements:
  - informal_pre_approval_chat
reason: チャット上の非公式合意は現行ActionDefinitionに存在しない
review_required: true
```

Open Proposal Modeの出力は、直接実行結果ではなく、Action Library改善と未知仮説探索の材料として扱う。

Open Proposal Modeで生成された `proposal_flags` は、未知仮説探索のためのメタ情報であり、Closed Action ModeのDetector性能評価には使用しない。

評価時は以下を分離する。

| 区分 | 評価対象 |
|---|---|
| Closed Action Mode | Event列からDetectorが不備候補を検出できたか |
| Open Proposal Mode | Action Library外の有用な行動仮説を生成できたか |
| Action Grounder | 提案行動を既存Actionへ正しくマッピングできたか |

`proposal_flags` はFinding候補の説明には使えるが、Precision / Recall算定時のDetector入力には含めない。

### 9.6 Action Space評価指標

LLMエージェントの行動空間が研究結果に与える影響を評価するため、以下の指標を追加する。

| 指標 | 内容 |
|---|---|
| action_space_coverage | 専門家が想定する代表的業務行動のうち、ActionDefinitionで表現できる割合 |
| unsupported_action_candidate_count | Open Proposal Modeで既存Actionに変換できなかった行動案の数 |
| useful_novel_action_rate | 人間レビューで有用と判断された新規行動案の割合 |
| action_label_leakage_risk | Action名が不備仮説を直接示していないかのレビュー結果 |
| neutral_action_ablation | 不備名を含むAction名と中立Action名で結果がどの程度変わるか |
| detector_derivation_rate | 不備Actionを直接選ばせず、イベントパターンからDetectorが不備候補を導けた割合 |

特に `neutral_action_ablation` は重要である。`submit_split_requests` を見せた場合と、`create_purchase_request` だけを見せた場合で、分割発注の発生率が大きく変わるなら、前者はエージェントの自律行動というより、Action名による誘導の影響が強いと解釈する。

---

## 10. 統制ルール設計

### 10.1 初期実装する統制

Rule Engineは、統制カード、ActionDefinition、権限・職務分掌マスタを組み合わせて判定する。AgentProfileは行動傾向の入力であり、権限判定の根拠にはしない。

| 統制ID | 実装方法 | 検出・判定ポイント |
|---|---|---|
| P2P-C-001 金額別承認 | 閾値ルール | 申請金額、合算金額、承認者権限 |
| P2P-C-002 職務分掌 | ロール・ユーザー照合 | 申請者、承認者、支払実行者の重複 |
| P2P-C-003 発注前承認 | 状態遷移制約 | 承認前の発注イベント |
| P2P-C-004 検収確認 | 必須イベント確認 | 検収前の支払承認 |
| P2P-C-005 3点照合 | PO・検収・請求書照合 | 金額、数量、取引先、請求番号 |
| P2P-C-006 取引先マスタ変更承認 | 変更ワークフロー | 二者承認、変更後支払、確認証跡 |
| P2P-C-007 緊急発注の事後承認 | 期限ルール | 48時間以内承認、理由コード |
| P2P-C-008 支払承認 | 権限・状態確認 | 支払承認者、照合完了、支払先 |

### 10.2 ルール判定結果

各イベントで、関連統制の判定結果を残す。

```json
{
  "control_id": "P2P-C-007",
  "result": "failed",
  "severity": "medium",
  "reason": "緊急発注から48時間以内に事後承認が完了していない",
  "evidence_event_ids": ["EVT-000201", "EVT-000244"],
  "rule_version": "p2p_controls.yaml@2026-05-19"
}
```

判定結果:

| result | 意味 |
|---|---|
| passed | 統制条件を満たした |
| failed | 統制条件に違反した |
| warning | 不備候補だが追加確認が必要 |
| not_applicable | 当該イベントでは対象外 |
| manual_review_required | 機械判定だけでは判断できない |

---

## 11. 監査分析設計

### 11.1 分析は2段階に分ける

監査分析は、決定的ロジックとLLM分析を分離する。

1. 決定的ロジックで不備候補を検出する
2. LLMで不備候補の説明、追加仮説、追加確認事項を生成する

これにより、LLMのもっともらしい説明に引きずられず、根拠イベントを明確にできる。

### 11.2 初期実装する検出器

| detector_id | 検出対象 | 主な条件 |
|---|---|---|
| split_order_detector | 分割発注 | 同一申請者・同一取引先・近接日付・同一プロジェクト・合算閾値超過 |
| emergency_abuse_detector | 緊急発注濫用 | 緊急理由反復、件数比率、事後承認遅延 |
| vendor_bank_change_detector | 口座変更リスク | 変更直後支払、二者承認欠落、確認証跡欠落 |
| sod_violation_detector | 職務分掌違反 | 申請、承認、支払実行の同一人物または同一ロール |
| goods_receipt_missing_detector | 検収未了支払 | 検収イベントなし、支払承認あり |
| quote_skip_detector | 比較見積省略 | 見積件数不足、例外理由反復 |
| duplicate_invoice_detector | 重複請求 | 同一請求番号、同一金額、同一取引先、近接日付 |

### 11.3 Detector詳細仕様

#### split_order_detector

目的:

承認閾値を回避するために、同一または関連する購買を複数申請に分割している疑いを検出する。

入力:

- Event logs
- PurchaseNeed
- PurchaseCase
- ApprovalMatrix
- ControlCard P2P-C-001
- VendorMaster
- Project ID

検出条件:

以下をすべて満たす場合、Finding候補を生成する。

1. 同一 `requester_user_id`
2. 同一 `purchase_need_id`、または同一 `vendor_id` かつ同一または類似 `project_id`
3. 申請日が `window_days` 以内
4. 個別金額は部長承認閾値未満
5. 合算金額は部長承認閾値以上
6. 個別申請が同一承認階層で承認されている

初期閾値:

```yaml
window_days: 7
min_combined_amount: 1000000
similar_description_threshold: 0.8
require_same_project_id: false
```

出力:

- `finding_type`: `split_order_suspected`
- `related_controls`: `[P2P-C-001]`
- `related_cases`
- `evidence_events`
- `combined_amount`
- `avoided_approval_level`
- `confidence`

限界:

- 意図的な分割か、正当な別案件かはログのみでは断定できない
- 案件IDやプロジェクトIDが未入力の場合、誤検知が増える
- 最終判断には承認者認識、申請理由、業務実態の確認が必要

#### emergency_abuse_detector

目的:

緊急発注ルートが通常購買の代替として反復利用されている疑いを検出する。

検出条件:

以下のいずれかを満たす場合、Finding候補を生成する。

1. 同一申請者または同一部門で、緊急発注率が一定閾値を超える
2. 同一理由コードの緊急発注が反復している
3. 48時間以内の事後承認が未完了
4. 緊急発注後に購買部門レビューが未実施
5. 平常時シナリオと比べて緊急発注率が有意に高い

初期閾値:

```yaml
emergency_rate_threshold: 0.2
same_reason_repeat_threshold: 3
post_approval_due_hours: 48
```

限界:

- 実際に緊急性があったかは、業務背景の確認が必要
- 外部環境シナリオによっては、緊急発注率が高いこと自体は合理的な場合がある

### 11.4 Severity / Risk Score の算定

Findingの重要度は、以下の4要素から算定する。

| 要素 | 内容 | スコア |
|---|---|---:|
| Impact | 想定影響額、支払額、承認回避額 | 1〜5 |
| Likelihood | 発生頻度、再発可能性、シナリオ上の発生しやすさ | 1〜5 |
| Control Evasion | 予防的統制を回避しているか、発見的統制でのみ検出可能か | 1〜5 |
| Evidence Strength | 根拠イベントの明確さ、関連イベント数、規程との対応 | 1〜5 |

初期スコアは以下で算出する。

```text
risk_score = Impact * Likelihood * Control_Evasion
```

Evidence Strengthは、重要度ではなくレビュー優先度の補正に使う。

| risk_score | severity |
|---:|---|
| 60以上 | high |
| 25〜59 | medium |
| 24以下 | low |

補足:

- `severity` はリスクの大きさを表す
- `confidence` は検出の確からしさを表す
- `review_status` は人間レビューの状態を表す
- severity、confidence、review_statusを混同しない

### 11.5 LLM監査分析の出力項目

LLMには、検出器が抽出した根拠イベントを渡し、以下の形式で説明を生成させる。

```json
{
  "finding_title": "分割発注による承認閾値回避の疑い",
  "classification": "運用不備候補",
  "related_controls": ["P2P-C-001"],
  "observed_facts": [
    "同一申請者が同一取引先に対して同日に2件の申請を登録している",
    "各申請は100万円未満だが、合算すると100万円を超える"
  ],
  "interpretation": "金額別承認が申請単位でのみ機能し、関連申請の合算判定がない可能性がある",
  "risk_impact": "権限者による承認を回避した発注が発生する可能性",
  "additional_procedures": [
    "案件IDまたはプロジェクトIDの一致を確認する",
    "承認者が関連申請を認識していたか確認する"
  ],
  "control_improvement_options": [
    "同一申請者・同一取引先・7日以内の合算判定を追加する",
    "案件ID入力を必須化する"
  ],
  "limitations": "ログ上の関連性からの推定であり、申請者の意図は追加確認が必要"
}
```

禁止事項:

- 存在しない規程条文を根拠として記載しない
- イベントログにない事実を観察事実として書かない
- AI出力だけで不備確定と書かない
- 監査意見を自動生成しない

---

## 12. 反実仮想比較設計

### 12.1 反実仮想比較モード

反実仮想比較は、以下の2モードで実施する。

#### Mode 1: Frozen Behavior Comparison

目的:

統制条件だけを変更した場合の直接効果を確認する。

方法:

- Baselineで生成されたエージェントの意図・初期Action候補・案件データを固定する
- Variantでは、可能な限り同一の行動意図を再生する
- Rule Engineと状態遷移のみをVariant条件に差し替える
- これにより、統制変更によって同じ行動が通るか、止まるかを比較する

用途:

- 統制ルールそのものの遮断効果を測る
- 分割発注、口座変更、職務分掌違反などの直接的な統制強化を評価する

#### Mode 2: Adaptive Agent Comparison

目的:

統制変更後に、エージェントが新しい統制を認識して行動を変える場合の副作用を確認する。

方法:

- Variant条件をLLMエージェントに提示する
- エージェントは新しい統制の下で再度Actionを選択する
- 代替回避行動、緊急発注化、申請延期、別取引先利用などを観察する

用途:

- 統制強化による現場の行動変化を見る
- 新たな例外ルートや副作用を探索する

PoCレポートでは、Frozen Behavior ComparisonとAdaptive Agent Comparisonの結果を混同しない。前者は統制の直接効果、後者は統制変更後の二次的影響として扱う。

### 12.2 実行単位

反実仮想比較は、以下の単位で実行する。

```text
Scenario x Variant x Seed x ComparisonMode
```

例:

| run_name | scenario | variant | seed | comparison_mode |
|---|---|---|---:|---|
| baseline_s002_seed1_frozen | S-002 | baseline | 101 | frozen_behavior |
| variant_a_s002_seed1_frozen | S-002 | variant_a | 101 | frozen_behavior |
| baseline_s002_seed1_adaptive | S-002 | baseline | 101 | adaptive_agent |
| variant_a_s002_seed1_adaptive | S-002 | variant_a | 101 | adaptive_agent |

同じseedでは、統制条件以外の初期データ、エージェントプロファイル、シナリオ圧力を同一にする。

### 12.3 Variant定義

```yaml
variant_id: variant_a
name: 7日以内合算判定
description: 同一申請者・同一取引先・同一プロジェクト・7日以内の申請を合算して承認閾値を判定する
overrides:
  controls:
    P2P-C-001:
      rule:
        aggregation:
          enabled: true
          window_days: 7
          keys:
            - requester_user_id
            - vendor_id
            - project_id
business_side_effects:
  approval_workload_multiplier: 1.2
  expected_return_rate_delta: 0.05
```

### 12.4 初回実装するVariant

初回PoCの実装対象は、以下に限定する。

| Variant | 実装優先度 | 理由 |
|---|---:|---|
| Baseline | 必須 | 現行統制の基準値 |
| Variant A: 7日以内合算判定 | 必須 | 分割発注検出と金額別承認の改善効果を検証しやすい |
| Variant B: 緊急発注の事後承認・理由コード必須化 | 必須 | 例外ルート濫用と業務副作用を検証しやすい |
| Variant C: 口座変更二者承認・コールバック | 次フェーズ | マスタ変更ワークフローの実装が必要 |
| Variant D: 代理承認時の職務分掌チェック | 次フェーズ | 組織・代理承認マスタの精緻化が必要 |

初回PoCでは、Baseline、Variant A、Variant Bを中心に、反実仮想比較の実装と評価方法を確立する。

### 12.5 比較指標

リスク指標:

- すり抜け成功率
- 統制違反件数
- 重大不備候補件数
- 想定影響額
- 検出までのステップ数

業務影響指標:

- 承認リードタイム
- 差戻し率
- 承認待ち件数
- 例外処理件数
- 手作業介入件数
- 担当者別負荷

AI信頼性指標:

- seedごとの結果ばらつき
- LLM不正JSON率
- LLM再試行率
- 監査エージェントの誤検知候補率
- 人間レビューでの有用判定率

Action Space指標:

- action_space_coverage
- unsupported_action_candidate_count
- useful_novel_action_rate
- action_label_leakage_risk
- neutral_action_ablation
- detector_derivation_rate

### 12.6 比較レポートの構成

```markdown
# 統制変更比較レポート

## 実行条件
- シナリオ
- 対象Variant
- 比較モード
- seed数
- 入力データ
- Run Manifest
- LLMモデル設定

## サマリ
- 最もリスク低減効果が高い案
- 業務副作用が大きい案
- 追加検証が必要な案

## 指標比較
| 指標 | Baseline | Variant A | Variant B | 解釈 |

## 不備候補の変化
| 不備候補 | Baseline | Variant A | Variant B |

## 業務副作用
| 影響 | 観察結果 | 留意点 |

## 推奨判断材料
- 採用候補
- 限定導入候補
- 継続検証候補
```

---

## 13. レビューUI設計

PoCのUIは、実験結果を人間がレビューするための軽量画面とする。業務システムのような入力画面は作り込まない。

### 13.1 画面一覧

| 画面 | 目的 | 主な表示項目 |
|---|---|---|
| Run一覧 | 過去の実行結果を選ぶ | run_id、シナリオ、Variant、seed、実行日時、ステータス |
| Runサマリ | 実行結果の全体像を確認する | ケース数、イベント数、不備候補数、主要KPI |
| イベントログ | 案件ごとの状態遷移を追う | タイムライン、actor、action、control_result、detector_annotations |
| 不備候補一覧 | 検出結果を確認する | severity、finding_type、関連統制、ステータス |
| 不備候補詳細 | 根拠イベントと説明を確認する | 観察事実、解釈、追加確認事項、関連イベント |
| 反実仮想比較 | 統制変更案の差分を見る | Baseline/Variant指標比較、グラフ、解釈 |
| LLM監査ログ | AI利用の再現性を確認する | prompt hash、model、temperature、response、validation結果 |
| レビュー進捗 | High findingのレビュー漏れを防ぐ | 未レビュー数、担当者、期限、ステータス |
| Confusion Matrix | Ground TruthとFindingの照合結果を確認する | TP、FP、FN、Partial Match |
| Detector別成績 | Detectorごとの誤検知・見逃し傾向を見る | precision、recall、partial match |
| Scenario別成績 | 外部環境ごとの不備発生傾向を見る | finding数、severity分布 |
| Action Space評価 | Open Proposal Modeの新規行動案を見る | unsupported candidate、有用判定 |

### 13.2 レビュー操作

PoCで必要な最小操作:

- 不備候補に `accepted` / `rejected` / `needs_more_evidence` / `duplicate` / `out_of_scope` を付ける
- レビューコメントを残す
- 関連イベントへジャンプする
- 不備候補レポートをMarkdownで出力する
- 比較レポートをMarkdownで出力する

表示例:

| 指標 | 件数 |
|---|---:|
| Ground Truth不備 | 25 |
| True Positive | 19 |
| False Positive | 6 |
| False Negative | 4 |
| Partial Match | 2 |
| 未レビューFinding | 8 |
| Unsupported Action Candidate | 5 |
| Useful Novel Action | 2 |

### 13.3 Ground Truth表示の権限制御

レビューUIでは、Ground Truth Labelの表示を以下の2モードに分ける。

Blind Review Mode:

- Ground Truth Labelを表示しない
- Confusion Matrixを表示しない
- Finding、Event、ControlCard、LLM説明のみを表示する

Evaluation Mode:

- Ground Truth Labelを表示する
- Confusion Matrixを表示する
- Precision / Recall / Partial Matchを表示する
- Detector別成績を表示する

原則として、Findingの `review_status` が付与されるまでは、Ground Truth情報を表示しない。

---

## 14. CLI設計

### 14.1 基本コマンド

```bash
ia-sim validate-config --config configs/run_configs/baseline.yaml
ia-sim run --config configs/run_configs/baseline.yaml
ia-sim analyze --run-id RUN-20260519-001
ia-sim compare --runs RUN-001 RUN-002 RUN-003 --output runs/comparison_report.md
ia-sim export-report --run-id RUN-20260519-001 --format markdown
```

### 14.2 コマンドの責務

| コマンド | 役割 |
|---|---|
| validate-config | YAML/JSONの必須項目、参照整合性、統制IDの存在を検証する |
| run | シミュレーションを実行し、イベントログを保存する |
| analyze | イベントログから不備候補を抽出する |
| compare | 複数Runを比較し、統制変更影響を集計する |
| export-report | Markdown/CSV/JSON形式で成果物を出力する |

---

## 15. LLM利用設計

### 15.1 LLM呼び出し箇所

| 呼び出し箇所 | 用途 | 構造化出力 | 温度の目安 |
|---|---|---|---:|
| 行動選択エージェント | allowed_actionsから行動を選ぶ | 必須 | 0.2〜0.5 |
| Open Proposalエージェント | 実行前の行動案を自由記述で提案する | 必須 | 0.4〜0.7 |
| 監査分析エージェント | 不備候補の説明・追加確認事項生成 | 必須 | 0.1〜0.3 |
| 仮説生成エージェント | 未知すり抜け仮説の生成 | 必須 | 0.4〜0.7 |
| レポート生成 | Markdown下書き | 任意 | 0.2〜0.4 |

### 15.2 LLMログ

各呼び出しで以下を保存する。

- call_id
- run_id
- case_id
- agent_id
- purpose
- model
- temperature
- prompt_hash
- prompt_text
- response_text
- parsed_json
- validation_result
- retry_count
- latency_ms
- token_usage

将来の実データ利用を見据え、LLM呼び出しログには以下のマスキング方針を適用する。

- 個人名は `USER-xxx` に置換する
- 取引先名は `VENDOR-xxx` に置換する
- 口座情報は保存せず、`BANK-ACCOUNT-HASH` のみ保存する
- 請求書番号はハッシュ化する
- `prompt_text` の保存可否はRunConfigで切り替える
- `prompt_text` を保存しない場合でも、`prompt_hash`、`template_version`、`input_snapshot_hash` は保存する

外部LLM APIを利用する場合は、Run Manifestに送信データ範囲、モデル名、ログ保存設定を記録する。

### 15.3 ガードレール

- 構造化出力を必須化する
- JSON Schemaで検証する
- allowed_actions外の行動を拒否する
- 統制IDは入力に含まれるものだけ参照可能にする
- 観察事実と推論を分ける
- 不備確定ではなく不備候補として出力する
- 人間レビュー状態を必ず持たせる

### 15.4 Control Visibility設定

LLMエージェントに提示する統制情報の粒度は、RunConfigで制御する。

```yaml
control_visibility:
  mode: summary
  include_thresholds: true
  include_prior_memory: true
  include_failure_modes: false
```

| mode | 内容 |
|---|---|
| none | 統制情報を提示しない |
| summary | 統制目的と主要閾値のみ提示する |
| full | 統制カードの詳細を提示する |
| redacted | 統制名は提示するが、具体閾値やfailure_modesは隠す |

評価時には、少なくとも以下を比較する。

- 閾値を提示した場合
- 閾値を提示しない場合
- 過去memoryを提示した場合
- 過去memoryを提示しない場合

これにより、エージェント行動が統制理解に基づくものか、プロンプト・memoryの誘導によるものかを確認する。

---

## 16. 合成データ設計

### 16.1 最小データ量

PoC初期は、以下の規模から開始する。

| データ | 件数目安 |
|---|---:|
| 部門 | 5 |
| ユーザー | 20 |
| 取引先 | 30 |
| PurchaseNeed | 100 |
| PurchaseCase | 100〜130 |
| 請求書 | 100〜130 |
| 埋め込み不備 | 20〜30 |

### 16.2 初回PoCの埋め込み不備対象

| 不備ID | 内容 | 初回PoC対象 | 件数目安 | 理由 |
|---|---|---|---:|---|
| D-001 | 分割発注 | 対象 | 5 | 金額別承認と反実仮想比較に直結する |
| D-002 | 緊急発注濫用 | 対象 | 5 | 外部環境シナリオとの関係を検証しやすい |
| D-003 | 口座変更確認不足 | 対象 | 3 | マスタ変更統制の代表例 |
| D-004 | 不適切代理承認 | 条件付き対象 | 3 | 代理承認マスタが整備できる場合に実装 |
| D-005 | 検収未了支払 | 対象 | 3 | 状態遷移と3点照合の妥当性確認に使える |
| D-006 | 比較見積省略 | 対象 | 4 | 外部圧力との関係を検証しやすい |
| D-007 | 重複請求 | 対象 | 2 | 決定的Detectorで検出しやすい |
| D-008 | 架空・関連当事者取引先 | 次フェーズ | 0 | 取引先属性と関連当事者データの設計が必要 |

D-008は、初回PoCでは設計候補として残し、合成データには埋め込まない。次フェーズで、取引先属性、住所、銀行口座、関連当事者情報、承認者との関係性データを設計したうえで実装する。

### 16.3 データ生成ルール

- 通常ニーズと不備を埋め込むニーズを混在させる
- `purchase_needs.csv` および生成後のPurchaseCaseには `seeded_deficiency_id` を含めない
- 正解ラベルは `data/synthetic/ground_truth_labels.yaml` に保存する
- 監査分析時には正解ラベルを隠す
- 評価時に正解ラベルと照合する
- 金額、日付、部署、取引先に現実的なばらつきを持たせる

---

## 17. 評価設計

### 17.1 定量評価

| 評価項目 | 指標 |
|---|---|
| 既知不備検出 | precision、recall、重要度Highの検出率 |
| 誤検知 | 人間レビューでrejectedになった割合 |
| 見逃し | Ground Truth Labelに存在するが未検出の件数 |
| 再現性 | 同一seed再実行時の主要指標差分 |
| 頑健性 | seed変更時の指標ばらつき |
| 構造化出力品質 | JSON validation failure rate |

### 17.2 既知不備検出の評価単位

既知不備検出の評価は、原則として `evaluation_group_id` 単位で行う。

| 評価区分 | 定義 |
|---|---|
| True Positive | Ground Truthの不備グループに対応するFindingが生成され、関連統制と不備種別が一致している |
| False Positive | Ground Truthに存在しない不備についてFindingが生成された |
| False Negative | Ground Truthに存在する不備グループについてFindingが生成されなかった |
| Partial Match | 不備の存在は検出したが、関連統制、関連案件、重要度のいずれかが不十分 |

Precision / Recallは以下で算出する。

```text
precision = true_positive / (true_positive + false_positive)
recall = true_positive / (true_positive + false_negative)
high_recall = high_severity_true_positive / high_severity_ground_truth_count
```

Partial Matchは、PoC初期ではTrue Positiveに含めず、別途件数を報告する。ただし、人間レビューで有用と判断された場合は、参考指標として扱う。

### 17.3 定性評価

人間レビューでは、以下を5段階で評価する。

| 評価観点 | 確認内容 |
|---|---|
| 業務妥当性 | イベントの流れが実務感覚から大きく外れていないか |
| 根拠明確性 | 不備候補がイベントと統制カードにひも付いているか |
| 追加調査可能性 | 監査手続や業務確認に落とせる粒度か |
| 統制改善への有用性 | 改善案の比較材料として使えるか |
| AI出力の信頼性 | もっともらしいが根拠のない記述が混ざっていないか |

### 17.4 Go / No-Go基準

Go条件:

- 重要度Highの埋め込み不備を概ね検出できる
- 不備候補の根拠イベントを追跡できる
- 統制変更案ごとのリスク低減と業務副作用を比較できる
- 専門家レビューで、追加調査に値する仮説が複数得られる

No-Go条件:

- LLM出力がイベントログや統制カードと結び付かない
- 同一条件の再実行で主要示唆が大きく変わる
- 説明が抽象的で追加監査手続に落とせない
- 業務担当者が主要行動を現実離れしていると評価する
- 架空の規程・証跡・システム制約を根拠にする

---

## 18. テスト設計

### 18.1 単体テスト

| 対象 | テスト内容 |
|---|---|
| State Machine | 不正な状態遷移が拒否されること |
| Rule Engine | 金額別承認、職務分掌、3点照合が期待通り判定されること |
| Detectors | 埋め込み不備の典型ケースを検出できること |
| JSON Schema | LLM出力の必須項目欠落を検出できること |
| Metrics | 指標計算が固定データで期待値になること |
| ActionDefinition | 未許可Action、必須パラメータ欠落、値域違反を拒否できること |

### 18.2 結合テスト

| テスト | 内容 |
|---|---|
| 平常時シナリオ | S-001で重大不備候補が過剰に出ないこと |
| 分割発注シナリオ | D-001をsplit_order_detectorが検出すること |
| 緊急発注シナリオ | 事後承認期限超過を検出すること |
| 口座変更シナリオ | 二者承認欠落と変更直後支払を検出すること |
| 反実仮想比較 | 同一seedでBaselineとVariantの差分が出ること |
| Ground Truth照合 | `evaluation_group_id` 単位でTP、FP、FN、Partial Matchを算出できること |

### 18.3 手動レビュー

初回PoCでは、以下を人間が確認する。

- 代表ケース10件のイベントタイムライン
- High finding全件
- LLM監査説明の根拠イベント
- 反実仮想比較レポートの解釈
- UI上で追跡しづらい箇所

---

## 19. セキュリティ・ガバナンス

### 19.1 データ取り扱い

- 初回PoCは合成データを原則とする
- 実データを使う場合は、個人名、取引先名、口座情報、請求番号を匿名化する
- 実データは `runs/` や `data/` に平文で置かない
- 外部LLM APIに送るデータ範囲を記録する
- 機密区分が高い文書は入力しない

### 19.2 AI利用統制

- LLM呼び出しログを保存する
- モデル、プロンプト、温度をRunConfigに残す
- AI出力は人間レビュー前に確定結果として扱わない
- レビュー結果を `accepted` / `rejected` / `needs_more_evidence` として保存する
- PoC結果を監査証拠そのものとして利用しない

---

## 20. 実装マイルストーン

### M1: 設定・データ基盤

成果物:

- ActionDefinition YAML
- ControlCard YAML
- 権限・職務分掌マスタ
- ScenarioCard YAML
- AgentProfile YAML
- 合成データCSV
- Ground Truth Label YAML
- RunConfig
- 設定バリデータ

完了条件:

- `validate-config` が通る
- Baseline実行に必要な入力が揃う

### M2: 決定的シミュレーションコア

成果物:

- 状態遷移
- ルールエンジン
- イベントログ出力
- 決定的PolicyによるAction選択
- LLMなしのS-001実行

完了条件:

- LLMを使わずに、S-001平常時シナリオを最後まで実行できる
- 主要イベントがJSONLに保存される
- 金額別承認、発注前承認、3点照合が判定される

### M2.5: LLM行動選択の導入

成果物:

- LLM Agent Adapter
- Prompt Builder
- JSON Schema validation
- LLMログ保存
- invalid action時のretry / fallback

完了条件:

- LLMが `allowed_actions` からActionを選択できる
- 不正JSON、未許可Action、必須パラメータ欠落を検出できる
- LLM出力失敗時に決定的Policyへfallbackできる

### M3: 監査分析

成果物:

- 主要検出器
- Finding生成
- LLM監査説明
- 不備候補Markdown出力

完了条件:

- D-001〜D-005の主要不備を検出できる
- 根拠イベントと関連統制を追跡できる

### M4: 反実仮想比較

成果物:

- Variant定義
- 複数Run実行
- Frozen Behavior / Adaptive Agent の比較モード
- 指標集計
- 比較レポート

完了条件:

- Baselineと2つ以上のVariantを比較できる
- リスク指標と業務影響指標を表で出せる

### M5: レビューUI

成果物:

- Run一覧
- イベントログ表示
- 不備候補一覧・詳細
- 比較結果表示
- Confusion Matrixとレビュー進捗表示
- Action Space評価表示
- レビューコメント保存

完了条件:

- 内部統制担当者が代表ケースと不備候補を追跡できる
- Markdownレポートを出力できる

---

## 21. 初回PoCで固定する判断

| 論点 | 初回PoCの判断 |
|---|---|
| 対象プロセス | 購買〜支払 |
| データ | 合成データを原則とする |
| UI | Streamlitによる軽量レビューUI |
| 実行方法 | CLIでRunを作成し、UIでレビュー |
| 保存形式 | JSONL + SQLite + Markdown |
| LLM役割 | 行動選択、監査説明、仮説生成 |
| 統制判定 | Rule Engineを主とし、LLMは補助 |
| 評価方法 | 埋め込み不備との照合 + 人間レビュー |
| 行動空間 | 通常実行はClosed Action Mode、未知仮説探索はOpen Proposal Mode |
| 初回Variant | Baseline、Variant A、Variant B |
| 実データ | 初回は使わない。必要なら次フェーズで匿名化ログを利用 |

---

## 22. First Vertical Slice

初回実装では、以下の最小シナリオを最優先で完成させる。

First Vertical Sliceは、初回PoC全体のうち、最初に実装する最小単位である。

- First Vertical Slice: S-002 × D-001 × P2P-C-001〜003 × Baseline / Variant A
- 初回PoC全体: Baseline / Variant A / Variant B、D-001〜D-007の主要不備

まずFirst Vertical Sliceを完成させ、Event → Detector → Finding → Review → Counterfactual Reportまでの流れを通す。その後、Variant BとD-002以降の不備シナリオを追加する。

### 22.1 対象シナリオ

- S-002: 四半期末の予算消化

### 22.2 対象不備

- D-001: 分割発注による承認閾値回避

### 22.3 対象統制

- P2P-C-001: 金額別承認
- P2P-C-002: 職務分掌
- P2P-C-003: 発注前承認

### 22.4 対象Variant

- Baseline
- Variant A: 7日以内合算判定

### 22.5 対象行動空間

Closed Action Mode:

- `create_purchase_request`
- `consult_manager`
- `consult_purchasing`
- `postpone_request`

Open Proposal Mode:

- `propose_behavior`

### 22.6 完了条件

- PurchaseNeed 100件の合成データを生成できる
- Baselineで分割発注疑いが発生する
- `submit_split_requests` をLLMに提示せず、複数の `create_purchase_request` の結果として分割発注疑いが発生する
- `split_order_detector` がD-001を検出する
- Variant Aで分割発注のすり抜け成功率が低下する
- EventからFindingまで根拠を追跡できる
- Open Proposal ModeでAction Library外の行動案を収集できる
- Streamlit UIで対象Findingのイベントタイムラインを確認できる
- Markdownで不備候補レポートと比較レポートを出力できる

---

## 23. 初回PoCと次フェーズの切り分け

初回PoCでは、合成データのみを利用し、Baseline、Variant A、Variant Bを実装対象とする。

Variant C、Variant D、匿名化実ログによる補正、実ERP連携、リアルタイム外部データ連携は次フェーズ以降の対象とする。

| 項目 | 初回PoC | 次フェーズ以降 |
|---|---|---|
| データ | 合成データのみ | 匿名化実ログで補正 |
| Variant | Baseline, A, B | C, D, その他 |
| 外部環境 | 固定ScenarioCard | 市況・取引先リスクデータ連携 |
| UI | Streamlit軽量レビュー | 業務利用向けUI |
| 判定 | 仮説・不備候補 | 継続モニタリング支援 |

---

## 24. 研究結果の表現ルール

本PoCでは、LLMエージェントの結果を以下のように表現する。

避ける表現:

- LLMが不備を発見した
- LLMが不正を検出した
- LLMが未知のすり抜けを自律的に発見した
- AIが内部統制上の不備を確定した

推奨する表現:

- LLMエージェントを含むシミュレーション環境において、不備候補が発生した
- Detectorがイベントログ上のパターンから不備候補を検出した
- Open Proposal Modeにより、Action Library外の行動仮説が提示された
- 人間レビューにより、追加調査に値する仮説として評価された
- Closed Action Modeでは、事前定義されたAction Library内で既知不備の再現と検出を評価した
- Open Proposal Modeでは、Action Library外の行動仮説を収集し、次フェーズのActionDefinition候補として整理した

LLMの出力は、監査判断や不備確定ではなく、追加調査・統制改善・シナリオ設計のための仮説として扱う。

---

## 25. 未決事項

PoC開始前に決めるべき事項は以下である。

| 論点 | 推奨初期値 | 決定者 |
|---|---|---|
| LLMモデル | 構造化出力に強いモデルを利用 | 技術担当 |
| 合成データの業種前提 | 製造業またはITサービス業のどちらかに固定 | 業務責任者 |
| 承認閾値 | 100万円、500万円を初期値にする | 内部統制担当 |
| 重要度判定基準 | 影響額、頻度、検出可能性でHigh/Medium/Low | 内部監査担当 |
| 人間レビュー担当 | 内部統制、購買、経理、内部監査から各1名 | PoC責任者 |
| 外部LLM利用可否 | 合成データのみなら可、実データ時は別途審査 | 情報セキュリティ |

---

## 26. 完成時の成果物

PoCプロトタイプ完成時には、以下が揃っている状態を目標とする。

- シミュレーション実行CLI
- ActionDefinition、統制カード、シナリオカード、エージェントプロファイル
- 権限・職務分掌マスタ
- 合成購買データ
- Ground Truth Label
- イベントログ
- 不備候補JSON / Markdownレポート
- 反実仮想比較レポート
- レビューUI
- LLM呼び出しログ
- 評価結果サマリ
- 次フェーズ課題リスト

---

## 27. 一言でまとめると

PoCプロトタイプは、購買〜支払プロセスを小さく再現する「実験装置」として作る。統制判定は明示ルールで管理し、通常実行は中立的なClosed Action Mode、未知仮説探索はOpen Proposal Modeで分ける。不備かどうかはAction名ではなく、イベント列とDetectorで判定する。すべてのイベント、判断、AI入出力を保存し、内部統制担当者が不備候補と統制変更案をレビューできる状態を最初の完成形とする。
