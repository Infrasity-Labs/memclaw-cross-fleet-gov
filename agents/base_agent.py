"""
BaseAgent — core governance-aware agent loop.

Retrieval flow:
  user_message
    -> recall from each authorized fleet (GOVERNANCE BOUNDARY)
    -> build system prompt with ONLY retrieved memories
    -> LLM reasoning (LLM never sees unauthorized memories)
    -> optional audit log
    -> return structured response

The boundary is structural: agents receive their fleet recall callables at
construction time. No fleet ID is ever derived from user input.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.llm_provider import LLMProvider


def _extract_memory_texts(recall_result) -> list:
    """Flatten a MemClaw recall response into a list of plain text strings."""
    if isinstance(recall_result, str):
        return [recall_result] if recall_result.strip() else []
    if isinstance(recall_result, list):
        texts = []
        for item in recall_result:
            texts.extend(_extract_memory_texts(item))
        return texts
    if isinstance(recall_result, dict):
        texts = []
        summary = recall_result.get("summary") or recall_result.get("answer") or recall_result.get("context")
        if summary:
            texts.append(str(summary))
        sources = recall_result.get("sources") or recall_result.get("memories") or []
        for s in sources:
            content = s.get("content", "").strip()
            if content:
                texts.append(content)
        return texts
    return []


class BaseAgent:
    """
    Governance-aware agent base class.

    Subclasses declare which fleets they own by passing fleet recall callables.
    The LLM is only ever given memories returned by those callables.
    """

    def __init__(
        self,
        agent_id: str,
        agent_label: str,
        allowed_fleets: list,
        blocked_fleets: list,
        fleet_recall_map: dict,
        audit_logger=None,
    ):
        """
        Args:
            agent_id: e.g. "sales-agent-1"
            agent_label: human-readable name, e.g. "Sales Agent"
            allowed_fleets: list of fleet_id strings this agent may access
            blocked_fleets: list of fleet_id strings explicitly denied
            fleet_recall_map: {fleet_id: callable(query, top_k) -> API response}
            audit_logger: optional AuditLogger instance
        """
        self.agent_id = agent_id
        self.agent_label = agent_label
        self.allowed_fleets = allowed_fleets
        self.blocked_fleets = blocked_fleets
        self._fleet_recall_map = fleet_recall_map
        self._audit_logger = audit_logger
        self._llm = LLMProvider()

    # ── Public API ────────────────────────────────────────────────────────────

    def ask(self, user_message: str, top_k: int = 5, recall_query: str = None) -> dict:
        """Run the full governance-aware reasoning loop.

        Args:
            user_message: The question shown to the LLM.
            top_k: Max memories per fleet.
            recall_query: Optional retrieval query for vector search. When the
                natural-language question doesn't match stored content well,
                pass a keyword-rich query here while keeping user_message intact
                for the LLM. Audit log always records user_message.

        Returns:
            {
                "response": str,
                "memories_by_fleet": {fleet_id: [text, ...]},
                "fleets_queried": [fleet_id, ...],
                "total_memories": int,
            }
        """
        query = recall_query if recall_query else user_message
        memories_by_fleet = self._recall_all(query, top_k)
        system_prompt = self._build_system_prompt(memories_by_fleet)
        response = self._llm.complete(system_prompt, user_message)

        if self._audit_logger is not None:
            self._audit_logger.record(
                self.agent_id, user_message, memories_by_fleet, response
            )

        return {
            "response": response,
            "memories_by_fleet": memories_by_fleet,
            "fleets_queried": list(memories_by_fleet.keys()),
            "total_memories": sum(len(v) for v in memories_by_fleet.values()),
        }

    def get_governance_summary(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "label": self.agent_label,
            "allowed_fleets": self.allowed_fleets,
            "blocked_fleets": self.blocked_fleets,
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _recall_all(self, query: str, top_k: int) -> dict:
        """Recall from all authorized fleets. Returns {fleet_id: [text, ...]}.

        When all fleet_recall_map entries point to the same callable (the combined
        recall_all pattern), a single API call is made and results are split by
        source fleet_id. When callables differ (per-fleet pattern), each is called
        separately.
        """
        if not self._fleet_recall_map:
            return {}

        unique_fns = list({id(fn): fn for fn in self._fleet_recall_map.values()}.values())

        if len(unique_fns) == 1:
            try:
                raw = unique_fns[0](query, top_k)
                split = self._split_by_fleet(raw)
                authorized = set(self._fleet_recall_map)
                return {fid: texts for fid, texts in split.items() if fid in authorized}
            except Exception:
                return {fid: [] for fid in self._fleet_recall_map}

        results = {}
        for fleet_id, recall_fn in self._fleet_recall_map.items():
            try:
                raw = recall_fn(query, top_k)
                results[fleet_id] = _extract_memory_texts(raw)
            except Exception:
                results[fleet_id] = []
        return results

    @staticmethod
    def _split_by_fleet(recall_result) -> dict:
        """Parse a multi-fleet recall response into {fleet_id: [text, ...]}."""
        results = {}
        if not isinstance(recall_result, dict):
            return results
        for source in recall_result.get("sources") or recall_result.get("memories") or []:
            fleet_id = source.get("fleet_id", "")
            content = source.get("content", "").strip()
            if fleet_id and content:
                results.setdefault(fleet_id, []).append(content)
        return results

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

        blocked_note = (
            f"You do NOT have access to: {', '.join(self.blocked_fleets)}. "
            "If asked about topics outside your authorized scope, state honestly "
            "that this information is not available to you. Do not speculate or hallucinate."
            if self.blocked_fleets
            else ""
        )

        return (
            f"You are the {self.agent_label}.\n\n"
            f"Your authorized data scope: {', '.join(self.allowed_fleets)}.\n"
            f"{blocked_note}\n\n"
            "Below is everything you know, retrieved from your authorized memory stores. "
            "Ground your response entirely in this context. "
            "If the context does not contain the answer, say so directly.\n\n"
            f"AUTHORIZED CONTEXT:\n{memory_block}"
        )
