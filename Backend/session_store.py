"""
session_store.py — In-memory session store for NamanDarshan Ops Agent.
Safe version with exported Session + session_store
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List

from config import SESSION_TTL_MIN

log = logging.getLogger("nd.sessions")


# ==========================================================
# SESSION MODEL
# ==========================================================

class Session:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()

        self.messages: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.action_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------

    def touch(self):
        self.last_active = datetime.utcnow()

    # ------------------------------------------------------

    def add_action(self, action_type: str, detail: Any):
        self.action_log.append(
            {
                "time": datetime.utcnow().isoformat(),
                "type": action_type,
                "detail": detail,
            }
        )

    # ------------------------------------------------------

    def reset(self):
        self.messages.clear()
        self.action_log.clear()
        self.touch()

    # ------------------------------------------------------

    def is_expired(self) -> bool:
        expiry = self.last_active + timedelta(minutes=SESSION_TTL_MIN)
        return datetime.utcnow() > expiry

    # ------------------------------------------------------

    def to_info(self) -> dict:
        return {
            "session_id": self.session_id,
            "context": self.context,
            "message_count": len(
                [m for m in self.messages if m.get("role") == "user"]
            ),
            "action_log": self.action_log,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
        }


# ==========================================================
# SESSION STORE
# ==========================================================

class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    # ------------------------------------------------------

    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            session.touch()
            return session

        new_id = session_id or str(uuid.uuid4())
        session = Session(new_id)
        self._sessions[new_id] = session

        log.info("Session created: %s", new_id)
        return session

    # ------------------------------------------------------

    def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    # ------------------------------------------------------

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    # ------------------------------------------------------

    def purge_expired(self):
        expired_ids = []

        for sid, session in self._sessions.items():
            if session.is_expired():
                expired_ids.append(sid)

        for sid in expired_ids:
            del self._sessions[sid]

    # ------------------------------------------------------

    def list_all(self) -> list:
        output = []

        for sid, session in self._sessions.items():
            output.append(
                {
                    "session_id": sid,
                    "last_active": session.last_active.isoformat(),
                    "messages": len(session.messages),
                }
            )

        return output

    # ------------------------------------------------------

    @property
    def count(self) -> int:
        return len(self._sessions)


# ==========================================================
# GLOBAL INSTANCE
# ==========================================================

session_store = SessionStore()