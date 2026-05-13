"""
Enterprise Governance Runtime — interactive agent console.

Run:  python app.py

Commands at the query prompt:
  exit   — save sessions and exit
  switch — return to agent selection
  reset  — clear the current agent's session history
"""
import sys
import os

# Windows terminals default to cp1252 which can't render LLM emoji/Unicode.
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from runtime.governance_engine import GovernanceEngine
from runtime.session_manager import SessionManager
from runtime.terminal_ui import (
    render_governance_header,
    render_memory_table,
    render_conflict_findings,
    render_agent_selection_menu,
)
from runtime.live_audit_monitor import LiveAuditMonitor
from admin.audit import AuditLogger
from admin.conflict_detector import ConflictDetector
from agents.sales_agent import SalesAgent
from agents.legal_agent import LegalAgent
from agents.admin_agent import AdminAgent
from config import AGENT_SALES, AGENT_LEGAL, AGENT_ADMIN

console = Console()

_AGENT_MENU_MAP = {
    "1": AGENT_SALES,
    "2": AGENT_LEGAL,
    "3": AGENT_ADMIN,
}

_AGENT_STYLES = {
    AGENT_SALES:  ("Sales Agent",  "yellow"),
    AGENT_LEGAL:  ("Legal Agent",  "red"),
    AGENT_ADMIN:  ("Admin Agent",  "magenta"),
}


def _print_header():
    console.print()
    console.print(
        Panel(
            "[bold white]Enterprise Multi-Agent Governance Runtime[/bold white]\n"
            "[dim]Governance enforced before reasoning. "
            "The LLM never receives unauthorized memories.[/dim]",
            border_style="white",
            padding=(0, 2),
        )
    )


def _pick_agent(engine: GovernanceEngine) -> str:
    render_agent_selection_menu(engine, console=console)
    while True:
        try:
            choice = input("  Select agent [1/2/3]: ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if choice in _AGENT_MENU_MAP:
            return _AGENT_MENU_MAP[choice]
        console.print("  [dim]Enter 1, 2, or 3.[/dim]")


def _run_session(agent, agent_id: str, engine: GovernanceEngine,
                 session_mgr: SessionManager, monitor: LiveAuditMonitor,
                 conflict_detector: ConflictDetector):
    label, color = _AGENT_STYLES.get(agent_id, (agent_id, "white"))
    console.print()
    render_governance_header(engine, agent_id, console=console)
    console.print()

    while True:
        try:
            user_input = input(f"  [{label}] Query (exit / switch / reset): ").strip()
        except (EOFError, KeyboardInterrupt):
            return "exit"

        if not user_input:
            continue
        cmd = user_input.lower()
        if cmd == "exit":
            return "exit"
        if cmd == "switch":
            return "switch"
        if cmd == "reset":
            session_mgr.reset(agent_id)
            console.print("  [dim]Session reset.[/dim]")
            continue

        session = session_mgr.get_or_create(agent_id)
        context_prefix = session.get_context_summary(max_turns=3)
        full_message = (context_prefix + "\n" + user_input) if context_prefix else user_input

        console.print()
        try:
            result = agent.ask(user_message=full_message, recall_query=user_input)
        except RuntimeError as exc:
            console.print(
                Panel(
                    f"[red]{exc}[/red]",
                    title="[red]LLM Not Configured[/red]",
                    border_style="red",
                )
            )
            continue

        session.add_turn(user_input, result["response"])

        # Memory recall summary
        console.print(render_memory_table(result["memories_by_fleet"]))
        console.print(f"  [dim]Total memories in context: {result['total_memories']}[/dim]")
        console.print()

        # Structural conflict detection (Admin Agent only — or any agent with both private fleets)
        findings = conflict_detector.detect(result["memories_by_fleet"])
        conflict_panel = render_conflict_findings(findings)
        if conflict_panel:
            console.print(conflict_panel)
            console.print()

        # LLM response
        console.print(
            Panel(
                result["response"] or "[dim](no response)[/dim]",
                title=f"[{color}]{label} Response (Turn {session.turn_count})[/]",
                border_style=color,
                padding=(1, 2),
            )
        )

        # Live audit event
        monitor.display_latest()
        console.print()


def main():
    _print_header()

    engine = GovernanceEngine()
    session_mgr = SessionManager()
    audit = AuditLogger()
    monitor = LiveAuditMonitor(audit, console=console)
    conflict_detector = ConflictDetector()

    # Instantiate all agents up front — share engine and audit logger
    agents = {
        AGENT_SALES: SalesAgent(audit_logger=audit, engine=engine),
        AGENT_LEGAL: LegalAgent(audit_logger=audit, engine=engine),
        AGENT_ADMIN: AdminAgent(audit_logger=audit, engine=engine),
    }

    try:
        while True:
            agent_id = _pick_agent(engine)
            if agent_id is None:
                break

            outcome = _run_session(
                agents[agent_id], agent_id, engine,
                session_mgr, monitor, conflict_detector,
            )

            if outcome == "exit":
                break
            # "switch" → loop back to agent selection

    except Exception as exc:
        console.print(f"\n[red]Unexpected error: {exc}[/red]")
    finally:
        session_mgr.save_all()
        console.print()
        console.print("[dim]Sessions saved. Goodbye.[/dim]")
        console.print()


if __name__ == "__main__":
    main()
