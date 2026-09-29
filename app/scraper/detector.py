"""
Dynamic Website Detector Module.
Analyzes web pages to identify dynamic rendering (SPA, React, Next.js, Vue, Angular, etc.)
and detects embedded APIs and hydration state blobs.
"""

from typing import Dict, Any, List
from bs4 import BeautifulSoup


def analyze_dynamism(html_content: str, content_type: str = "") -> Dict[str, Any]:
    """
    Examines HTML and headers to determine if the target website is dynamic.
    
    Key indicators:
    1. Direct JSON response (API endpoint).
    2. Framework mount containers (<div id="root">, <div id="__next">, <div id="app">).
    3. Prominent <noscript> tags warning that JavaScript is required.
    4. Embedded hydration state (<script id="__NEXT_DATA__">, window.__INITIAL_STATE__).
    5. Disproportionate script-to-content ratio.
    """
    if "application/json" in content_type:
        return {
            "is_dynamic": True,
            "type": "api_endpoint",
            "indicators": ["Direct JSON API response detected."],
            "framework": "REST/JSON API",
        }

    soup = BeautifulSoup(html_content, "html.parser")
    indicators: List[str] = []
    framework = "Static/SSR"

    # 1. Check for Next.js / Nuxt hydration state
    if soup.find("script", id="__NEXT_DATA__"):
        indicators.append("Found Next.js hydration state script (__NEXT_DATA__).")
        framework = "Next.js"
    elif "__NUXT__" in html_content:
        indicators.append("Found Nuxt.js state payload.")
        framework = "Nuxt.js"

    # 2. Check for SPA mounting points
    mount_points = [
        ("id", "root", "React (CRA/Vite)"),
        ("id", "__next", "Next.js"),
        ("id", "app", "Vue / Single Page App"),
        ("ng-app", None, "AngularJS"),
        ("ng-version", None, "Angular"),
    ]

    for attr, val, name in mount_points:
        if val and soup.find(attrs={attr: val}):
            indicators.append(f"Found dynamic app mount container with {attr}='{val}'.")
            if framework == "Static/SSR":
                framework = name
        elif not val and soup.find(attrs={attr: True}):
            indicators.append(f"Found Angular marker: {attr}.")
            if framework == "Static/SSR":
                framework = name

    # 3. Check for noscript JavaScript warnings
    noscript_tags = soup.find_all("noscript")
    for ns in noscript_tags:
        text = ns.get_text().strip().lower()
        if any(w in text for w in ["enable javascript", "javascript is required", "need to enable javascript"]):
            indicators.append("Found <noscript> warning requiring JavaScript for page rendering.")

    # 4. Check for inline dynamic JS data variables (e.g. var data = [...], window.__DATA__)
    inline_js_scripts = soup.find_all("script")
    for s in inline_js_scripts:
        if s.string and any(k in s.string for k in ["var data =", "let data =", "const data =", "var items =", "window.__INITIAL_STATE__"]):
            indicators.append("Found inline dynamic JavaScript data variable (var data / state) rendered at runtime.")
            if framework == "Static/SSR":
                framework = "Client-rendered Dynamic JS"

    # 5. Check for JSON-LD schemas
    ld_json_scripts = soup.find_all("script", type="application/ld+json")
    if ld_json_scripts:
        indicators.append(f"Found {len(ld_json_scripts)} embedded JSON-LD (Schema.org) structured scripts.")

    # 6. Ratio of visible text to script tags
    body = soup.find("body")
    text_length = len(body.get_text().strip()) if body else 0
    script_count = len(soup.find_all("script"))

    is_dynamic = len(indicators) > 0 or (text_length < 200 and script_count > 3)
    if is_dynamic and not indicators:
        indicators.append("Low text content with multiple script bundles (typical client-rendered SPA).")

    return {
        "is_dynamic": is_dynamic,
        "framework": framework,
        "indicators": indicators,
        "script_count": script_count,
        "text_length": text_length,
    }
