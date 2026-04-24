# PnC_insuranceNews Test フォルダ ガイド

## 📁 フォルダ構造

```
PnC_insuranceNews/
├── Test/
│   ├── README.md                              ← フォルダ概要・使い方ガイド
│   ├── TEST_SUMMARY.txt                       ← ⭐ テスト結果サマリー
│   ├── COMPREHENSIVE_TEST_REPORT.md           ← 詳細レポート（6社）
│   ├── VALIDATION_EVIDENCE_REPORT.md          ← 詳細レポート（初期検証）
│   ├── VALIDATION_SUMMARY.txt                 ← 初期検証サマリー
│   │
│   ├── comprehensive_validation.py            ← 複数会社テストスクリプト
│   ├── test_validation.py                     ← 初期テストスクリプト
│   ├── slack_notification_simulation.py       ← Slack メッセージシミュレーション
│   │
│   ├── comprehensive_validation_report.json   ← テスト実行ログ（複数会社）
│   ├── validation_report.json                 ← テスト実行ログ（初期）
│   └── slack_notification_report.json         ← Slack メッセージペイロード
│
├── src/
│   ├── lambda_function.py
│   ├── sites.py
│   ├── extractors.py
│   └── ...
│
├── terraform/
│   ├── main.tf
│   └── ...
│
└── README.md
```

---

## 📋 ファイルガイド

### 📄 推奨される読む順序

#### 1️⃣ **TEST_SUMMARY.txt** ← 最初に読むべき
概要: テスト結果の全体サマリー
- 形式: テキスト（視覚的にわかりやすい）
- 分量: 約8KB
- 内容:
  - テスト対象（6社）
  - テストパターン（1件差分/3件差分）
  - 個別テスト結果（全12テスト）
  - 統計サマリー
  - 検証項目の詳細
  - 本番環境での期待動作

**用途**: 
- プロジェクト関係者への報告
- 本番運用前のチェックリスト
- 概要把握

---

#### 2️⃣ **COMPREHENSIVE_TEST_REPORT.md**
概要: 複数会社テストの詳細レポート
- 形式: マークダウン（GitHub で見やすい）
- 分量: 約8KB
- 内容:
  - 概要
  - 全12テストケースの一覧表
  - 会社別詳細結果（AIG損保の例示）
  - 検証項目別サマリー
  - 統計情報
  - 結論

**用途**:
- 技術メンバーへの共有
- アーカイブ用ドキュメント
- 詳細な仕様確認

---

#### 3️⃣ **comprehensive_validation_report.json**
概要: テスト実行ログ（JSON形式）
- 形式: JSON
- 分量: 約20KB
- 内容:
  - タイムスタンプ
  - 各テストケースの詳細
  - 統計サマリー
  - 全ログメッセージ

**用途**:
- プログラム処理・自動解析
- 詳細な調査が必要な場合
- CI/CD パイプラインでの利用

---

### 📋 参考用ドキュメント

#### **VALIDATION_EVIDENCE_REPORT.md**
初期検証（AIG損保）の詳細レポート
- 用途: 参考資料、初期検証の詳細を知りたい場合

#### **VALIDATION_SUMMARY.txt**
初期検証（AIG損保）のサマリー
- 用途: 参考資料、簡潔なサマリーが必要な場合

---

### 🐍 テストスクリプト

#### **comprehensive_validation.py** ⭐ 推奨
複数会社（6社）のテストを実行

```bash
cd PnC_insuranceNews/Test
python3 comprehensive_validation.py
```

実行結果:
- コンソール出力: テスト進捗
- `comprehensive_validation_report.json` 生成

テスト対象:
1. AIG損保
2. 損保ジャパン
3. あいおいニッセイ同和損保
4. エイチ･エス損保
5. SBI損保
6. ドコモ損保

実行時間: 約1秒

---

#### **test_validation.py**
初期テスト（AIG損保）のみを実行

```bash
python3 test_validation.py
```

用途: 参考用・検証ロジックの確認

---

#### **slack_notification_simulation.py**
Slack メッセージ形式のシミュレーション

```bash
python3 slack_notification_simulation.py
```

出力:
- コンソール: メッセージプレビュー
- `slack_notification_report.json`: ペイロード

用途: Slack メッセージ形式の確認

---

### 📊 JSON レポート

#### **comprehensive_validation_report.json** ← 最新テスト結果
複数会社テストの実行ログ

**内容:**
```json
{
  "timestamp": "2026-04-24T02:07:36.xxx",
  "test_results": [
    {
      "site_name": "AIG損保 ニュースリリース",
      "pattern": "pattern1",
      "articles_found": 4,
      "prev_hrefs_count": 3,
      "new_articles_count": 1,
      "slack_notified": true,
      ...
    },
    ...
  ],
  "summary": {
    "total_tests": 12,
    "passed": 12,
    "failed": 0
  },
  "logs": [...]
}
```

**用途**: プログラム処理、自動解析、CI/CD パイプライン

