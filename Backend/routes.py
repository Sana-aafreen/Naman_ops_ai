"""
routes.py — All FastAPI route handlers for NamanDarshan.

Routers:
  /api/agent/...   — Agentic chat
  /api/data/...    — Raw Excel data endpoints
  /api/excel/...   — Excel reload/upload
  /api/health      — Health check
"""

import logging
from typing import Optional, Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi import Request
from pydantic import BaseModel

from config import EXCEL_PATH, GROQ_MODEL, MAX_TOOL_ROUNDS
from config import APP_VERSION

# SAFE IMPORTS (fix circular import)
import excel_store
from ops_agent import run_agent
from ops_agent import USE_GROQ
from session_store import session_store
from tools import TOOLS

log = logging.getLogger("nd.routes")


# ==========================================================
# HELPERS
# ==========================================================

def get_store():
    return excel_store.store


# ==========================================================
# PYDANTIC MODELS
# ==========================================================

class ChatRequest(BaseModel):
    message: Optional[str] = None
    messages: Optional[list[Any]] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    context: dict
    actions: list[dict]
    rounds: int


class LegacyMessage(BaseModel):
    role: str
    content: str


class LegacyChatRequest(BaseModel):
    messages: list[LegacyMessage]
    session_id: Optional[str] = None


class LegacyChatResponse(BaseModel):
    response: str
    status: str
    session_id: str
    context: dict
    actions: list[dict]
    rounds: int


class SessionInfo(BaseModel):
    session_id: str
    context: dict
    message_count: int
    action_log: list[dict]
    created_at: str
    last_active: str


# ==========================================================
# AGENT ROUTER
# ==========================================================

agent_router = APIRouter(prefix="/api/agent", tags=["Agent"])


