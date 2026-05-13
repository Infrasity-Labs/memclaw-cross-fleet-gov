"""
Static governance access matrix.

Defines which agent can access which fleet and prints it as a rich Table.
No API calls — this is the authoritative source of declared access policy.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table
from rich import box

from config import (
    FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL,
    AGENT_SALES, AGENT_LEGAL, AGENT_ADMIN,
)

console = Console()

MATRIX = {
    AGENT_SALES: {
        FLEET_ORG_SHARED: "READ/WRITE",
        FLEET_SALES:      "READ/WRITE",
        FLEET_LEGAL:      "BLOCKED",
    },
    AGENT_LEGAL: {
        FLEET_ORG_SHARED: "READ/WRITE",
        FLEET_SALES:      "BLOCKED",
        FLEET_LEGAL:      "READ/WRITE",
    },
    AGENT_ADMIN: {
        FLEET_ORG_SHARED: "READ/WRITE",
        FLEET_SALES:      "READ",
        FLEET_LEGAL:      "READ",
    },
}

FLEET_LABELS = {
    FLEET_ORG_SHARED: "fleet-org-shared",
    FLEET_SALES:      "fleet-sales",
    FLEET_LEGAL:      "fleet-legal",
}

AGENT_LABELS = {
    AGENT_SALES: "sales-agent-1",
    AGENT_LEGAL: "legal-agent-1",
    AGENT_ADMIN: "admin-agent",
}


def _cell_style(access: str) -> str:
    if access == "BLOCKED":
        return "bold red"
    if access == "READ/WRITE":
        return "bold green"
    return "yellow"


def print_matrix():
    table = Table(
        title="Agent Access Matrix",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Agent", style="bold white", min_width=16)
    for fleet_id, label in FLEET_LABELS.items():
        table.add_column(label, justify="center", min_width=16)

    for agent_id, perms in MATRIX.items():
        row = [AGENT_LABELS[agent_id]]
        for fleet_id in FLEET_LABELS:
            access = perms.get(fleet_id, "BLOCKED")
            row.append(f"[{_cell_style(access)}]{access}[/]")
        table.add_row(*row)

    console.print(table)


def get_agent_scope(agent_id: str) -> dict:
    return MATRIX.get(agent_id, {})


def get_allowed_fleets(agent_id: str) -> list:
    return [f for f, a in MATRIX.get(agent_id, {}).items() if a != "BLOCKED"]


def get_blocked_fleets(agent_id: str) -> list:
    return [f for f, a in MATRIX.get(agent_id, {}).items() if a == "BLOCKED"]
