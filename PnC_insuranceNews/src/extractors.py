import re
from urllib.parse import urljoin
from lxml import html as lxml_html


def resolve_url(href: str, base_url: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return href


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


def _extract_generic(container: lxml_html.HtmlElement, base_url: str,
                     skip_titles: tuple[str, ...] = (),
                     skip_hrefs: tuple[str, ...] = ()) -> list[dict]:
    items = []
    seen: set[str] = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        if title in skip_titles or raw_href in skip_hrefs:
            continue
        href = resolve_url(raw_href, base_url)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items


def extract_hs_sonpo(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_sbi_sonpo(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url, skip_titles=("一覧",))


def extract_docomo_sompo(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_capital_sonpo(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    items = []
    seen: set[str] = set()
    page_url = base_url.rstrip("/") + "/"
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not title or not raw_href:
            continue
        # urljoin で相対URL（/なし）も正しく解決する
        href = urljoin(page_url, raw_href)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items


def extract_kyoei_kasai(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_sakura_sonpo(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_jihoken(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_zkreiwa_sonpo(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_sony_sonpo(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_sompo_direct(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url, skip_hrefs=("#", "/#"))


def extract_ipet(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_daidokasai(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    """大同火災: <a class="link"> 内の <span class="title"> からタイトルを抽出"""
    items = []
    seen: set[str] = set()
    for a in container.xpath('.//a[contains(@class,"link")][@href]'):
        href = a.get("href", "").strip()
        title_els = a.xpath('.//span[@class="title"]')
        title = title_els[0].text_content().strip() if title_els else a.text_content().strip()
        if not href or not title or href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items


def extract_tokiomarine_nichido(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url, skip_hrefs=("/company/news/", "/company/news/oshirase_old.html"))


def extract_toare(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_nisshinfire(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    page_url = base_url.rstrip("/") + "/news_release/"
    items = []
    seen: set[str] = set()
    for a in container.xpath('.//a[@href]'):
        raw_href = a.get("href", "").strip()
        title = " ".join(a.text_content().split())
        if not raw_href or not title:
            continue
        href = urljoin(page_url, raw_href)
        if href in seen:
            continue
        seen.add(href)
        items.append({"href": href, "title": title})
    return items


def extract_nihonjishin(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_ms_ins(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_mitsui_direct(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


def extract_meijiyasuda(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    return _extract_generic(container, base_url)


EXTRACTORS = {
    "aig": extract_aig,
    "sompo_japan": extract_sompo_japan,
    "aioi": extract_aioi,
    "anicom": extract_anicom,
    "hs_sonpo": extract_hs_sonpo,
    "sbi_sonpo": extract_sbi_sonpo,
    "docomo_sompo": extract_docomo_sompo,
    "capital_sonpo": extract_capital_sonpo,
    "kyoei_kasai": extract_kyoei_kasai,
    "sakura_sonpo": extract_sakura_sonpo,
    "jihoken": extract_jihoken,
    "zkreiwa_sonpo": extract_zkreiwa_sonpo,
    "sony_sonpo": extract_sony_sonpo,
    "sompo_direct": extract_sompo_direct,
    "ipet": extract_ipet,
    "daidokasai": extract_daidokasai,
    "tokiomarine_nichido": extract_tokiomarine_nichido,
    "toare": extract_toare,
    "nisshinfire": extract_nisshinfire,
    "nihonjishin": extract_nihonjishin,
    "ms_ins": extract_ms_ins,
    "mitsui_direct": extract_mitsui_direct,
    "meijiyasuda": extract_meijiyasuda,
}
