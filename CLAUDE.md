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
│   ├── terraform/
│   └── debug/                 # デバッグスクリプト
├── PnC_insuranceNews/         # 損保会社ニュースリリース監視
│   ├── README.md
│   ├── memo.md                # 追加予定・完了済み会社の管理メモ
│   ├── requirements.txt
│   ├── deploy.ps1
│   ├── src/lambda_function.py
│   ├── terraform/
│   └── debug/                 # デバッグスクリプト
└── FSA/                       # 金融庁お知らせ監視
    ├── README.md
    ├── requirements.txt
    ├── deploy.ps1
    ├── src/lambda_function.py
    ├── terraform/
    └── debug/                 # デバッグスクリプト
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
4. `memo.md` に進捗を記録する
5. ローカルでデバッグ後、`deploy.ps1` でデプロイする

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

### FSA（RSS フィード使用）

1. RSS URL をブラウザで確認する
2. `SITES` リストに RSS URL を追加する
3. `EXTRACTORS` 辞書に対応する `extract_xxx()` 関数を実装する（XML パース）
4. ローカルでデバッグ後、`deploy.ps1` でデプロイする

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

### FSA

```powershell
cd D:\webUpdateDetecter
.\FSA\deploy.ps1 `
  -StateBucketName "my-fsa-state" `
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

- **エンコーディング**: `fetch_html()` は `res.apparent_encoding` を優先使用。HTTP デフォルトの ISO-8859-1 で文字化けするサイトに対応済み。
- **状態キーはURL**: S3 の state.json は `{サイトURL: [href, ...]}` の形式。同一 URL に複数の監視セクションがある場合は1エントリにまとめる。
- **年度別URL対応**: URL が年度などで変化するサイト（例: アニコム損保）は `url` の代わりに `url_template` + `{year}` プレースホルダを使用。`resolve_site_url()` が実行時に `datetime.now().year` で解決する。
- **JS動的レンダリング非対応**: 記事が JavaScript で動的に読み込まれるサイト（例: アクサ損保）は requests+lxml では取得不可。Playwright 等の導入が必要。
- **初回実行は通知しない**: `prev_hrefs` が空の場合はベースライン記録のみ行い、Slack 通知はしない。
- **GitHub Push Protection**: Slack Webhook URL をコードに含めると push が拒否される。環境変数 `SLACK_WEBHOOK_URL` を使うこと。
- **`.gitignore`**: `*/src/*/` パターンで全サイトのインストール済みライブラリを除外している。

## 開発ルール

- **ソース変更時は必ずブランチを切る**: `git checkout -b feature/xxx` → 実装 → PR → マージ。main への直接コミットは禁止。

## PnC_insuranceNews — 追加予定会社

`PnC_insuranceNews/memo.md` を参照。
完了済み: 34社以上（詳細は memo.md 参照）。
スキップ: アクサ損保、au損保、セコム損保、東京海上ダイレクト（JavaScript 動的レンダリング）。

## FSA — 実装状況

`FSA/` ディレクトリを参照。金融庁お知らせ RSS フィード監視。
