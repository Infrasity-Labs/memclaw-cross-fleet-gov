"""
Scope enforcement test: Legal agent recall from ['fleet-org-shared', 'fleet-legal']
must never return sales negotiation tactics written to fleet-sales.

Complements test_isolation.py (which tests the sales -> legal direction).
Requires seed_memories.py to have run first.

Run with: pytest tests/test_scope_enforcement.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fleets.legal_fleet import LegalFleet

SALES_SENTINEL_PHRASES = [
    "discount ceiling",
    "do not disclose",
    "negotiation tactic",
    "authorized to offer",
    "3-year term",
    "20% discount",
    "bundle pricing",
    "upsell pitch",
]


def _extract_text(result) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        parts = []
        for key in ("summary", "answer", "context", "content"):
            val = result.get(key)
            if val:
                parts.append(str(val))
        for source in result.get("sources", result.get("memories", [])):
            parts.append(source.get("content", ""))
        return " ".join(parts)
    if isinstance(result, list):
        return " ".join(_extract_text(item) for item in result)
    return str(result)


@pytest.fixture(scope="module")
def legal():
    return LegalFleet()


def test_legal_recall_contains_no_sales_data(legal):
    """
    Legal agent recalling from ['fleet-org-shared', 'fleet-legal'] for
    negotiation/discount terms must receive zero content originating from
    fleet-sales. Fleet scoping is the boundary.
    """
    result = legal.recall_all("discount ceiling negotiation tactic")
    text = _extract_text(result).lower()

    leaked = [phrase for phrase in SALES_SENTINEL_PHRASES if phrase.lower() in text]

    assert not leaked, (
        f"BOUNDARY BREACH: Legal recall from ['fleet-org-shared', 'fleet-legal'] "
        f"returned fleet-sales content.\n"
        f"Leaked sentinel phrases: {leaked}\n"
        f"Full recall text (truncated): {text[:500]}"
    )
