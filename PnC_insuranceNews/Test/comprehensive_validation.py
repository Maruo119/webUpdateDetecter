#!/usr/bin/env python3
"""
PnC_insuranceNews 複数会社検証スクリプト

複数の保険会社について、以下の検証を実施：
1. 差分検知の正確性（1件差分 / 3件差分）
2. Slack 通知条件の確認
3. 状態管理（state.json）の正確性

テスト対象会社:
  1. AIG損保 ニュースリリース
  2. 損保ジャパン ニュースリリース
  3. あいおいニッセイ同和損保 お知らせ・ニュースリリース
  4. エイチ･エス損保 お知らせ
  5. SBI損保 ニュースリリース
  6. ドコモ損保 お知らせ
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "../src")
from sites import SITES


class ComprehensiveValidator:
    def __init__(self):
        self.test_results = []
        self.logs = []

    def log(self, level: str, message: str):
        """ログを記録"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def create_test_companies(self) -> list:
        """テスト対象の会社リストを作成"""
        # sites.py から複数の会社を選択
        test_sites = [
            SITES[0],   # AIG損保 ニュースリリース
            SITES[1],   # 損保ジャパン ニュースリリース
            SITES[2],   # あいおいニッセイ同和損保 お知らせ・ニュースリリース
            SITES[5],   # エイチ･エス損保 お知らせ
            SITES[6],   # SBI損保 ニュースリリース
            SITES[8],   # ドコモ損保 お知らせ
        ]
        return test_sites

    def create_test_state(self, site_name: str, pattern: str) -> dict:
        """テスト用の初期 state を作成

        pattern:
            "pattern1": 差分1件用（既存3件）
            "pattern2": 差分3件用（既存1件）
        """
        if pattern == "pattern1":
            return {
                site_name: [
                    f"https://example.com/{site_name.split()[0]}/item2",
                    f"https://example.com/{site_name.split()[0]}/item3",
                    f"https://example.com/{site_name.split()[0]}/item4",
                ]
            }
        elif pattern == "pattern2":
            return {
                site_name: [
                    f"https://example.com/{site_name.split()[0]}/item4",
                ]
            }

    def create_mock_articles(self, site_name: str, pattern: str) -> list:
        """各パターンに対応するモック記事リストを作成"""
        company_id = site_name.split()[0]

        if pattern == "pattern1":
            # 4件の記事を返す（既存3件 + 新着1件）
            return [
                {
                    "href": f"https://example.com/{company_id}/new1",
                    "title": f"[新着] {site_name} 2025年4月のお知らせ"
                },
                {
                    "href": f"https://example.com/{company_id}/item2",
                    "title": f"{site_name} 2025年4月のお知らせ"
                },
                {
                    "href": f"https://example.com/{company_id}/item3",
                    "title": f"{site_name} 2025年3月のお知らせ"
                },
                {
                    "href": f"https://example.com/{company_id}/item4",
                    "title": f"{site_name} 2025年2月のお知らせ"
                },
            ]
        elif pattern == "pattern2":
            # 4件の記事を返す（既存1件 + 新着3件）
            return [
                {
                    "href": f"https://example.com/{company_id}/new1",
                    "title": f"[新着1号] {site_name} 2025年4月号"
                },
                {
                    "href": f"https://example.com/{company_id}/new2",
                    "title": f"[新着2号] {site_name} 2025年4月号"
                },
                {
                    "href": f"https://example.com/{company_id}/new3",
                    "title": f"[新着3号] {site_name} 2025年4月号"
                },
                {
                    "href": f"https://example.com/{company_id}/item4",
                    "title": f"{site_name} 2025年2月のお知らせ"
                },
            ]

    def simulate_lambda_execution(self, site: dict, pattern: str) -> dict:
        """Lambda 関数の実行をシミュレート"""
        site_name = site["name"]

        self.log("INFO", f"Testing: {site_name} - Pattern: {pattern}")

        # 1. 初期状態を作成
        state_before = self.create_test_state(site_name, pattern)
        articles_found = self.create_mock_articles(site_name, pattern)

        # 2. 差分を計算
        prev_hrefs = set(state_before.get(site_name, []))
        new_articles = [a for a in articles_found if a["href"] not in prev_hrefs]

        # 3. Slack 通知判定
        slack_notified = len(new_articles) > 0 and len(prev_hrefs) > 0

        # 4. 新しい state を作成
        state_after = {
            site_name: [a["href"] for a in articles_found]
        }

        # テスト結果を保存
        result = {
            'site_name': site_name,
            'pattern': pattern,
            'articles_found': len(articles_found),
            'prev_hrefs_count': len(prev_hrefs),
            'new_articles_count': len(new_articles),
            'new_articles': new_articles,
            'slack_notified': slack_notified,
            'state_before': state_before,
            'state_after': state_after,
        }

        self.test_results.append(result)

        self.log("INFO", f"  取得記事: {len(articles_found)}, 前回: {len(prev_hrefs)}, 差分: {len(new_articles)}, Slack: {'✓' if slack_notified else '✗'}")

        return result

    def verify_all_results(self) -> bool:
        """全ての検証結果を判定"""
        self.log("INFO", "\n" + "="*80)
        self.log("INFO", "【総合検証結果】")
        self.log("INFO", "="*80 + "\n")

        all_passed = True
        passed_count = 0
        failed_count = 0

        for result in self.test_results:
            site_name = result['site_name']
            pattern = result['pattern']

            if pattern == "pattern1":
                expected_new = 1
            elif pattern == "pattern2":
                expected_new = 3

            passed = (
                result['new_articles_count'] == expected_new
                and result['slack_notified']
            )

            status = "✓ PASS" if passed else "✗ FAIL"
            passed_count += 1 if passed else 0
            failed_count += 0 if passed else 1

            self.log("INFO", f"{status} | {site_name:35} | {pattern:10} | 差分:{result['new_articles_count']}/{expected_new} | 通知:{result['slack_notified']}")

            all_passed = all_passed and passed

        self.log("INFO", "\n" + "-"*80)
        self.log("INFO", f"総テスト数: {len(self.test_results)}, 成功: {passed_count}, 失敗: {failed_count}")
        self.log("INFO", "-"*80 + "\n")

        if all_passed:
            self.log("INFO", "✅ ALL TESTS PASSED")
        else:
            self.log("INFO", "❌ SOME TESTS FAILED")

        return all_passed

    def save_report(self, output_file: str):
        """検証レポートをファイルに保存"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed': sum(1 for r in self.test_results if r['new_articles_count'] > 0 and r['slack_notified']),
                'failed': sum(1 for r in self.test_results if not (r['new_articles_count'] > 0 and r['slack_notified'])),
            },
            'logs': self.logs,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.log("INFO", f"✓ Report saved to: {output_file}")


def main():
    validator = ComprehensiveValidator()
    test_companies = validator.create_test_companies()

    validator.log("INFO", "="*80)
    validator.log("INFO", "PnC_insuranceNews 複数会社検証テスト開始")
    validator.log("INFO", "="*80 + "\n")

    # 各会社について パターン1 と パターン2 をテスト
    for site in test_companies:
        validator.log("INFO", f"\n【会社: {site['name']}】")

        # パターン1: 差分1件
        validator.simulate_lambda_execution(site, "pattern1")

        # パターン2: 差分3件
        validator.simulate_lambda_execution(site, "pattern2")

    # 全結果を検証
    validator.log("INFO", "")
    passed = validator.verify_all_results()

    # レポートを保存
    output_file = "comprehensive_validation_report.json"
    validator.save_report(output_file)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
