import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.base_agent import BaseAgent
from fleets.sales_fleet import SalesFleet
from config import AGENT_SALES, FLEET_SALES, FLEET_ORG_SHARED, FLEET_LEGAL
from runtime.governance_engine import GovernanceEngine


class SalesAgent(BaseAgent):
    """
    Sales agent with access to fleet-org-shared and fleet-sales.
    Explicitly blocked from fleet-legal.

    Governance enforced at retrieval time: the LLM receives only memories
    from the two authorized fleets. GDPR flags, compliance risks, and legal
    counsel notes are structurally inaccessible.

    Fleet access policy is declared in policies/fleet_access.yaml and
    enforced structurally — the fleet_recall_map is fixed at construction.
    """

    def __init__(self, audit_logger=None, engine=None):
        if engine is None:
            engine = GovernanceEngine()
        fleet = SalesFleet()
        recall_fn = fleet.recall_all
        fleet_recall_map = {
            FLEET_ORG_SHARED: recall_fn,
            FLEET_SALES: recall_fn,
        }
        super().__init__(
            agent_id=AGENT_SALES,
            agent_label="Sales Agent",
            allowed_fleets=engine.get_authorized_fleets(AGENT_SALES),
            blocked_fleets=engine.get_blocked_fleets(AGENT_SALES),
            fleet_recall_map=fleet_recall_map,
            audit_logger=audit_logger,
        )
