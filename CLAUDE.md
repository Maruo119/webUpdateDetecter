# CLAUDE.md — webUpdateDetecter

## プロジェクト概要

Webページの更新を定期的に検知し、Slackへ通知するシステム。
AWS Lambda + EventBridge + S3 で構成し、Terraform で管理する。

## ディレクトリ構成

```
webUpdateDetecter/
├── CLAUDE.md                  # このファイル（Claude Code 向け文脈メモ）
├── README.md                  # プロジェクト全体の説明
├── .gitignore
├── cycleLifeBlog/             # kashiwanoha-cycle-life.blog.jp 監視
│   ├── README.md
│   ├── requirements.txt
│   ├── deploy.ps1
│   ├── src/lambda_function.py
│   └── terraform/
└── PnC_insuranceNews/         # 損保会社ニュースリリース監視
    ├── README.md
    ├── requirements.txt
    ├── deploy.ps1
    ├── src/lambda_function.py
    └── terraform/
        └── memo.md            # 追加予定・完了済み会社の管理メモ
```

## 共通アーキテクチャ

| 要素 | 内容 |
|------|------|
| 実行 | AWS Lambda (Python 3.12, Amazon Linux x86_64) |
| トリガー | EventBridge `rate(1 hour)` |
| 状態管理 | S3 に JSON (`{url: [href, ...]}`) を保存 |
| 通知 | Slack Incoming Webhook（Block Kit形式） |
| 秘密管理 | Lambda 環境変数 `SLACK_WEBHOOK_URL`（コードに直書き禁止） |
| IaC | Terraform（Lambda・S3・IAM・EventBridge・CloudWatch Logs） |

## 新しいサイトを追加する手順

### cycleLifeBlog（BeautifulSoup4 使用）

1. `SITES` リストに URL とカテゴリ名を追加する
2. 既存のパーサーで対応できなければ抽出ロジックを修正する

### PnC_insuranceNews（lxml + XPath 使用）

1. ブラウザ DevTools で監視対象要素の XPath を調査する
2. `SITES` リストにエントリを追加する（`extractor` キーで関数を指定）
3. `EXTRACTORS` 辞書に対応する `extract_xxx()` 関数を実装する
4. ローカルでデバッグ後、`deploy.ps1` でデプロイする

```python
# SITES エントリ例
{
    "name": "新会社名 ニュースリリース",
    "url": "https://example.com/news",
    "base_url": "https://example.com",
    "xpath": "//div[@id='news-list']",
    "extractor": "new_company",
}

# Extractor 実装例
def extract_new_company(container, base_url):
    items = []
    for a in container.xpath('.//a[@href]'):
        href = resolve_url(a.get("href", "").strip(), base_url)
        title = a.text_content().strip()
        if href and title:
            items.append({"href": href, "title": title})
    return items

EXTRACTORS["new_company"] = extract_new_company
```

## デプロイコマンド

### cycleLifeBlog

```powershell
cd D:\webUpdateDetecter
.\cycleLifeBlog\deploy.ps1 `
  -StateBucketName "my-cycle-life-blog-state" `
  -SlackWebhookUrl "https://hooks.slack.com/services/..."
```

### PnC_insuranceNews

```powershell
cd D:\webUpdateDetecter
.\PnC_insuranceNews\deploy.ps1 `
  -StateBucketName "my-insurance-news-state" `
  -SlackWebhookUrl "https://hooks.slack.com/services/..."
```

> **注意**: `lxml` は C 拡張を含むため、`deploy.ps1` 内で `--platform manylinux2014_x86_64 --python-version 312` を使って Linux 用ホイールをダウンロードしている。Windows 環境でのビルドは不可。

## 動作テスト手順（S3 書き換えによる通知確認）

1. 現在の state.json をバックアップとしてダウンロード
2. バックアップから最新記事の href を1件削除した test.json を作成
3. test.json を state.json として S3 にアップロード
4. Lambda を手動実行（`aws lambda invoke`）
5. Slack に通知が届くことを確認
6. バックアップを state.json として S3 に戻す

```powershell
# 例: cycleLifeBlog
$bucket = "my-cycle-life-blog-state"
$key = "cycleLifeBlog/state.json"

aws s3 cp "s3://$bucket/$key" state_backup.json
# ← state_backup.json を編集して href を1件削除 →
aws s3 cp state_test.json "s3://$bucket/$key"
aws lambda invoke --function-name cycle-life-blog-checker response.json
# 通知確認後:
aws s3 cp state_backup.json "s3://$bucket/$key"
```

## 注意事項・既知の問題

- **Shift-JIS 対応**: `fetch_html()` は `res.content.decode(encoding)` でデコードしてから lxml に渡す。`res.text` は使わない（文字化けする）。
- **状態キーはURL**: S3 の state.json は `{サイトURL: [href, ...]}` の形式。同一 URL に複数の監視セクションがある場合は1エントリにまとめる。
- **初回実行は通知しない**: `prev_hrefs` が空の場合はベースライン記録のみ行い、Slack 通知はしない。
- **GitHub Push Protection**: Slack Webhook URL をコードに含めると push が拒否される。環境変数 `SLACK_WEBHOOK_URL` を使うこと。
- **`.gitignore`**: `*/src/*/` パターンで全サイトのインストール済みライブラリを除外している。

## PnC_insuranceNews — 追加予定会社

`PnC_insuranceNews/terraform/memo.md` を参照。
完了済み: AIG損保、損保ジャパン、あいおいニッセイ同和損保。
