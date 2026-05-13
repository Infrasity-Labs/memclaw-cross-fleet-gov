"""
Live audit monitor — renders new governance events after each agent turn.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from runtime.terminal_ui import render_audit_event


class LiveAuditMonitor:
    """Wraps AuditLogger and displays new events after each agent turn.

    Uses a _last_seen pointer so only events recorded since the previous
    display_latest() call are printed.
    """

    def __init__(self, audit_logger, console: Console = None):
        self._audit = audit_logger
        self._console = console or Console()
        self._last_seen = 0

    def display_latest(self) -> None:
        events = self._audit.get_events()
        new_events = events[self._last_seen:]
        for event in new_events:
            self._console.print(
                f"  [dim][Audit] {render_audit_event(event)}[/dim]"
            )
        self._last_seen = len(events)
