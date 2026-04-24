#!/usr/bin/env python3
"""
FSA ページから取得した HTML をダンプして確認
"""
import requests
from lxml import html as lxml_html

FSA_URL = "https://www.fsa.go.jp/"
XPATH = "//*[@id='fsa_newslist_all']"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

print("[1] Fetching...")
res = requests.get(FSA_URL, headers=headers, timeout=30)
res.raise_for_status()
encoding = res.apparent_encoding or res.encoding or "utf-8"
html_text = res.content.decode(encoding, errors="replace")

tree = lxml_html.fromstring(html_text)

print("[2] Finding container...")
containers = tree.xpath(XPATH)
if not containers:
    print("   No container found!")
    exit(1)

container = containers[0]
print(f"   Container: {container.tag}#{container.get('id')}")

# コンテナ内の HTML を表示
container_html = lxml_html.tostring(container, encoding='unicode', method='html')
print(f"\n[3] Container HTML ({len(container_html)} chars):")
print(container_html[:2000])  # 最初の 2000 文字

print(f"\n[4] Checking structure:")
print(f"   Text content length: {len(container.text_content())} chars")
print(f"   Text: {container.text_content()[:200]}")

# 全体の HTML も保存
with open("D:/webUpdateDetecter/FSA/fsa_page_dump.html", "w", encoding="utf-8") as f:
    f.write(html_text)
print(f"\n[5] Full HTML saved to fsa_page_dump.html ({len(html_text)} chars)")

# news セクション全体を確認
news_section = tree.xpath("//section[@id='news']")
if news_section:
    print(f"\n[6] Found #news section")
    news_html = lxml_html.tostring(news_section[0], encoding='unicode', method='html')
    print(f"    Length: {len(news_html)} chars")
    print(f"    First 1500 chars:")
    print(news_html[:1500])
