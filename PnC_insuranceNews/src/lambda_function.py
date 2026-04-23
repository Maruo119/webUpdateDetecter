import datetime
import json
import os
from urllib.parse import urlparse
import boto3
import requests
from lxml import html as lxml_html

from sites import SITES
from extractors import EXTRACTORS

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
S3_BUCKET = os.environ.get("STATE_BUCKET", "")
S3_KEY = "PnC_insuranceNews/state.json"

_s3 = None
_SSL_SKIP_HOSTS = {"www.kyoeikasai.co.jp"}


def s3_client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3


def load_state() -> dict:
    if not S3_BUCKET:
        path = "/tmp/PnC_insuranceNews_state.json"
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}
    try:
        res = s3_client().get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        return json.loads(res["Body"].read().decode("utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    if not S3_BUCKET:
        with open("/tmp/PnC_insuranceNews_state.json", "w") as f:
            json.dump(state, f, ensure_ascii=False)
        return
    s3_client().put_object(
        Bucket=S3_BUCKET,
        Key=S3_KEY,
        Body=json.dumps(state, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json",
    )


def fetch_html(url: str) -> lxml_html.HtmlElement:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    verify = urlparse(url).hostname not in _SSL_SKIP_HOSTS
    res = requests.get(url, headers=headers, timeout=30, verify=verify)
    res.raise_for_status()
    # HTTPデフォルトのISO-8859-1より chardet の検出結果を優先する（Shift-JIS・UTF-8対応）
    encoding = res.apparent_encoding or res.encoding or "utf-8"
    html_text = res.content.decode(encoding, errors="replace")
    return lxml_html.fromstring(html_text)


def resolve_site_url(site: dict) -> str:
    template = site["url_template"] if "url_template" in site else site["url"]
    return template.format(year=datetime.datetime.now().year)


def fetch_articles(site: dict) -> list[dict]:
    url = resolve_site_url(site)
    tree = fetch_html(url)
    containers = tree.xpath(site["xpath"])
    if not containers:
        raise ValueError(f"XPath '{site['xpath']}' matched nothing on {url}")
    extractor = EXTRACTORS[site["extractor"]]
    return extractor(containers[0], site["base_url"])


def send_slack(site_name: str, new_articles: list[dict]) -> None:
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


def check_site(site: dict, state: dict) -> list[str]:
    url = resolve_site_url(site)
    name = site["name"]
    try:
        articles = fetch_articles(site)
    except Exception as e:
        print(f"[ERROR] fetch failed: {url} — {e}")
        return state.get(url, [])

    prev_hrefs: set[str] = set(state.get(url, []))
    new_articles = [a for a in articles if a["href"] not in prev_hrefs]

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
        new_state[resolve_site_url(site)] = check_site(site, state)
    save_state(new_state)
    return {"statusCode": 200, "body": "OK"}


if __name__ == "__main__":
    lambda_handler({}, None)
