# ディレクトリ構成
webUpdateDetecter/ (Repo Root)
├── .github/              # GitHub Actionsの設定（自動デプロイ用）
├── common/               # 各サイトで共通で使うユーティリティ（任意）
│   └── python_utils/     # 共通のログ出力や通知ロジックなど
├── site-a/               # サイトA専用のディレクトリ
│   ├── src/              # Lambdaのソースコード
│   │   └── lambda_function.py
│   ├── terraform/        # AWSリソース定義 (または CloudFormation/CDK)
│   │   ├── main.tf       # S3, Lambda, EventBridge, SecretManagerを定義
│   │   └── variables.tf
│   └── requirements.txt  # サイトAで必要なライブラリ
└── site-b/               # サイトB専用のディレクトリ
    ├── src/
    ├── terraform/
    └── requirements.txt

# cycleLifeBlog

## 更新チェック対象とするサイト

カテゴリ：【店舗・施設】 > 柏の葉キャンパス（店舗・施設）
https://kashiwanoha-cycle-life.blog.jp/archives/cat_861420.html

カテゴリ：【店舗・施設】 > 流山おおたかの森（店舗・施設）
https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041375.html

カテゴリ：【店舗・施設】 > 柏・流山周辺（店舗・施設）
https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041376.html

カテゴリ：【イベント】 > 柏の葉キャンパス（イベント）
https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041507.html

カテゴリ：【イベント】 > 流山おおたかの森（イベント）
https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041508.html

カテゴリ：【イベント】 > 柏・流山周辺（イベント）
https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041509.html

カテゴリ：【鉄道】 > つくばエクスプレス
https://kashiwanoha-cycle-life.blog.jp/archives/cat_861419.html
