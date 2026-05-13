import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

GOVERNANCE_ACCESS_GRANTED = "governance.access_granted"
GOVERNANCE_ACCESS_BLOCKED = "governance.access_blocked"
AUDIT_EVENT_RECORDED = "audit.event_recorded"
RECALL_COMPLETE = "recall.complete"
CONFLICT_DETECTED = "conflict.detected"


class EventBus:
    def __init__(self):
        self._handlers: dict = {}

    def subscribe(self, event_type: str, handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event_type: str, payload: dict) -> None:
        for handler in self._handlers.get(event_type, []):
            try:
                handler(payload)
            except Exception:
                pass  # handlers must never crash the publisher

    def unsubscribe_all(self, event_type: str) -> None:
        self._handlers.pop(event_type, None)
