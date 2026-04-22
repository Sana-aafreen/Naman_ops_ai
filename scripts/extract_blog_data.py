"""
extract_blog_data.py — Extract blog content from namandarshan.com JavaScript bundle
"""

import httpx
import json
import re
from pathlib import Path

def main():
    url = 'https://namandarshan.com/assets/index-BR4n9Ath.js'
    print(f"Fetching {url}...")
    resp = httpx.get(url, timeout=25, follow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
    js_text = resp.text
    print(f"Downloaded {len(js_text)} characters")

    # Look for blog data structures
    # Find arrays that look like blog data
    blog_arrays = re.findall(r'\[(\{[^}]*"title"[^}]*"content"[^}]*\}[^]]*)\]', js_text, re.DOTALL)
    print(f"Found {len(blog_arrays)} potential blog arrays")

    blogs = []
    for arr in blog_arrays:
        try:
            # Clean up the array string and parse as JSON
            arr = '[' + arr + ']'
            # Fix common JSON issues
            arr = re.sub(r',\s*}', '}', arr)  # Remove trailing commas
            arr = re.sub(r',\s*]', ']', arr)
            data = json.loads(arr)
            if isinstance(data, list) and data:
                print(f"Parsed array with {len(data)} items")
                blogs.extend(data)
        except json.JSONDecodeError as e:
            print(f"Failed to parse array: {e}")
            continue

    # Also look for individual blog objects
    blog_objects = re.findall(r'(\{"title"[^}]*"content"[^}]*\})', js_text, re.DOTALL)
    print(f"Found {len(blog_objects)} potential blog objects")

    for obj_str in blog_objects:
        try:
            obj = json.loads(obj_str)
            blogs.append(obj)
        except json.JSONDecodeError:
            continue

    print(f"Total blogs extracted: {len(blogs)}")

    # Save to file
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    output_file = data_dir / "namandarshan_blogs.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(blogs, f, ensure_ascii=False, indent=2)

    print(f"Saved blogs to {output_file}")

    # Show sample
    if blogs:
        sample = blogs[0]
        print("Sample blog:")
        print(f"Title: {sample.get('title', 'N/A')}")
        content = sample.get('content', '')
        print(f"Content length: {len(content)}")
        print(f"Content preview: {content[:300]}...")

if __name__ == "__main__":
    main()