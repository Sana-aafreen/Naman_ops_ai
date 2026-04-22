"""
config.py — Central configuration for NamanDarshan backend.
All env vars, paths, and constants live here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load Backend/.env if present (local dev convenience)
load_dotenv(Path(__file__).resolve().parent / ".env")

# ── Paths ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Frontend folder name is case-sensitive on Linux.
# Support either `Frontend/` or `frontend/` (or override via env).
_frontend_env = os.getenv("FRONTEND_DIR")
if _frontend_env:
    FRONTEND_DIR = Path(_frontend_env).expanduser().resolve()
else:
    FRONTEND_DIR = BASE_DIR / "Frontend"
    if not FRONTEND_DIR.exists():
        FRONTEND_DIR = BASE_DIR / "frontend"

EXCEL_PATH   = DATA_DIR / "namandarshan_data.xlsx"

# ── Groq ──────────────────────────────────────────────────────────────────
GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL       = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.5"))
GROQ_MAX_TOKENS  = int(os.getenv("GROQ_MAX_TOKENS", "800"))

NAMANDARSHAN_BASE_URL = os.getenv("NAMANDARSHAN_BASE_URL", "https://namandarshan.com").rstrip("/")
ENABLE_NAMANDARSHAN_SCRAPE = os.getenv("ENABLE_NAMANDARSHAN_SCRAPE", "true").lower() == "true"
SCRAPE_TIMEOUT_SEC = float(os.getenv("SCRAPE_TIMEOUT_SEC", "12"))
SCRAPE_MAX_PAGES = int(os.getenv("SCRAPE_MAX_PAGES", "4"))
SCRAPE_MAX_CHARS = int(os.getenv("SCRAPE_MAX_CHARS", "6000"))

# ── Agent ─────────────────────────────────────────────────────────────────
MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "5"))
SESSION_TTL_MIN = int(os.getenv("SESSION_TTL_MIN", "60"))

# ── Server ────────────────────────────────────────────────────────────────
HOST        = os.getenv("HOST", "0.0.0.0")
PORT        = int(os.getenv("PORT", "8000"))
RELOAD      = os.getenv("RELOAD", "true").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# ── App Meta ──────────────────────────────────────────────────────────────
APP_TITLE   = "NamanDarshan Ops API"
APP_VERSION = "2.0.0"
APP_DESC    = "Agentic temple operations assistant — Darshan, Pandits, Hotels, Cabs"
