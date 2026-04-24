# PnC_insuranceNews

損保会社のニュースリリースを監視し、新しいお知らせをSlackへ通知するチェッカー。

## 監視対象サイト

現在 **34社** を監視しています。詳細は以下を参照：

| # | 会社 | URL | 監視内容 |
|---|------|-----|---------|
| 1 | AIG損保 | https://www.aig.co.jp/sonpo/company/news | ニュースリリース |
| 2 | 損保ジャパン | https://www.sompo-japan.co.jp/ | ニュースリリース・トピックス |
| 3 | あいおいニッセイ同和損保 | https://www.aioinissaydowa.co.jp/ | お知らせ・ニュースリリース |
| 4 | アニコム損保 | https://www.anicom-sompo.co.jp/topics/{year}/ | トピックス（年度別URL） |
| 5 | アニコム損保 | https://www.anicom-sompo.co.jp/news-release/{year}/ | ニュースリリース（年度別URL） |
| 6 | エイチ･エス損保 | https://www.hs-sonpo.co.jp/ | お知らせ |
| 7 | ＳＢＩ損保 | https://www.sbisonpo.co.jp/company/ | ニュースリリース |
| 8 | ＳＢＩ損保 | https://www.sbisonpo.co.jp/company/ | お知らせ |
| 9 | ドコモ損保 | https://www.docomo-sompo.com/news/ | お知らせ |
| 10 | キャピタル損保 | https://www.capital-sonpo.co.jp/ | お知らせ |
| 11 | 共栄火災 | https://www.kyoeikasai.co.jp/ | お知らせ |
| 12 | さくら損保 | https://www.sakura-ssi.co.jp/ | お知らせ |
| 13 | ジェイアイ | https://www.jihoken.co.jp/ | お知らせ |
| 14 | 全管協れいわ損保 | https://www.zkreiwa-sonpo.co.jp/ | お知らせ |
| 15 | ソニー損保 | https://from.sonysonpo.co.jp/topics/information/N0086000.html | お知らせ |
| 16 | ソニー損保 | https://from.sonysonpo.co.jp/topics/information/N0086000.html | 自然災害等のお知らせ |
| 17 | SOMPOダイレクト | https://news-ins-saison.dga.jp/topics/?type=important | 大切なお知らせ |
| 18 | SOMPOダイレクト | https://news-ins-saison.dga.jp/topics/?type=news | ニュースリリース |
| 19 | 第一アイペット | https://www.ipet-ins.com/info/ | お知らせ |
| 20 | 大同火災 | https://www.daidokasai.co.jp/news/ | お知らせ |
| 21 | 東京海上日動 | https://www.tokiomarine-nichido.co.jp/company/news/ | お知らせ |
| 22 | トーア再保険 | https://www.toare.co.jp/ | お知らせ |
| 23 | 日新火災 | https://www.nisshinfire.co.jp/news_release/ | ニュースリリース |
| 24 | 日本地震再保険 | https://www.nihonjishin.co.jp/ | お知らせ |
| 25 | 三井住友海上 | https://www.ms-ins.com/news/fy{year}/ | ニュースリリース（年度別URL） |
| 26 | 三井ダイレクト損保 | https://news.mitsui-direct.co.jp/ | お知らせ・ニュースリリース |
| 27 | 明治安田損保 | https://www.meijiyasuda-sonpo.co.jp/news/ | お知らせ |
| 28 | ペット＆ファミリー損保 | https://www.petfamilyins.co.jp/news/news_category/notice/ | お知らせ |
| 29 | ヤマップネイチャランス | https://yamap-naturance.co.jp/news | お知らせ |
| 30 | 楽天損保 | https://www.rakuten-sonpo.co.jp/news/tabid/85/Default.aspx | お知らせ |
| 31 | レスキュー損保 | https://www.rescue-sonpo.jp/news.php | お知らせ |

## スキップ（JavaScript動的レンダリング対応が必要）

以下の会社はJavaScriptで動的レンダリングされるため、本システムの対象外です。Playwright などの導入が必要です：

- **アクサ損保** - https://www.axa-direct.co.jp/company/official_info/
- **au損保** - https://www.au-sonpo.co.jp/corporate/news/
- **セコム損保** - https://www.secom-sonpo.co.jp/
- **東京海上ダイレクト** - https://www.e-design.net/

詳細は [memo.md](memo.md) を参照。

### 新しい会社を追加する場合

1. ブラウザ DevTools で監視対象要素の XPath を調査する
2. `src/lambda_function.py` の `SITES` リストにエントリを追加する
3. `EXTRACTORS` 辞書に対応する `extract_xxx()` 関数を実装する

```python
SITES = [
    ...
    {
        "name": "新会社名 ニュースリリース",
        "url": "https://example.com/news",
        "base_url": "https://example.com",
        "xpath": "//div[@id='news-list']",
        "extractor": "new_company",   # EXTRACTORS に同名の関数を追加
    },
]
```

> **注意1**: 同一 URL に複数の監視セクションがある場合（例: あいおいニッセイ同和損保のお知らせ＋ニュースリリース）、state.json のキーが URL なので1エントリにまとめる。
>
> **注意2**: URL が年度などで変化するサイトは `url` の代わりに `url_template` を使い `{year}` プレースホルダを含める（例: アニコム損保）。実行時に `datetime.now().year` で置換される。
>
> **注意3**: JavaScript で動的レンダリングされるサイト（例: アクサ損保）は requests+lxml では取得できないため本システムの対象外。

## Slack通知仕様

新しいお知らせを検知した際、以下の情報を通知する。

- 会社名・ページ名（どのサイトで更新があったか）
- お知らせタイトル
- お知らせURL

**初回実行時は通知しない**（現在の一覧をベースラインとして記録するのみ）。

## 動作の仕組み

```
EventBridge (毎時) → Lambda → 各URLをfetch
                                  ↓
                             lxml XPathでコンテナ要素を特定
                                  ↓
                             サイト固有のExtractorでhref・タイトルを抽出
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
.\PnC_insuranceNews\deploy.ps1 `
  -StateBucketName "my-insurance-news-state" `
  -SlackWebhookUrl "https://hooks.slack.com/services/..."
```

### 再デプロイ（コード変更時）

```powershell
cd D:\webUpdateDetecter\PnC_insuranceNews\terraform
terraform apply -auto-approve `
  -var="state_bucket_name=my-insurance-news-state" `
  -var="slack_webhook_url=https://hooks.slack.com/services/..."
```

### 動作確認

`deploy.ps1` はデプロイ完了後に Lambda 実行 → S3 state.json の件数表示まで自動で行う。
手動で確認する場合：

```powershell
aws lambda invoke --function-name insurance-news-checker response.json
Get-Content response.json
# → {"statusCode": 200, "body": "OK"} が返れば正常
```

## AWSリソース

詳細は [terraform/README.md](terraform/README.md) を参照。

| リソース | 名前 |
|----------|------|
| Lambda関数 | `insurance-news-checker` |
| S3バケット | `my-insurance-news-state` |
| EventBridgeルール | `insurance-news-checker-hourly` |
| IAMロール | `insurance-news-checker-lambda-role` |
| CloudWatch Logs | `/aws/lambda/insurance-news-checker` |
