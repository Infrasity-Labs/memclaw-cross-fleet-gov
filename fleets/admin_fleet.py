import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from client import MemClawClient
from config import FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL, AGENT_SALES, AGENT_LEGAL


class AdminFleet:
    """
    Cross-fleet READ facade for the Admin Agent.

    Exposes recall from all three fleets. No write access to private fleets —
    the admin role is observer-only for sales and legal namespaces.

    Private fleet recalls pass the authoring agent's ID as filter_agent_id so
    the MemClaw API locates the memories each team wrote. The admin is authorized
    to read those memories; the agent_id here is a retrieval filter, not an
    access grant.
    """

    def __init__(self):
        self.client = MemClawClient()

    def recall_shared(self, query, top_k=5):
        return self.client.recall([FLEET_ORG_SHARED], None, query, top_k)

    def recall_sales(self, query, top_k=5):
        return self.client.recall([FLEET_SALES], AGENT_SALES, query, top_k)

    def recall_legal(self, query, top_k=5):
        return self.client.recall([FLEET_LEGAL], AGENT_LEGAL, query, top_k)

    def recall_all(self, query, top_k=5):
        """Single governed recall across all three fleets for cross-fleet visibility."""
        return self.client.recall(
            [FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL], None, query, top_k
        )
