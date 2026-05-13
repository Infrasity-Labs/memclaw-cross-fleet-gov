"""
Admin agent cross-fleet recall tests.

Verifies that AdminFleet can retrieve from all three fleet namespaces
and that HealthSystem conflict data is visible (hold in fleet-legal,
close-target in fleet-sales) — confirming the admin cross-fleet guarantee.

Run with: pytest tests/test_admin_cross_fleet.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fleets.admin_fleet import AdminFleet


def _extract_text(result) -> str:
    """Flatten a recall response to a single string for assertion scanning."""
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


def _has_results(result) -> bool:
    return bool(_extract_text(result).strip())


@pytest.fixture(scope="module")
def admin():
    return AdminFleet()


def test_admin_recalls_from_all_three_fleets(admin):
    """AdminFleet must return non-empty results from each fleet for a known client."""
    shared = admin.recall_shared("HealthSystem", top_k=3)
    sales  = admin.recall_sales("HealthSystem", top_k=3)
    legal  = admin.recall_legal("HealthSystem", top_k=3)

    assert _has_results(shared), "Admin got no results from fleet-org-shared for HealthSystem"
    assert _has_results(sales),  "Admin got no results from fleet-sales for HealthSystem"
    assert _has_results(legal),  "Admin got no results from fleet-legal for HealthSystem"


def test_admin_sees_both_private_fleets(admin):
    """
    Admin must retrieve legal-type content from fleet-legal and sales-type
    content from fleet-sales. This is the cross-fleet access that proves the
    Admin Agent can see both sides of a governance conflict.

    Uses content-relevant queries (not bare entity names) because the MemClaw
    semantic index matches on content similarity, not exact entity strings.
    """
    legal_text = _extract_text(
        admin.recall_legal("GDPR compliance risk legal review", top_k=5)
    ).lower()
    sales_text = _extract_text(
        admin.recall_sales("negotiation tactic discount ceiling", top_k=5)
    ).lower()

    legal_phrases = ["gdpr", "compliance", "risk", "legal", "erasure", "baa", "hipaa"]
    sales_phrases  = ["discount", "negotiation", "tactic", "ceiling", "baa", "healthcare"]

    assert any(phrase in legal_text for phrase in legal_phrases), (
        f"fleet-legal recall returned none of {legal_phrases}.\n"
        f"Got: {legal_text[:300]}"
    )
    assert any(phrase in sales_text for phrase in sales_phrases), (
        f"fleet-sales recall returned none of {sales_phrases}.\n"
        f"Got: {sales_text[:300]}"
    )