@agent_router.post("/chat", response_model=ChatResponse)
async def agent_chat(req: ChatRequest):
    session_store.purge_expired()

    # Support simple message or messages list
    user_msg = ""
    if req.message and req.message.strip():
        user_msg = req.message.strip()
    elif req.messages:
        for m in reversed(req.messages):
            # dict or object support
            m_role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
            m_cont = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else None)
            if (m_role or "").strip().lower() == "user" and (m_cont or "").strip():
                user_msg = m_cont.strip()
                break

    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session = session_store.get_or_create(req.session_id)

    try:
        result = run_agent(user_msg, session)
        
        # Robust construction
        return ChatResponse(
            reply=result.get("reply") or result.get("response") or "Namaste Ji 🙏",
            session_id=result.get("session_id") or session.session_id,
            context=result.get("context") or session.context,
            actions=result.get("actions") or [],
            rounds=result.get("rounds") or 1,
        )

    except Exception as exc:
        log.error("Agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# Compatibility endpoint for older frontend clients expecting `/api/chat`
legacy_router = APIRouter(prefix="/api", tags=["Agent"])


@legacy_router.post("/chat", response_model=LegacyChatResponse)
async def legacy_chat(req: ChatRequest):
    session_store.purge_expired()

    # Support BOTH formats: {message: "..."} and {messages: [{role: "user", content: "..."}]}
    user_msg = ""
    if req.message and req.message.strip():
        user_msg = req.message.strip()
    elif req.messages:
        for m in reversed(req.messages):
            m_role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
            m_cont = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else None)
            if (m_role or "").strip().lower() == "user" and (m_cont or "").strip():
                user_msg = m_cont.strip()
                break

    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session = session_store.get_or_create(req.session_id)

    try:
        result = run_agent(user_msg, session)

        # Fallback fields for robustness
        reply_text = result.get("reply") or result.get("response") or "Namaste Ji 🙏"

        return LegacyChatResponse(
            response=reply_text,
            status="ok",
            session_id=result.get("session_id") or session.session_id,
            context=result.get("context") or session.context,
            actions=result.get("actions") or [],
            rounds=result.get("rounds") or 1,
        )

    except Exception as exc:
        log.error("Legacy Agent error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@agent_router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    s = session_store.get(session_id)

    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionInfo(**s.to_info())


@agent_router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    deleted = session_store.delete(session_id)
    return {"deleted": deleted, "session_id": session_id}


@agent_router.post("/session/{session_id}/reset")
async def reset_session(session_id: str):
    s = session_store.get(session_id)

    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    s.reset()

    return {
        "reset": True,
        "session_id": session_id,
        "context": s.context
    }


@agent_router.get("/sessions")
async def list_sessions():
    return {
        "sessions": session_store.list_all(),
        "count": session_store.count
    }


@agent_router.get("/stats")
async def agent_stats():
    store = get_store()

    return {
        "active_sessions": session_store.count,
        "model": GROQ_MODEL,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "excel_sheets": store.sheets,
        "data_stats": store.get_stats()
    }


# ==========================================================
# DATA ROUTER
# ==========================================================

data_router = APIRouter(prefix="/api/data", tags=["Data"])


@data_router.get("/sheets")
async def list_sheets():
    return {"sheets": get_store().sheets}


@data_router.get("/{sheet}")
async def get_sheet(sheet: str):
    store = get_store()

    sheet_clean = (sheet or "").strip()
    data = store.get_all(sheet_clean)

    # For UI stability, return an empty dataset (200) for unknown/missing sheets
    # instead of a 404 (prevents noisy console errors like `/api/data/Temples`).
    known = {s.strip().lower() for s in store.sheets}
    if not data and sheet_clean.lower() not in known:
        return {"sheet": sheet_clean, "count": 0, "data": []}

    return {
        "sheet": sheet_clean,
        "count": len(data),
        "data": data
    }


@data_router.get("/{sheet}/stats")
async def sheet_stats(sheet: str):
    stats = get_store().get_stats()

    if sheet not in stats:
        raise HTTPException(status_code=404, detail="Sheet not found")

    return stats[sheet]


@data_router.get("/{sheet}/available")
async def get_available(sheet: str):
    store = get_store()

    if sheet == "Pandits":
        data = store.search_pandits()

    elif sheet == "Cabs":
        data = store.search_cabs()

    else:
        data = store.get_all(sheet)

    return {
        "sheet": sheet,
        "count": len(data),
        "data": data
    }


# ==========================================================
# EXCEL ROUTER
# ==========================================================

excel_router = APIRouter(prefix="/api/excel", tags=["Excel"])


@excel_router.post("/reload")
async def reload_excel():
    counts = get_store().reload()

    return {
        "message": "Excel reloaded",
        "sheets": counts
    }


@excel_router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files allowed")

    content = await file.read()

    with open(EXCEL_PATH, "wb") as f:
        f.write(content)

    counts = get_store().reload()

    return {
        "message": "Excel uploaded successfully",
        "sheets": counts
    }


# ==========================================================
# HEALTH ROUTER
# ==========================================================

health_router = APIRouter(tags=["Health"])


@health_router.get("/api/health")
async def health():
    store = get_store()

    return {
        "status": "ok",
        "api_version": APP_VERSION,
        "excel_loaded": bool(store.sheets),
        "sheets": store.sheets,
        "active_sessions": session_store.count,
        "model": GROQ_MODEL,
        "groq_enabled": bool(USE_GROQ),
    }


@health_router.get("/api/meta")
async def meta():
    return {
        "api_version": APP_VERSION,
        "tool_names": [t["function"]["name"] for t in TOOLS],
    }


# ==========================================================
# DEBUG ROUTER (dev only)
# ==========================================================

debug_router = APIRouter(prefix="/api/debug", tags=["Debug"])


@debug_router.get("/routes")
async def list_routes(request: Request):
    out = []
    for r in request.app.routes:
        methods = sorted(getattr(r, "methods", []) or [])
        path = getattr(r, "path", None) or getattr(r, "path_format", None)
        name = getattr(r, "name", "")
        if path:
            out.append({"path": path, "methods": methods, "name": name})
    return {"count": len(out), "routes": out}
