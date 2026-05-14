# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A multi-agent governance demo showing MemClaw enforcing fleet-scoped memory boundaries across three OpenClaw agents. Three agents (sales, legal, admin) share one MemClaw tenant with three isolated fleet partitions. Fleet boundaries are query predicates at the storage layer — not prompt instructions — so cross-scope leakage is structurally impossible.

## Prerequisites

- Node.js 24+
- OpenClaw CLI: `npm install -g openclaw@latest`
- A MemClaw account with API key ([memclaw.net](https://memclaw.net)) and three fleets provisioned: `fleet-org-shared`, `fleet-sales`, `fleet-legal`
- AISA API key for DeepSeek V3 model access

## Environment Setup

```powershell
copy .env.example .env
# Fill in: MEMCLAW_API_KEY, MEMCLAW_TENANT_ID, AISA_API_KEY
```

The `.env` variables are consumed by `.openclaw/openclaw.json` via `${VAR_NAME}` interpolation.

## Gateway Commands

```powershell
# First-time setup
openclaw onboard --install-daemon
openclaw auth set aisa:default --key "your-aisa-api-key"
openclaw doctor

# Normal operation
openclaw gateway restart
openclaw agents list --bindings      # verify all three agents registered
openclaw dashboard                   # opens http://127.0.0.1:18789
```

## Windows Workspace Path Issue (Critical)

OpenClaw's security validation rejects workspace paths outside `~/.openclaw`. The `openclaw.json` in this repo uses `"../agents/sales-agent"` (relative paths from `.openclaw/`), which resolve to the project `agents/` directory on Linux/Mac but may trigger "Rejected workspace path outside openclawDir" on Windows.

**Windows fix — create junctions (run as admin):**

```powershell
New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace-sales-agent" `
  -Target "E:\WORK\memclaw\memclaw-cross-fleet-gov\agents\sales-agent"

New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace-legal-agent" `
  -Target "E:\WORK\memclaw\memclaw-cross-fleet-gov\agents\legal-agent"

New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace-admin-agent" `
  -Target "E:\WORK\memclaw\memclaw-cross-fleet-gov\agents\admin-agent"
```

Then update `openclaw.json` agent workspaces to use the junction names:

```json
{ "id": "sales-agent",  "workspace": "workspace-sales-agent" },
{ "id": "legal-agent",  "workspace": "workspace-legal-agent" },
{ "id": "admin-agent",  "workspace": "workspace-admin-agent" }
```

Run `openclaw doctor` after any workspace path change.

## Architecture

### Agent Scope

| Agent | Fleet Access | Hard Boundary |
|---|---|---|
| `sales-agent` | `fleet-sales`, `fleet-org-shared` | Cannot access `fleet-legal` |
| `legal-agent` | `fleet-legal`, `fleet-org-shared` | Cannot access `fleet-sales` |
| `admin-agent` | All three fleets | None — cross-fleet synthesis |

### Configuration Layers

- **`.openclaw/openclaw.json`** — gateway config: model provider (AISA/DeepSeek V3), agent workspace paths, MemClaw plugin registration. The plugin is registered under `plugins.slots.memory = "memclaw"` and `plugins.slots.contextEngine = "memclaw"`.
- **`agents/<agent>/SOUL.md`** — injected first each session; defines persona and tone
- **`agents/<agent>/AGENTS.md`** — injected second; defines workspace conventions, memory protocol, tool usage rules
- **`agents/<agent>/IDENTITY.md`** — fleet scope and MemClaw-specific identity for that agent
- **`skills/memclaw-governance.md`** — shared governance skill copied into every agent workspace; update once, redeploy to all agents

### MemClaw Plugin

Lives at `.openclaw/plugins/memclaw/`. Key source files:

- [src/paths.ts](.openclaw/plugins/memclaw/src/paths.ts) — all paths resolve from `~/.openclaw`; plugin dir is always `~/.openclaw/plugins/memclaw`
- [src/resolve-agent.ts](.openclaw/plugins/memclaw/src/resolve-agent.ts) — agent ID resolution order: explicit `agent_id` param → session key → env var `MEMCLAW_AGENT_ID` → install-scoped fallback
- [src/validation.ts](.openclaw/plugins/memclaw/src/validation.ts) — workspace path containment check (`isContainedPath`), HMAC command signing, UUID validation
- [src/tools.ts](.openclaw/plugins/memclaw/src/tools.ts) — MCP tool implementations

### MCP Tools Exposed

`memclaw_write`, `memclaw_recall`, `memclaw_manage`, `memclaw_list`, `memclaw_insights`, `memclaw_stats`, `memclaw_evolve`, `memclaw_keystones`, `memclaw_tune`, `memclaw_entity_get`

Always pass `agent_id: "<this-agent-id>"` explicitly on every tool call. If omitted, the plugin falls back to an install-scoped default that may not isolate memories correctly.

## Key Constraints

- `MEMCLAW_AUTO_WRITE_TURNS` must be a boolean `false`, not the string `"false"` — incorrect type causes unintended auto-persistence
- `fleet_ids` in `memclaw_recall` is an array, not a string: `["fleet-sales", "fleet-org-shared"]`
- Keep `MEMCLAW_API_URL` on HTTPS for hosted deployments; the plugin warns (but doesn't block) HTTP when an API key is set
- Command signatures (HMAC) are optional by default — the plugin accepts unsigned commands and warns once per process. Set `MEMCLAW_REQUIRE_SIGNED_COMMANDS=true` only behind an enterprise signing gateway
