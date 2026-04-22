"""
fetch_darshan_data.py — Fetch structured darshan data from API for all slugs
"""

import json
import sys
import time
from pathlib import Path

# Add Backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "Backend"))

from namandarshan_api import get_darshan

def main():
    # Load scraped pages
    data_dir = Path(__file__).parent.parent / "data"
    input_file = data_dir / "namandarshan_scraped_pages.json"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        pages = json.load(f)

    # Extract darshan slugs
    darshan_urls = [p['url'] for p in pages if '/darshan/' in p['url'] and 'vipdarshan' in p['url']]
    
    slugs = []
    for url in darshan_urls:
        parts = url.split('/darshan/')
        if len(parts) > 1:
            slug = parts[1].replace('-vipdarshan', '')
            slugs.append(slug)

    print(f"Found {len(slugs)} darshan slugs")

    # Fetch data for each slug
    darshan_data = []
    for i, slug in enumerate(slugs, 1):
        print(f"[{i}/{len(slugs)}] Fetching data for {slug}")
        try:
            data = get_darshan(slug)
            if "error" not in data:
                darshan_data.append({"slug": slug, "data": data})
            else:
                print(f"  Error: {data}")
        except Exception as e:
            print(f"  Exception: {e}")
        
        # Small delay to be respectful
        time.sleep(0.5)

    # Save to file
    output_file = data_dir / "namandarshan_darshan_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(darshan_data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(darshan_data)} darshan records to {output_file}")

if __name__ == "__main__":
    main()