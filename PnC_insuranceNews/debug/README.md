# Debug Scripts — PnC_insuranceNews

このフォルダは開発・デバッグ用のスクリプトと過去のテストコードを含みます。本番環境では使用されません。

## ファイル説明

| ファイル | 用途 |
|---------|------|
| `debug_anicom.py` | アニコム損保の XPath・抽出ロジック検証用（過去開発時） |
| `debug_axa.py` | アクサ損保の検証用スクリプト（JavaScript 非対応のため、現在スキップ中） |
| `test_refactor.py` | 過去のリファクタリング時のテストコード |
| `test_state_migration.py` | S3 state.json の形式変更時の移行テストコード |

## 参照

実装の詳細は [../README.md](../README.md) および [../src/](../src/) を参照してください。
