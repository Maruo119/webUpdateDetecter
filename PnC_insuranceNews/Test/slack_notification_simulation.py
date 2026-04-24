#!/usr/bin/env python3
"""
Slack メッセージ形式のシミュレーション

実際の Lambda 関数が生成する Slack Block Kit メッセージを
 JSON 形式で生成して、メッセージプレビューと共に表示する
"""

import json
from datetime import datetime


def simulate_slack_notification(site_name: str, new_articles: list[dict]) -> dict:
    """実際の Lambda 関数と同じ形式の Slack Block Kit メッセージを生成"""
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":newspaper: *{site_name}* に新しいお知らせが掲載されました！",
            },
        },
        {"type": "divider"},
    ]
    for article in new_articles:
        title = article.get("title") or "（タイトルなし）"
        href = article.get("href", "")
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"<{href}|{title}>"},
            }
        )
    return {"blocks": blocks}


def print_slack_preview(pattern: str, site_name: str, new_articles: list[dict], num_items: int):
    """Slack メッセージのテキスト形式プレビューを表示"""
    print(f"\n{'='*80}")
    print(f"【{pattern}】Slack メッセージプレビュー")
    print(f"{'='*80}\n")

    print(f"🔔 受信者に表示される内容：\n")
    print(f"   📰 *{site_name}* に新しいお知らせが掲載されました！")
    print(f"   " + "-" * 70)

    for i, article in enumerate(new_articles, 1):
        title = article.get("title", "（タイトルなし）")
        href = article.get("href", "")
        print(f"   {i}. {title}")
        print(f"      🔗 {href}")
        if i < len(new_articles):
            print()

    print(f"\n   新着: {num_items}件\n")


def main():
    # パターン1: 差分1件
    pattern1_articles = [
        {
            "href": "https://www.aig.co.jp/sonpo/company/news/2025/04/item1",
            "title": "[新着] 2025年4月の新しいお知らせ - パターン1検証"
        }
    ]

    # パターン2: 差分3件
    pattern2_articles = [
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
        }
    ]

    site_name = "AIG損保 ニュースリリース"

    # パターン1のシミュレーション
    print_slack_preview(
        "パターン1（差分1件）",
        site_name,
        pattern1_articles,
        len(pattern1_articles)
    )

    slack_msg_1 = simulate_slack_notification(site_name, pattern1_articles)
    print("📋 Block Kit JSON（パターン1）:")
    print(json.dumps(slack_msg_1, ensure_ascii=False, indent=2))

    # パターン2のシミュレーション
    print_slack_preview(
        "パターン2（差分3件）",
        site_name,
        pattern2_articles,
        len(pattern2_articles)
    )

    slack_msg_2 = simulate_slack_notification(site_name, pattern2_articles)
    print("📋 Block Kit JSON（パターン2）:")
    print(json.dumps(slack_msg_2, ensure_ascii=False, indent=2))

    # レポートをファイルに保存
    report = {
        "timestamp": datetime.now().isoformat(),
        "pattern1": {
            "description": "差分1件検出時の Slack メッセージ",
            "articles_count": len(pattern1_articles),
            "articles": pattern1_articles,
            "slack_payload": slack_msg_1
        },
        "pattern2": {
            "description": "差分3件検出時の Slack メッセージ",
            "articles_count": len(pattern2_articles),
            "articles": pattern2_articles,
            "slack_payload": slack_msg_2
        }
    }

    with open("slack_notification_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Slack notification report saved to: slack_notification_report.json")


if __name__ == "__main__":
    main()
