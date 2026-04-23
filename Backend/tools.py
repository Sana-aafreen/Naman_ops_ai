"""
tools.py
Groq tool definitions + executor for NamanDarshan Ops Agent
"""

import json
import logging
from typing import TYPE_CHECKING

from excel_store import store
from namandarshan_scrape import search as nd_search, fetch_page as nd_fetch_page
from namandarshan_api import get_darshan as nd_get_darshan, get_live_darshan as nd_get_live_darshan
from web_search import google_search, scrape_website

if TYPE_CHECKING:
    from session_store import Session

log = logging.getLogger("nd.tools")


# ==========================================================
# TOOL DEFINITIONS
# ==========================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_pandits",
            "description": "Search pandits by name, city, specialization, price.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "city": {"type": "string"},
                    "specialization": {"type": "string"},
                    "available_only": {"type": "boolean"},
                    "max_price": {"type": "number"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": "Search hotels by city, budget, stars.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "max_price": {"type": "number"},
                    "min_stars": {"type": "integer"},
                    "available_only": {"type": "boolean"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_cabs",
            "description": "Search cabs by city, capacity, AC.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "min_capacity": {"type": "integer"},
                    "available_only": {"type": "boolean"},
                    "ac_required": {"type": "boolean"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_temple_info",
            "description": "Get temple details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "city": {"type": "string"},
                    "deity": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_database_stats",
            "description": "Get overall database stats.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_session_context",
            "description": "Store remembered user preferences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "budget_per_night": {"type": "number"},
                    "travel_date": {"type": "string"},
                    "group_size": {"type": "integer"},
                    "seva_type": {"type": "string"},
                    "language": {"type": "string"},
                    "notes": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "nd_web_search",
            "description": "Search namandarshan.com public pages (site-limited).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_pages": {"type": "integer"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "nd_fetch_page",
            "description": "Fetch a single namandarshan.com page by URL or path and extract readable text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path_or_url": {"type": "string"}
                },
                "required": ["path_or_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "nd_get_darshan",
            "description": "Fetch structured VIP darshan info (including schedule) from api.namandarshan.com for a given darshan slug.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string"}
                },
                "required": ["slug"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "nd_get_live_darshan",
            "description": "Fetch structured live-darshan info from api.namandarshan.com for a given live-darshan slug.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string"}
                },
                "required": ["slug"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Perform a general web search for information not found in internal database or namandarshan.com.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_website",
            "description": "Read content from a general website URL found during search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"]
            }
        }
    }
]


# ==========================================================
# EXECUTOR
# ==========================================================

def execute_tool(name: str, args: dict, session: "Session") -> str:
    try:
        log.info("Tool call: %s %s", name, args)

        if name == "search_pandits":
            data = store.search_pandits(**args)
            return json.dumps({"pandits": data, "count": len(data)})

        if name == "search_hotels":
            data = store.search_hotels(**args)
            return json.dumps({"hotels": data, "count": len(data)})

        if name == "search_cabs":
            data = store.search_cabs(**args)
            return json.dumps({"cabs": data, "count": len(data)})

        if name == "get_temple_info":
            data = store.get_temple_info(**args)
            result = {"temples": data, "count": len(data)}
            
            # If no temple found in Excel, suggest web search
            if not data and args.get("name"):
                temple_name = args.get("name")
                result["info"] = f"Temple '{temple_name}' not found in local database. " \
                               f"Searching NamanDarshan.com for this temple..."
                # Automatically search the web
                search_result = nd_search(f"{temple_name} temple", max_pages=3)
                if search_result.get("results"):
                    result["web_results"] = search_result.get("results")
                    result["suggestion"] = "Consider using nd_fetch_page() to get detailed timing information from these results."
            
            return json.dumps(result)

        if name == "get_database_stats":
            return json.dumps(store.get_stats())

        if name == "update_session_context":
            for k, v in args.items():
                if v is not None:
                    session.context[k] = v
            return json.dumps({"status": "ok", "stored": args})

        if name == "nd_web_search":
            q = (args.get("query") or "").strip()
            max_pages = args.get("max_pages")
            return json.dumps(nd_search(q, max_pages=max_pages))

        if name == "nd_fetch_page":
            path_or_url = (args.get("path_or_url") or "").strip()
            return json.dumps(nd_fetch_page(path_or_url))

        if name == "nd_get_darshan":
            slug = (args.get("slug") or "").strip()
            return json.dumps(nd_get_darshan(slug))

        if name == "nd_get_live_darshan":
            slug = (args.get("slug") or "").strip()
            return json.dumps(nd_get_live_darshan(slug))

        if name == "google_search":
            q = (args.get("query") or "").strip()
            n = args.get("max_results") or 5
            results = google_search(q, max_results=n)
            return json.dumps({"query": q, "results": results})

        if name == "scrape_website":
            url = (args.get("url") or "").strip()
            return json.dumps(scrape_website(url))

        return json.dumps({"error": "Unknown tool"})

    except Exception as e:
        log.exception("Tool error")
        return json.dumps({"error": str(e)})