---

#### **validation_report.json**
初期検証（AIG損保）のログ

**用途**: 参考資料

---

#### **slack_notification_report.json**
Slack Block Kit メッセージペイロード

**用途**: Slack メッセージ形式の確認

---

## 🎯 ユースケース別ガイド

### 📌 ユースケース1: テスト結果を報告したい

**推奨ファイル:**
1. `TEST_SUMMARY.txt` ← まずこれを読む
2. `comprehensive_validation_report.json` ← 詳細データが必要な場合

**手順:**
1. TEST_SUMMARY.txt の「【統計サマリー】」セクションをコピー
2. プレゼンテーションに貼り付け
3. 必要に応じて JSON データで詳細を補足

---

### 📌 ユースケース2: 仕様を詳しく知りたい

**推奨ファイル:**
1. `README.md` ← 概要・使い方
2. `COMPREHENSIVE_TEST_REPORT.md` ← 詳細仕様

**手順:**
1. README.md で「テスト概要」セクションを読む
2. COMPREHENSIVE_TEST_REPORT.md で詳細を確認

---

### 📌 ユースケース3: テストを再実行したい

**手順:**
```bash
cd PnC_insuranceNews/Test

# 複数会社テストを実行
python3 comprehensive_validation.py

# 結果を確認
cat TEST_SUMMARY.txt
```

---

### 📌 ユースケース4: 新しい会社を追加してテストしたい

**手順:**
1. `comprehensive_validation.py` を編集
2. `create_test_companies()` メソッドに新会社を追加
3. テストを実行
4. 結果を確認

**編集例:**
```python
def create_test_companies(self) -> list:
    test_sites = [
        SITES[0],   # AIG損保
        SITES[1],   # 損保ジャパン
        # ... 他の会社 ...
        SITES[10],  # 新しい会社を追加
    ]
    return test_sites
```

---

### 📌 ユースケース5: CI/CD パイプラインに組み込みたい

**推奨ファイル:**
- `comprehensive_validation.py` ← スクリプト
- `comprehensive_validation_report.json` ← テスト結果（自動解析用）

**手順:**
1. スクリプトを CI/CD パイプラインで実行
2. JSON レポートを解析
3. パイプライン内で結果を判定（成功/失敗）
4. 失敗時はアラート送信

**サンプル AWS CodePipeline:**
```yaml
- name: Test PnC Insurance News
  run: |
    cd PnC_insuranceNews/Test
    python3 comprehensive_validation.py
    if [ ! -f comprehensive_validation_report.json ]; then
      exit 1
    fi
    # JSON から成功数を抽出
    PASSED=$(jq '.summary.passed' comprehensive_validation_report.json)
    TOTAL=$(jq '.summary.total_tests' comprehensive_validation_report.json)
    if [ "$PASSED" -ne "$TOTAL" ]; then
      echo "Test failed: $PASSED/$TOTAL"
      exit 1
    fi
```

---

## ✅ 本番運用チェックリスト

本番環境への展開前に確認してください：

- [ ] TEST_SUMMARY.txt で全テストが PASS していることを確認
- [ ] 全12テストケース（2パターン × 6社）が成功
- [ ] Lambda 環境変数が正しく設定されている
  - [ ] `SLACK_WEBHOOK_URL` が有効
  - [ ] `STATE_BUCKET` が存在
- [ ] S3 バケットが Lambda から アクセス可能
- [ ] EventBridge スケジュール（rate(1 hour)）が有効
- [ ] CloudWatch Logs が記録されている
- [ ] Slack 通知先チャンネルが正しい
- [ ] state.json が S3 に存在する
- [ ] 手動テストで実際に通知が届くことを確認

---

## 📞 トラブルシューティング

### テストが実行できない

**エラー**: `ModuleNotFoundError: No module named 'sites'`

**解決方法**:
```bash
cd PnC_insuranceNews/Test
python3 comprehensive_validation.py
```

---

### テストは成功するが本番で通知が届かない

**原因**: Slack Webhook URL が無効

**確認方法**:
```bash
aws lambda get-function-configuration \
  --function-name PnC_insuranceNews_Checker \
  --query 'Environment.Variables'
```

**解決方法**:
1. Slack Webhook URL を再生成
2. Lambda 環境変数を更新

---

## 📚 関連ドキュメント

- `PnC_insuranceNews/README.md` - プロジェクト全体
- `PnC_insuranceNews/Test/README.md` - Test フォルダの詳細ガイド
- `CLAUDE.md` - プロジェクト方針・開発ルール

---

## 📞 サポート

テストに関する質問や問題がある場合:

1. `README.md` の「トラブルシューティング」を確認
2. `comprehensive_validation_report.json` のログを確認
3. Lambda CloudWatch Logs を確認

---

**最終更新**: 2026-04-24  
**テスト実行日**: 2026-04-24 02:07:36 UTC  
**総合評価**: ✅ **本番運用向け**
