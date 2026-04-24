# FSA Terraform Configuration

金融庁のニュース監視システムのための AWS インフラストラクチャを Terraform で管理します。

## リソース概要

このスタックは以下のリソースをデプロイします。

### S3 バケット
- **目的**: Lambda の実行状態（前回取得した記事の href リスト）を永続化
- **パス**: `FSA/state.json`
- **バージョニング**: 有効（過去状態の復旧に対応）
- **アクセス制限**: パブリックアクセス完全ブロック

### IAM ロール & ポリシー
- **Lambda Assume Role**: Lambda が AssumeRole できるように
- **権限内容**:
  - CloudWatch Logs: ログ作成・書き込み
  - S3: バケット一覧・`FSA/*` への読み取り・書き込み

### Lambda 関数
- **関数名**: `fsa-news-checker`
- **ランタイム**: Python 3.12
- **ハンドラ**: `lambda_function.lambda_handler`
- **タイムアウト**: 120秒
- **メモリ**: 256MB
- **環境変数**:
  - `STATE_BUCKET`: S3 バケット名
  - `SLACK_WEBHOOK_URL`: Slack Webhook URL

### EventBridge ルール
- **スケジュール**: `rate(1 hour)` （毎時実行）
- **ターゲット**: Lambda 関数 `fsa-news-checker`

### CloudWatch Logs
- **ロググループ**: `/aws/lambda/fsa-news-checker`
- **保持期間**: 14 日

## デプロイ手順

```powershell
cd D:\webUpdateDetecter\FSA\terraform
terraform init
terraform plan -var="state_bucket_name=my-fsa-state" -var="slack_webhook_url=https://hooks.slack.com/services/..."
terraform apply -var="state_bucket_name=my-fsa-state" -var="slack_webhook_url=https://hooks.slack.com/services/..."
```

## 変数一覧

| 変数 | 型 | デフォルト | 説明 |
|------|-----|---------|------|
| `aws_region` | string | `ap-northeast-1` | AWS リージョン |
| `project_name` | string | `fsa-news-checker` | リソース名のプレフィックス |
| `state_bucket_name` | string | - | S3 バケット名（**グローバル一意である必要がある**） |
| `slack_webhook_url` | string | - | Slack Incoming Webhook URL |
| `schedule_expression` | string | `rate(1 hour)` | EventBridge スケジュール表現 |

## デストロイ

```powershell
terraform destroy -var="state_bucket_name=my-fsa-state" -var="slack_webhook_url=https://..."
```

> **注意**: S3 バケットが空でない場合、`terraform destroy` は失敗します。手動削除が必要です。
