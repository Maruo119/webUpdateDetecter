# PnC_insuranceNews テストスイート

本フォルダには、`PnC_insuranceNews` システムの包括的なテストと検証ファイルが格納されています。

## 📁 ファイル構成

### 📋 レポートファイル（7個）

#### 1. **TEST_SUMMARY.txt** ⭐ 最初に読むべき
テスト結果の全体サマリー。視覚的にわかりやすいテキスト形式。

```
内容:
  • テスト対象: 6社 × 2パターン = 12テストケース
  • 総合結果: ✅ ALL TESTS PASSED (12/12)
  • 個別結果の詳細
  • 統計サマリー
  • 検証項目の詳細
  • 本番環境での期待動作
```

**推奨用途**: プロジェクト関係者への報告、本番運用前のチェックリスト

---

#### 2. **COMPREHENSIVE_TEST_REPORT.md**
複数会社テストの詳細レポート（マークダウン形式）。

```
内容:
  • 概要
  • 全12テストケースの一覧表
  • 会社別詳細結果
    - AIG損保
    - 損保ジャパン
    - あいおいニッセイ同和損保
    - エイチ･エス損保
    - SBI損保
    - ドコモ損保
  • 検証項目別サマリー
  • 統計情報
  • 結論
```

**推奨用途**: 技術メンバーへの共有、詳細な仕様確認

---

#### 3. **FINAL_TEST_REPORT.md** ⭐ 重要
検証完了の最終報告書。本番運用への推奨を含む。

```
内容:
  • 検証概要（6社 × 2パターン = 12テスト）
  • テスト結果サマリー
  • 検証内容の詳細
  • 成果物一覧
  • 本番運用への推奨
  • チェックリスト
  • 実装手順
  • 本番運用への適性評価
  • トラブルシューティング
```

**推奨用途**: 経営層・プロジェクト管理者への報告、本番導入判定

---

#### 4. **TEST_FOLDER_GUIDE.md** ⭐ ガイド
Test フォルダ全体のガイド。ファイルの説明と使い方を網羅。

```
内容:
  • フォルダ構造図
  • ファイルガイド（詳細説明）
  • ユースケース別ガイド
    - テスト結果を報告したい
    - 仕様を詳しく知りたい
    - テストを再実行したい
    - 新しい会社を追加したい
    - CI/CD に組み込みたい
  • 本番運用チェックリスト
  • トラブルシューティング
```

**推奨用途**: Test フォルダの使い方を学ぶ、ユースケース別の手順参照

---

#### 5. **VALIDATION_EVIDENCE_REPORT.md**（アーカイブ）
初期テスト（AIG損保のみ）の詳細検証レポート。参考用。

```
内容:
  • 初期検証概要
  • パターン1/2のテスト結果
  • Slack メッセージ形式
  • 差分検知ロジック検証
  • 状態管理の検証
```

**推奨用途**: 初期検証の詳細確認、参考資料

---

#### 6. **VALIDATION_SUMMARY.txt**（アーカイブ）
初期検証（AIG損保のみ）のサマリー。参考用。

```
内容:
  • テスト結果
  • Slack メッセージプレビュー
  • 差分検知ロジック検証
  • 状態管理の検証
```

**推奨用途**: 初期検証の概要確認、参考資料

---

### 🐍 テストスクリプト（3個）

#### 1. **comprehensive_validation.py** ⭐ 推奨
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

#### 2. **test_validation.py**
初期テスト（AIG損保のみ）を実行。参考用。

```bash
python3 test_validation.py
```

用途: 検証ロジックの確認、参考資料

---

#### 3. **slack_notification_simulation.py**
Slack メッセージ形式のシミュレーション。参考用。

```bash
python3 slack_notification_simulation.py
```

出力:
- コンソール: メッセージプレビュー
- `slack_notification_report.json`: ペイロード

用途: Slack メッセージ形式の確認

---

### 📊 JSON レポート（3個）

#### 1. **comprehensive_validation_report.json** ⭐ 最新
複数会社テストの実行ログ（完全なテスト結果）

```json
内容:
  • timestamp: テスト実行日時
  • test_results: 12個のテストケース詳細
  • summary: 成功数・失敗数
  • logs: 全ログメッセージ
```

**用途**: プログラム処理、自動解析、CI/CD パイプライン

---

#### 2. **validation_report.json**（アーカイブ）
初期テスト（AIG損保）の実行ログ。参考用。

---

#### 3. **slack_notification_report.json**
Slack Block Kit メッセージペイロード。参考用。

**用途**: Slack メッセージ形式の確認

---

## 🎯 推奨される読む順序

### 本番運用前の確認フロー

1️⃣ **TEST_SUMMARY.txt**
   - テスト結果が全部 PASS しているか確認
   - 統計情報（12/12 PASS）を確認

2️⃣ **FINAL_TEST_REPORT.md**
   - 検証結果の詳細を理解
   - 本番運用チェックリストを確認
   - 本番導入の判定

3️⃣ **TEST_FOLDER_GUIDE.md**
   - Test フォルダの使い方を理解
   - 今後のテスト実行方法を習得

4️⃣ **COMPREHENSIVE_TEST_REPORT.md**（必要に応じて）
   - 6社それぞれのテスト結果を確認
   - 詳細な仕様を理解

---

## 🚀 実行方法

### 複数会社テストの実行

```bash
cd PnC_insuranceNews/Test
python3 comprehensive_validation.py
```

実行後：
- コンソール出力で各社のテスト結果を確認
- `comprehensive_validation_report.json` で詳細ログを確認

---

### JSON レポートの解析

```bash
# テスト成功数を確認
jq '.summary' comprehensive_validation_report.json

# 特定の会社のテスト結果を確認
jq '.test_results[] | select(.site_name == "AIG損保 ニュースリリース")' \
  comprehensive_validation_report.json

# 全ログを確認
jq '.logs[]' comprehensive_validation_report.json
```

---

## ✅ 本番運用チェックリスト

本番環境への展開前に確認すべき項目：

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

- `../README.md` - PnC_insuranceNews プロジェクト全体
- `../src/lambda_function.py` - Lambda 関数のソースコード
- `../src/sites.py` - 監視対象サイトの定義
- `../src/extractors.py` - XPath ベースの記事抽出ロジック

---

## 📝 テスト成果

| 項目 | 結果 |
|------|------|
| **テスト対象企業** | 6社 |
| **テストパターン** | 2パターン |
| **総テストケース** | 12 |
| **成功** | 12/12 (100%) |
| **失敗** | 0/12 (0%) |
| **差分検知精度** | 100% |
| **Slack通知機能** | 100% |
| **状態管理機能** | 100% |

---

**作成日**: 2026-04-24  
**最終更新**: 2026-04-24  
**ステータス**: ✅ 検証完了 - 本番運用向け
