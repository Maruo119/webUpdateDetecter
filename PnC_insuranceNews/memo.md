
# 対象とする損害保険会社一覧
https://www.sonpo.or.jp/member/link/ev7otb0000000cwh-att/hensen.pdf

## 完了済み
- ＡＩＧ損保
- 損保ジャパン
- あいおいニッセイ同和損保
- アニコム損保（トピックス・ニュースリリース、年度別URL対応）
- エイチ･エス損保（お知らせ）
- ＳＢＩ損保（ニュースリリース・お知らせ）
- ドコモ損保（お知らせ）
- キャピタル損保（お知らせ）
- 共栄火災（お知らせ、XPath: `//*[@id="main"]/div[1]/section[1]/div/div/div[2]`、※WindowsローカルのみSSL証明書エラー発生・Lambda環境では問題なし）
- さくら損保（お知らせ）
- ジェイアイ（お知らせ）
- 全管協れいわ損保（お知らせ）
- ソニー損保（お知らせ・自然災害等のお知らせ、XPathはclass-based）
- SOMPOダイレクト（大切なお知らせ・ニュースリリース、メインサイトはJS動的→ニュースポータル news-ins-saison.dga.jp から取得）

## スキップ（JavaScript対応が必要）
### アクサ損保
https://www.axa-direct.co.jp/company/official_info/

お知らせ：「/html/body/main/div[1]/div[3]/div/div/div/section[2]」
ニュースリリース：「/html/body/main/div[1]/div[3]/div/div/div/section[1]」

### ａｕ損保
https://www.au-sonpo.co.jp/corporate/news/
お知らせ＆プレスリリース：「/html/body/main/div」
（記事一覧がJSで動的レンダリング）

### セコム損保
https://www.secom-sonpo.co.jp/
お知らせ：「//*[@id="public"]」
商品・サービスのお知らせ：「//*[@id="commodity"]」
（ulが空でJSで動的レンダリング）

## 未完了

### 第一アイペット
https://www.ipet-ins.com/info/
お知らせ：「/html/body/main/div/div/div/ul」

### 大同火災
https://www.daidokasai.co.jp/news/
お知らせ：「//*[@id="top"]/main/section[2]/div/div/div/ul」

### 東京海上ダイレクト
https://www.e-design.net/
お知らせ：「/html/body/div[1]/main/article/section[9]/div/div/div[1]/div[2]」
ニュースリリース：「/html/body/div[1]/main/article/section[9]/div/div/div[2]/div[2]」

### 東京海上日動

### トーア再保険

### 日新火災

### 日本地震

### ペット＆ファミリー損保

### 三井住友海上

### 三井ダイレクト損保

### 明治安田損保

### ヤマップネイチャランス

### 楽天損保

### レスキュー損保
