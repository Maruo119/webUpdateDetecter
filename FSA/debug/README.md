# Debug Scripts — FSA

このフォルダは開発・デバッグ用のスクリプトとテストデータを含みます。本番環境では使用されません。

## ファイル説明

| ファイル | 用途 |
|---------|------|
| `debug_fsa.py` | FSA ページ構造の初期デバッグスクリプト（過去開発時） |
| `debug_fsa_detailed.py` | RSS フィード解析の詳細ログ出力版 |
| `debug_fsa_extract.py` | 記事抽出ロジックの単体テスト |
| `test_html_dump.py` | ローカル HTML ファイルの検証用テスト |
| `test_local.py` | ローカル環境でのエンドツーエンドテスト |
| `fsa_page_dump.html` | 過去の FSA ページのキャプチャ（参照用） |

## 参照

実装の詳細は [../README.md](../README.md) および [../src/](../src/) を参照してください。
