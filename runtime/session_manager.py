import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from state.session_state import SessionState
from state.persistence import save_sessions, load_sessions


class SessionManager:
    """Per-agent stateful session tracking with optional persistence.

    Sessions are isolated by agent_id — no cross-agent history ever leaks.
    """

    def __init__(self, persist_path: str = None):
        self._path = persist_path
        self._sessions: dict = {}
        try:
            kwargs = {"path": self._path} if self._path else {}
            self._sessions.update(load_sessions(**kwargs))
        except Exception:
            pass  # corrupt or missing file — start fresh

    def get_or_create(self, agent_id: str) -> SessionState:
        if agent_id not in self._sessions:
            self._sessions[agent_id] = SessionState(agent_id)
        return self._sessions[agent_id]

    def save_all(self) -> None:
        try:
            kwargs = {"path": self._path} if self._path else {}
            save_sessions(self._sessions, **kwargs)
        except Exception:
            pass  # never crash the runtime on a save failure

    def reset(self, agent_id: str) -> None:
        self._sessions[agent_id] = SessionState(agent_id)
