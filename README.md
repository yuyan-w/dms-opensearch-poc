# DMS × OpenSearch 検証プロジェクト

## 概要

本プロジェクトは、Amazon Aurora から Amazon OpenSearch Service へのデータ同期を AWS Database Migration Service（DMS）を用いて実現し、全文検索の性能改善および運用上の課題を検証することを目的とする。

---

## 背景

### 前提となる問題

- `products.description` に対する LIKE 検索の性能が限界に近い
- データ増加に伴い検索遅延が顕著になる見込み

### 影響

- 検索レスポンスの悪化
- DB負荷の増加
- スケーラビリティの限界

---

## 方針

- 検索処理を OpenSearch にオフロード
- Aurora はトランザクション処理に専念
- データ同期は DMS（フルロード + CDC）で実現

---

## 現在の進捗

### 完了している検証

#### 1. DMSタスクの構築と実行

- Aurora → OpenSearch のレプリケーションタスクを作成
- フルロード + CDC の構成で実行確認

---

#### 2. LONGTEXT（LOB）の制約確認

- `LONGTEXT` カラムは LOB として扱われることを確認
- DMS → OpenSearch への同期において制約があることを確認

##### 結論

- LOBの扱いによっては **そのままでは同期不可または制限あり**
- 対策検討が必要（後述）

---

#### 3. エラー発生時の挙動確認（アラート検証）

- 意図的に不正データを投入
- DMSログにエラーが出力されることを確認
- CloudWatch メトリクスフィルタによりアラート発火を確認

##### 確認できたこと

- エラー検知 → アラート発火の一連の流れが成立
- 運用監視として最低限の仕組みは構築可能

---

## 現時点の課題

### 1. LOB（LONGTEXT）の扱い

#### 問題

- DMSはLOBを完全には扱えないケースがある

#### 影響

- description（全文検索対象）が同期できない可能性
- OpenSearch側で検索できない

#### 想定対応

- Inline LOB サイズの調整
- LOBを分割 or 別カラム化
- ETL（Lambda / Glue）による補完

---

### 2. エラーハンドリング方針の未確定

#### 問題

- エラー時の挙動（停止・スキップ）が運用設計に影響

#### 影響

- データ欠損
- CDC停止のリスク

#### 想定対応

- `ErrorBehavior` の調整
- アラート発火後の運用手順定義

---

### 3. OpenSearch 側の書き込み耐性未検証

#### 問題

- 高負荷時に 429（Too Many Requests）が発生する可能性

#### 影響

- CDC遅延
- データ欠損の可能性

---

## 次の検証ステップ

- LOB対応の実現可否検証
- OpenSearchへの負荷試験（書き込みスループット）
- CDC遅延の測定
- DMS再実行時の挙動確認（重複・再開位置）

---

## 技術構成

- Aurora MySQL
- AWS DMS
- Amazon OpenSearch Service
- CloudWatch（Logs / Metrics / Alarm）
- Terraform（インフラ管理）

---

## まとめ

- DMSによる Aurora → OpenSearch の基本的な同期は実現可能
- エラー検知・アラートの仕組みは構築済み
- 一方で、以下が主要な課題として残る
  - LOB（LONGTEXT）の扱い
  - エラーハンドリング方針
  - OpenSearchの書き込み耐性

---

## 注意事項（運用観点）

- DMSは「同期」は強いが「変換」は弱い
- binlog保持が不十分だとCDCが破綻する
- OpenSearchは検索よりも書き込みがボトルネックになりやすい
