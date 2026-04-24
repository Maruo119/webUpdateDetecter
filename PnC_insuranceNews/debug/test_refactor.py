"""
リファクタリング前後の動作等価性を検証するテスト。
旧実装の各 extractor をインライン再定義し、新実装と同一入力で比較する。
"""
import re
import sys
from urllib.parse import urljoin
from lxml import html as lxml_html

# ---------------------------------------------------------------------------
# 旧実装（lambda_function.py から抽出した original extractors）
# ---------------------------------------------------------------------------

def _old_resolve_url(href, base_url):
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return href

def old_extract_aig(container, base_url):
    items = []
    for li in container.xpath('.//li[contains(@class,"cmp-newslist__item")]'):
        a_els = li.xpath('.//a[contains(@class,"cmp-newslist__link")]')
        title_els = li.xpath('.//div[contains(@class,"cmp-newslist-item__title")]')
        if not a_els:
            continue
        href = _old_resolve_url(a_els[0].get("href", "").strip(), base_url)
        title = title_els[0].text_content().strip() if title_els else ""
        if href:
            items.append({"href": href, "title": title})
    return items

def old_extract_sompo_japan(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        href = _old_resolve_url(a.get("href", "").strip(), base_url)
        title = a.text_content().strip()
        if not href or not title or href in seen or "/media/SJNK/files/" not in href:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_aioi(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = a.text_content().strip()
        if not title or title in ("一覧はこちら",):
            continue
        js_match = re.search(r"Jump_File\('([^']+)'", raw_href)
        if js_match:
            href = js_match.group(1)
        else:
            href = _old_resolve_url(raw_href, base_url)
        if not href or href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_anicom(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href or raw_href.startswith("javascript:"):
            continue
        href = _old_resolve_url(raw_href, base_url)
        if re.search(r'/(topics|news-release|news)/\d{4}/?$', href):
            continue
        if re.search(r'^https?://[^/]+(/topics/?|/news-release/?|/news/?|/?)?$', href):
            continue
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_hs_sonpo(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        href = _old_resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_sbi_sonpo(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href or title in ("一覧",):
            continue
        href = _old_resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_docomo_sompo(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        href = _old_resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_capital_sonpo(container, base_url):
    items = []
    seen = set()
    page_url = base_url.rstrip("/") + "/"
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        href = urljoin(page_url, raw_href)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_kyoei_kasai(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        href = _old_resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_sakura_sonpo(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        href = _old_resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_jihoken(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        href = _old_resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_zkreiwa_sonpo(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        href = _old_resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_sony_sonpo(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        href = _old_resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

def old_extract_sompo_direct(container, base_url):
    items = []
    seen = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href or raw_href in ("#", "/#"):
            continue
        href = _old_resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items

OLD_EXTRACTORS = {
    "aig": old_extract_aig,
    "sompo_japan": old_extract_sompo_japan,
    "aioi": old_extract_aioi,
    "anicom": old_extract_anicom,
    "hs_sonpo": old_extract_hs_sonpo,
    "sbi_sonpo": old_extract_sbi_sonpo,
    "docomo_sompo": old_extract_docomo_sompo,
    "capital_sonpo": old_extract_capital_sonpo,
    "kyoei_kasai": old_extract_kyoei_kasai,
    "sakura_sonpo": old_extract_sakura_sonpo,
    "jihoken": old_extract_jihoken,
    "zkreiwa_sonpo": old_extract_zkreiwa_sonpo,
    "sony_sonpo": old_extract_sony_sonpo,
    "sompo_direct": old_extract_sompo_direct,
}

# ---------------------------------------------------------------------------
# テストケース定義
# ---------------------------------------------------------------------------

TEST_CASES = [
    # (extractor_key, base_url, html_snippet)
    ("aig", "https://www.aig.co.jp", """
      <ul>
        <li class="cmp-newslist__item">
          <a class="cmp-newslist__link" href="/sonpo/news/001">リンク</a>
          <div class="cmp-newslist-item__title">タイトル1</div>
        </li>
        <li class="cmp-newslist__item">
          <a class="cmp-newslist__link" href="https://ext.example.com/x">外部</a>
        </li>
      </ul>
    """),
    ("sompo_japan", "https://www.sompo-japan.co.jp", """
      <div>
        <a href="/media/SJNK/files/news/2024/001.pdf">PDF記事</a>
        <a href="/about/">会社概要</a>
        <a href="/media/SJNK/files/news/2024/001.pdf">PDF記事</a>
      </div>
    """),
    ("aioi", "https://www.aioinissaydowa.co.jp", """
      <section>
        <a href="javascript:Jump_File('https://pdf.example.com/doc.pdf')">PDFリリース</a>
        <a href="/news/001">お知らせ</a>
        <a href="/list/">一覧はこちら</a>
      </section>
    """),
    ("anicom", "https://www.anicom-sompo.co.jp", """
      <div id="main">
        <a href="/topics/2026/">年度インデックス</a>
        <a href="/topics/2026/article-001/">記事001</a>
        <a href="javascript:void(0)">無視</a>
        <a href="https://www.anicom-sompo.co.jp/topics/">一覧</a>
        <a href="/news-release/2025/press-001/">プレスリリース001</a>
      </div>
    """),
    ("hs_sonpo", "https://www.hs-sonpo.co.jp", """
      <section>
        <a href="/news/001">お知らせ1</a>
        <a href="/news/002">お知らせ2</a>
        <a href="/news/001">重複</a>
      </section>
    """),
    ("sbi_sonpo", "https://www.sbisonpo.co.jp", """
      <div>
        <a href="/news/001">ニュース1</a>
        <a href="/list/">一覧</a>
        <a href="/news/002">ニュース2</a>
      </div>
    """),
    ("docomo_sompo", "https://www.docomo-sompo.com", """
      <ul>
        <a href="/news/001">お知らせ1</a>
        <a href="/news/002">お知らせ2</a>
      </ul>
    """),
    ("capital_sonpo", "https://www.capital-sonpo.co.jp", """
      <dl>
        <a href="news/001.html">記事1（相対パス）</a>
        <a href="/news/002.html">記事2（絶対パス）</a>
      </dl>
    """),
    ("kyoei_kasai", "https://www.kyoeikasai.co.jp", """
      <div>
        <a href="/news/001">お知らせ1</a>
        <a href="/news/002">お知らせ2</a>
      </div>
    """),
    ("sakura_sonpo", "https://www.sakura-ssi.co.jp", """
      <ul>
        <a href="/info/001">情報1</a>
        <a href="/info/002">情報2</a>
      </ul>
    """),
    ("jihoken", "https://www.jihoken.co.jp", """
      <ul>
        <a href="/news/001">ニュース1</a>
        <a href="/news/002">ニュース2</a>
      </ul>
    """),
    ("zkreiwa_sonpo", "https://www.zkreiwa-sonpo.co.jp", """
      <ul>
        <a href="/info/001">情報1</a>
        <a href="/info/002">情報2</a>
      </ul>
    """),
    ("sony_sonpo", "https://from.sonysonpo.co.jp", """
      <ul>
        <a href="/news/001">お知らせ1</a>
        <a href="https://ext.example.com/x">外部リンク</a>
      </ul>
    """),
    ("sompo_direct", "https://news-ins-saison.dga.jp", """
      <ul>
        <a href="/news/001">記事1</a>
        <a href="#">アンカー（除外）</a>
        <a href="/#">アンカー2（除外）</a>
        <a href="/news/002">記事2</a>
      </ul>
    """),
]

# ---------------------------------------------------------------------------
# 実行
# ---------------------------------------------------------------------------

def run():
    import pathlib
    sys.path.append(str(pathlib.Path(__file__).parent / "src"))
    from extractors import EXTRACTORS as NEW_EXTRACTORS

    passed = 0
    failed = 0

    for key, base_url, html_snippet in TEST_CASES:
        container = lxml_html.fromstring(html_snippet)
        old_fn = OLD_EXTRACTORS[key]
        new_fn = NEW_EXTRACTORS[key]
        old_result = old_fn(container, base_url)

        # 新実装は同じ container を再利用できないので同じ HTML から再生成
        container2 = lxml_html.fromstring(html_snippet)
        new_result = new_fn(container2, base_url)

        if old_result == new_result:
            print(f"  PASS  {key}")
            passed += 1
        else:
            print(f"  FAIL  {key}")
            print(f"    OLD: {old_result}")
            print(f"    NEW: {new_result}")
            failed += 1

    # SITES / EXTRACTORS のキー整合性チェック
    from sites import SITES
    extractor_keys_in_sites = {s["extractor"] for s in SITES}
    missing = extractor_keys_in_sites - set(NEW_EXTRACTORS.keys())
    if missing:
        print(f"  FAIL  EXTRACTORS に未登録のキー: {missing}")
        failed += 1
    else:
        print(f"  PASS  SITES の全 extractor キーが EXTRACTORS に存在する")
        passed += 1

    print(f"\n結果: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    run()
