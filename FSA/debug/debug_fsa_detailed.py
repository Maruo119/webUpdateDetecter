#!/usr/bin/env python3
"""
FSA のニュース一覧ページをより詳細にデバッグ
コンテナの HTML 構造を確認
"""
import sys
import requests
from lxml import html as lxml_html

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
    tree = fetch_html(FSA_URL)
    print("     ✓ HTML fetched successfully")

    print(f"\n[2] Searching XPath: {XPATH}")
    containers = tree.xpath(XPATH)
    print(f"     Matched {len(containers)} element(s)")

    if not containers:
        print("     ✗ XPath did not match!")
        sys.exit(1)

    container = containers[0]

    # コンテナのタグと属性を確認
    print(f"\n[3] Container element info:")
    print(f"     Tag: {container.tag}")
    print(f"     Attributes: {dict(container.attrib)}")
    print(f"     Text length: {len(container.text_content())} chars")

    # コンテナの HTML を表示（最初の 2000 文字）
    container_html = lxml_html.tostring(container, encoding='unicode')
    print(f"\n[4] Container HTML (first 2000 chars):")
    print(container_html[:2000])

    # 子要素の構造を確認
    print(f"\n[5] Child elements:")
    for i, child in enumerate(container):
        print(f"     [{i}] <{child.tag}> with {len(list(child))} children, text={child.text_content()[:50]}")

    # 様々な XPath パターンを試す
    print(f"\n[6] Trying different XPath patterns inside container:")
    patterns = [
        ('.//a[@href]', 'direct links'),
        ('.//ul', 'ul elements'),
        ('.//li', 'li elements'),
        ('.//div', 'div elements'),
        ('.//tr', 'tr elements (table)'),
        ('.//dt', 'dt elements (definition list)'),
        ('.//dd', 'dd elements (definition list)'),
    ]
    for pattern, desc in patterns:
        matches = container.xpath(pattern)
        print(f"     {desc:30s}: {len(matches):3d} match(es)")
        if matches and len(matches) <= 5:
            for m in matches:
                text = m.text_content()[:60]
                print(f"         - {text}")

if __name__ == "__main__":
    main()
