# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A multi-agent governance demo showing MemClaw enforcing fleet-scoped memory boundaries across three OpenClaw agents. Three agents (sales, legal, admin) share one MemClaw tenant with three isolated fleet partitions. Fleet boundaries are query predicates at the storage layer - not prompt instructions - so data outside declared `fleet_ids` is never loaded, scored, or returned. For hard cross-domain isolation (cannot be bypassed at the prompt level), use separate tenants per domain or the managed service.

## Prerequisites

- Node.js 24+
- Docker (to run MemClaw locally)
- OpenClaw CLI: `npm install -g openclaw@latest`
- LLM gateway API key for DeepSeek V3 (or any OpenAI-compatible model)

This repo defaults to a **local MemClaw instance** - no cloud account or API key required for MemClaw. Fleet partitions (`fleet-org-shared`, `fleet-sales`, `fleet-legal`) are created automatically on first write.

## Environment Setup

```powershell
# 1. Start MemClaw locally (clone the repo and use docker compose)
git clone https://github.com/caura-ai/caura-memclaw ~/caura-memclaw
cp ~/caura-memclaw/.env.example ~/caura-memclaw/.env
docker compose -f ~/caura-memclaw/docker-compose.yml up -d

# 2. Copy and configure env (only LLM_GATEWAY_API_KEY is required)
copy .env.example .env
# Fill in: LLM_GATEWAY_API_KEY (your LLM gateway key; MEMCLAW_API_KEY can stay blank for local deploy)
```

The `.env` variables are consumed by `.openclaw/openclaw.json` via `${VAR_NAME}` interpolation. Default `MEMCLAW_API_URL=http://localhost:8000` and `MEMCLAW_TENANT_ID=default` work out of the box.

## Gateway Commands

```powershell
# First-time setup
openclaw onboard --install-daemon
# For any OpenAI-compatible endpoint:
openclaw onboard --non-interactive --accept-risk `
  --custom-api-key "your-llm-gateway-key" `
  --custom-base-url "https://your-gateway.example.com/v1"
openclaw doctor

# Normal operation
openclaw gateway restart
openclaw agents list --bindings      # verify all three agents registered
openclaw dashboard                   # opens http://127.0.0.1:18789
```

## Windows Workspace Path Issue (Critical)

OpenClaw's security validation rejects workspace paths outside `~/.openclaw`. The `openclaw.json` in this repo uses `"../agents/sales-agent"` (relative paths from `.openclaw/`), which resolve to the project `agents/` directory on Linux/Mac but may trigger "Rejected workspace path outside openclawDir" on Windows.

**Windows fix - run the setup script (handles this automatically):**

```powershell
.\setup.ps1
```

If you need to create junctions manually (run as admin):

```powershell
$REPO = $PSScriptRoot   # or set manually to your clone path

New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace-sales-agent" `
  -Target "$REPO\agents\sales-agent"

New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace-legal-agent" `
  -Target "$REPO\agents\legal-agent"

New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace-admin-agent" `
  -Target "$REPO\agents\admin-agent"
```

Run `openclaw doctor` after any workspace path change.

## Architecture

### Agent Scope

| Agent | Fleet Access | Hard Boundary |
|---|---|---|
| `sales-agent` | `fleet-sales`, `fleet-org-shared` | Cannot access `fleet-legal` |
| `legal-agent` | `fleet-legal`, `fleet-org-shared` | Cannot access `fleet-sales` |
| `admin-agent` | All three fleets | None - cross-fleet synthesis |

### Configuration Layers

- **`.openclaw/openclaw.json`** - gateway config: model provider (LLM gateway/DeepSeek V3), agent workspace paths, MemClaw plugin registration. The plugin is registered under `plugins.slots.memory = "memclaw"`.
- **`agents/<agent>/SOUL.md`** - injected first each session; defines persona and tone
- **`agents/<agent>/AGENTS.md`** - injected second; defines workspace conventions, memory protocol, tool usage rules
- **`agents/<agent>/IDENTITY.md`** - fleet scope and MemClaw-specific identity for that agent
- **`skills/memclaw-governance.md`** - shared governance skill copied into every agent workspace; update once, redeploy to all agents

### MemClaw Plugin

Installed at `~/.openclaw/plugins/memclaw/` by the setup script via the canonical `install-plugin` endpoint. The plugin source is not vendored in this repo — `setup.sh`/`setup.ps1` fetch the live plugin on first run.

### MCP Tools Exposed

`memclaw_write`, `memclaw_recall`, `memclaw_manage`, `memclaw_list`, `memclaw_insights`, `memclaw_stats`, `memclaw_evolve`, `memclaw_tune`, `memclaw_entity_get`, `memclaw_keystones`, `memclaw_keystones_set`, `memclaw_doc`

Always pass `agent_id: "<this-agent-id>"` explicitly on every tool call. If omitted, the plugin falls back to an install-scoped default that may not isolate memories correctly.

## Key Constraints

- `fleet_ids` in `memclaw_recall` is an array, not a string: `["fleet-sales", "fleet-org-shared"]`
- Keep `MEMCLAW_API_URL` on HTTPS for hosted deployments; the plugin warns (but doesn't block) HTTP when an API key is set
- Command signatures (HMAC) are optional by default - the plugin accepts unsigned commands and warns once per process. Set `MEMCLAW_REQUIRE_SIGNED_COMMANDS=true` only behind an enterprise signing gateway
