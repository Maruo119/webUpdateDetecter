#!/usr/bin/env python3
"""
FSA のニュース抽出をローカルでテスト
requests + lxml のみを使用
"""
import sys
import requests
from lxml import html as lxml_html

FSA_URL = "https://www.fsa.go.jp/"
XPATH = "//*[@id='fsa_newslist_all']"


def fetch_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    res = requests.get(url, headers=headers, timeout=30)
    res.raise_for_status()
    encoding = res.apparent_encoding or res.encoding or "utf-8"
    html_text = res.content.decode(encoding, errors="replace")
    return lxml_html.fromstring(html_text)


def extract_articles(container, limit=10):
    items = []
    seen = set()

    for li in container.xpath('.//li[@id]'):
        if len(items) >= limit:
            break

        a_elems = li.xpath('.//a[@href]')
        if not a_elems:
            print(f"[DEBUG] No <a> in {li.get('id')}")
            continue

        a = a_elems[0]
        raw_href = a.get("href", "").strip()
        if not raw_href:
            print(f"[DEBUG] No href in {li.get('id')}")
            continue

        title = " ".join(a.text_content().split())
        title = title.replace(" NEW", "").replace("NEW", "").strip()

        if not title:
            print(f"[DEBUG] No title in {li.get('id')}")
            continue

        # resolve URL
        if raw_href.startswith("http"):
            href = raw_href
        elif raw_href.startswith("/"):
            href = "https://www.fsa.go.jp" + raw_href
        else:
            href = raw_href

        if href in seen:
            print(f"[DEBUG] Duplicate: {href}")
            continue

        seen.add(href)
        items.append({"href": href, "title": title})
        print(f"[OK] {title[:60]}")

    return items


print(f"[1] Fetching {FSA_URL}")
try:
    tree = fetch_html(FSA_URL)
    print(f"    ✓ Fetched {len(tree.text_content())} chars")
except Exception as e:
    print(f"    ✗ Error: {e}")
    sys.exit(1)

print(f"\n[2] Finding container with XPath: {XPATH}")
containers = tree.xpath(XPATH)
print(f"    Found {len(containers)} container(s)")

if not containers:
    print("    ✗ No container found!")
    sys.exit(1)

container = containers[0]
print(f"    Tag: {container.tag}, id={container.get('id')}")

print(f"\n[3] Extracting articles...")
articles = extract_articles(container)
print(f"\n[RESULT] Extracted {len(articles)} article(s)")

if articles:
    print("\nFirst 5 articles:")
    for i, a in enumerate(articles[:5]):
        print(f"  [{i}] {a['title'][:70]}")
        print(f"       {a['href'][:70]}")
else:
    print("\n✗ No articles extracted!")

    # Debug
    print(f"\n[DEBUG] Checking <li> elements...")
    all_li = container.xpath('.//li[@id]')
    print(f"  Total <li> elements: {len(all_li)}")

    if all_li:
        for i, li in enumerate(all_li[:3]):
            print(f"  [{i}] {li.get('id')}")
            a_list = li.xpath('.//a[@href]')
            print(f"       <a> count: {len(a_list)}")
            if a_list:
                print(f"       href: {a_list[0].get('href')[:60]}")
                print(f"       text: {a_list[0].text_content()[:60]}")
