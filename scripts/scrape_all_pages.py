"""
scrape_all_pages.py — Scrape all pages from namandarshan.com sitemap and save content.
Run from project root: python scripts/scrape_all_pages.py
"""

import json
import sys
import os
from pathlib import Path

# Add Backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "Backend"))

from namandarshan_scrape import sitemap_urls, fetch_page

def main():
    print("Fetching sitemap URLs...")
    urls = sitemap_urls()
    print(f"Found {len(urls)} URLs in sitemap")

    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    output_file = data_dir / "namandarshan_scraped_pages.json"
    
    # Load existing data if file exists
    scraped_data = []
    processed_urls = set()
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
                processed_urls = {page['url'] for page in scraped_data if 'url' in page}
            print(f"Loaded {len(scraped_data)} existing pages")
        except Exception as e:
            print(f"Error loading existing data: {e}")

    total = len(urls)
    new_pages = 0

    for i, url in enumerate(urls, 1):
        if url in processed_urls:
            print(f"[{i}/{total}] Skipping {url} (already processed)")
            continue
            
        print(f"[{i}/{total}] Scraping {url}")
        try:
            page_data = fetch_page(url)
            if "error" not in page_data:
                scraped_data.append(page_data)
                new_pages += 1
                processed_urls.add(url)
                
                # Save every 10 pages
                if new_pages % 10 == 0:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(scraped_data, f, ensure_ascii=False, indent=2)
                    print(f"  Saved progress: {len(scraped_data)} total pages")
            else:
                print(f"  Error: {page_data.get('error')} - {page_data.get('message', '')}")
        except KeyboardInterrupt:
            print("Interrupted by user")
            break
        except Exception as e:
            print(f"  Unexpected error: {e}")

    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(scraped_data)} pages to {output_file} ({new_pages} new)")

if __name__ == "__main__":
    main()