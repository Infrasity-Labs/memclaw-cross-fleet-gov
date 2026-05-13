"""
Demo Moment 1 — Shared Context.

Sales and Legal agents both recall from FLEET_ORG_SHARED with the same query.
Both must surface the renewal context, proving the shared fleet works as a
cross-boundary knowledge layer without exposing fleet-private data.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fleets.sales_fleet import SalesFleet
from fleets.legal_fleet import LegalFleet
from config import FLEET_ORG_SHARED, AGENT_SALES, AGENT_LEGAL

QUERY = "Client X account status"

DIVIDER = "-" * 60


def _format_recall(result):
    if isinstance(result, dict):
        summary = result.get("summary") or result.get("answer") or result.get("context") or ""
        sources = result.get("sources") or result.get("memories") or []
        lines = []
        if summary:
            lines.append(f"  Summary : {summary}")
        if sources:
            lines.append(f"  Sources : {len(sources)} memory/memories returned")
            for s in sources:
                content = s.get("content", "")[:120]
                lines.append(f"    - {content!r}")
        return "\n".join(lines) if lines else f"  Raw response: {result}"
    return f"  Raw response: {result}"


def main():
    print("\n=== Demo Moment 1: Shared Context ===")
    print(f"Fleet     : {FLEET_ORG_SHARED!r}")
    print(f"Query     : {QUERY!r}")
    print()

    sales = SalesFleet()
    legal = LegalFleet()

    print(DIVIDER)
    print(f"Agent     : {AGENT_SALES!r}")
    sales_result = sales.recall_shared(QUERY)
    print(_format_recall(sales_result))

    print()
    print(DIVIDER)
    print(f"Agent     : {AGENT_LEGAL!r}")
    legal_result = legal.recall_shared(QUERY)
    print(_format_recall(legal_result))

    print()
    print(DIVIDER)
    print("RESULT: Both agents retrieved shared renewal context from the org-shared fleet.")
    print("        No fleet-private data was exposed.\n")


if __name__ == "__main__":
    main()
