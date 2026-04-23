import json
import os
import boto3
import requests
from lxml import html as lxml_html

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

SITES = [
    {
        "name": "AIG損保 ニュースリリース",
        "url": "https://www.aig.co.jp/sonpo/company/news",
        "base_url": "https://www.aig.co.jp",
        "xpath": "/html/body/div[1]/div[1]/div/div[3]/div/div[3]/ul",
        "extractor": "aig",
    },
    {
        "name": "損保ジャパン ニュースリリース",
        "url": "https://www.sompo-japan.co.jp/",
        "base_url": "https://www.sompo-japan.co.jp",
        "xpath": '//*[@id="contentswrapper"]/div[5]',
        "extractor": "sompo_japan",
    },
]

S3_BUCKET = os.environ.get("STATE_BUCKET", "")
S3_KEY = "insuranceNews/state.json"

_s3 = None


def s3_client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3


def load_state() -> dict:
    if not S3_BUCKET:
        path = "/tmp/insuranceNews_state.json"
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
        with open("/tmp/insuranceNews_state.json", "w") as f:
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
    res = requests.get(url, headers=headers, timeout=30)
    res.raise_for_status()
    return lxml_html.fromstring(res.content)


def resolve_url(href: str, base_url: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return href


# ---------------------------------------------------------------------------
# Extractors — one per site structure
# ---------------------------------------------------------------------------

def extract_aig(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    items = []
    for li in container.xpath('.//li[contains(@class,"cmp-newslist__item")]'):
        a_els = li.xpath('.//a[contains(@class,"cmp-newslist__link")]')
        title_els = li.xpath('.//div[contains(@class,"cmp-newslist-item__title")]')
        if not a_els:
            continue
        href = resolve_url(a_els[0].get("href", "").strip(), base_url)
        title = title_els[0].text_content().strip() if title_els else ""
        if href:
            items.append({"href": href, "title": title})
    return items


def extract_sompo_japan(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    items = []
    seen: set[str] = set()
    for a in container.xpath('.//a[@href]'):
        href = resolve_url(a.get("href", "").strip(), base_url)
        title = a.text_content().strip()
        if not href or not title or href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items


EXTRACTORS = {
    "aig": extract_aig,
    "sompo_japan": extract_sompo_japan,
}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def fetch_articles(site: dict) -> list[dict]:
    tree = fetch_html(site["url"])
    containers = tree.xpath(site["xpath"])
    if not containers:
        raise ValueError(f"XPath '{site['xpath']}' matched nothing on {site['url']}")
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
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title}*\n<{href}|詳細を見る>",
                },
            }
        )
    res = requests.post(SLACK_WEBHOOK_URL, json={"blocks": blocks}, timeout=10)
    res.raise_for_status()


def check_site(site: dict, state: dict) -> list[str]:
    url = site["url"]
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
        new_state[site["url"]] = check_site(site, state)

    save_state(new_state)
    return {"statusCode": 200, "body": "OK"}


if __name__ == "__main__":
    lambda_handler({}, None)
