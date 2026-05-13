import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class SessionState:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.session_id = f"{agent_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._history: list = []  # list of (user_msg, response) tuples
        self.created_at = datetime.now().isoformat()

    def add_turn(self, user_message: str, response: str) -> None:
        self._history.append((user_message, response))

    def get_context_summary(self, max_turns: int = 3) -> str:
        recent = self._history[-max_turns:]
        if not recent:
            return ""
        lines = []
        for i, (u, r) in enumerate(recent, 1):
            lines.append(f"Turn {i}: User asked: {u[:100]}")
            lines.append(f"  Response summary: {r[:150]}")
        return "Prior conversation context:\n" + "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "history": [{"user": u, "response": r} for u, r in self._history],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        s = cls(data["agent_id"])
        s.session_id = data.get("session_id", s.session_id)
        s.created_at = data.get("created_at", s.created_at)
        for turn in data.get("history", []):
            s._history.append((turn["user"], turn["response"]))
        return s

    @property
    def turn_count(self) -> int:
        return len(self._history)
