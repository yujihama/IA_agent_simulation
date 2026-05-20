# LLM分岐探索 実LLM検証メモ

作成日: 2026-05-20

## 目的

`branching_proposal` の最小実装が、単に動作するだけでなく、内部統制ストレステストとして有用な分岐仮説を生成できるかを確認した。

検証では、同じ S-002 購買ニーズに対して実LLMを複数回実行し、以下を見た。

- 分割申請、過少申請、緊急例外、非公式相談がWorldとして生成されるか
- Rule Engine / Detector がどのWorldを検出または停止できるか
- Detectorで残るリスクが、統制・ログ・Action Library不足として解釈できるか

## 実行条件

- provider: `openai`
- model: `gpt-4.1-mini`
- behavior_mode: `branching_proposal`
- proposal_count_per_node: `5`
- 対象: `NEED-001` / S-002 四半期末・納期圧力
- 温度条件: `0.3`, `0.7`, `0.9`

## 解釈境界

今回のプロンプトでは、coverage target として split / underreported amount / emergency route / informal preapproval を明示している。

したがって、この結果は「LLMが未知の統制不備を自律的に発見した」という意味ではない。より正確には、**統制ストレステスト用のカバレッジ目標を与えたとき、代表的な高リスクWorldを安定生成できた** という結果である。

PR#6時点の実装は初期状態から複数Worldを生成する最小実装だった。本追補では最小スコープの多段階探索として、`max_depth=2` で expandable な中間Worldを `parent_world_context` としてLLMへ再入力し、子Worldを生成する。

## Run Artifact方針

PR#6までは、実LLM run artifacts はPoC検証時に一時ディレクトリへ出力し、コミットしない方針だった。

理由は以下である。

- `branching_calls.jsonl` にはLLMリクエスト/レスポンス全文が含まれるため、将来のプロンプトや環境情報の取り扱い方針を先に決める必要がある
- 実LLM結果は非決定的で、コミット済み証跡として固定する前に再現条件・モデルバージョン・秘匿情報レビューのルールが必要である
- 今回は、実LLM検証から得られた示唆を本メモに要約し、回帰テストはstub providerで安定化する

本追補ではこの方針を改め、少なくとも1つの代表runについて redacted artifacts をPoC evidenceとして保存する。prompt / raw response / parsed JSON / validation status はレビュー可能性のため保持し、API keyやtokenに見える文字列、ローカルユーザーパスのみpattern redactionする。

## 観察結果

| 温度 | 生成World | 検出率 | 分子/分母 | 主なWorld | 残余リスク |
|---:|---:|---:|---|---|
| 0.3 | 5 | 0.75 | 3 / 4 | 正規申請、分割申請、過少申請、緊急ルート、非公式事前承認 | 非公式事前承認 |
| 0.7 | 5 | 0.75 | 3 / 4 | 正規申請、分割申請、緊急ルート、過少申請、非公式事前承認 | 非公式事前承認 |
| 0.9 | 5 | 0.75 | 3 / 4 | 正規申請、分割申請、緊急ルート、過少申請、非公式事前承認 | 非公式事前承認 |

検出率の分母は高リスクWorld数、分子はDetector findingが生成された高リスクWorld数である。正規申請Worldは分母に含めない。

実LLMは、単一行動選択では自然に出にくかった分割申請を、分岐仮説としては安定して生成した。これは方針転換メモの中心仮説である「LLMを直接実行者として使うより、複数の行動可能性を提案させる方が統制ストレステストに向く」を支持する結果である。

## 有用な示唆

1. **分割申請は検出可能なWorldとして安定生成された。**  
   Baselineでは同一申請者・同一取引先・同一プロジェクトの近接日付申請として `split_order_detector` が検出した。

2. **過少申請はAction Grounder側の補完が重要だった。**  
   実LLMは「申請額を下げる」仮説を出す一方、初回実行では `economic_amount` を明示しない場合があった。そのため、`classification=misrepresentation` かつ申請額が購買ニーズ総額を下回る場合は、合成環境上で `economic_amount` を補完するよう修正した。

3. **緊急ルートは検出候補になるが、実務上は証跡レビューが焦点になる。**  
   LLMは緊急・例外ルートを提案した。Detectorはルート利用を拾えるが、妥当性判断には理由証跡、事後承認、反復利用の評価が必要になる。

4. **非公式事前承認は一貫して残余リスクになった。**  
   LLMはチャットや非公式相談による事前合意を繰り返し提案したが、初回実装のAction Libraryでは実行・ログ化できなかった。この示唆を受けて、`informal_preapproval_chat` を分岐探索専用Actionとして実装対象に引き上げた。

