"""
アニコム損保のページ構造確認スクリプト。
ローカルで実行し、XPath・リンク構造を確認する。
"""
import datetime
import requests
from lxml import html as lxml_html

BASE_URL = "https://www.anicom-sompo.co.jp"
YEAR = datetime.datetime.now().year
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


# ── 1. メモのXPathを試す ─────────────────────────────────────────────────
XPATH_MEMO = '//*[@id="main"]'

for label, url in [
    (f"トピックス {YEAR}", f"{BASE_URL}/topics/{YEAR}/"),
    (f"ニュースリリース {YEAR}", f"{BASE_URL}/news-release/{YEAR}/"),
]:
    print(f"\n■ {label}: {url}")
    tree = fetch(url)

    els = tree.xpath(XPATH_MEMO)
    print(f"  XPath '{XPATH_MEMO}' → {len(els)} 件マッチ")
    if els:
        print(f"  ヒット要素: {els[0].tag}  class={els[0].get('class','')}")
        print_links(els[0], label + " (memo XPath)")
    else:
        print("  → マッチなし。main 直下の構造を確認:")
        for i, child in enumerate(tree.xpath('//*[@id="main"]/*'), 1):
            cls = child.get("class", "")
            print(f"    [{i}] {child.tag}  class={cls!r}")

    # フォールバック: main 以下の全 a タグ
    main_els = tree.xpath('//*[@id="main"]')
    if main_els:
        print(f"\n  ── main 内の全リンク ──")
        print_links(main_els[0], label + " (main全体)")
