import xml.etree.ElementTree as ET


def extract_rss_items(rss_content, limit=10):
    items = []
    try:
        root = ET.fromstring(rss_content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid RSS XML: {e}")

    for item_elem in root.findall('.//item'):
        if len(items) >= limit:
            break

        title_elem = item_elem.find('title')
        link_elem = item_elem.find('link')

        if title_elem is None or link_elem is None:
            continue

        title = (title_elem.text or "").strip()
        href = (link_elem.text or "").strip()

        if not title or not href:
            continue

        items.append({"href": href, "title": title})

    return items


def extract_fsa(rss_content):
    return extract_rss_items(rss_content, limit=10)


EXTRACTORS = {
    "fsa": extract_fsa,
}
