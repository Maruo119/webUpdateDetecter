# cycleLifeBlog — AWSインフラ

Terraformで管理するAWSリソースの詳細。

## 構成図

```
EventBridge Rule (rate: 1 hour)
        │
        ▼
  Lambda Function (cycle-life-blog-checker)
  ├─ Runtime: Python 3.12
  ├─ Timeout: 120秒
  ├─ Memory: 256MB
  ├─ 環境変数: STATE_BUCKET, SLACK_WEBHOOK_URL
  │
  ├─ 読み書き → S3 Bucket (my-cycle-life-blog-state)
  │              └─ cycleLifeBlog/state.json
  │
  └─ 通知 → Slack Incoming Webhook
```

## リソース一覧

| Terraformリソース | AWSリソース種別 | 名前 |
|-------------------|----------------|------|
| `aws_lambda_function.checker` | Lambda | `cycle-life-blog-checker` |
| `aws_s3_bucket.state` | S3 | `my-cycle-life-blog-state` |
| `aws_cloudwatch_event_rule.hourly` | EventBridge Rule | `cycle-life-blog-checker-hourly` |
| `aws_cloudwatch_event_target.lambda` | EventBridge Target | `cycleLifeBlogChecker` |
| `aws_lambda_permission.allow_eventbridge` | Lambda Permission | `AllowExecutionFromEventBridge` |
| `aws_iam_role.lambda` | IAM Role | `cycle-life-blog-checker-lambda-role` |
| `aws_iam_role_policy.lambda` | IAM Policy | `cycle-life-blog-checker-lambda-policy` |
| `aws_cloudwatch_log_group.checker` | CloudWatch Logs | `/aws/lambda/cycle-life-blog-checker` |
| `aws_s3_bucket_versioning.state` | S3 Versioning | — |
| `aws_s3_bucket_public_access_block.state` | S3 Public Access Block | — |

## 変数

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `state_bucket_name` | ✅ | — | 状態保存用S3バケット名（グローバルで一意） |
| `slack_webhook_url` | ✅ | — | Slack Incoming Webhook URL |
| `aws_region` | | `ap-northeast-1` | デプロイリージョン |
| `project_name` | | `cycle-life-blog-checker` | リソース名のプレフィックス |
| `schedule_expression` | | `rate(1 hour)` | EventBridgeのスケジュール式 |

## IAM権限

Lambdaロールに付与している最小権限。

```
CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents
S3 (バケット): ListBucket
S3 (オブジェクト): GetObject, PutObject  ※ cycleLifeBlog/* のみ
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

`cycleLifeBlog/state.json` のスキーマ。キーがURL、値が記事hrefの配列。

```json
{
  "https://kashiwanoha-cycle-life.blog.jp/archives/cat_861420.html": [
    "https://kashiwanoha-cycle-life.blog.jp/archives/51887545.html",
    "https://kashiwanoha-cycle-life.blog.jp/archives/51880000.html"
  ],
  ...
}
```

## ログ確認

```powershell
aws logs tail /aws/lambda/cycle-life-blog-checker --since 1h
```
