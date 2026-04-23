# webUpdateDetecter

Webページの更新を定期的に検知し、Slackへ通知するシステム。
サイトごとにディレクトリを分け、それぞれ独立したLambda関数・AWSリソースとして管理する。

## ディレクトリ構成

```
webUpdateDetecter/
├── README.md                  # このファイル
├── .gitignore
├── common/                    # 複数サイトで共通利用するユーティリティ（任意）
│   └── python_utils/
├── cycleLifeBlog/             # サイト: kashiwanoha-cycle-life.blog.jp
│   ├── README.md              # サイト固有の仕様・手順
│   ├── requirements.txt
│   ├── deploy.ps1             # デプロイスクリプト (Windows PowerShell)
│   ├── src/
│   │   └── lambda_function.py
│   └── terraform/
│       ├── README.md          # AWSインフラ詳細
│       ├── main.tf
│       └── variables.tf
└── PnC_insuranceNews/         # サイト: 損保会社ニュースリリース
    ├── README.md
    ├── requirements.txt
    ├── deploy.ps1
    ├── src/
    │   └── lambda_function.py
    └── terraform/
        ├── README.md
        ├── main.tf
        └── variables.tf
```

## 新しいサイトを追加する場合

1. サイト名でディレクトリを作成する（例: `newSite/`）
2. 既存の `cycleLifeBlog/` をテンプレートとしてコピーする
3. `src/lambda_function.py` の `SITES` リストを監視対象URLに書き換える
4. `terraform/variables.tf` の `project_name` デフォルト値を変更する
5. `deploy.ps1` を実行してAWSへデプロイする
6. サイト固有の `README.md` を作成する

## 共通の仕組み

| 項目 | 内容 |
|------|------|
| 実行環境 | AWS Lambda (Python 3.12) |
| スケジュール | EventBridge（デフォルト: 毎時1回） |
| 状態管理 | S3にJSONで記事URL一覧を保存 |
| 通知 | Slack Incoming Webhook |
| シークレット管理 | Lambda環境変数（コードに直書きしない） |
