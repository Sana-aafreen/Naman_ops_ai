"""
namandarshan_scrape.py — Site-limited scraping helpers for namandarshan.com

Safety/guardrails:
  - Only allows fetching from NAMANDARSHAN_BASE_URL host (and subpaths).
  - Best-effort robots.txt respect (User-agent: *).
  - Small, rate-limited fetches with caching to avoid hammering the site.

This module is intentionally simple and synchronous so it can be used from `tools.execute_tool`.
"""

from __future__ import annotations

import re
import time
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib import robotparser

import httpx
from bs4 import BeautifulSoup

from config import (
    NAMANDARSHAN_BASE_URL,
    ENABLE_NAMANDARSHAN_SCRAPE,
    SCRAPE_TIMEOUT_SEC,
    SCRAPE_MAX_PAGES,
    SCRAPE_MAX_CHARS,
)

log = logging.getLogger("nd.scrape")


USER_AGENT = "NamanDarshanOpsAI/1.0 (+internal assistant)"


def _base_parts() -> Tuple[str, str]:
    parsed = urlparse(NAMANDARSHAN_BASE_URL)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    return scheme, netloc


def _is_allowed_url(url: str) -> bool:
    try:
        u = urlparse(url)
        if u.scheme not in {"http", "https"}:
            return False
        _, base_netloc = _base_parts()
        return u.netloc.lower() == base_netloc
    except Exception:
        return False


def _canonical_url(path_or_url: str) -> str:
    if not path_or_url:
        return NAMANDARSHAN_BASE_URL + "/"

    # Treat bare paths as relative to base
    if path_or_url.startswith("/"):
        return urljoin(NAMANDARSHAN_BASE_URL + "/", path_or_url.lstrip("/"))

    parsed = urlparse(path_or_url)
    if not parsed.scheme:
        return urljoin(NAMANDARSHAN_BASE_URL + "/", path_or_url)

    return path_or_url


@dataclass
class _CacheItem:
    value: object
    expires_at: float


_cache: Dict[str, _CacheItem] = {}
_last_fetch_at = 0.0


def _cache_get(key: str):
    item = _cache.get(key)
    if not item:
        return None
    if time.time() > item.expires_at:
        _cache.pop(key, None)
        return None
    return item.value


def _cache_set(key: str, value: object, ttl_sec: float):
    _cache[key] = _CacheItem(value=value, expires_at=time.time() + ttl_sec)


def _rate_limit(min_interval_sec: float = 0.6):
    global _last_fetch_at
    now = time.time()
    wait = (_last_fetch_at + min_interval_sec) - now
    if wait > 0:
        time.sleep(wait)
    _last_fetch_at = time.time()


def _http_client() -> httpx.Client:
    return httpx.Client(
        timeout=SCRAPE_TIMEOUT_SEC,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
    )


def _robots() -> robotparser.RobotFileParser:
    cached = _cache_get("robots")
    if cached:
        return cached  # type: ignore[return-value]

    rp = robotparser.RobotFileParser()
    robots_url = urljoin(NAMANDARSHAN_BASE_URL + "/", "robots.txt")
    rp.set_url(robots_url)
    try:
        _rate_limit()
        with _http_client() as client:
            resp = client.get(robots_url)
        if resp.status_code == 200:
            rp.parse(resp.text.splitlines())
        else:
            # If robots.txt not present, treat as allowed (common for small sites)
            rp.parse([])
    except Exception:
        rp.parse([])

    _cache_set("robots", rp, ttl_sec=60 * 10)
    return rp


