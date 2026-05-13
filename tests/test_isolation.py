"""
Critical isolation test: after seeding, a Sales agent recall for GDPR-related
content against ['fleet-org-shared', 'fleet-sales'] must return zero content
originating from fleet-legal.

Run with: pytest tests/test_isolation.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fleets.sales_fleet import SalesFleet

LEGAL_SENTINEL_PHRASES = [
    "GDPR Article 17",
    "right-to-erasure",
    "erasure request",
    "legal sign-off",
    "compliance team",
    "Risk level HIGH",
]


def _extract_text(result):
    """Flatten a recall response to a single string for sentinel scanning."""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        parts = []
        for key in ("summary", "answer", "context", "content"):
            val = result.get(key)
            if val:
                parts.append(str(val))
        for source in result.get("sources", result.get("memories", [])):
            content = source.get("content", "")
            fleet = source.get("fleet_id", "")
            parts.append(f"{fleet} {content}")
        return " ".join(parts)
    if isinstance(result, list):
        return " ".join(_extract_text(item) for item in result)
    return str(result)


@pytest.fixture(scope="module")
def sales():
    return SalesFleet()


def test_sales_recall_contains_no_legal_data(sales):
    """
    Sales agent recalling from ['fleet-org-shared', 'fleet-sales'] must receive
    no content that originated in fleet-legal. Fleet-ID scoping is the boundary.
    """
    result = sales.recall_all("GDPR erasure compliance")
    text = _extract_text(result).lower()

    leaked = [phrase for phrase in LEGAL_SENTINEL_PHRASES if phrase.lower() in text]

    assert not leaked, (
        f"BOUNDARY BREACH: Sales recall from ['fleet-org-shared', 'fleet-sales'] "
        f"returned fleet-legal content.\n"
        f"Leaked sentinel phrases: {leaked}\n"
        f"Full recall text (truncated): {text[:500]}"
    )
