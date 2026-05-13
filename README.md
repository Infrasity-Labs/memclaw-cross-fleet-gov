# MemClaw × OpenClaw: Governed Multi-Agent Memory

> A reference implementation for governed multi-agent memory orchestration using MemClaw and OpenClaw.

This project demonstrates how specialized AI agents can share organizational memory without sharing unrestricted access to the same retrieval layer.

Traditional shared RAG systems expose every indexed memory to every agent. MemClaw solves this through fleet-scoped retrieval and governed memory access.

In this architecture:

- Sales agents retrieve commercial context
- Legal agents retrieve compliance context
- Admin agents perform cross-fleet synthesis

Unauthorized memories are never retrieved or ranked, which prevents cross-domain leakage before context reaches the model.

This repository showcases:

- Governed memory retrieval
- Multi-agent context isolation
- Fleet-scoped recall
- Cross-fleet orchestration
- Hybrid semantic + keyword retrieval
- Trust-aware memory access

---

# Shared RAG vs Governed Retrieval

| Shared RAG Systems             | MemClaw Governed Retrieval              |
| ------------------------------ | --------------------------------------- |
| Shared retrieval pool          | Fleet-scoped retrieval                  |
| Prompt-level restrictions      | Query-time enforcement                  |
| Agents can retrieve everything | Agents retrieve only authorized context |
| Weak auditability              | Read/write audit trail                  |
| Retrieval leakage risk         | Governed search boundaries              |
| Context contamination          | Explicit memory partitions              |

---

# Core Concepts

## MemClaw

MemClaw is a governed shared memory platform for AI agent fleets.

It provides:

- Fleet-scoped memory isolation
- Query-time retrieval enforcement
- Hybrid semantic + keyword recall
- Trust-aware retrieval policies
- Structured memory lifecycle management
- Auditability for reads and writes

Every memory stored in MemClaw carries governance metadata including:

- `fleet_id`
- `agent_id`
- `tenant_id`
- `visibility_scope`
- `trust_level`

Core MCP tools used in this repository:

| Tool                 | Purpose                                   |
| -------------------- | ----------------------------------------- |
| `memclaw_write`      | Persist governed memory                   |
| `memclaw_recall`     | Hybrid retrieval with fleet scoping       |
| `memclaw_manage`     | Update, archive, or delete memory         |
| `memclaw_list`       | Metadata-based browsing                   |
| `memclaw_entity_get` | Retrieve entities and graph relationships |

---

## OpenClaw

OpenClaw acts as the orchestration layer.

It manages:

- Agent sessions
- Context assembly
- MCP routing
- Workspace loading
- Tool execution

Each agent loads its own:

- `SOUL.md`
- `AGENTS.md`
- governance skill

during session startup.

---

# System Architecture

![Architecture Diagram](./memclaw%20flow.png)


---

# Repository Structure

```text
.
├── openclaw.json
├── .env.example
├── README.md
├── agents/
│   ├── sales-agent/
│   ├── legal-agent/
│   └── admin-agent/
├── skills/
│   └── memclaw-governance.md
└── workspace/
    └── .openclaw/
        ├── workspace-sales-agent/
        ├── workspace-legal-agent/
        └── workspace-admin-agent/
```

---

# Agent Profiles

| Agent         | Fleet Access                                     | Responsibilities                                                        | Restricted From                                      |
| ------------- | ------------------------------------------------ | ----------------------------------------------------------------------- | ---------------------------------------------------- |
| `sales-agent` | `fleet-org-shared`, `fleet-sales`                | Renewals, pipeline context, commercial discussions, account health      | Compliance reviews, legal holds, GDPR investigations |
| `legal-agent` | `fleet-org-shared`, `fleet-legal`                | Compliance reviews, regulatory risk, GDPR workflows, policy enforcement | Pricing strategy, commercial pipeline data           |
| `admin-agent` | `fleet-org-shared`, `fleet-sales`, `fleet-legal` | Cross-fleet synthesis, governance escalation, contradiction detection   | N/A                                                  |

---

# The Governance Skill

`skills/memclaw-governance.md` acts as the shared behavioral contract across all agents.

It defines:

- retrieval conventions
- fleet-scoping rules
- write protocols
- governance constraints

Core rules:

1. Always pass `fleet_ids` as arrays
2. Recall before entity-specific responses
3. Persist durable context
4. Write to the correct fleet
5. Do not infer across inaccessible scopes

---

# Installation

## Clone the repository

```bash
git clone https://github.com/your-org/memclaw-cross-fleet-gov.git
cd memclaw-cross-fleet-gov
```

## Configure environment variables

```bash
cp .env.example .env
```

```env
MEMCLAW_API_KEY=your_api_key
MEMCLAW_API_URL=http://localhost:8000
```

## Configure fleets

```bash
curl -X PATCH http://localhost:8000/api/v1/agents/sales-agent \
-H "Content-Type: application/json" \
-d '{"fleet_id":"fleet-sales","trust_level":2}'
```

```bash
curl -X PATCH http://localhost:8000/api/v1/agents/legal-agent \
-H "Content-Type: application/json" \
-d '{"fleet_id":"fleet-legal","trust_level":3}'
```

```bash
curl -X PATCH http://localhost:8000/api/v1/agents/admin-agent \
-H "Content-Type: application/json" \
-d '{"fleet_id":"fleet-admin","trust_level":3}'
```

## Start the gateway

```bash
openclaw gateway
```

## Open a session

```bash
openclaw chat --session governance-demo
```

---

# Verification

## Write governed memory

```text
/agent legal-agent
```

```text
Use memclaw_write to store:
"Stratus Aero compliance review identified unresolved export-control restrictions affecting aerospace telemetry datasets."

Fleet: fleet-legal
```

## Successful retrieval

```text
Use memclaw_recall to summarize Stratus Aero compliance review.
```

Expected:

- export-control restrictions
- aerospace telemetry datasets
- legal-context retrieval

---

## Governance isolation test

```text
/agent sales-agent
```

```text
Use memclaw_recall to summarize Stratus Aero compliance review.
```

Expected:

- no accessible memories
- retrieval denial
- fleet isolation enforcement

---

# Cross-Fleet Conflict Detection

The admin agent enables cross-fleet synthesis.

Example:

```text
fleet-sales:
  HealthSystem Inc renewal in negotiation

fleet-legal:
  HealthSystem Inc blocked by GDPR compliance hold
```

The sales agent sees only commercial context.

The legal agent sees only compliance context.

The admin agent sees both.

This enables:

- contradiction detection
- governance escalation
- enterprise-wide synthesis

---

# Troubleshooting

## Retrieval hangs indefinitely

Most common cause:

```text
Rejected workspace path outside openclawDir
```

Fix:

- use relative workspace paths
- avoid malformed Windows absolute paths
- restart the gateway after config updates

Recommended workspace config:

```json
{
  "id": "legal-agent",
  "workspace": "./workspace/.openclaw/workspace-legal-agent"
}
```

---

## Gateway restart fails

```powershell
taskkill /F /IM node.exe
```

Then restart:

```bash
openclaw gateway
```

---

## No memories returned

Check:

- fleet configuration
- trust levels
- memory counts
- active gateway session

---

## Context instability

Avoid reusing overloaded sessions.

```bash
openclaw chat --session clean-demo
```
