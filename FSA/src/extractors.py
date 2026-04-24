import re
from urllib.parse import urljoin
from lxml import html as lxml_html


def resolve_url(href, base_url):
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return base_url.rstrip("/") + href
    return href


def extract_fsa(container, base_url, limit=10):
    items = []
    seen = set()

    for li in container.xpath('.//li[@id]'):
        if len(items) >= limit:
            break

        a_elems = li.xpath('.//a[@href]')
        if not a_elems:
            continue

        a = a_elems[0]
        raw_href = a.get("href", "").strip()
        if not raw_href:
            continue

        title = " ".join(a.text_content().split())
        title = title.replace(" NEW", "").replace("NEW", "").strip()

        if not title:
            continue

        href = resolve_url(raw_href, base_url)
        if href in seen:
            continue

        seen.add(href)
        items.append({"href": href, "title": title})

    return items


EXTRACTORS = {
    "fsa": extract_fsa,
}
