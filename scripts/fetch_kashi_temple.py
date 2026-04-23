#!/usr/bin/env python3
"""
fetch_kashi_temple.py - Fetch Kashi Vishwanath temple info including timings
"""

import json
import httpx
import pandas as pd
from pathlib import Path

BASE = "https://api.namandarshan.com"

def get_temple_by_slug(slug: str):
    """Fetch structured darshan info from api.namandarshan.com"""
    try:
        url = f"{BASE}/api/darshan/{slug}"
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            r = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"✗ Failed to fetch {slug}: {e}")
        return None

def scrape_page(path_or_url: str):
    """Fetch and clean text from a page"""
    try:
        from bs4 import BeautifulSoup
        
        url = f"https://namandarshan.com{path_or_url}" if path_or_url.startswith("/") else path_or_url
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            r = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:2000]
    except Exception as e:
        print(f"✗ Failed to scrape {path_or_url}: {e}")
        return None

print("🕉️  Fetching Kashi Vishwanath Temple Information...")

# Try fetching from API
print("\n1️⃣  Trying API endpoint...")
temple_data = get_temple_by_slug("kashi-vishwanath-temple")
if temple_data and 'error' not in temple_data:
    print(f"✓ Got API data: {json.dumps(temple_data, indent=2)[:500]}...")
else:
    print("✗ API endpoint not available or missing")

# Try scraping the page
print("\n2️⃣  Scraping NamanDarshan page...")
page_content = scrape_page("/temples/kashi-vishwanath-temple")
if page_content:
    print(f"✓ Page content retrieved ({len(page_content)} chars)")
    if 'timing' in page_content.lower() or 'time' in page_content.lower():
        print("  ✓ Found timing information on page")
        # Extract timing lines
        lines = page_content.split('\n')
        timing_lines = [l for l in lines if any(k in l.lower() for k in ['time', 'open', 'close', 'am', 'pm', ':'])]
        if timing_lines:
            print("  Timing lines found:")
            for line in timing_lines[:5]:
                print(f"    - {line.strip()}")
    else:
        print("  ⚠️  No timing information visible on current page")

# Prepare temple data to add to Excel
print("\n3️⃣  Preparing temple data for Excel...")

temple_record = {
    'Name': 'Kashi Vishwanath Temple',
    'City': 'Varanasi',
    'State': 'Uttar Pradesh',
    'Deity': 'Lord Shiva',
    'Opening_Time': 'Check website for current timings',
    'Closing_Time': 'Check website for current timings',
    'Special_Timings': 'Varies by season and puja schedule',
    'Website': 'https://namandarshan.com/temples/kashi-vishwanath-temple',
    'Phone': 'Contact via NamanDarshan.com',
    'VIP_Darshan': 'Available (check website)',
    'Accommodation': 'Multiple hotels nearby',
    'Parking': 'Limited, hotels have parking',
}

# Load existing Excel and add Temples sheet if missing
excel_path = Path('data/namandarshan_data.xlsx')
if excel_path.exists():
    xl = pd.read_excel(excel_path, sheet_name=None)
    
    if 'Temples' not in xl:
        print("  Adding Temples sheet to Excel...")
        df_temples = pd.DataFrame([temple_record])
        
        # Append to Excel
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            for sheet_name, df in xl.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            df_temples.to_excel(writer, sheet_name='Temples', index=False)
        print("✓ Temples sheet added to Excel")
    else:
        print("  Temples sheet already exists")
else:
    print("✗ Excel file not found")

print("\n💡 Next steps:")
print("   1. Visit https://namandarshan.com/temples/kashi-vishwanath-temple")
print("   2. Update Temple timings in Excel manually if needed")
print("   3. AI agent can fetch page for latest info: nd_fetch_page('/temples/kashi-vishwanath-temple')")
print("   4. Or use nd_web_search('Kashi Vishwanath temple timings') for web results")
