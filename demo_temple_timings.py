#!/usr/bin/env python3
"""
Demo: Test Kashi Vishwanath temple timing retrieval
"""

import json
import sys
sys.path.insert(0, 'Backend')

from excel_store import store
from namandarshan_scrape import search as nd_search, fetch_page as nd_fetch_page

print("=" * 70)
print("🕉️  TEMPLE TIMING RETRIEVAL DEMO - Kashi Vishwanath Temple")
print("=" * 70)

# ──────────────────────────────────────────────────────────────────────────
# APPROACH 1: Check Local Database
# ──────────────────────────────────────────────────────────────────────────
print("\n1️⃣  APPROACH 1: Local Database")
print("-" * 70)

temples = store.get_temple_info(name="Kashi")
if temples:
    print("✅ Found in local database:")
    for t in temples:
        print(f"   • {t.get('Name')} ({t.get('City')})")
        print(f"     Deity: {t.get('Deity')}")
        print(f"     Website: {t.get('Website')}")
else:
    print("❌ Not found in local database (Temples sheet may be empty)")

# ──────────────────────────────────────────────────────────────────────────
# APPROACH 2: Web Search on NamanDarshan
# ──────────────────────────────────────────────────────────────────────────
print("\n2️⃣  APPROACH 2: Search NamanDarshan.com Pages")
print("-" * 70)

search_results = nd_search("Kashi Vishwanath temple", max_pages=3)
if search_results.get("results"):
    print(f"✅ Found {len(search_results['results'])} matching pages:")
    for i, result in enumerate(search_results['results'][:3], 1):
        print(f"\n   [{i}] {result.get('title', 'No title')}")
        print(f"       URL: {result.get('url')}")
        print(f"       Match score: {result.get('score')}")
        snippet = result.get('snippet', '')[:150]
        print(f"       Preview: {snippet}...")
else:
    print("❌ No results from web search")

# ──────────────────────────────────────────────────────────────────────────
# APPROACH 3: Fetch Full Page
# ──────────────────────────────────────────────────────────────────────────
print("\n3️⃣  APPROACH 3: Fetch Full Page Content")
print("-" * 70)

page = nd_fetch_page("/temples/kashi-vishwanath-temple")
if not page.get("error"):
    print(f"✅ Successfully fetched page:")
    print(f"   Title: {page.get('title')}")
    print(f"   URL: {page.get('url')}")
    
    text = page.get('text', '')[:300]
    print(f"\n   Page content preview:")
    for line in text.split('\n')[:5]:
        if line.strip():
            print(f"   {line}")
    
    # Check for timing keywords
    full_text = page.get('text', '').lower()
    timing_keywords = ['time', 'open', 'close', 'am', 'pm', 'hour', 'darshan', 'timing']
    found_keywords = [kw for kw in timing_keywords if kw in full_text]
    if found_keywords:
        print(f"\n   ✓ Found timing-related keywords: {', '.join(found_keywords)}")
    else:
        print(f"\n   ⚠️  No obvious timing keywords found on page")
else:
    print(f"❌ Failed to fetch page: {page.get('error')}")

# ──────────────────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("📋 SUMMARY: Agent Tool Flow")
print("=" * 70)

print("""
When you ask the agent: "What are the timings for Kashi Vishwanath Temple?"

The agent will:
  1. Use get_temple_info(name="Kashi Vishwanath") → Check local Excel
  2. If found → Return immediately with cached data
  3. If not found → Use nd_web_search() → Get matching pages
  4. Then use nd_fetch_page() → Extract full page content
  5. Return timing information from the web page

This 3-layer approach ensures:
  ✓ Fast response from cache when available
  ✓ Up-to-date info from website when needed
  ✓ Graceful fallback if primary source unavailable
  ✓ Respects robots.txt and uses rate limiting
""")

print("=" * 70)
