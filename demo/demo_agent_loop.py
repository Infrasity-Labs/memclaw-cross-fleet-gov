"""
Demo Moment 5 — Flagship Agent Loop.

Runs three governed reasoning turns across Sales and Legal agents.
Each turn shows: authorized fleets, memories recalled, and the LLM response.
The governance boundary is enforced before every LLM call.

Scenario:
  Turn 1 — Sales:  "What's the status on Client X? Can we offer a discount?"
  Turn 2 — Legal:  "Is Client X approved for renewal?"
  Turn 3 — Sales:  "What compliance risks exist for Client X?"

Expected:
  Sales sees org context + sales tactics. Never sees GDPR flag.
  Legal sees org context + legal compliance. Never sees discount ceiling.
  Turn 3 demonstrates scoped ignorance: Sales honestly cannot answer compliance questions.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich import box

from agents.sales_agent import SalesAgent
from agents.legal_agent import LegalAgent
from admin.audit import AuditLogger
from config import FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL

console = Console()

FLEET_STYLES = {
    FLEET_ORG_SHARED: ("cyan",   "fleet-org-shared"),
    FLEET_SALES:      ("yellow", "fleet-sales"),
    FLEET_LEGAL:      ("red",    "fleet-legal"),
}

SCENARIOS = [
    {
        "agent": "sales",
        "query": "What's the status on Client X? Can we offer a discount?",
    },
    {
        "agent": "legal",
        "query": "Is Client X approved for renewal?",
    },
    {
        "agent": "sales",
        "query": "What compliance risks exist for Client X?",
    },
]


def _render_memory_summary(memories_by_fleet: dict):
    table = Table(box=box.SIMPLE, show_header=True, header_style="dim")
    table.add_column("Fleet", style="dim", min_width=20)
    table.add_column("Memories recalled", justify="right", min_width=6)

    for fleet_id, texts in memories_by_fleet.items():
        style, label = FLEET_STYLES.get(fleet_id, ("white", fleet_id))
        count = len(texts)
        count_str = f"[bold green]{count}[/]" if count > 0 else "[dim]0[/dim]"
        table.add_row(f"[{style}]{label}[/]", count_str)

    return table


def _run_turn(agent, turn_num: int, query: str, agent_label: str, agent_style: str):
    gov = agent.get_governance_summary()

    allowed = ", ".join(gov["allowed_fleets"])
    blocked = ", ".join(gov["blocked_fleets"])

    console.print()
    console.rule(f"[{agent_style}]Turn {turn_num} — {agent_label}[/]")
    console.print()

    console.print(f"  [bold]Query:[/bold] \"{query}\"")
    console.print(f"  [dim]Authorized fleets:[/dim] [{agent_style}]{allowed}[/]")
    console.print(f"  [dim]Blocked fleets:   [/dim] [red]{blocked}[/]")
    console.print()

    try:
        result = agent.ask(query)
    except RuntimeError as exc:
        if "AISA_API_KEY" in str(exc):
            console.print(
                Panel(
                    f"[red]{exc}[/red]",
                    title="[red]LLM Not Configured[/red]",
                    border_style="red",
                )
            )
            return

        raise

    memories_by_fleet = result["memories_by_fleet"]
    total = result["total_memories"]

    console.print(_render_memory_summary(memories_by_fleet))
    console.print(f"  [dim]Total memories injected into LLM context: {total}[/dim]")
    console.print()

    console.print(
        Panel(
            result["response"],
            title=f"[{agent_style}]{agent_label} Response[/]",
            border_style=agent_style,
            padding=(1, 2),
        )
    )


def main():
    audit = AuditLogger()

    sales = SalesAgent(audit_logger=audit)
    legal = LegalAgent(audit_logger=audit)

    console.print()
    console.rule("[bold white]Demo Moment 5: Governed Agent Reasoning Loop[/bold white]")
    console.print()
    console.print(
        "  [bold]Principle:[/bold] Governance is enforced [italic]before[/italic] reasoning.\n"
        "  The LLM receives only memories from authorized fleets.\n"
        "  Blocked fleet data is never constructed into the prompt.\n"
    )

    agents = {"sales": (sales, "Sales Agent", "yellow"), "legal": (legal, "Legal Agent", "red")}

    for i, scenario in enumerate(SCENARIOS, start=1):
        agent_obj, agent_label, agent_style = agents[scenario["agent"]]
        _run_turn(agent_obj, i, scenario["query"], agent_label, agent_style)

    console.print()
    console.rule("[bold white]Session Governance Summary[/bold white]")
    console.print()

    events = audit.get_events()
    if events:
        summary_table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        summary_table.add_column("Turn", justify="center", min_width=4)
        summary_table.add_column("Agent", min_width=16)
        summary_table.add_column("Query", min_width=40)
        summary_table.add_column("Fleets", min_width=30)
        summary_table.add_column("Memories", justify="right", min_width=8)

        for idx, event in enumerate(events, start=1):
            fleets_str = ", ".join(
                f"{f}({c})" for f, c in event["memory_counts"].items()
            )
            summary_table.add_row(
                str(idx),
                event["agent_id"],
                event["query"][:45] + ("..." if len(event["query"]) > 45 else ""),
                fleets_str or "-",
                str(event["total_memories"]),
            )

        console.print(summary_table)
        console.print()
        console.print(
            "  [dim]Note: fleet-legal never appears in sales-agent events.[/dim]\n"
            "  [dim]Note: fleet-sales never appears in legal-agent events.[/dim]\n"
        )
    else:
        console.print("  [dim](No events recorded — LLM may not have been configured)[/dim]\n")

    console.print()


if __name__ == "__main__":
    main()
