"""
main.py — NamanDarshan FastAPI application entry point.

Registers all routers and mounts the frontend.
Run with:
    python main.py
    uvicorn main:app --reload --port 8000
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import (
    APP_TITLE, APP_VERSION, APP_DESC,
    CORS_ORIGINS, FRONTEND_DIR, HOST, PORT, RELOAD,
)
from routes import agent_router, legacy_router, data_router, excel_router, health_router, debug_router

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("nd.main")

# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = APP_TITLE,
    version     = APP_VERSION,
    description = APP_DESC,
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ── Middleware ────────────────────────────────────────────────────────────
_allow_all_origins = len(CORS_ORIGINS) == 1 and CORS_ORIGINS[0].strip() == "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # Starlette cannot combine `allow_credentials=True` with `allow_origins=["*"]`.
    # We don't use cookie auth, so when wildcard is requested we disable credentials.
    allow_credentials=not _allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_cache_for_frontend(request, call_next):
    response = await call_next(request)
    path = request.url.path or ""
    if path == "/" or path.startswith("/assets/"):
        response.headers["Cache-Control"] = "no-store"
    return response

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(agent_router)
app.include_router(legacy_router)
app.include_router(data_router)
app.include_router(excel_router)
app.include_router(health_router)
app.include_router(debug_router)

# ── Frontend static files ─────────────────────────────────────────────────
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(full_path: str):
        file = FRONTEND_DIR / full_path
        if file.exists() and file.is_file():
            return FileResponse(str(file))
        return FileResponse(str(FRONTEND_DIR / "index.html"))

else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "service": APP_TITLE,
            "version": APP_VERSION,
            "docs":    "/docs",
            "note":    "Frontend not found. Place it in /frontend/",
        }

# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    log.info("Starting %s v%s on http://%s:%s", APP_TITLE, APP_VERSION, HOST, PORT)
    uvicorn.run("main:app", host=HOST, port=PORT, reload=RELOAD)
