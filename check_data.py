#!/usr/bin/env python3
import json
import pandas as pd

# Check darshan data
try:
    with open('data/namandarshan_darshan_data.json') as f:
        darshan_data = json.load(f)
    print(f"✓ Darshan data: {len(darshan_data)} temples")
    
    # Look for Kashi
    kashi = [t for slug, t in darshan_data.items() if 'kashi' in str(t).lower()]
    if kashi:
        print(f"  Found {len(kashi)} Kashi temple(s)")
        print(f"  Sample: {list(kashi[0].items())[:3]}")
except Exception as e:
    print(f"✗ Darshan data error: {e}")

# Check pages data
try:
    with open('data/namandarshan_scraped_pages.json') as f:
        pages = json.load(f)
    print(f"\n✓ Scraped pages: {len(pages)} URLs cached")
except Exception as e:
    print(f"\n✗ Scraped pages error: {e}")

# Check Excel
try:
    xl = pd.read_excel('data/namandarshan_data.xlsx', sheet_name=None)
    print(f"\n✓ Excel sheets: {list(xl.keys())}")
    for name, df in xl.items():
        print(f"  {name}: {len(df)} rows")
except Exception as e:
    print(f"\n✗ Excel error: {e}")

print("\n📌 Action: Need to fetch Kashi Vishwanath temple info from namandarshan.com API")
