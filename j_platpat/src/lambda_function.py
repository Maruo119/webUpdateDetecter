import asyncio
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Set

import boto3
import requests
from playwright.async_api import async_playwright

# AWS & Slack 設定
S3_CLIENT = boto3.client("s3")
STATE_BUCKET = os.environ.get("STATE_BUCKET_NAME")
STATE_KEY = os.environ.get("STATE_KEY", "j_platpat/state.json")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# j-platpat 設定
J_PLATPAT_URL = "https://www.j-platpat.inpit.go.jp/s0100"
TIMEOUT_MS = 60000


def fetch_state_from_s3() -> Dict[str, List[Dict]]:
    """S3 から現在の状態を取得"""
    try:
        response = S3_CLIENT.get_object(Bucket=STATE_BUCKET, Key=STATE_KEY)
        state = json.loads(response["Body"].read().decode("utf-8"))
        return state
    except S3_CLIENT.exceptions.NoSuchKey:
        return {}
    except Exception as e:
        print(f"Error fetching state from S3: {e}")
        return {}


def save_state_to_s3(state: Dict[str, List[Dict]]) -> None:
    """現在の状態を S3 に保存"""
    try:
        S3_CLIENT.put_object(
            Bucket=STATE_BUCKET,
            Key=STATE_KEY,
            Body=json.dumps(state, ensure_ascii=False, indent=2),
            ContentType="application/json",
        )
        print(f"State saved to S3: {STATE_KEY}")
    except Exception as e:
        print(f"Error saving state to S3: {e}")


async def scrape_j_platpat() -> List[Dict]:
    """Playwright で j-platpat をスクレイプして特許一覧を取得"""
    patents = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            print(f"Navigating to {J_PLATPAT_URL}...")
            await page.goto(J_PLATPAT_URL, wait_until="networkidle", timeout=TIMEOUT_MS)

            # 「四法全て」ラジオボタンを選択
            print("Selecting '四法全て' radio button...")
            await page.click('input[value="1"][name="s01_srchTarget_rdoSimpleSearch"]')
            await asyncio.sleep(1)

            # 検索ボタンをクリック
            print("Clicking search button...")
            await page.click("#s01_srchBtn_btnSearch")
            await page.wait_for_selector(
                "#patentUtltyIntnlSimpleBibLst", timeout=TIMEOUT_MS
            )
            await asyncio.sleep(2)

            # 結果テーブルから行を抽出
            print("Extracting patent data...")
            rows = await page.locator("#patentUtltyIntnlSimpleBibLst tbody tr").count()
            print(f"Found {rows} rows")

            for i in range(rows):
                try:
                    row = page.locator(
                        f"#patentUtltyIntnlSimpleBibLst tbody tr:nth-child({i + 1})"
                    )

                    # 文献番号（リンク）
                    doc_num_link = await row.locator("a").first.get_attribute("href")
                    doc_num_text = await row.locator(
                        f"#patentUtltyIntnlSimpleBibLst_tableView_docNum"
                    ).first.text_content()
                    doc_num = (doc_num_text or "").strip()

                    # 出願番号
                    app_num_text = await row.locator(
                        f"#patentUtltyIntnlSimpleBibLst_tableView_appNum{i}"
                    ).text_content()
                    app_num = (app_num_text or "").strip()

                    # 発明の名称
                    inven_name_text = await row.locator(
                        f"#patentUtltyIntnlSimpleBibLst_tableView_invenName{i}"
                    ).text_content()
                    inven_name = (inven_name_text or "").strip()

                    # 出願人/権利者
                    applicant_text = await row.locator(
                        f"#patentUtltyIntnlSimpleBibLst_tableView_appnRightHolder{i}"
                    ).text_content()
                    applicant = (applicant_text or "").strip()

                    # ステータス
                    status_text = await row.locator(
                        f"#patentUtltyIntnlSimpleBibLst_tableView_status{i}"
                    ).text_content()
                    status = (status_text or "").strip().replace("\n", " ")

                    if app_num and inven_name:
                        patents.append(
                            {
                                "doc_num": doc_num,
                                "doc_num_link": doc_num_link or "",
                                "app_num": app_num,
                                "inven_name": inven_name,
                                "applicant": applicant,
                                "status": status,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                except Exception as e:
                    print(f"Error extracting row {i}: {e}")
                    continue

        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await browser.close()

    print(f"Scraped {len(patents)} patents")
    return patents


def detect_new_patents(
    previous_patents: List[Dict], current_patents: List[Dict]
) -> List[Dict]:
    """前回の状態と比較して新規特許を検出"""
    prev_app_nums = {p["app_num"] for p in previous_patents}
    new_patents = [p for p in current_patents if p["app_num"] not in prev_app_nums]
    return new_patents


def send_slack_notification(new_patents: List[Dict]) -> None:
    """Slack に新規特許の通知を送信"""
    if not new_patents:
        print("No new patents to notify")
        return

    if not SLACK_WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL not set")
        return

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🔍 j-platpat 新規特許情報 ({len(new_patents)}件)",
            },
        },
        {
            "type": "divider",
        },
    ]

    for patent in new_patents[:20]:  # Slack メッセージサイズ制限対策
        # 文献番号をリンク化
        doc_num_str = patent["doc_num"]
        if patent["doc_num_link"]:
            # doc_num_link は javascript:void(0) の可能性があるため、直接URLを構築
            # または j-platpat から詳細ページ URL を取得
            doc_num_display = f"`{doc_num_str}`"
        else:
            doc_num_display = f"`{doc_num_str}`"

        # Slack block を構築
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{doc_num_display}*\n{patent['app_num']} | {patent['inven_name']}\n出願人: {patent['applicant']}\nステータス: {patent['status']}",
                },
            }
        )
        blocks.append({"type": "divider"})

    payload = {
        "blocks": blocks,
    }

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        print(f"Slack notification sent successfully ({len(new_patents)} patents)")
    except Exception as e:
        print(f"Error sending Slack notification: {e}")


async def lambda_handler(event, context):
    """Lambda ハンドラー"""
    print(f"Starting j-platpat monitoring at {datetime.utcnow().isoformat()}")

    # 前回の状態を取得
    previous_state = fetch_state_from_s3()
    previous_patents = previous_state.get(J_PLATPAT_URL, [])
    print(f"Previous state: {len(previous_patents)} patents")

    # 現在のデータをスクレイプ
    current_patents = await scrape_j_platpat()

    # 新規特許を検出
    new_patents = detect_new_patents(previous_patents, current_patents)
    print(f"New patents detected: {len(new_patents)}")

    # 初回実行の場合は通知しない
    if len(previous_patents) == 0:
        print("First run - baseline established, no notification sent")
    else:
        # Slack に通知
        send_slack_notification(new_patents)

    # 状態を更新・保存
    updated_state = {J_PLATPAT_URL: current_patents}
    save_state_to_s3(updated_state)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "j-platpat monitoring completed",
                "previous_count": len(previous_patents),
                "current_count": len(current_patents),
                "new_patents_count": len(new_patents),
            }
        ),
    }


def lambda_handler_sync(event, context):
    """Lambda ハンドラー（同期ラッパー）"""
    return asyncio.run(lambda_handler(event, context))
