"""
Shared Rich terminal UI primitives for the governance runtime.

All functions are display-only. No business logic lives here.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

_console = Console()

# Fleet color palette — consistent with existing demo scripts
_FLEET_STYLES = {
    "fleet-org-shared": ("cyan",    "fleet-org-shared"),
    "fleet-sales":      ("yellow",  "fleet-sales"),
    "fleet-legal":      ("red",     "fleet-legal"),
}

_AGENT_LABELS = {
    "sales-agent-1": ("Sales Agent",  "yellow"),
    "legal-agent-1": ("Legal Agent",  "red"),
    "admin-agent":   ("Admin Agent",  "magenta"),
}

_SEVERITY_BORDER = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "white"}


def render_governance_header(engine, agent_id: str, console: Console = None) -> None:
    c = console or _console
    label, color = _AGENT_LABELS.get(agent_id, (agent_id, "white"))
    authorized = engine.get_authorized_fleets(agent_id)
    blocked = engine.get_blocked_fleets(agent_id)

    auth_str = "  ".join(
        f"[{_FLEET_STYLES.get(f, ('white', f))[0]}]✓ {f}[/]" for f in authorized
    )
    block_str = (
        "  ".join(f"[red]✗ {f}[/]" for f in blocked)
        if blocked else "[dim]none (cross-fleet access)[/dim]"
    )

    policy_path = getattr(engine, "policy_path", "policies/fleet_access.yaml")
    policy_short = os.path.basename(os.path.dirname(policy_path)) + "/" + os.path.basename(policy_path)

    body = (
        f"[bold]Agent:[/bold]   [{color}]{label}[/] [dim]({agent_id})[/dim]\n"
        f"[bold]Policy:[/bold]  [dim]{policy_short}[/dim]  [green]ACTIVE[/green]\n"
        f"[bold]Access:[/bold]  {auth_str}\n"
        f"[bold]Blocked:[/bold] {block_str}"
    )
    c.print(Panel(body, title="[bold white]Governance Engine[/bold white]", border_style=color, padding=(0, 2)))


def render_memory_table(memories_by_fleet: dict, console: Console = None) -> Table:
    table = Table(box=box.SIMPLE, show_header=True, header_style="dim")
    table.add_column("Fleet", style="dim", min_width=22)
    table.add_column("Memories recalled", justify="right", min_width=6)

    for fleet_id, texts in memories_by_fleet.items():
        style, label = _FLEET_STYLES.get(fleet_id, ("white", fleet_id))
        count = len(texts)
        count_str = f"[bold green]{count}[/]" if count > 0 else "[dim]0[/dim]"
        table.add_row(f"[{style}]{label}[/]", count_str)

    return table


def render_conflict_findings(findings: list, console: Console = None):
    if not findings:
        return None

    top_severity = "HIGH" if any(f["severity"] == "HIGH" for f in findings) else \
                   "MEDIUM" if any(f["severity"] == "MEDIUM" for f in findings) else "LOW"
    border = _SEVERITY_BORDER.get(top_severity, "white")

    lines = []
    for f in findings:
        sev_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "white"}.get(f["severity"], "white")
        lines.append(
            f"[{sev_color}][bold]{f['rule_id']}[/bold][/] ({f['severity']}) — {f['description']}"
        )
        lines.append(f"  [dim]Sales signal:[/dim]  [yellow]{f['sales_signal']}[/yellow]")
        lines.append(f"  [dim]Legal signal:[/dim]  [red]{f['legal_signal']}[/red]")

    body = "\n".join(lines)
    return Panel(
        body,
        title=f"[bold red]GOVERNANCE CONFLICT — {len(findings)} rule(s) triggered[/bold red]",
        border_style=border,
        padding=(0, 2),
    )


def render_audit_event(event: dict) -> str:
    ts = event.get("timestamp", "")
    if "T" in ts:
        ts = ts.split("T")[1]  # HH:MM:SS
    agent = event.get("agent_id", "?")
    fleets = event.get("fleets_accessed", [])
    fleet_short = "+".join(
        f.replace("fleet-", "") for f in fleets
    ) or "none"
    total = event.get("total_memories", 0)
    return f"[{ts}] {agent} | fleets: {fleet_short} | memories: {total}"


def render_agent_selection_menu(engine, console: Console = None) -> None:
    c = console or _console
    c.print()
    c.rule("[bold white]Enterprise Governance Runtime[/bold white]")
    c.print()
    c.print("  [bold]Select Agent:[/bold]")
    c.print()

    agents = engine.list_agents()
    menu_order = ["sales-agent-1", "legal-agent-1", "admin-agent"]
    ordered = [a for a in menu_order if a in agents] + [a for a in agents if a not in menu_order]

    for i, agent_id in enumerate(ordered, start=1):
        label, color = _AGENT_LABELS.get(agent_id, (agent_id, "white"))
        authorized = engine.get_authorized_fleets(agent_id)
        blocked = engine.get_blocked_fleets(agent_id)

        if not blocked:
            scope = "[magenta]ALL fleets — cross-fleet observer[/magenta]"
        else:
            auth_short = ", ".join(authorized)
            block_short = ", ".join(f"[red]{b}[/red]" for b in blocked)
            scope = f"[dim]{auth_short}[/dim] | blocked: {block_short}"

        c.print(f"  [bold]{i}.[/bold] [{color}]{label}[/] [dim]({agent_id})[/dim]")
        c.print(f"       {scope}")
        c.print()
