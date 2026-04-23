# cycleLifeBlog

**kashiwanoha-cycle-life.blog.jp** のカテゴリページを監視し、新記事をSlackへ通知するチェッカー。

## 監視対象サイト

| カテゴリ | URL |
|----------|-----|
| 【店舗・施設】柏の葉キャンパス | https://kashiwanoha-cycle-life.blog.jp/archives/cat_861420.html |
| 【店舗・施設】流山おおたかの森 | https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041375.html |
| 【店舗・施設】柏・流山周辺 | https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041376.html |
| 【イベント】柏の葉キャンパス | https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041507.html |
| 【イベント】流山おおたかの森 | https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041508.html |
| 【イベント】柏・流山周辺 | https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041509.html |
| 【鉄道】つくばエクスプレス | https://kashiwanoha-cycle-life.blog.jp/archives/cat_861419.html |

## Slack通知仕様

新記事を検知した際、以下の情報をSlack Block Kit形式で通知する。

- カテゴリ名（どのページで新記事が出たか）
- 記事タイトル（`img.pict3` の `title` 属性）
- 記事URL（`itemBox` の親 `<a>` の `href` 属性）

**初回実行時は通知しない**（現在の記事一覧をベースラインとして記録するのみ）。

## 動作の仕組み

```
EventBridge (毎時) → Lambda → 各URLをfetch
                                  ↓
                             BeautifulSoupでitemBoxをパース
                                  ↓
                             S3のstate.jsonと差分比較
                                  ↓
                      新記事あり → Slack通知 → state.jsonを更新
```

## デプロイ手順

### 前提条件

- Python 3.x（`python --version` で確認）
- Terraform CLI（[インストール](https://developer.hashicorp.com/terraform/install)）
- AWS CLI（`aws configure` で認証済み）

### 初回デプロイ

PowerShellで実行する。

```powershell
cd D:\webUpdateDetecter
.\cycleLifeBlog\deploy.ps1 `
  -StateBucketName "my-cycle-life-blog-state"
```

Terraform apply の際に Slack Webhook URL の入力を求められる。

### 再デプロイ（コード変更時）

```powershell
cd D:\webUpdateDetecter\cycleLifeBlog\terraform
terraform apply -auto-approve `
  -var="state_bucket_name=my-cycle-life-blog-state" `
  -var="slack_webhook_url=<Webhook URL>"
```

### 動作確認

```powershell
aws lambda invoke --function-name cycle-life-blog-checker response.json
Get-Content response.json
# → {"statusCode": 200, "body": "OK"} が返れば正常
```

## AWSリソース

詳細は [terraform/README.md](terraform/README.md) を参照。

| リソース | 名前 |
|----------|------|
| Lambda関数 | `cycle-life-blog-checker` |
| S3バケット | `my-cycle-life-blog-state` |
| EventBridgeルール | `cycle-life-blog-checker-hourly` |
| IAMロール | `cycle-life-blog-checker-lambda-role` |
| CloudWatch Logs | `/aws/lambda/cycle-life-blog-checker` |
