"""
Demo Moment 7 — Conflict of Interest: The HealthSystem Deal.

Demonstrates why fleet boundaries matter in practice.

Scenario:
  The HealthSystem deal is a $3.6M renewal. The sales team is ready to close.
  Legal has placed a compliance hold — a HIPAA BAA is not yet executed and
  contract signing is blocked. Neither agent knows what the other knows.

  Turn 1 — Sales:  "Is the HealthSystem deal ready to close?"
  Turn 2 — Legal:  "Can HealthSystem proceed with contract execution?"
  Turn 3 — Admin:  "What is the full governance picture for HealthSystem?"

Expected:
  Sales sees: renewal status + sales tactics. Recommends closing.
  Legal sees: renewal status + HIPAA hold. Says contract is blocked.
  Admin sees: ALL THREE fleets. Surfaces the conflict explicitly.

The conflict is not visible to any single-fleet agent. Only the Admin Agent
can see both sides — and it is the only agent that can flag the risk before
a premature deal closure creates a compliance violation.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Windows terminals default to cp1252 which can't render LLM emoji/Unicode output.
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich import box

from agents.sales_agent import SalesAgent
from agents.legal_agent import LegalAgent
from agents.admin_agent import AdminAgent
from admin.audit import AuditLogger
from config import (
    FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL,
    AGENT_SALES, AGENT_LEGAL, AGENT_ADMIN,
)

console = Console()

FLEET_STYLES = {
    FLEET_ORG_SHARED: ("cyan",   "fleet-org-shared"),
    FLEET_SALES:      ("yellow", "fleet-sales"),
    FLEET_LEGAL:      ("red",    "fleet-legal"),
}

SCENARIOS = [
    {
        "agent": "sales",
        "query": "Is the HealthSystem deal ready to close?",
        "recall_query": "HealthSystem deal close renewal status negotiation discount",
    },
    {
        "agent": "legal",
        "query": "Can HealthSystem proceed with contract execution?",
        "recall_query": "HealthSystem HIPAA BAA hold contract compliance execution",
    },
    {
        "agent": "admin",
        "query": "What is the full governance picture for HealthSystem?",
        "recall_query": "HealthSystem HIPAA BAA compliance contract execution blocked renewal",
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


def _run_turn(agent, turn_num: int, query: str, agent_label: str, agent_style: str, recall_query: str = None):
    gov = agent.get_governance_summary()

    allowed = ", ".join(gov["allowed_fleets"])
    blocked_fleets = gov["blocked_fleets"]
    blocked = ", ".join(blocked_fleets) if blocked_fleets else "[dim]none (cross-fleet access)[/dim]"

    console.print()
    console.rule(f"[{agent_style}]Turn {turn_num} — {agent_label}[/]")
    console.print()

    console.print(f"  [bold]Query:[/bold] \"{query}\"")
    console.print(f"  [dim]Authorized fleets:[/dim] [{agent_style}]{allowed}[/]")
    if blocked_fleets:
        console.print(f"  [dim]Blocked fleets:   [/dim] [red]{blocked}[/]")
    else:
        console.print(f"  [dim]Blocked fleets:   [/dim] {blocked}")
    console.print()

    response_text = None
    memories_by_fleet = {}

    try:
        result = agent.ask(query, recall_query=recall_query)
        memories_by_fleet = result["memories_by_fleet"]
        total = result["total_memories"]
        response_text = result["response"]

        console.print(_render_memory_summary(memories_by_fleet))
        console.print(f"  [dim]Total memories injected into LLM context: {total}[/dim]")
        console.print()

        console.print(
            Panel(
                response_text,
                title=f"[{agent_style}]{agent_label} Response[/]",
                border_style=agent_style,
                padding=(1, 2),
            )
        )
    except RuntimeError as exc:
        if "AISA_API_KEY" in str(exc) or "model" in str(exc).lower():
            console.print(
                Panel(
                    f"[red]{exc}[/red]",
                    title="[red]LLM Not Configured[/red]",
                    border_style="red",
                )
            )
        else:
            raise

    return response_text, memories_by_fleet


def _render_conflict_summary(sales_response, legal_response, admin_response):
    console.print()
    console.rule("[bold white]Conflict Detection Summary[/bold white]")
    console.print()

    console.print(
        Panel(
            "[bold yellow]Sales Agent[/bold yellow]  (fleet-org-shared + fleet-sales only)\n"
            + (f'  "{sales_response[:120]}..."' if sales_response and len(sales_response) > 120 else f'  "{sales_response}"' if sales_response else "  [dim](LLM not available)[/dim]")
            + "\n\n"
            "[bold red]Legal Agent[/bold red]  (fleet-org-shared + fleet-legal only)\n"
            + (f'  "{legal_response[:120]}..."' if legal_response and len(legal_response) > 120 else f'  "{legal_response}"' if legal_response else "  [dim](LLM not available)[/dim]")
            + "\n\n"
            "[bold magenta]Admin Agent[/bold magenta]  (all three fleets)\n"
            + (f'  "{admin_response[:120]}..."' if admin_response and len(admin_response) > 120 else f'  "{admin_response}"' if admin_response else "  [dim](LLM not available)[/dim]"),
            title="[bold white]HealthSystem Deal — Agent Views[/bold white]",
            border_style="white",
            padding=(1, 2),
        )
    )

    console.print()
    console.print(
        "  [bold]Why this matters:[/bold]\n"
        "  Sales is ready to close. Legal has a hard compliance block.\n"
        "  Without cross-fleet visibility, neither agent knows about the other's position.\n"
        "  A premature deal closure would create a [bold red]HIPAA violation[/bold red].\n"
        "  Only the Admin Agent can see both sides — and only it can flag the conflict.\n"
    )


def _render_boundary_proof(events: list):
    console.print()
    console.rule("[bold white]Boundary Enforcement Proof[/bold white]")
    console.print()

    sales_accessed_legal = any(
        FLEET_LEGAL in event["fleets_accessed"] and event["agent_id"] == AGENT_SALES
        for event in events
    )
    legal_accessed_sales = any(
        FLEET_SALES in event["fleets_accessed"] and event["agent_id"] == AGENT_LEGAL
        for event in events
    )
    admin_accessed_all = any(
        FLEET_LEGAL in event["fleets_accessed"]
        and FLEET_SALES in event["fleets_accessed"]
        and event["agent_id"] == AGENT_ADMIN
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

    if admin_accessed_all:
        console.print(
            "  [bold green]PASS[/bold green]  "
            "[magenta]admin-agent[/magenta] accessed [yellow]fleet-sales[/yellow] "
            "+ [red]fleet-legal[/red] — cross-fleet visibility confirmed"
        )
    else:
        console.print(
            "  [bold yellow]INFO[/bold yellow]  "
            "[magenta]admin-agent[/magenta] cross-fleet recall: "
            + ("no events recorded (LLM may not have been configured)" if not events else "partial")
        )

    console.print()
    console.print(
        "  [dim]The boundary is structural. Sales and Legal recall callables are\n"
        "  fixed at agent construction — no user input can expand fleet access.\n"
        "  The Admin Agent is the only agent whose recall map includes all three fleets.[/dim]"
    )
    console.print()


def main():
    audit = AuditLogger()

    sales = SalesAgent(audit_logger=audit)
    legal = LegalAgent(audit_logger=audit)
    admin = AdminAgent(audit_logger=audit)

    console.print()
    console.rule("[bold white]Demo Moment 7: Conflict of Interest — The HealthSystem Deal[/bold white]")
    console.print()
    console.print(
        "  [bold]Scenario:[/bold] A $3.6M HealthSystem deal appears ready to close.\n"
        "  Sales is pushing to sign. Legal has an active HIPAA compliance hold.\n"
        "  Neither agent knows what the other knows.\n"
        "  [bold]Question:[/bold] Who surfaces the conflict?\n"
    )

    agent_map = {
        "sales": (sales, "Sales Agent", "yellow"),
        "legal": (legal, "Legal Agent", "red"),
        "admin": (admin, "Admin Agent", "magenta"),
    }

    responses = {}
    for i, scenario in enumerate(SCENARIOS, start=1):
        key = scenario["agent"]
        agent_obj, agent_label, agent_style = agent_map[key]
        response_text, _ = _run_turn(agent_obj, i, scenario["query"], agent_label, agent_style, recall_query=scenario.get("recall_query"))
        responses[key] = response_text

    _render_conflict_summary(
        responses.get("sales"),
        responses.get("legal"),
        responses.get("admin"),
    )

    events = audit.get_events()
    _render_boundary_proof(events)


if __name__ == "__main__":
    main()
