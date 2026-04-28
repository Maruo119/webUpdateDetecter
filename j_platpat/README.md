# j-platpat 特許情報監視システム

特許情報プラットフォーム（j-platpat）の検索結果を定期的に監視し、新規特許・実用新案をSlackへ通知するシステムです。

## 概要

- **監視対象**: https://www.j-platpat.inpit.go.jp/s0100
- **検索条件**: 「四法全て」（特許・実用新案・意匠・商標）
- **公知年**: 最新年（2026年）
- **実行頻度**: 1時間ごと（EventBridge トリガー）
- **通知方法**: Slack Webhook

## アーキテクチャ

| 要素 | 内容 |
|------|------|
| **実行環境** | AWS Lambda (Python 3.12, Amazon Linux x86_64) |
| **ブラウザ自動化** | Playwright (headless Chrome) |
| **状態管理** | S3 に JSON (`{url: [{app_num, ...}]}`) 形式で保存 |
| **通知** | Slack Incoming Webhook（Block Kit 形式） |
| **秘密管理** | Lambda 環境変数 `SLACK_WEBHOOK_URL` |
| **IaC** | Terraform |

## セットアップ手順

### 1. 環境変数の設定

Lambda の環境変数として以下を設定してください：

```
STATE_BUCKET_NAME=my-j-platpat-state
STATE_KEY=j_platpat/state.json
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 2. S3 バケットの作成

```bash
aws s3 mb s3://my-j-platpat-state --region ap-northeast-1
```

### 3. デプロイ

```powershell
cd j_platpat
.\deploy.ps1 `
  -StateBucketName "my-j-platpat-state" `
  -SlackWebhookUrl "https://hooks.slack.com/services/..."
```

## スクレイピング仕様

### 要素抽出

- **「四法全て」選択**: `input[value="1"][name="s01_srchTarget_rdoSimpleSearch"]`
- **検索ボタン**: `#s01_srchBtn_btnSearch`
- **結果テーブル**: `#patentUtltyIntnlSimpleBibLst tbody tr`

### 抽出データ

各行から以下を取得：

- **文献番号** (`doc_num`): 表示文字列のみ（リンク先はJavaScript）
- **出願番号** (`app_num`): 差分検出のキーとして使用
- **発明の名称** (`inven_name`)
- **出願人/権利者** (`applicant`)
- **ステータス** (`status`)

## 状態管理

### S3 保存形式

```json
{
  "https://www.j-platpat.inpit.go.jp/s0100": [
    {
      "doc_num": "特開2026-069578",
      "app_num": "特願2026-014038",
      "inven_name": "情報処理装置、情報処理方法及びプログラム",
      "applicant": "東京海上日動火災保険株式会社",
      "status": "審査請求前 / 公開公報の発行",
      "timestamp": "2026-04-28T03:00:00.000000"
    }
  ]
}
```

### 差分検出

- 前回実行時の `app_num` セット と現在の `app_num` セット を比較
- **初回実行**: ベースライン記録のみ、通知なし
- **2回目以降**: 新規エントリーのみ Slack 通知

## Slack 通知フォーマット

### Block Kit 形式

```
🔍 j-platpat 新規特許情報 (N件)

---

`特開2026-069578`
特願2026-014038 | 情報処理装置、情報処理方法及びプログラム
出願人: 東京海上日動火災保険株式会社
ステータス: 審査請求前 / 公開公報の発行

---
```

## デバッグ

### ローカルテスト

```bash
cd j_platpat/debug
python test_scraper.py
```

### Lambda ログ確認

```bash
aws logs tail /aws/lambda/j-platpat-checker --follow
```

### 手動実行

```bash
aws lambda invoke --function-name j-platpat-checker response.json
cat response.json
```

## 既知の制限事項

- **JavaScript 動的レンダリング**: Playwright で対応（headless Chrome が必須）
- **Chromium イメージサイズ**: Lambda Layers での配布制限（250MB超）
- **タイムアウト**: Lambda タイムアウト 600 秒以上を推奨
- **メモリ**: 1024 MB 以上を推奨

## トラブルシューティング

### `TimeoutError: Timeout 60000ms` が発生

ページ読み込みが遅い場合があります：

1. タイムアウト値を増やす（`TIMEOUT_MS`）
2. ネットワーク遅延を確認
3. j-platpat サーバーの負荷状況を確認

### Slack 通知が来ない

1. `SLACK_WEBHOOK_URL` が正しく設定されているか確認
2. S3 バケットへのアクセス権を確認
3. CloudWatch Logs でエラーを確認

### スクレイプデータが不完全

HTML 構造の変更の可能性：

1. ブラウザ開発者ツールで最新の XPath/セレクタを確認
2. `lambda_function.py` の要素抽出ロジックを更新

## 参考資料

- [j-platpat 公式](https://www.j-platpat.inpit.go.jp/)
- [Playwright ドキュメント](https://playwright.dev/python/)
- [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html)
