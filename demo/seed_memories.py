"""
Seed enterprise scenario memories. Idempotent: skips a write if a
near-identical memory already exists in the target fleet (checked via /search).

Dataset: 5 enterprise clients × 3 fleets = 15 memories.
Source: scenarios/enterprise_scenario.py
"""
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from client import MemClawClient
from config import AGENT_SALES, AGENT_LEGAL
from scenarios.enterprise_scenario import MEMORIES, DEDUP_QUERIES

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _already_exists(client, fleet_id, agent_id, query):
    # Use recall() not search() — recall() is fleet-scoped.
    # Within a fleet multiple clients share the same agent_id, so a high-scoring
    # result may belong to a different client. Verify the recalled content actually
    # contains the client name before treating it as a real duplicate.
    words = query.split()
    # All dedup queries start with the client name; "Client X" is two words.
    client_name = "Client X" if words[0] == "Client" else words[0]
    try:
        result = client.recall([fleet_id], agent_id, query, top_k=1)
        if isinstance(result, dict):
            if result.get("memory_count", 0) == 0:
                return False
            sources = result.get("sources", result.get("memories", []))
            for s in sources:
                if client_name.lower() in s.get("content", "").lower():
                    return True
            return False
        return False
    except RuntimeError as exc:
        logger.warning("Recall check failed (%s) — proceeding with write.", exc)
        return False


def _extract_duplicate_id(err_text):
    try:
        return err_text.split("Duplicate memory exists: ")[1].split('"')[0].strip()
    except IndexError:
        return "unknown"


def _setup_trust_levels(client):
    """Ensure private-fleet agents have trust_level=3 (required to write to private fleets)."""
    for agent_id in [AGENT_SALES, AGENT_LEGAL]:
        try:
            client.set_agent_trust(agent_id, 3)
            logger.info("Set trust_level=3 for %s", agent_id)
        except RuntimeError as exc:
            logger.warning("Could not set trust for %s: %s — writes may fail", agent_id, exc)


def main():
    client = MemClawClient()
    print("\n=== MemClaw Demo — Seed Memories ===\n")

    _setup_trust_levels(client)

    for mem, dedup_query in zip(MEMORIES, DEDUP_QUERIES):
        fleet = mem["fleet_id"]
        agent = mem["agent_id"]
        snippet = mem["content"][:60] + "..."

        if _already_exists(client, fleet, agent, dedup_query):
            print(f"[SKIP]  fleet={fleet!r}  agent={agent!r}")
            print(f"        Near-identical memory already exists for: {dedup_query!r}\n")
            continue

        try:
            response = client.write_memory(fleet, agent, mem["content"])
        except RuntimeError as exc:
            err = str(exc)
            if "409" in err:
                dup_id = _extract_duplicate_id(err)
                print(f"[SKIP]  fleet={fleet!r}  agent={agent!r}")
                print(f"        API reports duplicate (409). Existing id={dup_id!r}\n")
                continue
            raise

        memory_id = (
            response.get("id")
            or response.get("memory_id")
            or response.get("data", {}).get("id", "unknown")
        )
        print(f"[WROTE] fleet={fleet!r}  agent={agent!r}")
        print(f"        id={memory_id!r}")
        print(f"        content={snippet!r}\n")

    print("Seeding complete.\n")


if __name__ == "__main__":
    main()
