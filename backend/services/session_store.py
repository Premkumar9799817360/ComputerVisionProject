"""
In-memory session store for SightFlow.
"""

import uuid
import time
from typing import Dict, Optional
from backend.models.session import SessionData

_sessions: Dict[str, SessionData] = {}


def create_session(candidate_name: str) -> SessionData:
    session_id = str(uuid.uuid4())[:8].upper()
    session = SessionData(session_id=session_id, candidate_name=candidate_name)
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[SessionData]:
    return _sessions.get(session_id)


def update_session(session: SessionData) -> None:
    """Save updated session back to the store (replaces in-memory entry)."""
    _sessions[session.session_id] = session


def end_session(session_id: str) -> Optional[SessionData]:
    session = _sessions.get(session_id)
    if session:
        session.end_time = time.time()
    return session


def list_sessions() -> list:
    return [
        {
            "session_id":    s.session_id,
            "candidate_name": s.candidate_name,
            "risk_score":    s.get_risk_score(),
            "risk_level":    s.get_risk_level(),
            "active":        s.end_time is None,
        }
        for s in _sessions.values()
    ]


def delete_session(session_id: str):
    _sessions.pop(session_id, None)