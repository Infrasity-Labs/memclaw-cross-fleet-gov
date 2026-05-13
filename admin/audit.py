"""
Session-local audit logger with optional file persistence.

The MemClaw /audit API endpoint currently returns 404. This module provides
an in-process audit log that captures every agent recall and response during
a session. Events are written to logs/session_audit.log as JSON lines.
"""
import json
import os
from datetime import datetime

_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
_LOG_DIR = os.path.normpath(os.path.join(_REPO_ROOT, "logs"))
_LOG_FILE = os.path.join(_LOG_DIR, "session_audit.log")


class AuditLogger:
    def __init__(self, log_to_file: bool = True, session_id: str = None):
        self.events = []
        self._log_to_file = log_to_file
        self._session_id = session_id or f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def record(self, agent_id: str, query: str, memories_by_fleet: dict, response: str):
        """Log one agent interaction.

        Args:
            agent_id: the agent that made the query
            query: the user message / query string
            memories_by_fleet: {fleet_id: [memory_text, ...]} — only authorized fleets
            response: the LLM-generated response text
        """
        event = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "agent_id": agent_id,
            "query": query[:120],
            "fleets_accessed": list(memories_by_fleet.keys()),
            "memory_counts": {f: len(m) for f, m in memories_by_fleet.items()},
            "total_memories": sum(len(m) for m in memories_by_fleet.values()),
            "response_preview": (response or "")[:100],
            "response_summary": (response or "")[:150],
            "session_id": self._session_id,
        }
        self.events.append(event)
        if self._log_to_file:
            self._write_to_file(event)

    def _write_to_file(self, event: dict) -> None:
        try:
            os.makedirs(_LOG_DIR, exist_ok=True)
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass  # never crash the agent loop for a logging failure

    def get_events(self):
        return list(self.events)

    def governance_summary(self, all_fleet_ids: list) -> dict:
        """Return per-agent access counts across all known fleets."""
        summary = {}
        for event in self.events:
            agent = event["agent_id"]
            if agent not in summary:
                summary[agent] = {f: 0 for f in all_fleet_ids}
                summary[agent]["_queries"] = 0
            summary[agent]["_queries"] += 1
            for fleet_id, count in event["memory_counts"].items():
                summary[agent][fleet_id] = summary[agent].get(fleet_id, 0) + count
        return summary
