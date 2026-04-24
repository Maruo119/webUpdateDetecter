#!/usr/bin/env python3
"""
FSA のニュース一覧ページをデバッグ
XPath と抽出ロジックが正しく動作するか確認
"""
import sys
import requests
from lxml import html as lxml_html

# FSA サイト情報
FSA_URL = "https://www.fsa.go.jp/"
BASE_URL = "https://www.fsa.go.jp"
XPATH = "//*[@id='fsa_newslist_all']"

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
    print(f"[1] Fetching: {FSA_URL}")
    try:
        tree = fetch_html(FSA_URL)
        print("     ✓ HTML fetched successfully")
    except Exception as e:
        print(f"     ✗ Error: {e}")
        sys.exit(1)

    print(f"\n[2] Searching XPath: {XPATH}")
    containers = tree.xpath(XPATH)
    print(f"     Matched {len(containers)} element(s)")

    if not containers:
        print("\n     ✗ XPath did not match! Let's investigate...")
        print("\n[3] Checking for similar elements:")

        # id が 'fsa_newslist' で始まる要素を探す
        similar = tree.xpath("//*[contains(@id, 'fsa_newslist')]")
        print(f"     Found {len(similar)} elements with id containing 'fsa_newslist':")
        for i, elem in enumerate(similar[:5]):  # 最初の5つのみ表示
            elem_id = elem.get("id", "N/A")
            elem_tag = elem.tag
            print(f"       [{i}] <{elem_tag} id='{elem_id}'>")

        print("\n[4] Checking page structure for news/info sections:")
        # いくつかの一般的なニュース要素を探す
        news_patterns = [
            ("//ul[@id]", "ul with id"),
            ("//div[@id='news']", "div#news"),
            ("//section[@id]", "section with id"),
            ("//article", "article elements"),
            ("//li/a[@href]", "list items with links"),
        ]
        for pattern, desc in news_patterns:
            matches = tree.xpath(pattern)
            if matches:
                print(f"     ✓ {desc}: {len(matches)} match(es)")

        sys.exit(1)

    print(f"\n[3] Extracting links from container...")
    container = containers[0]
    links = container.xpath('.//a[@href]')
    print(f"     Found {len(links)} links")

    if links:
        print(f"\n[4] First 10 links:")
        for i, a in enumerate(links[:10]):
            href = a.get("href", "").strip()
            title = " ".join(a.text_content().split())
            print(f"     [{i}] href={href[:80]}")
            print(f"         title={title[:80]}")
    else:
        print("\n     ✗ No links found in the container!")
        print("\n[4] Checking container HTML structure:")
        print(container.text_content()[:500])

if __name__ == "__main__":
    main()
