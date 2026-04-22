"""
web_search.py — General web searching and scraping logic.
Uses DuckDuckGo (HTML version) and BeautifulSoup for lightweight, key-less search.
"""

import re
import logging
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

log = logging.getLogger("nd.web_search")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def google_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Perform a general web search using DuckDuckGo (key-less).
    Returns a list of {title, url, snippet}.
    """
    try:
        # Using DuckDuckGo's HTML-only version for easier scraping
        url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        with httpx.Client(timeout=10.0, follow_redirects=True, headers=headers) as client:
            resp = client.post(url, data=params)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            
            # DuckDuckGo HTML structure
            for item in soup.select(".result")[:max_results]:
                title_tag = item.select_one(".result__a")
                snippet_tag = item.select_one(".result__snippet")
                
                if title_tag and title_tag.get("href"):
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "url": title_tag.get("href"),
                        "snippet": snippet_tag.get_text(strip=True) if snippet_tag else ""
                    })
            
            return results
            
    except Exception as e:
        log.error("Search failed: %s", e)
        return []

def scrape_website(url: str, max_chars: int = 4000) -> Dict[str, str]:
    """
    General purpose website scraper.
    Extracts title and main text content.
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        
        with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Remove scripts, styles, etc.
            for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
                tag.decompose()
            
            title = soup.title.get_text(strip=True) if soup.title else "No Title"
            
            # Get text from body
            body = soup.find("body") or soup
            text = body.get_text(separator="\n", strip=True)
            
            # Clean up whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r'[ \t]{2,}', ' ', text)
            
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
                
            return {
                "url": url,
                "title": title,
                "text": text
            }
            
    except Exception as e:
        log.error("Scrape failed for %s: %s", url, e)
        return {"url": url, "error": str(e)}

if __name__ == "__main__":
    # Quick test
    res = google_search("temples in Haridwar")
    import json
    print(json.dumps(res, indent=2))
