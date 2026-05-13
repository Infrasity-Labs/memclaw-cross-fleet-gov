import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.base_agent import BaseAgent
from fleets.legal_fleet import LegalFleet
from config import AGENT_LEGAL, FLEET_LEGAL, FLEET_ORG_SHARED, FLEET_SALES
from runtime.governance_engine import GovernanceEngine


class LegalAgent(BaseAgent):
    """
    Legal agent with access to fleet-org-shared and fleet-legal.
    Explicitly blocked from fleet-sales.

    Governance enforced at retrieval time: the LLM receives only memories
    from the two authorized fleets. Negotiation tactics, discount ceilings,
    and sales strategy are structurally inaccessible.

    Fleet access policy is declared in policies/fleet_access.yaml and
    enforced structurally — the fleet_recall_map is fixed at construction.
    """

    def __init__(self, audit_logger=None, engine=None):
        if engine is None:
            engine = GovernanceEngine()
        fleet = LegalFleet()
        recall_fn = fleet.recall_all
        fleet_recall_map = {
            FLEET_ORG_SHARED: recall_fn,
            FLEET_LEGAL: recall_fn,
        }
        super().__init__(
            agent_id=AGENT_LEGAL,
            agent_label="Legal Agent",
            allowed_fleets=engine.get_authorized_fleets(AGENT_LEGAL),
            blocked_fleets=engine.get_blocked_fleets(AGENT_LEGAL),
            fleet_recall_map=fleet_recall_map,
            audit_logger=audit_logger,
        )
