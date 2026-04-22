"""
ops_agent.py — Safe NamanDarshan Ops Agent core

Works even if Groq package/API key is missing.
Imported by routes.py as:
from ops_agent import run_agent
"""

import json
import logging

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_TEMPERATURE,
    GROQ_MAX_TOKENS,
    MAX_TOOL_ROUNDS,
)

from session_store import Session
from tools import TOOLS, execute_tool

log = logging.getLogger("nd.agent")


# ==========================================================
# SAFE GROQ IMPORT
# ==========================================================

USE_GROQ = False
client = None

try:
    from groq import Groq

    if GROQ_API_KEY:
        # Groq SDK versions may internally create an `httpx.Client(proxies=...)` which
        # breaks with httpx>=0.28 (parameter renamed to `proxy`).
        # Passing our own `http_client` keeps things compatible.
        import httpx

        client = Groq(
            api_key=GROQ_API_KEY,
            http_client=httpx.Client(trust_env=True),
        )
        USE_GROQ = True

except Exception as e:
    log.warning("Groq unavailable: %s", e)


# ==========================================================
# SYSTEM PROMPT
# ==========================================================

def _system_prompt(context: dict) -> str:
    memory = ""

    if context:
        memory = "\nRemembered user context:\n"
        for k, v in context.items():
            memory += f"- {k}: {v}\n"

    return f"""
You are NamanDarshan Ops AI, a premium travel assistant for pilgrims in India.
Your goal is to provide accurate, helpful, and warm assistance for Darshan, Puja, Hotels, Cabs, and Temple information.

{memory}

DATA SOURCES:
1. INTERNAL EXCEL: For Pandits, Hotels, Cabs, and basic Temple info. Always check this first if applicable.
2. NAMANDARSHAN.COM: For latest Aarti timings, VIP darshan packages, and official site info.
3. GENERAL WEB SEARCH (GOOGLE): For general travel news, broad temple history, or info not found above.

RULES:
- When using tools, ONLY use the data returned by the tool. Do NOT invent names or prices.
- If info is missing in Excel, search namandarshan.com.
- If still missing, perform a 'google_search' and 'scrape_website'.
- Be concise but warm (Namaste Ji 🙏).
- If you find conflicting info, prioritize namandarshan.com for timings and Excel for contacts.

Available tools: search_pandits, search_hotels, search_cabs, get_temple_info, nd_web_search, nd_fetch_page, google_search, scrape_website.
"""


# ==========================================================
# FALLBACK LOCAL RESPONSE
# ==========================================================

def _local_reply(user_message: str, session: Session) -> dict:
    text = user_message.lower()

    actions = []

    if "hotel" in text:
        result = execute_tool("search_hotels", {}, session)
        actions.append({"tool": "search_hotels", "args": {}, "result": result})

    elif "pandit" in text or "puja" in text:
        result = execute_tool("search_pandits", {}, session)
        actions.append({"tool": "search_pandits", "args": {}, "result": result})

    elif "cab" in text or "taxi" in text:
        result = execute_tool("search_cabs", {}, session)
        actions.append({"tool": "search_cabs", "args": {}, "result": result})

    elif "temple" in text or "darshan" in text:
        result = execute_tool("get_temple_info", {}, session)
        actions.append({"tool": "get_temple_info", "args": {}, "result": result})

    else:
        result = json.dumps(
            {
                "message": "How may I help you Ji? You can ask for temples, pandits, hotels or cabs."
            }
        )

    reply = f"Namaste Ji 🙏\n{result}"

    return {
        "reply": reply,
        "session_id": session.session_id,
        "context": session.context,
        "actions": actions,
        "rounds": 1,
    }


# ==========================================================
# WEBSITE ENRICHMENT (namandarshan.com)
# ==========================================================

def _needs_website_lookup(text: str) -> bool:
    t = (text or "").lower()
    keywords = [
        "timing", "timings", "darshan", "aarti", "opening", "closing",
        "contact", "phone", "number", "address", "location",
        "package", "packages", "vip", "booking", "book", "price", "cost",
        "today", "tomorrow", "news", "event",
        "namandarshan.com", "google", "search"
    ]
    return any(k in t for k in keywords)


def _website_lookup(user_message: str, session: Session) -> tuple[list[dict], str]:
    """
    Deterministically fetch site/web context via our internal tools.
    Returns (actions, combined_context_text).
    """
    actions: list[dict] = []
    combined_ctx = []

    # 1. Try namandarshan.com search
    search_result = execute_tool("nd_web_search", {"query": user_message, "max_pages": 3}, session)
    actions.append({"tool": "nd_web_search", "args": {"query": user_message, "max_pages": 3}, "result": search_result})
    combined_ctx.append(f"Site Search results:\n{search_result}")

    # 2. Try Google Search if query seems general or site search returned little
    if len(search_result) < 200 or "news" in user_message.lower() or "google" in user_message.lower():
        g_search = execute_tool("google_search", {"query": user_message, "max_results": 3}, session)
        actions.append({"tool": "google_search", "args": {"query": user_message, "max_results": 3}, "result": g_search})
        combined_ctx.append(f"General Web Search (Google) results:\n{g_search}")

    return actions, "\n\n".join(combined_ctx)


