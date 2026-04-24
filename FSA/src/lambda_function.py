import json
import os
import boto3
import requests

from sites import SITES
from extractors import EXTRACTORS

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
S3_BUCKET = os.environ.get("STATE_BUCKET", "")
S3_KEY = "FSA/state.json"

_s3 = None


def s3_client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3


def load_state():
    if not S3_BUCKET:
        path = "/tmp/FSA_state.json"
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}
    try:
        res = s3_client().get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        return json.loads(res["Body"].read().decode("utf-8"))
    except Exception:
        return {}


def save_state(state):
    if not S3_BUCKET:
        with open("/tmp/FSA_state.json", "w") as f:
            json.dump(state, f, ensure_ascii=False)
        return
    s3_client().put_object(
        Bucket=S3_BUCKET,
        Key=S3_KEY,
        Body=json.dumps(state, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )


def fetch_rss(rss_url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    res = requests.get(rss_url, headers=headers, timeout=30)
    res.raise_for_status()
    encoding = res.apparent_encoding or res.encoding or "utf-8"
    return res.content.decode(encoding, errors="replace")


def fetch_articles(site):
    rss_url = site["rss_url"]
    rss_content = fetch_rss(rss_url)
    extractor = EXTRACTORS[site.get("extractor", "fsa")]
    return extractor(rss_content)


def send_slack(site_name, new_articles):
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
    res = requests.post(SLACK_WEBHOOK_URL, json={"blocks": blocks}, timeout=10)
    res.raise_for_status()


def _lookup_prev_hrefs(site, state):
    name = site["name"]
    if name in state:
        return list(state.get(name, []))
    return []


def check_site(site, state):
    name = site["name"]
    try:
        articles = fetch_articles(site)
    except Exception as e:
        print(f"[ERROR] fetch failed: {name} - {e}")
        return _lookup_prev_hrefs(site, state)

    prev_hrefs = set(_lookup_prev_hrefs(site, state))
    new_articles = [a for a in articles if a["href"] not in prev_hrefs]

    print(
        f"[INFO] {name}: extracted={len(articles)}, "
        f"prev={len(prev_hrefs)}, new={len(new_articles)}"
    )

    if new_articles and prev_hrefs:
        try:
            send_slack(name, new_articles)
            print(f"[INFO] notified {len(new_articles)} new item(s) for {name}")
        except Exception as e:
            print(f"[ERROR] slack notification failed for {name}: {e}")
    elif not prev_hrefs:
        print(f"[INFO] first run for {name}: recorded {len(articles)} item(s)")

    return [a["href"] for a in articles]


def lambda_handler(event, context):
    state = load_state()
    new_state = {}
    for site in SITES:
        new_state[site["name"]] = check_site(site, state)
    save_state(new_state)
    return {"statusCode": 200, "body": "OK"}


if __name__ == "__main__":
    lambda_handler({}, None)
