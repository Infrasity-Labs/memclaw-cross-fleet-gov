"""
Demo Moment 2 — Hard Boundary Enforcement.

Sales agent queries its own private fleet for "Client X GDPR compliance risk".
The GDPR erasure memory lives in FLEET_LEGAL — inaccessible to FLEET_SALES.
Any result surfaced here must contain ZERO content from the legal fleet.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fleets.sales_fleet import SalesFleet
from config import FLEET_SALES, AGENT_SALES

QUERY = "Client X GDPR compliance risk"
LEGAL_SENTINEL_PHRASES = [
    "GDPR Article 17",
    "right-to-erasure",
    "erasure request",
    "legal sign-off",
    "compliance team",
    "Risk level HIGH",
]

DIVIDER = "=" * 60


def _contains_legal_data(result):
    text = str(result).lower()
    return [phrase for phrase in LEGAL_SENTINEL_PHRASES if phrase.lower() in text]


def main():
    print("\n=== Demo Moment 2: Hard Boundary Enforcement ===")
    print(f"Agent     : {AGENT_SALES!r}")
    print(f"Fleet     : {FLEET_SALES!r}  (Sales private — legal fleet is separate)")
    print(f"Query     : {QUERY!r}")
    print()

    sales = SalesFleet()
    result = sales.recall_private(QUERY)

    print("--- Raw Recall Response ---")
    if isinstance(result, dict):
        summary = result.get("summary") or result.get("answer") or result.get("context") or ""
        sources = result.get("sources") or result.get("memories") or []

        if summary:
            print(f"Summary : {summary}")
        else:
            print("Summary : (none)")

        if sources:
            print(f"Sources : {len(sources)} result(s)")
            for s in sources:
                print(f"  - {s.get('content', '')[:140]!r}")
        else:
            print("Sources : (no results)")

        if not summary and not sources:
            print(f"Full response: {result}")
    else:
        print(result)

    print()
    print(DIVIDER)

    leaked = _contains_legal_data(result)
    if leaked:
        print("BOUNDARY BREACH DETECTED — legal data present in sales recall!")
        for phrase in leaked:
            print(f"  ! Found sentinel phrase: {phrase!r}")
    else:
        print("BOUNDARY ENFORCED")
        print("Zero legal fleet data leaked into Sales agent recall.")
        print("The GDPR erasure memory is isolated inside FLEET_LEGAL.")
        print("Sales agent received no GDPR compliance information.")

    print(DIVIDER)
    print()


if __name__ == "__main__":
    main()
