import datetime
import json
import os
import re
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
    {
        "name": "あいおいニッセイ同和損保 お知らせ・ニュースリリース",
        "url": "https://www.aioinissaydowa.co.jp/",
        "base_url": "https://www.aioinissaydowa.co.jp",
        "xpath": "//section[contains(@class,'p-top-spread')]",
        "extractor": "aioi",
    },
    {
        "name": "アニコム損保 トピックス",
        "url_template": "https://www.anicom-sompo.co.jp/topics/{year}/",
        "base_url": "https://www.anicom-sompo.co.jp",
        "xpath": '//*[@id="main"]',
        "extractor": "anicom",
    },
    {
        "name": "アニコム損保 ニュースリリース",
        "url_template": "https://www.anicom-sompo.co.jp/news-release/{year}/",
        "base_url": "https://www.anicom-sompo.co.jp",
        "xpath": '//*[@id="main"]',
        "extractor": "anicom",
    },
    {
        "name": "エイチ･エス損保 お知らせ",
        "url": "https://www.hs-sonpo.co.jp/",
        "base_url": "https://www.hs-sonpo.co.jp",
        "xpath": '//*[@id="frontpage"]/main/section[2]',
        "extractor": "hs_sonpo",
    },
]

S3_BUCKET = os.environ.get("STATE_BUCKET", "")
S3_KEY = "PnC_insuranceNews/state.json"

_s3 = None


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
    res = requests.get(url, headers=headers, timeout=30)
    res.raise_for_status()
    # HTTPデフォルトのISO-8859-1より chardet の検出結果を優先する（Shift-JIS・UTF-8対応）
    encoding = res.apparent_encoding or res.encoding or "utf-8"
    html_text = res.content.decode(encoding, errors="replace")
    return lxml_html.fromstring(html_text)


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
        # ナビゲーションリンクを除外し、実際のニュース・PDF文書のみ対象にする
        if not href or not title or href in seen or "/media/SJNK/files/" not in href:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items


def extract_aioi(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    items = []
    seen: set[str] = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = a.text_content().strip()

        # ナビゲーションリンク（一覧はこちら等）を除外
        if not title or title in ("一覧はこちら",):
            continue

        # ニュースリリース: javascript:Jump_File('URL') からURLを抽出
        js_match = re.search(r"Jump_File\('([^']+)'", raw_href)
        if js_match:
            href = js_match.group(1)
        else:
            href = resolve_url(raw_href, base_url)

        if not href or href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items


def extract_anicom(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    items = []
    seen: set[str] = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        # タブ・改行を含む可能性があるためスペース正規化
        title = " ".join(a.text_content().split())
        if not title or not raw_href or raw_href.startswith("javascript:"):
            continue
        href = resolve_url(raw_href, base_url)
        # 年度インデックスページ（/topics/2026/ 、/news-release/2025/ 、/news/2020/ 等）を除外
        if re.search(r'/(topics|news-release|news)/\d{4}/?$', href):
            continue
        # トップページ・一覧ページ等のシンプルなパスを除外
        if re.search(r'^https?://[^/]+(/topics/?|/news-release/?|/news/?|/?)?$', href):
            continue
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items


def extract_hs_sonpo(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    items = []
    seen: set[str] = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        href = resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items


EXTRACTORS = {
    "aig": extract_aig,
    "sompo_japan": extract_sompo_japan,
    "aioi": extract_aioi,
    "anicom": extract_anicom,
    "hs_sonpo": extract_hs_sonpo,
}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def resolve_site_url(site: dict) -> str:
    """url_template があれば {year} を現在年に置換、なければ url をそのまま返す。"""
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
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{href}|{title}>",
                },
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
