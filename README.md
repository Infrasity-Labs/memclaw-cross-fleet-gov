<p align="center">
  <img src="./docs/images/memclaw_banner.jpeg" alt="MemClaw Cross-Fleet Governance" width="100%" />
</p>

<h1 align="center">MemClaw Cross-Fleet Governed Memory</h1>

<p align="center">
  <strong>MemClaw gives multi-agent fleets governed, shared, self-improving memory.</strong><br/>
  This repo shows MemClaw enforcing fleet-scoped memory boundaries across three OpenClaw agents<br/>
  with query-time fleet filtering, per-row agent ACLs, and cross-fleet synthesis.
</p>


<p align="center">
  <a href="https://memclaw.net/docs"><img src="https://img.shields.io/badge/docs-memclaw.net-2A9D8F?style=flat-square" /></a>
  <a href="https://github.com/caura-ai/caura-memclaw"><img src="https://img.shields.io/badge/Memory-MemClaw-2A9D8F?style=flat-square" /></a>
  <img src="https://img.shields.io/badge/Orchestration-OpenClaw-3A86FF?style=flat-square" />
  <img src="https://img.shields.io/badge/Isolation-Fleet--Scoped-E76F51?style=flat-square" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache--2.0-yellow.svg?style=flat-square" /></a>
  <a href="https://github.com/Infrasity-Labs/memclaw-cross-fleet-gov/stargazers"><img src="https://img.shields.io/github/stars/Infrasity-Labs/memclaw-cross-fleet-gov?style=flat-square" /></a>
</p>

<p align="center">
  <a href="#what-is-openclaw">OpenClaw</a> ·
  <a href="#what-is-memclaw">MemClaw</a> ·
  <a href="#demo">Demo</a> ·
  <a href="#the-problem">The Problem</a> ·
  <a href="#how-it-works">How It Works</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#agent-scope-matrix">Agent Scope</a> ·
  <a href="#quickstart">Quickstart</a> ·
  <a href="#governance-validation">Validation</a> ·
  <a href="#creating-a-new-fleet">New Fleet</a> ·
  <a href="https://memclaw.net/docs">Docs</a>
</p>

---

> _Three agents. One memory backend. Fleet-scoped recall._
> Sales sees pipeline. Legal sees compliance. Admin sees everything and surfaces the conflicts.

---

## What is OpenClaw

