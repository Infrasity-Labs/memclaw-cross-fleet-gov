from client import MemClawClient
from config import AGENT_ADMIN, FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL

_ALL_FLEETS = [FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL]


class AdminInsights:
    def __init__(self):
        self.client = MemClawClient()
        self._set_trust_with_registration()

    def _set_trust_with_registration(self):
        try:
            self.client.set_agent_trust(AGENT_ADMIN, 3)
        except RuntimeError as exc:
            if "404" not in str(exc):
                raise
            # Agents auto-register on first write; seed a probe then retry.
            self.client.write_memory(FLEET_ORG_SHARED, AGENT_ADMIN, "Admin agent registration probe.")
            self.client.set_agent_trust(AGENT_ADMIN, 3)

    def generate(self, focus="discover", fleet_ids=None):
        """Generate insights across all three fleets (or a specified subset).

        Calls generate_insights once per fleet_id and aggregates list-valued
        keys (findings, insights, etc.) so callers get a unified view.
        """
        if fleet_ids is None:
            fleet_ids = _ALL_FLEETS
        aggregated = {}
        for fid in fleet_ids:
            try:
                result = self.client.generate_insights(
                    focus=focus, agent_id=AGENT_ADMIN, fleet_id=fid
                )
                for key, val in result.items():
                    if isinstance(val, list):
                        aggregated.setdefault(key, []).extend(val)
                    elif key not in aggregated:
                        aggregated[key] = val
            except RuntimeError:
                pass
        return aggregated

    def get_audit_log(self):
        return self.client.get_audit_log()