5. **system_blocked は通常フローとして進めず、試行イベントとして記録すべきだった。**  
   初回実行で、ブロック対象の仮説が支払完了まで進んでしまう問題を確認した。これを修正し、`system_blocked` は `blocked_attempt` のイベントだけを残す扱いにした。

## 結論

`branching_proposal` は、Closed Action Modeでは観察しにくかった統制弱点候補をWorldとして安定生成できた。

特に、分割申請・過少申請・緊急ルートはDetectorやRule Engineの評価対象にできる。初回検証で残余リスクとして残った非公式事前承認は、`informal_preapproval_chat` と `informal_preapproval_detector` を追加した後、合成環境上では検出可能になった。

## 追補検証

ユーザー指摘後の追補実装として、以下を追加した。

- `informal_preapproval_chat` を `branching_action` としてAction Libraryに追加
- `informal_preapproval_detector` を追加し、非公式事前承認Worldを `D-004` としてレビュー候補化
- `detector_detection_rate_numerator` / `detector_detection_rate_denominator` をsummaryとreportへ明記
- `system_blocked` actionが通常フローに進まず、`blocked_attempt` の試行イベントだけを残すテストを追加
- 同一Branching World群を Baseline / Variant A / Variant B でリプレイ比較する `run-branching-variant-comparison` を追加

追補後に `gpt-4.1-mini` / temperature `0.7` で1回再実行したところ、5Worldが生成され、高リスクWorld 4件すべてにDetector findingが付いた。検出率は `4 / 4 = 1.0`、Action Library candidate は0件だった。

Variant比較では、Baselineで未緩和だったWorld群に対し、Variant Aは分割申請 `D-001`、Variant Bは緊急ルート `D-002` をそれぞれ緩和する。一方、過少申請 `D-003` と非公式事前承認 `D-004` は、別の統制・証跡設計が必要なレビュー面として残る。

さらに本PRで、`gpt-4.1-mini` / temperature `0.7` / `max_depth=2` の代表runを作成し、`runs/evidence/RUN-S002-BRANCHING-MULTISTAGE-GPT41-MINI/` にredacted PoC evidenceとして保存した。結果は以下である。

- 生成World: 10件 (`depth=1`: 5件, `depth=2`: 5件)
- 展開World: 1件 (`WORLD-005` 非公式事前承認から `WORLD-006` - `WORLD-010` へ展開)
- `detector_detection_rate`: `8 / 8 = 1.0`
- Baseline未緩和finding: 15件
- Variant A: 2件をmitigate (`D-001`)
- Variant B: 2件をmitigate (`D-002`)

子Worldでは親Worldの非公式事前承認イベントが引き継がれるため、通常申請や分割申請に進んだ後も `D-004` が残る。この点は、多段階探索で「前段のシステム外運用が後続の通常フローに残留する」ことを追跡できるようになった、という有用な示唆である。

## 次フェーズ

## 多段階探索・Evidence追補

本追補では、Priority 1 / 2として以下を実装した。

- `max_depth`, `beam_width`, `max_total_worlds` を実際の探索制御に使う
- 親Worldのイベント列を `parent_world_context` としてLLMへ再入力する
- 子Worldに `parent_world_id` と `depth` を持たせ、`world_tree.json` に親子関係を出力する
- 終端理由として `paid`, `blocked_attempt`, `unsupported`, `max_depth_reached`, `no_valid_action`, `expanded`, `open` を集計する
- `export-branching-evidence` で代表runをredacted PoC evidenceとして保存する

この追補により、PoCは「初期World生成」から「最小スコープの多段階Branching Proposal探索」へ進む。

残る次フェーズ課題は以下である。

1. `max_depth=3` 以上での枝刈り・重複排除・beam selectionの評価
2. D-003 / D-004に効く追加Variantの設計
3. 実LLM evidenceを複数temperature・複数scenarioへ拡張する

## max_depth=3・親子リスク分解追補

PR#7後の指摘を受け、次の追補では以下を優先する。

- `max_depth=3`, `beam_width=2`, `max_total_worlds=25` で複数parent展開を疎通する
- child proposalの重複を、同一parentと同一action signature単位で実行前に除外する
- findingを `current`, `inherited`, `mixed` に分類し、親Worldから引き継がれたriskと子Worldで新規発生したriskを分ける
- summaryに `lineage_detection_rate`, `current_world_detection_rate`, `new_risk_detection_rate`, `inherited_risk_count`, `inherited_only_high_risk_world_count` を追加する

この変更により、`detector_detection_rate=1.0` が親World由来の `D-004` によって過大に見える問題を避ける。従来の `detector_detection_rate` は互換性のためlineage detectionとして残し、新規riskの評価には `new_risk_detection_rate` を使う。
