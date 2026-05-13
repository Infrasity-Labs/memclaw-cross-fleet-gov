import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from state.session_state import SessionState

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "sessions.json")


def save_sessions(sessions: dict, path: str = None) -> None:
    target = path or _DEFAULT_PATH
    data = {agent_id: s.to_dict() for agent_id, s in sessions.items()}
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_sessions(path: str = None) -> dict:
    target = path or _DEFAULT_PATH
    if not os.path.exists(target):
        return {}
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {agent_id: SessionState.from_dict(s) for agent_id, s in data.items()}