def _clean_text(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    title = (soup.title.string.strip() if soup.title and soup.title.string else "")

    # Remove noisy elements
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    # Prefer main content if present
    main = soup.find("main") or soup.find(attrs={"role": "main"})
    root = main if main else soup.body if soup.body else soup

    text = root.get_text(separator="\n", strip=True)
    # Collapse repeated whitespace/newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return title, text


def fetch_page(path_or_url: str) -> Dict[str, object]:
    if not ENABLE_NAMANDARSHAN_SCRAPE:
        return {"error": "scrape_disabled", "message": "Website scraping is disabled."}

    url = _canonical_url(path_or_url)
    if not _is_allowed_url(url):
        return {"error": "blocked_domain", "message": "Only namandarshan.com is allowed.", "url": url}

    rp = _robots()
    if not rp.can_fetch(USER_AGENT, url):
        return {"error": "blocked_by_robots", "message": "Blocked by robots.txt rules.", "url": url}

    cache_key = f"page:{url}"
    cached = _cache_get(cache_key)
    if cached:
        return cached  # type: ignore[return-value]

    try:
        _rate_limit()
        with _http_client() as client:
            resp = client.get(url)
        if resp.status_code >= 400:
            return {"error": "http_error", "status": resp.status_code, "url": url}

        title, text = _clean_text(resp.text)
        if len(text) > SCRAPE_MAX_CHARS:
            text = text[:SCRAPE_MAX_CHARS] + "…"

        out = {"url": url, "title": title, "text": text}
        _cache_set(cache_key, out, ttl_sec=60 * 5)
        return out

    except Exception as exc:
        log.warning("Fetch failed: %s", exc)
        return {"error": "fetch_failed", "message": str(exc), "url": url}


def _parse_sitemap(xml_text: str) -> List[str]:
    urls: List[str] = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return urls

    # Handle sitemap index or urlset
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    if root.tag.endswith("sitemapindex"):
        for sm in root.findall(f".//{ns}sitemap"):
            loc = sm.find(f"{ns}loc")
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
        return urls

    for u in root.findall(f".//{ns}url"):
        loc = u.find(f"{ns}loc")
        if loc is not None and loc.text:
            urls.append(loc.text.strip())
    return urls


def sitemap_urls() -> List[str]:
    cached = _cache_get("sitemap_urls")
    if cached:
        return cached  # type: ignore[return-value]

    if not ENABLE_NAMANDARSHAN_SCRAPE:
        return []

    sitemap = urljoin(NAMANDARSHAN_BASE_URL + "/", "sitemap.xml")
    if not _is_allowed_url(sitemap):
        return []

    try:
        _rate_limit()
        with _http_client() as client:
            resp = client.get(sitemap, headers={"Accept": "application/xml,text/xml,*/*"})
        if resp.status_code >= 400:
            _cache_set("sitemap_urls", [], ttl_sec=60 * 10)
            return []

        first = _parse_sitemap(resp.text)
        # If it's an index, follow a few child sitemaps
        urls: List[str] = []
        if any(u.endswith(".xml") for u in first):
            for child in first[:5]:
                if not _is_allowed_url(child):
                    continue
                _rate_limit()
                with _http_client() as client:
                    c = client.get(child, headers={"Accept": "application/xml,text/xml,*/*"})
                if c.status_code < 400:
                    urls.extend(_parse_sitemap(c.text))
        else:
            urls = first

        # Keep only base-domain URLs
        urls = [u for u in urls if _is_allowed_url(u)]
        _cache_set("sitemap_urls", urls, ttl_sec=60 * 20)
        return urls

    except Exception:
        _cache_set("sitemap_urls", [], ttl_sec=60 * 10)
        return []


def search(query: str, max_pages: Optional[int] = None) -> Dict[str, object]:
    if not ENABLE_NAMANDARSHAN_SCRAPE:
        return {"error": "scrape_disabled", "message": "Website scraping is disabled.", "results": []}

    q = (query or "").strip()
    if not q:
        return {"error": "empty_query", "results": []}

    max_pages = int(max_pages or SCRAPE_MAX_PAGES)
    max_pages = max(1, min(max_pages, 8))

    # Tokenize query for scoring
    tokens = [t for t in re.split(r"[^a-zA-Z0-9]+", q.lower()) if len(t) >= 3]
    tokens = tokens[:10]

    candidates = sitemap_urls()
    if tokens and candidates:
        # URL substring filter first for speed
        filt = []
        for u in candidates:
            ul = u.lower()
            if any(t in ul for t in tokens):
                filt.append(u)
        candidates = filt or candidates

    # Always include homepage as a fallback context page
    if NAMANDARSHAN_BASE_URL + "/" not in candidates:
        candidates = [NAMANDARSHAN_BASE_URL + "/"] + candidates

    seen = set()
    ranked: List[Tuple[int, Dict[str, object]]] = []

    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        page = fetch_page(url)
        if page.get("error"):
            continue
        text = (page.get("text") or "").lower()
        score = 0
        for t in tokens:
            score += text.count(t)
        ranked.append((score, page))
        if len(ranked) >= max_pages:
            break

    ranked.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, page in ranked[:max_pages]:
        snippet = str(page.get("text") or "")
        if len(snippet) > 700:
            snippet = snippet[:700] + "…"
        results.append(
            {
                "url": page.get("url"),
                "title": page.get("title"),
                "score": score,
                "snippet": snippet,
            }
        )

    return {"query": q, "base_url": NAMANDARSHAN_BASE_URL, "results": results}

