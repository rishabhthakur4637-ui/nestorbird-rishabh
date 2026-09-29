"""
Parser Module for extracting structured data from HTML and JSON.
Supports CSS selectors, Next.js hydration state, JSON-LD, tables, and fallback DOM parsing.
"""

import json
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, Tag


def parse_inline_js_data(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Extract dynamic data rendered by client-side scripts.
    Identifies patterns like `var data = [...]`, `const items = [...]`,
    or `window.__INITIAL_STATE__ = {...}` embedded in <script> tags.
    """
    records = []
    scripts = soup.find_all("script")
    
    # Patterns matching dynamic data variables
    patterns = [
        r"(?:var|let|const)\s+(?:data|items|quotes|products|records|articles)\s*=\s*(\[.*?\]);",
        r"(?:window\.)?(?:__INITIAL_STATE__|__DATA__)\s*=\s*(\{.*?\});",
    ]

    for script in scripts:
        if not script.string:
            continue
        script_text = script.string.strip()
        for pat in patterns:
            match = re.search(pat, script_text, re.DOTALL)
            if match:
                try:
                    payload = json.loads(match.group(1))
                    items = payload if isinstance(payload, list) else [payload]
                    for idx, item in enumerate(items):
                        if isinstance(item, dict):
                            title = (
                                item.get("title")
                                or item.get("name")
                                or (item.get("author", {}).get("name") if isinstance(item.get("author"), dict) else None)
                                or f"Dynamic Record #{idx + 1}"
                            )
                            content = (
                                item.get("text")
                                or item.get("description")
                                or item.get("content")
                                or item.get("body")
                                or ""
                            )
                            records.append({
                                "title": str(title)[:255],
                                "content": str(content),
                                "raw_data": item,
                            })
                except Exception:
                    continue
    return records


def parse_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract structured records from <script type="application/ld+json">."""
    records = []
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            content = script.string
            if not content:
                continue
            data = json.loads(content.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    title = item.get("name") or item.get("headline") or item.get("@type", "JSON-LD Entity")
                    records.append({
                        "title": str(title)[:255],
                        "content": str(item.get("description") or item.get("articleBody") or ""),
                        "raw_data": item,
                    })
        except Exception:
            continue
    return records


def parse_next_data(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract hydration state from Next.js <script id="__NEXT_DATA__">."""
    records = []
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return records

    try:
        data = json.loads(script.string.strip())
        page_props = data.get("props", {}).get("pageProps", {})
        
        # Recursively scan for lists of dicts or substantial objects
        def find_entities(obj: Any, depth: int = 0):
            if depth > 4:
                return
            if isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict) and len(item) >= 2:
                        title = item.get("title") or item.get("name") or item.get("heading") or "Next.js Entity"
                        records.append({
                            "title": str(title)[:255],
                            "content": str(item.get("description") or item.get("text") or item.get("body") or ""),
                            "raw_data": item,
                        })
                    else:
                        find_entities(item, depth + 1)
            elif isinstance(obj, dict):
                for v in obj.values():
                    find_entities(v, depth + 1)

        find_entities(page_props)
    except Exception:
        pass
    return records


def parse_by_selector(soup: BeautifulSoup, selector: str) -> List[Dict[str, Any]]:
    """Extract records using a user-specified CSS selector (e.g. '.quote', '.product', 'article')."""
    records = []
    elements = soup.select(selector)

    for idx, el in enumerate(elements):
        # Find likely title (heading or first bold/strong or element text)
        heading = el.find(["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b"])
        title = heading.get_text().strip() if heading else f"Element #{idx + 1}"
        
        # Extract full text
        content = el.get_text(separator=" ", strip=True)
        
        # Collect element attributes and child links
        links = [a.get("href") for a in el.find_all("a", href=True)]
        images = [img.get("src") for img in el.find_all("img", src=True)]
        
        raw_data = {
            "tag": el.name,
            "classes": el.get("class", []),
            "links": links[:10],
            "images": images[:5],
            "text": content,
        }
        
        records.append({
            "title": title[:255],
            "content": content,
            "raw_data": raw_data,
        })
    return records


def parse_html_tables(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract HTML tables into structured key-value rows."""
    records = []
    tables = soup.find_all("table")

    for t_idx, table in enumerate(tables):
        headers = [th.get_text().strip() for th in table.find_all("th")]
        rows = table.find_all("tr")

        for r_idx, tr in enumerate(rows):
            cells = tr.find_all(["td", "th"])
            if not cells or tr.find("th") and not tr.find("td"):
                continue  # skip header-only row

            row_data = {}
            for c_idx, cell in enumerate(cells):
                col_name = headers[c_idx] if c_idx < len(headers) and headers[c_idx] else f"col_{c_idx + 1}"
                row_data[col_name] = cell.get_text().strip()

            if row_data:
                first_val = next(iter(row_data.values()), f"Table {t_idx + 1} Row {r_idx}")
                records.append({
                    "title": f"Table Row: {str(first_val)[:60]}",
                    "content": " | ".join(f"{k}: {v}" for k, v in row_data.items()),
                    "raw_data": row_data,
                })
    return records


def parse_generic_html(soup: BeautifulSoup, url: str) -> List[Dict[str, Any]]:
    """
    Fallback parser for standard HTML pages.
    Extracts page metadata, sections, headings, and prominent content blocks.
    """
    records = []
    
    # 1. Page Title & Meta summary
    page_title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled Page"
    meta_desc = ""
    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    # 2. Extract prominent sections or articles
    sections = soup.find_all(["article", "section", "main"])
    if sections:
        for idx, sec in enumerate(sections[:10]):
            heading = sec.find(["h1", "h2", "h3"])
            sec_title = heading.get_text().strip() if heading else f"{page_title} - Section {idx + 1}"
            sec_text = sec.get_text(separator=" ", strip=True)
            if len(sec_text) > 30:
                records.append({
                    "title": sec_title[:255],
                    "content": sec_text[:2000],
                    "raw_data": {
                        "source": url,
                        "section_index": idx + 1,
                        "heading": sec_title,
                        "full_length": len(sec_text),
                    },
                })

    # If no distinct sections were extracted, parse headings and paragraphs
    if not records:
        headings = soup.find_all(["h1", "h2", "h3"])
        for h in headings[:10]:
            h_text = h.get_text().strip()
            # find next sibling paragraphs
            p_texts = []
            sib = h.next_sibling
            while sib and len(p_texts) < 3:
                if isinstance(sib, Tag) and sib.name == "p":
                    p_texts.append(sib.get_text().strip())
                sib = sib.next_sibling
            
            combined_content = " ".join(p_texts) if p_texts else meta_desc
            records.append({
                "title": h_text[:255] or page_title,
                "content": combined_content or f"Heading extracted from {url}",
                "raw_data": {"heading_level": h.name, "url": url},
            })

    # If still empty, create an overarching page record
    if not records:
        body_text = soup.get_text(separator=" ", strip=True)
        records.append({
            "title": page_title[:255],
            "content": meta_desc or body_text[:1000],
            "raw_data": {"url": url, "meta_description": meta_desc},
        })

    return records