[OpenClaw](https://www.stack-junkie.com/blog/openclaw-system-prompt-design-guide) is an open-source agent orchestration gateway. It runs locally as a daemon, registers named agents from workspace directories, and exposes them through a unified chat interface and API. Each agent has its own workspace (a directory containing identity files: `SOUL.md`, `AGENTS.md`, `IDENTITY.md`) that are injected as system context at session start, along with its own plugin bindings (MCP servers, memory backends, tools).

In this repo, OpenClaw is doing three things:

- **Routing:** `/agent sales-agent` targets a specific registered agent
- **Context injection:** loads each agent's `SOUL.md` and `AGENTS.md` before the first message
- **Plugin wiring:** registers the MemClaw MCP server so agents can call `memclaw_*` tools natively as tool calls

```bash
npm install -g openclaw@latest
```

---

## What is MemClaw

[MemClaw](https://github.com/caura-ai/caura-memclaw) is open-source multi-agent memory for AI agent fleets: governed, shared, and self-improving. Agents write plain text. MemClaw turns it into searchable, governed, structured memory with automatic enrichment, lifecycle management, and cross-agent knowledge sharing.

**The core loop: write, recall, compound.** Every interaction makes the next one smarter.

What makes MemClaw different from a vector database:

| Capability                  | What it means                                                                                                                                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Fleet isolation**         | Memory partitioned by `fleet_id`. Every recall passes a `WHERE fleet_id IN (...)` predicate before the search runs. Boundaries are a query-layer contract, not prompt instructions.                          |
| **LLM enrichment on write** | Every `memclaw_write` auto-classifies type, generates title/summary/tags, scans PII, extracts entities, detects contradictions from a single `content` field                                                 |
| **Hybrid recall**           | `memclaw_recall` combines vector similarity, keyword search, and knowledge graph traversal in one call                                                                                                       |
| **8-status lifecycle**      | Memories move through `active`, `pending`, `confirmed`, `outdated`, `conflicted`, `archived`, `deleted` statuses automatically; supersession is tracked via `supersedes_id` FK (`memclaw_manage op=lineage`) |
| **Crystallizer**            | LLM batch process that merges near-duplicate memories into canonical atomic facts with full provenance                                                                                                       |
| **Audit trail**             | Every read and write logged. "Which agent recalled this memory and when" is always answerable                                                                                                                |
| **Karpathy Loop**           | Agents report outcomes via `memclaw_evolve`; the system reinforces what works and generates preventive rules on failure                                                                                      |

This repo is a **use-case implementation**: three OpenClaw agents (Sales, Legal, Admin) operating against a single MemClaw tenant with three fleet partitions, showing what MemClaw's governance layer looks like in a real multi-agent deployment.

> **Do you need a MemClaw API key?** No. For the local Docker deploy, `MEMCLAW_API_KEY` stays blank. You only need a key if you use the managed cloud service at [memclaw.net](https://memclaw.net).

<p align="center">
  <a href="https://github.com/caura-ai/caura-memclaw"><strong>MemClaw source (Apache 2.0)</strong></a> ·
  <a href="https://memclaw.net/docs"><strong>Documentation</strong></a> ·
  <a href="https://memclaw.net"><strong>Managed cloud (free tier available)</strong></a>
</p>

---

## Demo

![memclaw demo gif](./docs/images/memclaw-demo.gif)

### 1. Sales agent writes to `fleet-sales`

![Sales agent write](./docs/images/2_memclaw_write_sales_agent.png)

### 2. Legal agent writes to `fleet-legal`

![Legal agent write](./docs/images/legal-agent-memclaw-write.png)

### 3. Admin agent recalls cross-fleet and surfaces the conflict

![Admin agent cross-fleet recall](./docs/images/memclaw%20recall.png)

> **The conflict:** `fleet-sales` shows the Acme Corp renewal in active negotiation. `fleet-legal` shows the MSA auto-renewal clause requiring legal review before any amendments. Only the admin agent sees both, because only it declares all three fleets in its `memclaw_recall` call.

---

## The Problem

**Why not just use a single-agent memory system?** In an enterprise, you cannot dump all AI memory into one flat database. Legal handles sensitive compliance data that Sales should not see, but both need to share general account context. Single-agent setups force you to choose between completely siloed amnesia or a massive security nightmare.

| Approach                | Problem                                                                                             |
| ----------------------- | --------------------------------------------------------------------------------------------------- |
| Total memory siloing    | Agents repeat work, miss shared context, have amnesia                                               |
| Open shared memory      | Sales reads Legal holds. Legal reads negotiation ceilings. Data leaks.                              |
| Prompt-level separation | "Don't mention compliance data" -- the data still passes through recall. LLMs can still surface it. |

**MemClaw resolves this at the retrieval layer.** Fleet boundaries are enforced as query predicates before the hybrid search runs. An agent cannot surface what it was never given. No prompt engineering required -- the enforcement happens in the query layer, not in the system prompt.

---

## How MemClaw Enforces Fleet Boundaries

Every recall call passes through MemClaw's fleet filter before the search executes:

```
Agent calls memclaw_recall(fleet_ids=["fleet-sales", "fleet-org-shared"])
                                |
                                v
              MemClaw applies: WHERE fleet_id IN ('fleet-sales', 'fleet-org-shared')
                                |
                      +---------+----------+
                      |  Search executes   |
                      |  inside boundary   |
                      +---------+----------+
                                |
              fleet-legal records: never searched, never scored, never returned
                                |
                                v
                    Ranked results returned to agent
```

This is not a prompt rule. It is a database predicate inside MemClaw's storage layer -- the `fleet_ids` filter runs before context assembly, before scoring, before ranking.

**Important:** in the OSS self-hosted deploy, the boundary holds as long as the agent declares its `fleet_ids` honestly. An agent that passes `["fleet-legal"]` instead of `["fleet-sales"]` would cross the boundary -- the storage layer filters to what is declared, but does not validate what is declared against the agent's identity. For hard cross-domain isolation that cannot be bypassed at the prompt level, use separate tenants (see below) or the managed service.

---

## Memory Scope and Visibility Mechanisms

MemClaw's access model has three layers, each enforced independently:

### 1. Tenant boundary (strongest)

A tenant is a full database-level partition. Memories in tenant A are physically separated from tenant B -- no query can cross tenants. In the managed service ([memclaw.net](https://memclaw.net)), each organization gets its own tenant with full row-level database isolation. In the OSS local deploy, a single `default` tenant is used; separate tenants require separate instances.

**For hard cross-domain isolation** (legal data must never be reachable by a sales agent, period), the recommended pattern is separate tenants per domain. The admin agent performs explicit fan-out recall with provenance merging:

1. Recall from tenant-A / fleet-A
2. Recall from tenant-B / fleet-B
3. Merge with source labels
4. Write synthesis to governance scope

This is the only configuration where the isolation cannot be bypassed by changing `fleet_ids`.

### 2. Fleet boundary (query-time enforcement)

Inside a tenant, fleets are the primary scope mechanism. Every memory record carries a `fleet_id`. On every `memclaw_recall` call, the declared `fleet_ids` array becomes a `WHERE fleet_id IN (...)` predicate that executes before the hybrid search. Records outside the declared fleets are never loaded, never scored, never ranked.

```
memclaw_recall(fleet_ids=["fleet-sales"])
    -> WHERE fleet_id IN ('fleet-sales')
    -> vector + keyword search runs only on matching rows
    -> fleet-legal rows: not loaded, not scored, not returned
```

The boundary is enforced by the storage layer and is auditable. Its strength depends on agents declaring their `fleet_ids` according to their `AGENTS.md` contract -- the governance contract is real, but it is a query-layer contract, not a physical key boundary.

### 3. `scope_agent` -- per-row agent ACL

When a memory is written with `scope: "scope_agent"`, only the writing agent can read it back. This is a real per-row server-side ACL enforced regardless of `fleet_ids`. Use it for agent-private working memory that should never appear in shared recall results.

### 4. Agent trust tier (write scope)

Each agent has a declared scope in its `IDENTITY.md`. MemClaw uses this to enforce:

- **Write scope:** which `fleet_id` an agent can write to (gated by trust tier)
- **Cross-fleet synthesis:** only agents with multi-fleet read access (like `admin-agent`) are configured to perform fan-out recall and merge results with source provenance labels

### OSS vs. managed isolation

| Isolation layer    | OSS local deploy                                     | Managed (memclaw.net)                          |
| ------------------ | ---------------------------------------------------- | ---------------------------------------------- |
| Tenant isolation   | Single tenant; separate instances for true isolation | Full DB-level tenant isolation per org         |
| Fleet isolation    | Query predicate enforcement (this repo)              | Query predicate + row-level security           |
| `scope_agent` ACL  | Per-row server-side ACL                              | Per-row server-side ACL                        |
| Audit trail        | Available                                            | Available with retention policies              |
| Fleet provisioning | Auto-created on first write                          | Dashboard or API, with access control policies |

For production deployments where legal/sales data separation must be auditable, the managed service or a separate-tenant pattern provides the stronger guarantee. For experimentation, learning, and development, the local OSS deploy used in this repo demonstrates the fleet boundary mechanics end to end.

---

## Architecture

```
+---------------------------------------------------------------------+
|  OpenClaw Gateway                                                   |
|                                                                     |
|  +--------------+  +--------------+  +------------------------+    |
|  | sales-agent  |  | legal-agent  |  |      admin-agent       |    |
|  |              |  |              |  |                        |    |
|  | fleet_ids:   |  | fleet_ids:   |  | fleet_ids:             |    |
|  | fleet-sales  |  | fleet-legal  |  | fleet-sales            |    |
|  | fleet-org    |  | fleet-org    |  | fleet-legal            |    |
|  |   -shared    |  |   -shared    |  | fleet-org-shared       |    |
|  +------+-------+  +------+-------+  +----------+-------------+    |
|         |                 |                      |                  |
|         +-----------------+----------------------+                  |
|                           |  memclaw_* MCP tools                   |
+---------------------------+-----------------------------------------+
                            |
                            v
+---------------------------------------------------------------------+
|  MemClaw  (local Docker / memclaw.net)                              |
|                                                                     |
|  Layer 1 -- Tenant boundary (strongest)                            |
|  Full DB-level partition. Managed service only (or separate         |
|  OSS instances). Cannot be crossed by any query.                    |
|                                                                     |
|  Layer 2 -- scope_agent  (per-row ACL)                             |
|  Server-side ACL on each memory row. Only the writing agent         |
|  can recall it, regardless of fleet_ids.                            |
|                                                                     |
|  Layer 3 -- fleet_ids filter  (query predicate)                    |
|  WHERE fleet_id IN (...) runs before vector + keyword search.       |
|  Records outside declared fleets are never loaded or scored.        |
|  Boundary strength depends on agents declaring fleet_ids            |
|  honestly per their AGENTS.md contract.                             |
|                                                                     |
|  +-----------------+  +-----------------+  +------------------+    |
|  |  fleet-sales    |  |  fleet-legal    |  | fleet-org-shared |    |
|  |                 |  |                 |  |                  |    |
|  | pipeline        |  | GDPR hold       |  | account context  |    |
|  | deal stages     |  | compliance      |  | shared rules     |    |
|  | renewals        |  | risk flags      |  |                  |    |
|  +-----------------+  +-----------------+  +------------------+    |
+---------------------------------------------------------------------+
```

---

## Agent Scope Matrix

| Agent         | Fleet Access                       | Primary Use                               | Hard Boundary               |
| ------------- | ---------------------------------- | ----------------------------------------- | --------------------------- |
| `sales-agent` | `fleet-sales` · `fleet-org-shared` | Pipeline, renewals, deal stage            | Cannot access `fleet-legal` |
| `legal-agent` | `fleet-legal` · `fleet-org-shared` | Holds, compliance, risk flags             | Cannot access `fleet-sales` |
| `admin-agent` | All three fleets                   | Cross-fleet synthesis, conflict detection | None                        |

### Governance boundaries verified

The fleet scoping in each agent's `AGENTS.md` is confirmed correct:

- `sales-agent` always passes `fleet_ids: ["fleet-sales", "fleet-org-shared"]`. The instruction "never include `fleet-legal`" is explicit and unconditional.
- `legal-agent` always passes `fleet_ids: ["fleet-legal", "fleet-org-shared"]`. The instruction "never include `fleet-sales`" is explicit and unconditional.
- `admin-agent` uses all three fleets and is required to label the source fleet on every synthesized result. Conflict escalation is mandatory -- the agent cannot resolve conflicts unilaterally.
- All three agents pass `agent_id` on every tool call, which is required for per-row ACL enforcement and audit logging.

The boundaries are enforced at two levels: the query predicate in MemClaw (storage layer) and the `AGENTS.md` contract (prompt layer). The query predicate is the primary enforcement mechanism; the `AGENTS.md` instruction is the governance contract that prevents an agent from deliberately passing wrong `fleet_ids`.

---

## MemClaw MCP Tools

MemClaw exposes its full capability surface through 10 MCP tools. OpenClaw registers these at gateway start and agents call them as standard tool calls.

| Tool                 | What it does                                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `memclaw_write`      | Store memory with auto-enrichment: type, title, tags, PII scan, entity extraction, contradiction check                   |
| `memclaw_recall`     | Hybrid vector + keyword search scoped to declared `fleet_ids`                                                            |
| `memclaw_manage`     | Read, update, transition, delete, bulk-delete, or trace lineage of a specific memory                                     |
| `memclaw_list`       | Browse by metadata: type, status, agent, date                                                                            |
| `memclaw_insights`   | LLM-powered reflection with six focus modes: `contradictions`, `failures`, `stale`, `divergence`, `patterns`, `discover` |
| `memclaw_stats`      | Aggregate counts by type, agent, status                                                                                  |
| `memclaw_evolve`     | Report outcomes against recalled memories and close the learning loop                                                    |
| `memclaw_tune`       | Adjust recall weighting and enrichment parameters                                                                        |
| `memclaw_entity_get` | Fetch a specific entity record from the knowledge graph                                                                  |
| `memclaw_doc`        | Return tool schema documentation                                                                                         |

**Memory lifecycle:** MemClaw moves memories through eight statuses (`active`, `pending`, `confirmed`, `cancelled`, `outdated`, `conflicted`, `archived`, `deleted`) based on contradiction detection and outcome feedback. Supersession relationships are tracked via the `supersedes_id` field; use `memclaw_manage op=lineage` to trace them. No manual cleanup required.

**Crystallizer:** MemClaw's LLM batch process merges near-duplicate memories into canonical atomic facts with full provenance retained. Runs nightly or on-demand.

**Karpathy Loop:** agents call `memclaw_evolve` with `related_ids` to report whether recalled memories led to good outcomes. MemClaw reinforces memories that work and auto-generates preventive `rule`-type memories on failure.

---

## Why MemClaw vs a Vector DB

|                         | Shared RAG                    | MemClaw Fleet Governance                                                                                      |
| ----------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Separation mechanism    | Prompt instruction            | Query predicate enforced at storage layer                                                                     |
| Retrieval scope         | Broad: all vectors searched   | Narrow: `fleet_ids` filter before search                                                                      |
| Cross-agent leakage     | Possible if prompt is ignored | Data outside declared `fleet_ids` is never retrieved; boundary strength depends on isolation tier (see above) |
| Audit trail             | None                          | Every read and write logged                                                                                   |
| Contradiction detection | Manual                        | Automatic on write: RDF triple comparison + LLM analysis                                                      |

---

## Repository Structure

```
.
+-- .env.example
+-- .openclaw/
|   +-- openclaw.json               <- Gateway config: model, agents, MCP server
+-- agents/
|   +-- sales-agent/
|   |   +-- SOUL.md                 <- Personality, tone, hard limits
|   |   +-- AGENTS.md               <- Fleet scope, recall protocol, write rules
|   |   +-- IDENTITY.md             <- Fleet scope and MemClaw identity
|   +-- legal-agent/
|   |   +-- SOUL.md
|   |   +-- AGENTS.md
|   |   +-- IDENTITY.md
|   +-- admin-agent/
|       +-- SOUL.md
|       +-- AGENTS.md
|       +-- IDENTITY.md
+-- skills/
    +-- memclaw-governance.md       <- Shared skill: fleet_ids rules, recall + write protocol
```

**`SOUL.md`** is injected first on every session and defines who the agent is.
**`AGENTS.md`** is injected second and defines what the agent does, which fleets it can access, and how it uses MemClaw.
**`memclaw-governance.md`** is a shared skill copied into every agent workspace. Update once, redeploy to all agents.

---

## Prerequisites

- [Node.js 24+](https://nodejs.org/)
- OpenClaw CLI: `npm install -g openclaw@latest`
- [Docker](https://www.docker.com/) (to run MemClaw locally -- the default path)
- An LLM gateway API key, or a local model via Ollama (no key required, see below)

This repo runs against a **local MemClaw instance** by default -- no account, no API key, no cloud dependency. You spin up MemClaw with a single Docker command and the three fleet partitions are created automatically on first write.

**Two LLM options:**

| Option                                  | Requires                                                | Notes                                     |
| --------------------------------------- | ------------------------------------------------------- | ----------------------------------------- |
| **LLM gateway / DeepSeek V3** (default) | API key from your LLM gateway provider                  | OpenAI-compatible endpoint; fastest setup |
| **Ollama** (fully local, no key)        | [Ollama](https://ollama.com) installed + a pulled model | Free, private, no rate limits             |

> **Want managed MemClaw instead of Docker?** [memclaw.net](https://memclaw.net) offers a hosted service (free tier available) with a dashboard and provisioned fleets. Set `MEMCLAW_API_URL=https://memclaw.net/api/v1` and `MEMCLAW_API_KEY=mc_...` in your `.env` -- everything else stays the same. The managed service also provides full tenant isolation at the database level.

---

## OpenClaw Setup

Do this once before running the quickstart.

### New users

```bash
openclaw onboard --install-daemon

# LLM gateway (OpenAI-compatible endpoint):
openclaw onboard --non-interactive --accept-risk \
  --custom-api-key "your-llm-gateway-key" \
  --custom-base-url "https://your-gateway.example.com/v1"

# Ollama (fully local, no key):
openclaw onboard --non-interactive --accept-risk \
  --custom-api-key "ollama" \
  --custom-base-url "http://localhost:11434/v1"

openclaw doctor
```

### Existing users

If agent workspace paths are doubling on Windows (known path resolution issue), use the junction approach in the Quickstart below. `openclaw agents add` takes an absolute path to register the workspace, but `openclaw.json` stores only the directory name relative to `~/.openclaw/`. The two are consistent -- `workspace-sales-agent` in `openclaw.json` resolves to `~/.openclaw/workspace-sales-agent`:

```json
{
  "agents": {
    "list": [
      { "id": "sales-agent", "workspace": "workspace-sales-agent" },
      { "id": "legal-agent", "workspace": "workspace-legal-agent" },
      { "id": "admin-agent", "workspace": "workspace-admin-agent" }
    ]
  }
}
```

Run `openclaw doctor` if any agent fails to bind on gateway start.

---

## Quickstart

### 1. Clone

```bash
git clone https://github.com/Infrasity-Labs/memclaw-cross-fleet-gov.git
cd memclaw-cross-fleet-gov
```

### 2. Start MemClaw locally

```bash
docker run -d --name memclaw -p 8000:8000 ghcr.io/caura-ai/caura-memclaw:latest
```

MemClaw is now running at `http://localhost:8000`. No API key required. Fleet partitions (`fleet-org-shared`, `fleet-sales`, `fleet-legal`) are created automatically on first write.

### 3. Configure environment

```bash
cp .env.example .env
```

The defaults in `.env.example` already point to your local MemClaw instance. Fill in your LLM provider:

**Option A -- LLM gateway (OpenAI-compatible)**

```env
# MemClaw (local)
MEMCLAW_API_URL=http://localhost:8000
MEMCLAW_API_KEY=                        # leave blank for local deploy
MEMCLAW_TENANT_ID=default
MEMCLAW_AUTO_WRITE_TURNS=false

# LLM gateway
LLM_API_KEY=sk-...                      # your LLM gateway API key
LLM_MODEL=deepseek-v3                   # or any model your gateway supports
LLM_BASE_URL=https://your-gateway.example.com/v1
```

**Option B -- Ollama (fully local, no API key)**

First pull a model:

```bash
ollama pull qwen2.5:14b   # or llama3.1:8b, mistral, etc.
```

Then set your `.env`:

```env
# MemClaw (local)
MEMCLAW_API_URL=http://localhost:8000
MEMCLAW_API_KEY=
MEMCLAW_TENANT_ID=default
MEMCLAW_AUTO_WRITE_TURNS=false

# Ollama
LLM_API_KEY=ollama                      # any non-empty string
LLM_MODEL=qwen2.5:14b                   # must match your pulled model name
LLM_BASE_URL=http://localhost:11434/v1
```

Ollama's OpenAI-compatible endpoint (`/v1`) works with OpenClaw's `--custom-base-url` flag out of the box.

### 4. Deploy agent workspaces

**macOS / Linux**

```bash
cp -r agents/sales-agent ~/.openclaw/workspace-sales-agent
cp -r agents/legal-agent ~/.openclaw/workspace-legal-agent
cp -r agents/admin-agent ~/.openclaw/workspace-admin-agent

for agent in sales-agent legal-agent admin-agent; do
  mkdir -p ~/.openclaw/workspace-$agent/skills
  cp skills/memclaw-governance.md ~/.openclaw/workspace-$agent/skills/
done
```

**Windows (PowerShell, run as admin)**

```powershell
# Set $REPO to the directory where you cloned this repo
$REPO = "C:\path\to\memclaw-cross-fleet-gov"   # <-- update this

# Create junctions so OpenClaw resolves paths correctly
New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace-sales-agent" `
  -Target "$REPO\agents\sales-agent"

New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace-legal-agent" `
  -Target "$REPO\agents\legal-agent"

New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace-admin-agent" `
  -Target "$REPO\agents\admin-agent"

# Copy shared governance skill into each workspace
foreach ($agent in @("sales-agent","legal-agent","admin-agent")) {
  New-Item -ItemType Directory -Force "$HOME\.openclaw\workspace-$agent\skills" | Out-Null
  Copy-Item "skills\memclaw-governance.md" "$HOME\.openclaw\workspace-$agent\skills\"
}
```

### 5. Register agents with OpenClaw

```bash
# macOS / Linux
openclaw agents add sales-agent --workspace ~/.openclaw/workspace-sales-agent --non-interactive
openclaw agents add legal-agent --workspace ~/.openclaw/workspace-legal-agent --non-interactive
openclaw agents add admin-agent --workspace ~/.openclaw/workspace-admin-agent --non-interactive
```

```powershell
# Windows (PowerShell)
openclaw agents add sales-agent --workspace "$HOME\.openclaw\workspace-sales-agent" --non-interactive
openclaw agents add legal-agent --workspace "$HOME\.openclaw\workspace-legal-agent" --non-interactive
openclaw agents add admin-agent --workspace "$HOME\.openclaw\workspace-admin-agent" --non-interactive
```

### 6. Install the MemClaw plugin

```bash
# macOS / Linux -- run once per fleet
MEMCLAW_URL=http://localhost:8000
for fleet in fleet-org-shared fleet-sales fleet-legal; do
  curl -sf "$MEMCLAW_URL/api/v1/install-plugin?fleet_id=$fleet&api_url=$MEMCLAW_URL" | bash
done
```

```powershell
# Windows (PowerShell)
$MEMCLAW_URL = "http://localhost:8000"
foreach ($fleet in @("fleet-org-shared","fleet-sales","fleet-legal")) {
  Invoke-Expression (Invoke-RestMethod "$MEMCLAW_URL/api/v1/install-plugin?fleet_id=$fleet&api_url=$MEMCLAW_URL")
}
```

If you are using the managed service with an API key, add `-H "X-API-Key: $MEMCLAW_API_KEY"` to the curl call.

### 7. Start the gateway

```bash
openclaw gateway restart
openclaw agents list --bindings   # verify all three agents are registered
openclaw dashboard                 # http://127.0.0.1:18789
```

### 8. Confirm MemClaw tools are loaded

```
List available tools.
```

Expected: `memclaw_recall`, `memclaw_write`, `memclaw_stats`, and other `memclaw_*` tools appear in the session.

---

## Governance Validation

Run these in sequence to verify that MemClaw's fleet isolation is working end to end. Each step demonstrates a different layer of MemClaw's governance model: scoped writes, blocked recall, permitted recall, contradiction seeding, and cross-fleet synthesis.

### Step A: Write to `fleet-legal`

```
/agent legal-agent

Use memclaw_write to store:
  content: "HealthSystem Inc is under active GDPR hold pending DPO sign-off. No contracts or renewals can execute until hold is lifted."
  memory_type: "rule"
  fleet_id: "fleet-legal"
  agent_id: "legal-agent"
```

### Step B: Sales agent should not see it

```
/agent sales-agent

Use memclaw_recall with:
  fleet_ids: ["fleet-sales", "fleet-org-shared"]
  query: "HealthSystem Inc GDPR hold"
  agent_id: "sales-agent"
```

**Expected:** empty result. `fleet-legal` is not in the search space for this call.

### Step C: Legal agent sees it

```
/agent legal-agent

Use memclaw_recall with:
  fleet_ids: ["fleet-legal", "fleet-org-shared"]
  query: "HealthSystem Inc GDPR hold"
  agent_id: "legal-agent"
```

**Expected:** the compliance hold memory is returned.

### Step D: Write a conflicting sales record

```
/agent sales-agent

Use memclaw_write to store:
  content: "HealthSystem Inc renewal in final commercial negotiation. Proposed $420k. Deal stage: negotiation. Expected close Q3 2026."
  memory_type: "episode"
  fleet_id: "fleet-sales"
  agent_id: "sales-agent"
```

### Step E: Admin sees both and surfaces the conflict

```
/agent admin-agent

Use memclaw_recall with:
  fleet_ids: ["fleet-sales", "fleet-legal", "fleet-org-shared"]
  query: "HealthSystem Inc status"
  agent_id: "admin-agent"
```

**Expected:** admin surfaces both the active renewal negotiation from `fleet-sales` and the GDPR hold from `fleet-legal`, flags the contradiction, and identifies this as a cross-team escalation.

### Step F: Run insights on the admin agent

```
/agent admin-agent

Use memclaw_insights with focus: "contradictions"
```

**Expected:** MemClaw's LLM-powered reflection surfaces the HealthSystem Inc conflict with source fleet labels.

---

## Tenant and Fleet Model

```
Tenant: your-org
+-- fleet-org-shared    -> company-wide context, all agents read + write
+-- fleet-sales         -> commercial pipeline, sales-agent + admin-agent only
+-- fleet-legal         -> compliance and risk, legal-agent + admin-agent only
```

**Tenant** = organization boundary (row-level DB isolation in the managed service; separate instances in OSS)
**Fleet** = access boundary inside a tenant (query predicate enforcement + `scope_agent` per-row ACL)
**Agent trust tier** = controls cross-fleet write permissions

For the strongest cross-domain isolation, use **separate tenants per domain** rather than separate fleets within one tenant. See [Memory Scope and Visibility Mechanisms](#memory-scope-and-visibility-mechanisms) for a full comparison of isolation layers.

---

## Creating a New Fleet

To add a fourth agent scope (e.g. `fleet-engineering`) without touching existing agents:

### 1. Provision the fleet in MemClaw

With the local OSS deploy, fleets are provisioned automatically on first write -- no dashboard needed. Simply use the fleet ID (e.g. `fleet-engineering`) in your first `memclaw_write` call and the fleet is created.

If you're using the managed service at [memclaw.net](https://memclaw.net), log in, go to your tenant, select **Fleets**, then **New Fleet**, set the fleet ID, and copy it for the next steps.

### 2. Create an agent workspace

```bash
mkdir -p agents/engineering-agent
```

Create `agents/engineering-agent/SOUL.md` (persona), `AGENTS.md` (fleet scope + tool rules), and `IDENTITY.md` (fleet identity). Use an existing agent's files as a template:

```bash
# macOS / Linux
cp agents/sales-agent/SOUL.md agents/engineering-agent/SOUL.md
cp agents/sales-agent/AGENTS.md agents/engineering-agent/AGENTS.md
cp agents/sales-agent/IDENTITY.md agents/engineering-agent/IDENTITY.md
```

Edit each file and replace all references to `sales-agent` / `fleet-sales` with `engineering-agent` / `fleet-engineering`.

### 3. Copy the shared governance skill

```bash
# macOS / Linux
mkdir -p agents/engineering-agent/skills
cp skills/memclaw-governance.md agents/engineering-agent/skills/
```

### 4. Deploy the workspace

**macOS / Linux**

```bash
cp -r agents/engineering-agent ~/.openclaw/workspace-engineering-agent
```

**Windows (PowerShell, run as admin)**

```powershell
$REPO = "C:\path\to\memclaw-cross-fleet-gov"   # <-- update this
New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace-engineering-agent" `
  -Target "$REPO\agents\engineering-agent"
```

### 5. Register the agent in `openclaw.json`

Add a new entry to the `agents.list` array in `.openclaw/openclaw.json`:

```json
{ "id": "engineering-agent", "workspace": "workspace-engineering-agent" }
```

### 6. Restart the gateway and verify

```bash
openclaw gateway restart
openclaw agents list --bindings   # engineering-agent should appear
```

### 7. Validate fleet isolation

```
/agent engineering-agent

Use memclaw_recall with:
  fleet_ids: ["fleet-engineering", "fleet-org-shared"]
  query: "test"
  agent_id: "engineering-agent"
```

Expected: only memories in `fleet-engineering` and `fleet-org-shared` are returned. Other fleet records are not loaded, scored, or returned.

---


## Related

- [MemClaw documentation](https://memclaw.net/docs)
- [MemClaw open source (Apache 2.0)](https://github.com/caura-ai/caura-memclaw)
- [OpenClaw agent workspace guide](https://www.stack-junkie.com/blog/openclaw-system-prompt-design-guide)
- [eToro case study: 20+ agents on MemClaw](https://memclaw.net/blog/etoro-company-brain/)

---

<p align="center">
  <strong>Built on <a href="https://memclaw.net">MemClaw</a>: open-source multi-agent memory for AI agent fleets. Governed, shared, self-improving.</strong><br/>
  <a href="https://github.com/caura-ai/caura-memclaw">Source (Apache 2.0)</a> ·
  <a href="https://memclaw.net/docs">Documentation</a> ·
  <a href="https://memclaw.net/blog/etoro-company-brain/">eToro case study</a>
</p>
