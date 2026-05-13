import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.base_agent import BaseAgent
from fleets.admin_fleet import AdminFleet
from config import AGENT_ADMIN, FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL
from runtime.governance_engine import GovernanceEngine


class AdminAgent(BaseAgent):
    """
    Admin agent with READ access to all three fleets.

    Purpose: governance observer. Can see org-shared, sales-private, and
    legal-private context simultaneously. Surfaces conflicts between fleet
    data (e.g., sales pushing to close a deal that legal has on hold).

    Does NOT make commercial decisions or legal rulings. When conflicts are
    detected, it flags them for human escalation.

    Fleet access policy is declared in policies/fleet_access.yaml and
    enforced structurally — the fleet_recall_map is fixed at construction.
    """

    def __init__(self, audit_logger=None, engine=None):
        if engine is None:
            engine = GovernanceEngine()
        fleet = AdminFleet()
        recall_fn = fleet.recall_all
        fleet_recall_map = {
            FLEET_ORG_SHARED: recall_fn,
            FLEET_SALES:      recall_fn,
            FLEET_LEGAL:      recall_fn,
        }
        super().__init__(
            agent_id=AGENT_ADMIN,
            agent_label="Admin Agent",
            allowed_fleets=engine.get_authorized_fleets(AGENT_ADMIN),
            blocked_fleets=engine.get_blocked_fleets(AGENT_ADMIN),
            fleet_recall_map=fleet_recall_map,
            audit_logger=audit_logger,
        )

    def _build_system_prompt(self, memories_by_fleet: dict) -> str:
        all_memories = []
        for fleet_id, texts in memories_by_fleet.items():
            for text in texts:
                all_memories.append(f"[{fleet_id}] {text}")

        memory_block = (
            "\n".join(f"- {m}" for m in all_memories)
            if all_memories
            else "(no relevant memories retrieved)"
        )

        return (
            "You are the Admin Agent — a cross-fleet governance observer.\n\n"
            "You have read access to all three memory fleets:\n"
            "  - fleet-org-shared: organization-wide account context\n"
            "  - fleet-sales: sales team private data (tactics, discounts, pipeline)\n"
            "  - fleet-legal: legal team private data (compliance flags, holds, risk)\n\n"
            "Your role is to synthesize information across fleet boundaries and surface "
            "conflicts or risks that individual agents cannot see.\n\n"
            "When sales and legal data contradict each other — for example, sales is "
            "pushing to close a deal that legal has placed on hold — you MUST:\n"
            "1. State the conflict explicitly\n"
            "2. Describe what each side knows\n"
            "3. Recommend escalation to a human governance owner\n\n"
            "You do NOT approve or block deals. You do NOT make legal rulings. "
            "You surface information. Decisions are made by humans.\n\n"
            "Ground your response entirely in the context below. "
            "If the context does not contain the answer, say so directly.\n\n"
            f"AUTHORIZED CONTEXT (ALL FLEETS):\n{memory_block}"
        )
