# PnC_insuranceNews — AWSインフラ

Terraformで管理するAWSリソースの詳細。

## 構成図

```
EventBridge Rule (rate: 1 hour)
        │
        ▼
  Lambda Function (insurance-news-checker)
  ├─ Runtime: Python 3.12
  ├─ Timeout: 120秒
  ├─ Memory: 256MB
  ├─ 環境変数: STATE_BUCKET, SLACK_WEBHOOK_URL
  │
  ├─ 読み書き → S3 Bucket (my-insurance-news-state)
  │              └─ PnC_insuranceNews/state.json
  │
  └─ 通知 → Slack Incoming Webhook
```

## リソース一覧

| Terraformリソース | AWSリソース種別 | 名前 |
|-------------------|----------------|------|
| `aws_lambda_function.checker` | Lambda | `insurance-news-checker` |
| `aws_s3_bucket.state` | S3 | `my-insurance-news-state` |
| `aws_cloudwatch_event_rule.hourly` | EventBridge Rule | `insurance-news-checker-hourly` |
| `aws_cloudwatch_event_target.lambda` | EventBridge Target | `PnC_insuranceNewsChecker` |
| `aws_lambda_permission.allow_eventbridge` | Lambda Permission | `AllowExecutionFromEventBridge` |
| `aws_iam_role.lambda` | IAM Role | `insurance-news-checker-lambda-role` |
| `aws_iam_role_policy.lambda` | IAM Policy | `insurance-news-checker-lambda-policy` |
| `aws_cloudwatch_log_group.checker` | CloudWatch Logs | `/aws/lambda/insurance-news-checker` |

## 変数

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `state_bucket_name` | ✅ | — | 状態保存用S3バケット名（グローバルで一意） |
| `slack_webhook_url` | ✅ | — | Slack Incoming Webhook URL |
| `aws_region` | | `ap-northeast-1` | デプロイリージョン |
| `project_name` | | `insurance-news-checker` | リソース名のプレフィックス |
| `schedule_expression` | | `rate(1 hour)` | EventBridgeのスケジュール式 |

## IAM権限

```
CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents
S3 (バケット): ListBucket
S3 (オブジェクト): GetObject, PutObject  ※ PnC_insuranceNews/* のみ
```

## Terraform操作

```powershell
# 初期化
terraform init

# 差分確認
terraform plan -var="state_bucket_name=xxx" -var="slack_webhook_url=xxx"

# 適用
terraform apply -auto-approve -var="state_bucket_name=xxx" -var="slack_webhook_url=xxx"

# 削除（全リソース破棄）
terraform destroy -var="state_bucket_name=xxx" -var="slack_webhook_url=xxx"
```

## S3の状態ファイル

`PnC_insuranceNews/state.json` のスキーマ。キーがURL、値がhrefの配列。

```json
{
  "https://www.aig.co.jp/sonpo/company/news": [
    "https://www.aig.co.jp/sonpo/company/news/2026/20260420-1",
    "https://www.aig.co.jp/sonpo/company/news/2026/20260415-1"
  ],
  "https://www.sompo-japan.co.jp/": [
    "https://www.sompo-japan.co.jp/-/media/SJNK/files/topics/2026/20260416_1.pdf"
  ]
}
```

## ログ確認

```powershell
aws logs tail /aws/lambda/insurance-news-checker --since 1h
```