# ==========================================================
# MAIN FUNCTION
# ==========================================================

def run_agent(user_message: str, session: Session) -> dict:
    """
    Main callable used by routes.py
    """

    session.messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    session.add_action("user_message", user_message)

    # ------------------------------------------------------
    # FALLBACK MODE (No Groq)
    # ------------------------------------------------------
    if not USE_GROQ:
        return _local_reply(user_message, session)

    # ------------------------------------------------------
    # FULL AGENT LOOP
    # ------------------------------------------------------
    actions_this_turn = []

    try:
        # If the user is asking for info likely only on the website, do a deterministic
        # site lookup first and ask Groq to answer WITHOUT tool calls. This avoids tool
        # validation failures and keeps responses grounded in fetched content.
        if _needs_website_lookup(user_message):
            website_actions, website_context = _website_lookup(user_message, session)
            actions_this_turn.extend(website_actions)

            response0 = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=GROQ_TEMPERATURE,
                max_tokens=GROQ_MAX_TOKENS,
                messages=[
                    {
                        "role": "system",
                        "content": _system_prompt(session.context)
                        + "\nYou are given namandarshan.com data below. Answer using it."
                          "\nIf it doesn't contain the answer, say it's not listed on namandarshan.com."
                          "\nDo not mention tools, tool calls, or function names. Just answer.",
                    },
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": website_context},
                ],
            )

            reply0 = response0.choices[0].message.content or "Namaste Ji 🙏"
            session.messages.append({"role": "assistant", "content": reply0})

            return {
                "reply": reply0,
                "session_id": session.session_id,
                "context": session.context,
                "actions": actions_this_turn,
                "rounds": 1,
            }

        for round_num in range(1, MAX_TOOL_ROUNDS + 1):

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=GROQ_TEMPERATURE,
                max_tokens=GROQ_MAX_TOKENS,
                tools=TOOLS,
                tool_choice="auto",
                messages=[
                    {
                        "role": "system",
                        "content": _system_prompt(session.context)
                    },
                    *session.messages
                ],
            )

            choice = response.choices[0]
            msg = choice.message

            # Final response
            if not getattr(msg, "tool_calls", None):
                reply = msg.content or "Namaste Ji 🙏"

                session.messages.append(
                    {
                        "role": "assistant",
                        "content": reply
                    }
                )

                return {
                    "reply": reply,
                    "session_id": session.session_id,
                    "context": session.context,
                    "actions": actions_this_turn,
                    "rounds": round_num,
                }

            # Tool calls
            # Record the assistant message that requested tool calls (required for correct tool-call chaining)
            session.messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )

            for tc in msg.tool_calls:
                fn_name = tc.function.name

                try:
                    fn_args = json.loads(tc.function.arguments)
                except:
                    fn_args = {}

                result = execute_tool(fn_name, fn_args, session)

                actions_this_turn.append(
                    {
                        "tool": fn_name,
                        "args": fn_args,
                        "result": result,
                    }
                )

                session.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    }
                )

        # exceeded rounds

                session.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    }
                )

        # exceeded rounds
        return {
            "reply": "Please rephrase your request Ji 🙏",
            "session_id": session.session_id,
            "context": session.context,
            "actions": actions_this_turn,
            "rounds": MAX_TOOL_ROUNDS,
        }

    except Exception as e:
        err = str(e)
        log.error("Agent loop crash: %s", err, exc_info=True)

        # If Groq rejects the request due to tool-call validation, fall back to doing
        # a deterministic site scrape ourselves, then ask Groq to answer WITHOUT tools.
        if ("tool call validation failed" in err or "tool_use_failed" in err) and USE_GROQ:
            try:
                website = execute_tool("nd_web_search", {"query": user_message, "max_pages": 3}, session)
                actions = [{"tool": "nd_web_search", "args": {"query": user_message, "max_pages": 3}, "result": website}]

                response2 = client.chat.completions.create(
                    model=GROQ_MODEL,
                    temperature=GROQ_TEMPERATURE,
                    max_tokens=GROQ_MAX_TOKENS,
                    messages=[
                        {"role": "system", "content": _system_prompt(session.context) + "\nAnswer using only the website results provided. Do not call tools."},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": f"Website search results (JSON):\n{website}"},
                    ],
                )
                reply = response2.choices[0].message.content or "Namaste Ji 🙏"
                session.messages.append({"role": "assistant", "content": reply})
                return {
                    "reply": reply,
                    "session_id": session.session_id,
                    "context": session.context,
                    "actions": actions,
                    "rounds": 1,
                }
            except Exception as e2:
                log.error("Tool-validation fallback failed: %s", e2)

        # Final fallback
        return _local_reply(user_message, session)
