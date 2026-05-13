from client import MemClawClient
from config import FLEET_ORG_SHARED, FLEET_SALES, AGENT_SALES


class SalesFleet:
    def __init__(self):
        self.client = MemClawClient()
        self.agent_id = AGENT_SALES

    def write_private(self, content, memory_type=None):
        return self.client.write_memory(FLEET_SALES, self.agent_id, content, memory_type)

    def write_shared(self, content, memory_type=None):
        return self.client.write_memory(FLEET_ORG_SHARED, self.agent_id, content, memory_type)

    def recall_shared(self, query, top_k=5):
        return self.client.recall([FLEET_ORG_SHARED], None, query, top_k)

    def recall_private(self, query, top_k=5):
        return self.client.recall([FLEET_SALES], self.agent_id, query, top_k)

    def recall_all(self, query, top_k=5):
        """Single governed recall across all authorized sales fleets."""
        return self.client.recall([FLEET_ORG_SHARED, FLEET_SALES], self.agent_id, query, top_k)
