"""
Shared-fleet access symmetry tests: both Sales and Legal agents must be able
to recall the org-shared renewal context. Requires seed_memories.py to have run.

Run with: pytest tests/test_shared_access.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fleets.sales_fleet import SalesFleet
from fleets.legal_fleet import LegalFleet

SHARED_QUERY = "Client X account status"
SHARED_INDICATORS = ["renewal", "2.4m", "2.4", "client x"]


def _extract_text(result):
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
def sales():
    return SalesFleet()


@pytest.fixture(scope="module")
def legal():
    return LegalFleet()


def test_sales_can_recall_shared_context(sales):
    """Sales agent must surface the shared renewal context from fleet-org-shared."""
    result = sales.recall_shared(SHARED_QUERY)
    text = _extract_text(result).lower()
    matched = [ind for ind in SHARED_INDICATORS if ind in text]
    assert matched, (
        f"Sales agent got no shared renewal context from fleet-org-shared.\n"
        f"Expected at least one of: {SHARED_INDICATORS}\n"
        f"Got (truncated): {text[:400]}"
    )


def test_legal_can_recall_shared_context(legal):
    """Legal agent must surface the shared renewal context from fleet-org-shared."""
    result = legal.recall_shared(SHARED_QUERY)
    text = _extract_text(result).lower()
    matched = [ind for ind in SHARED_INDICATORS if ind in text]
    assert matched, (
        f"Legal agent got no shared renewal context from fleet-org-shared.\n"
        f"Expected at least one of: {SHARED_INDICATORS}\n"
        f"Got (truncated): {text[:400]}"
    )
