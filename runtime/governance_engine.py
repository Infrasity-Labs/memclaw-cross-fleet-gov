import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.policy_loader import PolicyLoader

_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")


class GovernanceEngine:
    """Central fleet access policy engine.

    Loads declarative policy from fleet_access.yaml. Agents call
    get_authorized_fleets() and get_blocked_fleets() instead of hardcoding
    their access lists. The engine provides string lists only — actual
    fleet recall callables are still constructed in each agent subclass.
    """

    def __init__(self, policy_path: str = "policies/fleet_access.yaml"):
        resolved = os.path.normpath(os.path.join(_REPO_ROOT, policy_path))
        policy = PolicyLoader.load(resolved)
        self._agents: dict = policy.get("agents", {})
        self._policy_path = resolved

    def can_access(self, agent_id: str, fleet_id: str) -> bool:
        return fleet_id in self.get_authorized_fleets(agent_id)

    def get_authorized_fleets(self, agent_id: str) -> list:
        return list(self._agents.get(agent_id, {}).get("allow", []))

    def get_blocked_fleets(self, agent_id: str) -> list:
        return list(self._agents.get(agent_id, {}).get("deny", []))

    def validate_recall_map(self, agent_id: str, fleet_recall_map: dict) -> bool:
        """Warn if the recall map includes fleets not in the authorized policy."""
        authorized = set(self.get_authorized_fleets(agent_id))
        unauthorized = [f for f in fleet_recall_map if f not in authorized]
        if unauthorized:
            import warnings
            warnings.warn(
                f"GovernanceEngine: {agent_id} recall map contains fleets not "
                f"in policy: {unauthorized}. Check policies/fleet_access.yaml.",
                RuntimeWarning,
                stacklevel=3,
            )
            return False
        return True

    def list_agents(self) -> list:
        return list(self._agents.keys())

    @property
    def policy_path(self) -> str:
        return self._policy_path
