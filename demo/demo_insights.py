"""
Demo Moment 3 — Admin Insights (per-fleet).

Calls generate_insights once per fleet so findings are correctly attributed.
Admin-agent (trust=3) queries each fleet in sequence and displays results
under color-coded boundary panels using rich.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box

from admin.insights import AdminInsights
from admin.governance_matrix import print_matrix
from config import FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL, AGENT_ADMIN

console = Console()

FLEET_CONFIG = {
    FLEET_ORG_SHARED: {"label": "ORG-SHARED",    "style": "bold cyan"},
    FLEET_SALES:      {"label": "SALES-PRIVATE",  "style": "bold yellow"},
    FLEET_LEGAL:      {"label": "LEGAL-PRIVATE",  "style": "bold red"},
}


def _parse_findings(result: dict) -> list:
    if isinstance(result, dict):
        return (
            result.get("findings")
            or result.get("insights")
            or result.get("patterns")
            or result.get("results")
            or result.get("entities")
            or []
        )
    if isinstance(result, list):
        return result
    return []


def _render_finding(finding, style: str):
    if not isinstance(finding, dict):
        console.print(f"  [dim]- {str(finding)[:120]}[/dim]")
        return

    kind = finding.get("type", "finding").upper()
    title = (
        finding.get("title")
        or finding.get("entity")
        or finding.get("name")
        or finding.get("pattern")
        or str(finding)[:80]
    )
    description = (
        finding.get("description")
        or finding.get("insight")
        or finding.get("summary")
        or ""
    )
    recommendation = finding.get("recommendation", "")
    confidence = finding.get("confidence")

    console.print(f"  [{style}][{kind}][/] {title}")
    if description:
        console.print(f"    [dim]{description[:200]}[/dim]")
    if recommendation:
        console.print(f"    [italic]Recommendation: {recommendation[:160]}[/italic]")
    if confidence is not None:
        console.print(f"    [dim]Confidence: {confidence}[/dim]")


def generate_per_fleet(admin: AdminInsights) -> dict:
    """Call generate_insights once per fleet, returning {fleet_id: result_or_error}."""
    results = {}
    for fleet_id in FLEET_CONFIG:
        try:
            results[fleet_id] = admin.client.generate_insights(
                focus="discover",
                agent_id=AGENT_ADMIN,
                fleet_id=fleet_id,
            )
        except RuntimeError as exc:
            results[fleet_id] = {"error": str(exc)}
    return results


def main():
    console.print()
    console.rule("[bold white]Demo Moment 3: Admin Insights (Per-Fleet)[/bold white]")
    console.print(f"  Agent : [bold]{AGENT_ADMIN}[/bold]  (trust level 3 / admin)")
    console.print(f"  Focus : 'discover'")
    console.print()

    admin = AdminInsights()
    console.print("[dim]Trust level set. Generating per-fleet insights...[/dim]\n")

    per_fleet = generate_per_fleet(admin)

    total_findings = 0
    for fleet_id, cfg in FLEET_CONFIG.items():
        result = per_fleet[fleet_id]
        label = cfg["label"]
        style = cfg["style"]

        if isinstance(result, dict) and "error" in result:
            console.print(
                Panel(
                    f"[red]{result['error'][:200]}[/red]",
                    title=f"[{style}]{label}[/]",
                    border_style="red",
                )
            )
            continue

        findings = _parse_findings(result)
        total_findings += len(findings)

        if not findings:
            body = "[dim](No findings returned for this fleet)[/dim]"
        else:
            lines = []
            for f in findings:
                kind = (f.get("type", "finding") if isinstance(f, dict) else "finding").upper()
                title = (
                    f.get("title") or f.get("entity") or f.get("name") or str(f)[:80]
                    if isinstance(f, dict) else str(f)[:80]
                )
                desc = (
                    f.get("description") or f.get("insight") or f.get("summary") or ""
                    if isinstance(f, dict) else ""
                )
                reco = f.get("recommendation", "") if isinstance(f, dict) else ""
                lines.append(f"  [{style}][{kind}][/] {title}")
                if desc:
                    lines.append(f"    [dim]{desc[:200]}[/dim]")
                if reco:
                    lines.append(f"    [italic]Recommendation: {reco[:160]}[/italic]")
            body = "\n".join(lines)

        console.print(
            Panel(
                body,
                title=f"[{style}] {label} [/]  ({fleet_id})",
                border_style=style.replace("bold ", ""),
                padding=(1, 2),
            )
        )

    console.print()
    console.rule("[bold white]Governance Access Matrix[/bold white]")
    console.print()
    print_matrix()
    console.print()
    console.print(
        f"[dim]Total findings across all fleets: {total_findings}[/dim]"
    )
    console.print()


if __name__ == "__main__":
    main()
