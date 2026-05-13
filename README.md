# Enterprise Multi-Agent Governance Runtime

A production-quality reference implementation of governed enterprise AI: multiple agents with isolated memory fleets, declarative access policies, structural conflict detection, stateful sessions, live audit logging, and an interactive control-plane terminal.

**Built on:** [MemClaw](https://memclaw.net) (fleet-scoped memory API) + AISA LLM gateway.

---

## Core Principle: Governance Before Reasoning

Unauthorized memories are **never retrieved**. The LLM never sees forbidden context.

```
User Query
    │
    ▼
GovernanceEngine  ←── policies/fleet_access.yaml
    │  validates access before recall
    ▼
BaseAgent._recall_all()   ◄── fixed fleet_recall_map (set at construction)
    │  calls only authorized fleet facades
    ▼
MemClaw REST API  (/recall?fleet_id=fleet-sales)
    │  server-side fleet isolation
    ▼
Authorized memories only
    │
    ▼
_build_system_prompt()    ◄── LLM only ever sees authorized content
    │
    ▼
LLMProvider.complete()
    │
    ▼
Response + AuditLogger → logs/session_audit.log
```

Fleet access is structural — **no user input can expand it at runtime**. The `fleet_recall_map` passed to `BaseAgent.__init__` is a fixed dict of callable closures. There is no code path that adds to it after construction.

---

## Architecture

```
memclaw-cross-fleet-gov/
│
├── app.py                        # Interactive governance runtime (entry point)
├── config.py                     # Fleet IDs, agent IDs, API credentials
├── client.py                     # MemClaw REST client
│
├── policies/                     # Declarative governance policy
│   ├── fleet_access.yaml         # Agent fleet access rules (single source of truth)
│   └── governance_rules.yaml     # Conflict detection keyword patterns
│
├── runtime/                      # Governance runtime layer
│   ├── governance_engine.py      # Central access validator (loads fleet_access.yaml)
│   ├── policy_loader.py          # YAML policy loader
│   ├── session_manager.py        # Per-agent stateful sessions
│   ├── terminal_ui.py            # Rich UI primitives
│   ├── live_audit_monitor.py     # Real-time audit event display
│   └── event_bus.py              # Synchronous pub/sub for governance events
│
├── agents/                       # Agent implementations
│   ├── base_agent.py             # Governance loop: recall → prompt → LLM → audit
│   ├── sales_agent.py            # fleet-org-shared + fleet-sales
│   ├── legal_agent.py            # fleet-org-shared + fleet-legal
│   ├── admin_agent.py            # All 3 fleets — cross-fleet observer
│   └── llm_provider.py           # AISA gateway (OpenAI SDK)
│
├── fleets/                       # Fleet facade layer
│   ├── sales_fleet.py            # SalesFleet: recall/write for fleet-sales
│   ├── legal_fleet.py            # LegalFleet: recall/write for fleet-legal
│   └── admin_fleet.py            # AdminFleet: READ across all 3 fleets
│
├── admin/                        # Governance observability
│   ├── audit.py                  # AuditLogger → logs/session_audit.log
│   ├── conflict_detector.py      # Keyword-based structural conflict detection
│   ├── insights.py               # AdminInsights wrapper (trust=3)
│   └── governance_matrix.py      # Static access matrix display
│
├── state/                        # Session persistence
│   ├── session_state.py          # Per-agent conversation history
│   └── persistence.py            # state/sessions.json I/O
│
├── scenarios/
│   └── enterprise_scenario.py    # 15 enterprise memories (5 clients x 3 fleets)
│
├── demo/                         # Standalone demos
├── tests/                        # pytest suite (8 tests)
├── logs/                         # session_audit.log (created at runtime)
├── docker/                       # Container packaging
└── openclaw/                     # OpenClaw deployment layer
```

---

## Fleet Access Matrix

| Agent | fleet-org-shared | fleet-sales | fleet-legal |
|---|---|---|---|
| `sales-agent-1` | READ/WRITE | READ/WRITE | **BLOCKED** |
| `legal-agent-1` | READ/WRITE | **BLOCKED** | READ/WRITE |
| `admin-agent` | READ/WRITE | READ | READ |

The Admin Agent is the only agent that can see both private fleets simultaneously — and therefore the only agent that can detect governance conflicts before they cause compliance violations.

---

## Declarative Policy System

Fleet access is declared in [`policies/fleet_access.yaml`](policies/fleet_access.yaml):

```yaml
agents:
  sales-agent-1:
    allow: [fleet-org-shared, fleet-sales]
    deny: [fleet-legal]

  legal-agent-1:
    allow: [fleet-org-shared, fleet-legal]
    deny: [fleet-sales]

  admin-agent:
    allow: [fleet-org-shared, fleet-sales, fleet-legal]
    deny: []
```

`GovernanceEngine` loads this file at startup. Agent subclasses call `engine.get_authorized_fleets(agent_id)` instead of hardcoding their fleet lists. **To add a new agent or change access rules, edit the YAML — no Python changes required.**

Conflict detection rules live in [`policies/governance_rules.yaml`](policies/governance_rules.yaml). Each rule maps keyword patterns in fleet-sales content against keyword patterns in fleet-legal content. When both sides match, the conflict is flagged — deterministically, without an LLM call.

---

## Quick Start

```bash
# 1. Clone and install
git clone <repo>
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Fill in MEMCLAW_API_KEY, MEMCLAW_TENANT_ID
# Optional: AISA_API_KEY, AISA_MODEL for LLM features

# 3. Seed enterprise memories (15 records, idempotent)
python demo/seed_memories.py

# 4. Launch the interactive governance runtime
python app.py
```

**Docker quick start:**
```bash
# Copy and fill .env first, then:
docker compose -f docker/docker-compose.yml up
```

---

## Interactive Runtime (`app.py`)

```
Enterprise Multi-Agent Governance Runtime
Governance enforced before reasoning. The LLM never receives unauthorized memories.

  Select Agent:

  1. Sales Agent   (sales-agent-1)
       fleet-org-shared, fleet-sales | blocked: fleet-legal

  2. Legal Agent   (legal-agent-1)
       fleet-org-shared, fleet-legal | blocked: fleet-sales

  3. Admin Agent   (admin-agent)
       ALL fleets -- cross-fleet observer

  Select agent [1/2/3]: 1

Governance Engine
  Agent:   Sales Agent (sales-agent-1)
  Policy:  policies/fleet_access.yaml  ACTIVE
  Access:  v fleet-org-shared  v fleet-sales
  Blocked: x fleet-legal

  [Sales Agent] Query (exit / switch / reset): Is HealthSystem ready to close?

   fleet-org-shared   3
   fleet-sales        2
  Total memories in context: 5

  Sales Agent Response (Turn 1)
  Based on the available context ...

  [Audit] [14:22:31] sales-agent-1 | fleets: org-shared+sales | memories: 5
```

Multi-turn sessions are maintained per agent. Prior conversation context (last 3 turns) is automatically injected. Commands: `exit`, `switch` (return to agent selection), `reset` (clear session history).

---

## Conflict Detection Walkthrough

**Scenario:** The HealthSystem deal is a $3.6M contract. Sales is ready to close. Legal has placed a HIPAA BAA compliance hold.

When the Admin Agent queries HealthSystem, it retrieves from all three fleets:
- `fleet-org-shared`: Account status, contract value, timeline
- `fleet-sales`: Close pressure, negotiation tactics, BAA discussion
- `fleet-legal`: HIPAA hold, BAA not executed, CONTRACT EXECUTION BLOCKED

`ConflictDetector` matches rule `HIPAA-001` against both private fleet texts:
- Sales signal: `"contract"` found in fleet-sales content
- Legal signal: `"hipaa"` found in fleet-legal content

```
GOVERNANCE CONFLICT -- 1 rule(s) triggered:
  [HIGH] HIPAA-001: HIPAA BAA hold blocks contract execution
         Sales signal: 'contract'
         Legal signal: 'hipaa'
```

Sales Agent and Legal Agent each see only their side. **Only the Admin Agent can surface this conflict** — the structural fleet boundary is what makes the conflict detectable rather than invisible.

Run the flagship demo: `python demo/demo_conflict.py` (requires `AISA_API_KEY`)

---

## Governance Evidence: Audit Log

Every agent interaction is appended to `logs/session_audit.log` as a JSON line:

```json
{
  "timestamp": "2026-05-12T14:22:31",
  "agent_id": "sales-agent-1",
  "query": "Is HealthSystem ready to close?",
  "fleets_accessed": ["fleet-org-shared", "fleet-sales"],
  "memory_counts": {"fleet-org-shared": 3, "fleet-sales": 2},
  "total_memories": 5,
  "response_summary": "Based on the available context, the HealthSystem deal...",
  "session_id": "sales-agent-1-20260512142231"
}
```

This log is machine-verifiable governance evidence: which agent accessed which fleets, when, for which query, and what it retrieved. `fleet-legal` never appears in a `sales-agent-1` event — the boundary is structurally enforced and the log proves it.

---

## Environment Variables

Copy `.env.example` to `.env`:

| Variable | Required | Description |
|---|---|---|
| `MEMCLAW_API_KEY` | Yes | MemClaw dashboard API key |
| `MEMCLAW_TENANT_ID` | Yes | Tenant identifier |
| `MEMCLAW_BASE_URL` | No | Default: `https://memclaw.net/api/v1` |
| `AISA_API_KEY` | For LLM features | AISA gateway key |
| `AISA_MODEL` | No | Default: `deepseek/deepseek-chat` |
| `AISA_BASE_URL` | No | Default: `https://api.aisa.one/v1` |

Non-LLM features (policy validation, conflict detection, memory recall, audit logging) work without `AISA_API_KEY`.

---

## Demo Scripts

| Script | Requires LLM | Description |
|---|---|---|
| `demo/seed_memories.py` | No | Seed 15 enterprise memories (idempotent) |
| `demo/demo_shared.py` | No | Both agents recall from fleet-org-shared |
| `demo/demo_boundary.py` | No | Hard boundary: Sales queries fleet-legal -> zero results |
| `demo/demo_insights.py` | No | Per-fleet admin insights |
| `demo/demo_audit.py` | No | Audit log API attempt |
| `demo/demo_agent_loop.py` | Yes | 3-turn LLM reasoning loop |
| `demo/demo_audit_trail.py` | Yes | Session audit with LLM responses |
| `demo/demo_conflict.py` | Yes | HealthSystem conflict: only Admin sees both sides |

---

## Tests

```bash
pytest tests/ -v
```

| Test | What It Verifies |
|---|---|
| `test_isolation.py` | Sales recall contains no legal-fleet sentinel phrases |
| `test_scope_enforcement.py` | Legal recall contains no sales-fleet sentinel phrases |
| `test_shared_access.py` (x2) | Both agents can recall from fleet-org-shared |
| `test_agent_visibility.py::test_admin_generates_insights` | Admin insights API returns structured response |
| `test_agent_visibility.py::test_sales_agent_structural_boundary` | FLEET_LEGAL absent from SalesAgent allowed_fleets, blocked_fleets, and fleet_recall_map |
| `test_admin_cross_fleet.py` (x2) | AdminFleet recalls from all 3 fleets; sees both compliance and sales content |

The structural boundary test (`test_sales_agent_structural_boundary`) is the most important. It verifies that the governance guarantee is enforced in code — `fleet-legal` is not just absent from the LLM context but structurally unreachable from the sales agent.

---

## Extending the System

**Add a new fleet:**
1. Add the fleet ID constant to `config.py`
2. Update `policies/fleet_access.yaml` with which agents may access it
3. Create a new fleet facade in `fleets/`
4. Update relevant agent `__init__` to include the new recall callable

**Add a new agent:**
1. Add the agent ID to `config.py`
2. Add the agent's access policy to `policies/fleet_access.yaml`
3. Subclass `BaseAgent` with the appropriate `fleet_recall_map`
4. Add it to `app.py`'s agent map

**Add a conflict detection rule:**
Edit `policies/governance_rules.yaml` — no code changes required.

**Add a new enterprise client:**
Add 3 memory records to `scenarios/enterprise_scenario.py` (shared, sales, legal) and re-run `python demo/seed_memories.py`.

---

## Phase B — OpenClaw Deployment

[OpenClaw](https://openclaw.ai) adds a messaging runtime layer on top of the Python governance architecture. It enables the Sales, Legal, and Admin agents to operate in Slack, Telegram, Discord, or any OpenClaw-supported platform.

Fleet boundaries are identical to the Python implementation — enforced at the MemClaw API layer via `fleet_ids` arrays, regardless of runtime.

| Agent | Fleet Access |
|---|---|
| sales-agent | fleet-org-shared, fleet-sales |
| legal-agent | fleet-org-shared, fleet-legal |
| admin-agent | fleet-org-shared, fleet-sales, fleet-legal (read) |

See [openclaw/README.md](openclaw/README.md) for full setup.

```
openclaw/
├── openclaw.json               # Gateway config (models, agents, MCP server)
├── agents/
│   ├── sales-agent/            # SOUL.md + AGENTS.md
│   ├── legal-agent/            # SOUL.md + AGENTS.md
│   └── admin-agent/            # SOUL.md + AGENTS.md
└── skills/
    └── memclaw-governance.md   # Shared governance skill
```
