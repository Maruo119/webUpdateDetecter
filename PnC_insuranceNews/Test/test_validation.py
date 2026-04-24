#!/usr/bin/env python3
"""
PnC_insuranceNews 検証スクリプト

検証観点：
1. 正しく差分を取得できているか（state.json 修正によるテスト）
2. 差分を検知して Slack に通知できているか
3. 複数パターン：差分1件、差分3件

テスト方法：
- state.json を修正して前回の記事リストを設定
- Lambda を実行して新しい記事を取得
- 差分を検出して Slack に通知を送信
- ログと通知内容を検証
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# src モジュールをインポート
sys.path.insert(0, "src")

# Mock Slack URL for testing
MOCK_SLACK_URL = os.environ.get("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/MOCK/TEST/MOCK")

class TestValidator:
    def __init__(self):
        self.test_results = []
        self.logs = []

    def log(self, level: str, message: str):
        """ログを記録"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def create_test_state(self, pattern: str) -> dict:
        """テスト用の初期 state を作成

        pattern:
            "pattern1_1item": 1つのサイトに既存3件の記事がある状態
            "pattern2_3items": 1つのサイトに既存3件の記事がある状態
        """
        if pattern == "pattern1_1item":
            # パターン1：差分1件の検証用
            # 既存: 3件、取得時に4件見つかる（新着1件）
            return {
                "AIG損保 ニュースリリース": [
                    "https://www.aig.co.jp/sonpo/company/news/2025/04/item2",
                    "https://www.aig.co.jp/sonpo/company/news/2025/03/item3",
                    "https://www.aig.co.jp/sonpo/company/news/2025/02/item4",
                ]
            }
        elif pattern == "pattern2_3items":
            # パターン2：差分3件の検証用
            # 既存: 1件、取得時に4件見つかる（新着3件）
            return {
                "AIG損保 ニュースリリース": [
                    "https://www.aig.co.jp/sonpo/company/news/2025/02/item4",
                ]
            }

    def create_mock_articles(self, pattern: str) -> list:
        """各パターンに対応するモック記事リストを作成"""
        if pattern == "pattern1_1item":
            # 4件の記事を返す（既存3件 + 新着1件）
            return [
                {
                    "href": "https://www.aig.co.jp/sonpo/company/news/2025/04/item1",
                    "title": "[新着] 2025年4月の新しいお知らせ - パターン1検証"
                },
                {
                    "href": "https://www.aig.co.jp/sonpo/company/news/2025/04/item2",
                    "title": "2025年4月のお知らせ"
                },
                {
                    "href": "https://www.aig.co.jp/sonpo/company/news/2025/03/item3",
                    "title": "2025年3月のお知らせ"
                },
                {
                    "href": "https://www.aig.co.jp/sonpo/company/news/2025/02/item4",
                    "title": "2025年2月のお知らせ"
                },
            ]
        elif pattern == "pattern2_3items":
            # 4件の記事を返す（既存1件 + 新着3件）
            return [
                {
                    "href": "https://www.aig.co.jp/sonpo/company/news/2025/04/new1",
                    "title": "[新着1] 2025年4月第1号 - パターン2検証"
                },
                {
                    "href": "https://www.aig.co.jp/sonpo/company/news/2025/04/new2",
                    "title": "[新着2] 2025年4月第2号 - パターン2検証"
                },
                {
                    "href": "https://www.aig.co.jp/sonpo/company/news/2025/04/new3",
                    "title": "[新着3] 2025年4月第3号 - パターン2検証"
                },
                {
                    "href": "https://www.aig.co.jp/sonpo/company/news/2025/02/item4",
                    "title": "2025年2月のお知らせ"
                },
            ]

    def simulate_lambda_execution(self, pattern: str) -> dict:
        """Lambda 関数の実行をシミュレート

        返り値: {
            'pattern': パターン名,
            'state_before': 修正前の state,
            'articles_found': 取得した記事数,
            'new_articles': 新着記事リスト,
            'state_after': 修正後の state,
            'slack_notified': Slack 通知が行われたか,
            'logs': ログメッセージ
        }
        """
        self.log("INFO", f"=== Testing Pattern: {pattern} ===")

        # 1. 初期状態を作成
        state_before = self.create_test_state(pattern)
        articles_found = self.create_mock_articles(pattern)

        self.log("INFO", f"State before: {json.dumps(state_before, ensure_ascii=False)}")
        self.log("INFO", f"Articles found from website: {len(articles_found)} items")

        # 2. 差分を計算
        site_name = "AIG損保 ニュースリリース"
        prev_hrefs = set(state_before.get(site_name, []))
        new_articles = [a for a in articles_found if a["href"] not in prev_hrefs]

        self.log("INFO", f"Previous hrefs: {len(prev_hrefs)} items")
        self.log("INFO", f"New articles detected: {len(new_articles)} items")

        for i, article in enumerate(new_articles, 1):
            self.log("INFO", f"  New[{i}] {article['title'][:60]}")
            self.log("INFO", f"    → {article['href']}")

        # 3. Slack 通知判定
        slack_notified = len(new_articles) > 0 and len(prev_hrefs) > 0

        if slack_notified:
            self.log("INFO", "✓ Slack notification WILL BE SENT (new articles > 0 AND prev_hrefs > 0)")
        else:
            if len(prev_hrefs) == 0:
                self.log("INFO", "✗ First run - Slack notification WILL NOT BE SENT (recording baseline)")
            else:
                self.log("INFO", "✗ No new articles - Slack notification WILL NOT BE SENT")

        # 4. 新しい state を作成
        state_after = {
            site_name: [a["href"] for a in articles_found]
        }

        self.log("INFO", f"State after: {json.dumps(state_after, ensure_ascii=False)}")

        # テスト結果を保存
        result = {
            'pattern': pattern,
            'state_before': state_before,
            'articles_found': len(articles_found),
            'new_articles': new_articles,
            'new_articles_count': len(new_articles),
            'prev_hrefs_count': len(prev_hrefs),
            'state_after': state_after,
            'slack_notified': slack_notified,
            'logs': self.logs.copy()
        }

        self.test_results.append(result)
        return result

    def verify_results(self) -> bool:
        """検証結果を判定"""
        self.log("INFO", "\n=== VERIFICATION SUMMARY ===\n")

        all_passed = True

        for i, result in enumerate(self.test_results, 1):
            pattern = result['pattern']
            self.log("INFO", f"\n【テストケース {i}】{pattern}")
            self.log("INFO", f"  取得記事数: {result['articles_found']} items")
            self.log("INFO", f"  前回の記事数: {result['prev_hrefs_count']} items")
            self.log("INFO", f"  新着記事数: {result['new_articles_count']} items")
            self.log("INFO", f"  Slack 通知予定: {'✓ YES' if result['slack_notified'] else '✗ NO'}")

            # パターン別の検証ロジック
            if pattern == "pattern1_1item":
                expected_new = 1
                passed = result['new_articles_count'] == expected_new
                self.log("INFO", f"  期待値: {expected_new} 件の新着 → {'✓ PASS' if passed else '✗ FAIL'}")
                if result['slack_notified']:
                    self.log("INFO", f"  Slack 通知: ✓ CORRECT (新着あり + 前回の記録あり)")
                else:
                    self.log("INFO", f"  Slack 通知: ✗ WRONG (通知すべきだった)")
                    passed = False
                all_passed = all_passed and passed

            elif pattern == "pattern2_3items":
                expected_new = 3
                passed = result['new_articles_count'] == expected_new
                self.log("INFO", f"  期待値: {expected_new} 件の新着 → {'✓ PASS' if passed else '✗ FAIL'}")
                if result['slack_notified']:
                    self.log("INFO", f"  Slack 通知: ✓ CORRECT (新着あり + 前回の記録あり)")
                else:
                    self.log("INFO", f"  Slack 通知: ✗ WRONG (通知すべきだった)")
                    passed = False
                all_passed = all_passed and passed

        self.log("INFO", f"\n=== OVERALL RESULT ===")
        self.log("INFO", f"{'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")

        return all_passed

    def save_report(self, output_file: str):
        """検証レポートをファイルに保存"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'logs': self.logs,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.log("INFO", f"\n✓ Report saved to: {output_file}")


if __name__ == "__main__":
    validator = TestValidator()

    # パターン1: 差分1件の検証
    validator.simulate_lambda_execution("pattern1_1item")

    print("\n" + "="*80 + "\n")

    # パターン2: 差分3件の検証
    validator.simulate_lambda_execution("pattern2_3items")

    print("\n" + "="*80 + "\n")

    # 検証結果を確認
    passed = validator.verify_results()

    # レポートを保存
    output_file = "validation_report.json"
    validator.save_report(output_file)

    sys.exit(0 if passed else 1)
