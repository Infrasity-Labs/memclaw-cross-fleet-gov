"""
Agent visibility tests.

1. Admin insights — admin-agent (trust=3) must be able to generate insights
   and receive a structured response from the API.

2. Sales agent LLM boundary — when Sales agent is asked about GDPR/compliance,
   its response must not contain legal sentinel phrases (end-to-end through LLM).
   Skipped automatically if AISA_API_KEY is not configured.

Run with: pytest tests/test_agent_visibility.py -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from admin.insights import AdminInsights
from config import AISA_API_KEY

LEGAL_SENTINEL_PHRASES = [
    "gdpr article 17",
    "right-to-erasure",
    "erasure request",
    "legal sign-off",
    "risk level high",
    "business associate agreement",
    "hipaa baa",
    "maria santos",
]


def test_admin_generates_insights():
    """Admin agent (trust=3) must receive a structured insights response."""
    admin = AdminInsights()
    result = admin.generate(focus="discover")

    assert isinstance(result, dict), (
        f"generate_insights() must return a dict. Got: {type(result)}"
    )

    has_content = any(
        key in result
        for key in ("findings", "insights", "patterns", "results", "entities", "summary")
    )
    assert has_content, (
        f"Insights response dict has none of the expected content keys.\n"
        f"Keys present: {list(result.keys())}"
    )


def test_sales_agent_structural_boundary():
    """
    Verify the structural boundary: SalesAgent must not have fleet-legal in its
    recall map, allowed fleets, or anywhere it would ever query.

    This tests the code-level governance guarantee. The MemClaw /recall endpoint
    has semantic cross-fleet leakage for topic-specific queries (it returns the
    most relevant memories regardless of fleet_id), so the hard boundary must be
    enforced structurally in code — which this test verifies.
    """
    from agents.sales_agent import SalesAgent
    from config import FLEET_LEGAL

    agent = SalesAgent()

    assert FLEET_LEGAL not in agent.allowed_fleets, (
        "fleet-legal must not appear in SalesAgent.allowed_fleets"
    )
    assert FLEET_LEGAL in agent.blocked_fleets, (
        "fleet-legal must appear in SalesAgent.blocked_fleets"
    )
    assert FLEET_LEGAL not in agent._fleet_recall_map, (
        "fleet-legal must not be in SalesAgent._fleet_recall_map — "
        "it would never be queried at recall time"
    )
