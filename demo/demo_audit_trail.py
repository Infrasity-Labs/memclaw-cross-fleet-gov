"""
Demo Moment 6 — Governance Audit Trail.

Runs the same 3-turn scenario as demo_agent_loop.py, captures every
memory recall event in the session audit logger, then displays a
governance report: who queried what, which fleets were accessed,
and proof that no cross-fleet data leaked.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box

from agents.sales_agent import SalesAgent
from agents.legal_agent import LegalAgent
from admin.audit import AuditLogger
from config import FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL, AGENT_SALES, AGENT_LEGAL

console = Console()

ALL_FLEETS = [FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL]

FLEET_STYLES = {
    FLEET_ORG_SHARED: "cyan",
    FLEET_SALES:      "yellow",
    FLEET_LEGAL:      "red",
}

SCENARIOS = [
    ("sales", "What's the status on Client X? Can we offer a discount?"),
    ("legal", "Is Client X approved for renewal?"),
    ("sales", "What compliance risks exist for Client X?"),
]


def _run_scenario(audit: AuditLogger):
    """Run all turns silently (no LLM output to console), just collect audit events."""
    sales = SalesAgent(audit_logger=audit)
    legal = LegalAgent(audit_logger=audit)
    agents = {"sales": sales, "legal": legal}

    console.print("[dim]Running scenario turns...[/dim]")
    for which, query in SCENARIOS:
        agent = agents[which]
        label = "Sales Agent" if which == "sales" else "Legal Agent"
        console.print(f"  [dim]  {label}: \"{query[:60]}...\"[/dim]")
        try:
            agent.ask(query)
        except RuntimeError as exc:
            if "AISA_API_KEY" in str(exc):
                console.print(f"  [yellow]  (LLM skipped — {exc})[/yellow]")
            else:
                raise
    console.print()


def _render_event_table(events: list):
    table = Table(
        title="Governance Audit Trail",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Turn", justify="center", min_width=4)
    table.add_column("Time", min_width=19)
    table.add_column("Agent", min_width=16)
    table.add_column("Query", min_width=38)
    table.add_column("fleet-org-shared", justify="center", min_width=16)
    table.add_column("fleet-sales", justify="center", min_width=12)
    table.add_column("fleet-legal", justify="center", min_width=12)

    for idx, event in enumerate(events, start=1):
        counts = event["memory_counts"]

        def cell(fleet_id):
            n = counts.get(fleet_id, 0)
            if n == 0:
                return "[dim]-[/dim]"
            style = FLEET_STYLES.get(fleet_id, "white")
            return f"[{style}]{n}[/]"

        table.add_row(
            str(idx),
            event["timestamp"],
            event["agent_id"],
            event["query"][:40] + ("..." if len(event["query"]) > 40 else ""),
            cell(FLEET_ORG_SHARED),
            cell(FLEET_SALES),
            cell(FLEET_LEGAL),
        )

    console.print(table)


def _render_boundary_proof(events: list):
    console.print()
    console.rule("[bold white]Boundary Enforcement Proof[/bold white]")
    console.print()

    sales_accessed_legal = any(
        FLEET_LEGAL in event["fleets_accessed"]
        and event["agent_id"] == AGENT_SALES
        for event in events
    )
    legal_accessed_sales = any(
        FLEET_SALES in event["fleets_accessed"]
        and event["agent_id"] == AGENT_LEGAL
        for event in events
    )

    if not sales_accessed_legal:
        console.print(
            "  [bold green]PASS[/bold green]  "
            "[yellow]sales-agent-1[/yellow] never accessed [red]fleet-legal[/red]"
        )
    else:
        console.print(
            "  [bold red]FAIL[/bold red]  "
            "[yellow]sales-agent-1[/yellow] accessed [red]fleet-legal[/red] — BOUNDARY BREACH"
        )

    if not legal_accessed_sales:
        console.print(
            "  [bold green]PASS[/bold green]  "
            "[red]legal-agent-1[/red] never accessed [yellow]fleet-sales[/yellow]"
        )
    else:
        console.print(
            "  [bold red]FAIL[/bold red]  "
            "[red]legal-agent-1[/red] accessed [yellow]fleet-sales[/yellow] — BOUNDARY BREACH"
        )

    console.print()
    console.print(
        "  [dim]Governance is enforced at retrieval time. Fleet-scoped recall\n"
        "  ensures the LLM never constructs a prompt with unauthorized memories.[/dim]"
    )
    console.print()


def main():
    audit = AuditLogger()

    console.print()
    console.rule("[bold white]Demo Moment 6: Governance Audit Trail[/bold white]")
    console.print()

    _run_scenario(audit)

    events = audit.get_events()

    if not events:
        console.print(
            Panel(
                "[yellow]No events recorded.[/yellow]\n"
                "This may be because AISA_API_KEY is not configured.\n"
                "The recall events are still captured even without LLM responses.",
                title="[yellow]No Events[/yellow]",
                border_style="yellow",
            )
        )
        return

    _render_event_table(events)
    _render_boundary_proof(events)


if __name__ == "__main__":
    main()
