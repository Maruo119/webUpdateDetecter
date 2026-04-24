import re
from urllib.parse import urljoin
from lxml import html as lxml_html


def resolve_url(href: str, base_url: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return href


def _extract_generic(container: lxml_html.HtmlElement, base_url: str,
                     skip_titles: tuple[str, ...] = (),
                     skip_hrefs: tuple[str, ...] = (),
                     limit: int = 10) -> list[dict]:
    """汎用的なリンク抽出器（ナビゲーション除外対応）"""
    items = []
    seen: set[str] = set()
    for a in container.xpath('.//a[@href]'):
        if len(items) >= limit:
            break
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


def extract_fsa(container: lxml_html.HtmlElement, base_url: str) -> list[dict]:
    """金融庁のニュース要素から href・title を抽出"""
    return _extract_generic(container, base_url)


EXTRACTORS = {
    "fsa": extract_fsa,
}
