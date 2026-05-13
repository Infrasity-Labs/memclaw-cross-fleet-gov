import logging
import requests
from config import MEMCLAW_API_KEY, MEMCLAW_TENANT_ID, MEMCLAW_BASE_URL

logger = logging.getLogger(__name__)


class MemClawClient:
    def __init__(self):
        self.base_url = MEMCLAW_BASE_URL
        self.headers = {"X-API-Key": MEMCLAW_API_KEY, "Content-Type": "application/json"}
        self.tenant_id = MEMCLAW_TENANT_ID

    def _request(self, method, endpoint, *, params=None, json=None):
        url = f"{self.base_url}{endpoint}"
        logger.debug("%s %s", method.upper(), endpoint)
        resp = requests.request(method, url, headers=self.headers, params=params, json=json)
        if not resp.ok:
            raise RuntimeError(
                f"MemClaw {resp.status_code} {method.upper()} {endpoint}: {resp.text}"
            )
        return resp.json()

    def write_memory(self, fleet_id, agent_id, content, memory_type=None):
        body = {
            "tenant_id": self.tenant_id,
            "fleet_id": fleet_id,
            "agent_id": agent_id,
            "content": content,
        }
        if memory_type is not None:
            body["memory_type"] = memory_type
        return self._request("post", "/memories", json=body)

    def recall(self, fleet_ids, agent_id, query, top_k=5):
        body = {
            "tenant_id": self.tenant_id,
            "fleet_ids": fleet_ids if isinstance(fleet_ids, list) else [fleet_ids],
            "query": query,
            "top_k": top_k,
        }
        if agent_id is not None:
            body["filter_agent_id"] = agent_id
        return self._request("post", "/recall", json=body)

    def search(self, fleet_id, agent_id, query, top_k=5):
        """WARNING: not fleet-scoped. Use recall() for governed retrieval."""
        body = {
            "tenant_id": self.tenant_id,
            "fleet_id": fleet_id,
            "query": query,
            "top_k": top_k,
        }
        return self._request("post", "/search", json=body)

    def generate_insights(self, focus="discover", agent_id=None, fleet_id=None):
        body = {
            "tenant_id": self.tenant_id,
            "focus": focus,
        }
        if agent_id is not None:
            body["agent_id"] = agent_id
        if fleet_id is not None:
            body["fleet_id"] = fleet_id
        return self._request("post", "/insights/generate", json=body)

    def set_agent_trust(self, agent_id, trust_level):
        return self._request(
            "patch",
            f"/agents/{agent_id}/trust",
            params={"tenant_id": self.tenant_id},
            json={"trust_level": trust_level},
        )

    def get_audit_log(self):
        return self._request("get", "/audit", params={"tenant_id": self.tenant_id})
