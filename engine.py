"""
Core Scraper Engine Module.
Orchestrates HTTP fetching, dynamic site detection, and structured parsing.
"""

from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

from app.config import settings
from app.scraper.detector import analyze_dynamism
from app.scraper.parser import (
    parse_by_selector,
    parse_generic_html,
    parse_html_tables,
    parse_inline_js_data,
    parse_json_ld,
    parse_next_data,
)


class ScraperEngine:
    """
    Robust Web Scraping Engine capable of handling dynamic websites,
    direct API endpoints, and generic web pages.
    """

    def __init__(self, timeout: Optional[int] = None, user_agent: Optional[str] = None):
        self.timeout = timeout or settings.REQUEST_TIMEOUT
        self.headers = {
            "User-Agent": user_agent or settings.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _validate_url(self, url: str) -> str:
        """Validate and normalize target URL."""
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError(f"Invalid URL provided: {url}")
        return url

    def scrape(
        self,
        url: str,
        entity_type: Optional[str] = None,
        css_selector: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Scrapes data from the specified URL and returns structured records.
        """
        clean_url = self._validate_url(url)
        entity_name = entity_type.strip() if entity_type and entity_type.strip() else "generic"

        try:
            response = requests.get(
                clean_url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"HTTP request failed for {clean_url}: {str(e)}") from e

        content_type = response.headers.get("Content-Type", "").lower()
        extracted_items: List[Dict[str, Any]] = []

        # 1. Direct JSON / API Endpoint
        if "application/json" in content_type:
            try:
                json_data = response.json()
                dynamism = {
                    "is_dynamic": True,
                    "type": "api_endpoint",
                    "framework": "REST API",
                    "indicators": ["Direct JSON API response."],
                }
                items = json_data if isinstance(json_data, list) else [json_data]
                for idx, item in enumerate(items):
                    if isinstance(item, dict):
                        title = item.get("title") or item.get("name") or f"Record #{idx + 1}"
                        extracted_items.append({
                            "title": str(title)[:255],
                            "content": str(item.get("description") or item.get("body") or item.get("text") or ""),
                            "raw_data": item,
                        })
                    else:
                        extracted_items.append({
                            "title": f"Value #{idx + 1}",
                            "content": str(item),
                            "raw_data": {"value": item},
                        })
                return self._build_result(clean_url, entity_name, dynamism, extracted_items)
            except Exception:
                pass

        # 2. HTML Processing
        html_text = response.text
        dynamism = analyze_dynamism(html_text, content_type)
        soup = BeautifulSoup(html_text, "html.parser")

        # Custom CSS selector extraction
        if css_selector and css_selector.strip():
            extracted_items = parse_by_selector(soup, css_selector.strip())

        # If no selector or selector yielded 0 results, use automated discovery
        if not extracted_items:
            # Check dynamic inline JavaScript data (e.g. quotes.toscrape.com/js/)
            js_items = parse_inline_js_data(soup)
            if js_items:
                extracted_items.extend(js_items)

            # Check Next.js hydration state
            next_items = parse_next_data(soup)
            if next_items:
                extracted_items.extend(next_items)

            # Check JSON-LD
            ld_items = parse_json_ld(soup)
            if ld_items:
                extracted_items.extend(ld_items)

            # Check HTML tables
            table_items = parse_html_tables(soup)
            if table_items:
                extracted_items.extend(table_items)

        # Fallback to generic DOM extraction
        if not extracted_items:
            extracted_items = parse_generic_html(soup, clean_url)

        return self._build_result(clean_url, entity_name, dynamism, extracted_items)

    def _build_result(
        self,
        url: str,
        entity_name: str,
        dynamism: Dict[str, Any],
        raw_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Format final list of records with metadata."""
        formatted_records = []
        for item in raw_items:
            formatted_records.append({
                "source_url": url,
                "entity_type": entity_name,
                "title": item.get("title", "Untitled Record"),
                "content": item.get("content", ""),
                "raw_data": item.get("raw_data", {}),
            })

        return {
            "source_url": url,
            "entity_type": entity_name,
            "dynamism_analysis": dynamism,
            "total_extracted": len(formatted_records),
            "records": formatted_records,
        }
