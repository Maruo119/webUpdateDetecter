#!/usr/bin/env python3
"""
FSA のニュース抽出テスト（実際のextractors.pyロジックを使用）
"""
import sys
sys.path.insert(0, '/sessions/compassionate-lucid-faraday/mnt/webUpdateDetecter/FSA/src')

import requests
from lxml import html as lxml_html
from sites import SITES
from extractors import EXTRACTORS

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
    encoding = res.apparent_encoding or res.encoding or "utf-8"
    html_text = res.content.decode(encoding, errors="replace")
    return lxml_html.fromstring(html_text)

def main():
    site = SITES[0]
    print(f"[1] Site config:")
    print(f"    Name: {site['name']}")
    print(f"    URL: {site['url']}")
    print(f"    XPath: {site['xpath']}")
    print(f"    Extractor: {site['extractor']}")

    print(f"\n[2] Fetching...")
    url = site['url']
    tree = fetch_html(url)
    print(f"    ✓ Fetched {len(tree.text_content())} chars")

    print(f"\n[3] Finding container with XPath: {site['xpath']}")
    containers = tree.xpath(site['xpath'])
    print(f"    Found {len(containers)} container(s)")

    if not containers:
        print("    ✗ No container found!")
        sys.exit(1)

    container = containers[0]
    print(f"    Container tag: {container.tag}")
    print(f"    Container classes: {container.get('class', 'N/A')}")

    print(f"\n[4] Extracting articles with '{site['extractor']}' extractor...")
    extractor = EXTRACTORS[site['extractor']]
    articles = extractor(container, site['base_url'])
    print(f"    Extracted {len(articles)} article(s)")

    if articles:
        print(f"\n[5] Articles (first 10):")
        for i, article in enumerate(articles[:10]):
            href = article.get('href', 'N/A')[:70]
            title = article.get('title', 'N/A')[:70]
            print(f"    [{i}] href: {href}")
            print(f"        title: {title}")
    else:
        print("\n    ✗ No articles extracted!")

        # デバッグ：直接 XPath で `<a>` を探す
        print(f"\n[D] Debugging: searching for all <a> in container...")
        all_links = container.xpath('.//a[@href]')
        print(f"    Found {len(all_links)} <a> elements")
        if all_links:
            for i, a in enumerate(all_links[:3]):
                print(f"    [{i}] href={a.get('href')}, text={a.text_content()[:50]}")

if __name__ == "__main__":
    main()
