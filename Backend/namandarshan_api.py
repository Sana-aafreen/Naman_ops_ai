"""
namandarshan_api.py — Read-only client for api.namandarshan.com

This is used to fetch structured data that the public namandarshan.com site renders via JS.
Guardrails:
  - Only allows the api.namandarshan.com host.
  - Only fetches known read-only endpoints.
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse

import httpx

from config import SCRAPE_TIMEOUT_SEC

log = logging.getLogger("nd.nd_api")


BASE = "https://api.namandarshan.com"


@dataclass
class _CacheItem:
    value: object
    expires_at: float


_cache: Dict[str, _CacheItem] = {}


def _cache_get(key: str):
    item = _cache.get(key)
    if not item:
        return None
    if time.time() > item.expires_at:
        _cache.pop(key, None)
        return None
    return item.value


def _cache_set(key: str, value: object, ttl_sec: float = 60.0):
    _cache[key] = _CacheItem(value=value, expires_at=time.time() + ttl_sec)


def _safe_url(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    url = urljoin(BASE + "/", path.lstrip("/"))
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "api.namandarshan.com":
        raise ValueError("Blocked domain")
    return url


def _get_json(path: str, cache_ttl_sec: float = 60.0) -> Dict[str, Any]:
    url = _safe_url(path)
    ck = f"json:{url}"
    cached = _cache_get(ck)
    if cached:
        return cached  # type: ignore[return-value]

    with httpx.Client(timeout=SCRAPE_TIMEOUT_SEC, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as c:
        r = c.get(url)
    r.raise_for_status()
    data = r.json()
    _cache_set(ck, data, ttl_sec=cache_ttl_sec)
    return data


def get_darshan(slug: str) -> Dict[str, Any]:
    slug = (slug or "").strip().strip("/")
    if not slug:
        return {"error": "empty_slug"}
    return _get_json(f"/api/darshan/{slug}", cache_ttl_sec=60 * 5)


def get_live_darshan(slug: str) -> Dict[str, Any]:
    slug = (slug or "").strip().strip("/")
    if not slug:
        return {"error": "empty_slug"}
    return _get_json(f"/api/live-darshan/{slug}", cache_ttl_sec=60 * 5)

