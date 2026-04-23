import json
import os
import boto3
import requests
from bs4 import BeautifulSoup

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

SITES = [
    {
        "name": "【店舗・施設】柏の葉キャンパス",
        "url": "https://kashiwanoha-cycle-life.blog.jp/archives/cat_861420.html",
    },
    {
        "name": "【店舗・施設】流山おおたかの森",
        "url": "https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041375.html",
    },
    {
        "name": "【店舗・施設】柏・流山周辺",
        "url": "https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041376.html",
    },
    {
        "name": "【イベント】柏の葉キャンパス",
        "url": "https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041507.html",
    },
    {
        "name": "【イベント】流山おおたかの森",
        "url": "https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041508.html",
    },
    {
        "name": "【イベント】柏・流山周辺",
        "url": "https://kashiwanoha-cycle-life.blog.jp/archives/cat_10041509.html",
    },
    {
        "name": "【鉄道】つくばエクスプレス",
        "url": "https://kashiwanoha-cycle-life.blog.jp/archives/cat_861419.html",
    },
]

S3_BUCKET = os.environ.get("STATE_BUCKET", "")
S3_KEY = "cycleLifeBlog/state.json"

_s3 = None


def s3_client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3


def load_state() -> dict:
    if not S3_BUCKET:
        path = "/tmp/cycleLifeBlog_state.json"
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    try:
        res = s3_client().get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        return json.loads(res["Body"].read().decode("utf-8"))
    except s3_client().exceptions.NoSuchKey:
        return {}


def save_state(state: dict) -> None:
    if not S3_BUCKET:
        with open("/tmp/cycleLifeBlog_state.json", "w") as f:
            json.dump(state, f, ensure_ascii=False)
        return

    s3_client().put_object(
        Bucket=S3_BUCKET,
        Key=S3_KEY,
        Body=json.dumps(state, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )


def fetch_articles(url: str) -> list[dict]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    res = requests.get(url, headers=headers, timeout=30)
    res.raise_for_status()
    res.encoding = res.apparent_encoding

    soup = BeautifulSoup(res.text, "html.parser")
    articles = []

    for item_box in soup.select(".article-body .itemBox"):
        parent_a = item_box.find_parent("a")
        if not parent_a:
            continue
        href = parent_a.get("href", "").strip()
        if not href:
            continue

        img = item_box.find("img", class_="pict3")
        title = img.get("title", "").strip() if img else ""

        articles.append({"href": href, "title": title})

    return articles


def send_slack(site_name: str, new_articles: list[dict]) -> None:
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":new: *{site_name}* に新しい記事が投稿されました！",
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
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title}*\n<{href}|記事を読む>",
                },
            }
        )

    res = requests.post(SLACK_WEBHOOK_URL, json={"blocks": blocks}, timeout=10)
    res.raise_for_status()


def check_site(site: dict, state: dict) -> list[str]:
    url = site["url"]
    name = site["name"]

    try:
        articles = fetch_articles(url)
    except Exception as e:
        print(f"[ERROR] fetch failed: {url} — {e}")
        return state.get(url, [])

    prev_hrefs: set[str] = set(state.get(url, []))
    new_articles = [a for a in articles if a["href"] not in prev_hrefs]

    # Skip notification on first run (prev_hrefs is empty) to avoid bulk spam
    if new_articles and prev_hrefs:
        try:
            send_slack(name, new_articles)
            print(f"[INFO] notified {len(new_articles)} new article(s) for {name}")
        except Exception as e:
            print(f"[ERROR] slack notification failed for {name}: {e}")
    elif not prev_hrefs:
        print(f"[INFO] first run for {name}: recorded {len(articles)} article(s)")

    return [a["href"] for a in articles]


def lambda_handler(event, context):
    state = load_state()
    new_state = {}

    for site in SITES:
        new_state[site["url"]] = check_site(site, state)

    save_state(new_state)
    return {"statusCode": 200, "body": "OK"}


if __name__ == "__main__":
    lambda_handler({}, None)
