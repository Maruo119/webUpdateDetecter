# FSA

金融庁のお知らせを監視し、新しい情報をSlackへ通知するチェッカー。

## 監視対象サイト

| 対象 | URL | 監視箇所 |
|------|-----|---------|
| 金融庁 | https://www.fsa.go.jp/ | お知らせ一覧（`//*[@id='fsa_newslist_all']`） |

## Slack通知仕様

新しいお知らせを検知した際、以下の情報を通知する。

- 金融庁お知らせ（どのサイトで更新があったか）
- お知らせタイトル
- お知らせURL

**初回実行時は通知しない**（現在の一覧をベースラインとして記録するのみ）。

## 動作の仕組み

```
EventBridge (毎時) → Lambda → FSAをfetch
                                  ↓
                             lxml XPathでコンテナ要素を特定
                                  ↓
                             extract_fsaでhref・タイトルを抽出
                                  ↓
                             S3のstate.jsonと差分比較
                                  ↓
                      新記事あり → Slack通知 → state.jsonを更新
```

## デプロイ手順

### 前提条件

- Python 3.x
- Terraform CLI（[インストール](https://developer.hashicorp.com/terraform/install)）
- AWS CLI（`aws configure` で認証済み）

### 初回デプロイ

```powershell
cd D:\webUpdateDetecter
.\FSA\deploy.ps1 `
  -StateBucketName "my-fsa-state" `
  -SlackWebhookUrl "https://hooks.slack.com/services/..."
```

### 再デプロイ（コード変更時）

```powershell
cd D:\webUpdateDetecter\FSA\terraform
terraform apply -auto-approve `
  -var="state_bucket_name=my-fsa-state" `
  -var="slack_webhook_url=https://hooks.slack.com/services/..."
```

### 動作確認

`deploy.ps1` はデプロイ完了後に Lambda 実行 → S3 state.json の件数表示まで自動で行う。
手動で確認する場合：

```powershell
aws lambda invoke --function-name fsa-news-checker response.json
Get-Content response.json
# → {"statusCode": 200, "body": "OK"} が返れば正常
```

## AWSリソース

| リソース | 名前 |
|----------|------|
| Lambda関数 | `fsa-news-checker` |
| S3バケット | `my-fsa-state` |
| EventBridgeルール | `fsa-news-checker-hourly` |
| IAMロール | `fsa-news-checker-lambda-role` |
| CloudWatch Logs | `/aws/lambda/fsa-news-checker` |
