"""
アクサ損保のページ構造確認スクリプト。
ローカルで実行し、XPath・リンク構造を確認する。
"""
import re
import requests
from lxml import html as lxml_html

BASE_URL = "https://www.axa-direct.co.jp"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def fetch(url):
    res = requests.get(url, headers=HEADERS, timeout=30)
    res.raise_for_status()
    encoding = res.encoding or res.apparent_encoding or "utf-8"
    return lxml_html.fromstring(res.content.decode(encoding, errors="replace"))


def print_links(tree, label):
    print(f"\n{'='*60}")
    print(f"[{label}]")
    links = tree.xpath('.//a[@href]')
    for a in links:
        href = a.get("href", "").strip()
        text = a.text_content().strip().replace("\n", " ")[:80]
        if text:
            print(f"  {text!r:50s}  {href}")
    print(f"  合計 {len(links)} リンク")


# ── 1. メインページ（official_info）の構造確認 ──────────────────────────
print("\n■ メインページ: /company/official_info/")
tree_main = fetch(f"{BASE_URL}/company/official_info/")

# メモのXPathを試す
for label, xpath in [
    ("section[1] (ニュースリリース候補)", "/html/body/main/div[1]/div[3]/div/div/div/section[1]"),
    ("section[2] (お知らせ候補)",         "/html/body/main/div[1]/div[3]/div/div/div/section[2]"),
]:
    els = tree_main.xpath(xpath)
    print(f"\n  XPath: {xpath}")
    if els:
        print(f"  ヒット: {els[0].tag}  class={els[0].get('class','')}")
        print_links(els[0], label)
    else:
        print("  → マッチなし")

# main 直下の section を全部列挙
print("\n  ── main 直下の全 section ──")
for i, sec in enumerate(tree_main.xpath("//main//section"), 1):
    cls = sec.get("class", "")
    links = sec.xpath('.//a[@href]')
    print(f"  section[{i}]  class={cls!r}  リンク数={len(links)}")

# ── 2. プレスリリース一覧ページ ──────────────────────────────────────────
print("\n■ プレスリリース一覧: /company/official_info/pr/")
tree_pr = fetch(f"{BASE_URL}/company/official_info/pr/")
print_links(tree_pr, "pr top")

# 2025年ページも確認
print("\n■ プレスリリース 2025年: /company/official_info/pr/2025/")
tree_pr25 = fetch(f"{BASE_URL}/company/official_info/pr/2025/")
print_links(tree_pr25, "pr 2025")

# ── 3. お知らせ一覧ページ ────────────────────────────────────────────────
print("\n■ お知らせ一覧: /company/official_info/announce/")
tree_ann = fetch(f"{BASE_URL}/company/official_info/announce/")
print_links(tree_ann, "announce top")

print("\n■ お知らせ 2025年: /company/official_info/announce/2025/")
tree_ann25 = fetch(f"{BASE_URL}/company/official_info/announce/2025/")
print_links(tree_ann25, "announce 2025")
