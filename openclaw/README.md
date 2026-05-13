# OpenClaw Deployment

This directory contains the OpenClaw Gateway configuration and agent workspace files for running the Sales, Legal, and Admin agents via [OpenClaw](https://openclaw.ai) — enabling deployment to Slack, Telegram, Discord, or any OpenClaw-supported messaging platform.

## Architecture Position

OpenClaw adds a messaging runtime layer on top of the Python governance architecture:

```
User message (Slack / Telegram / Discord)
    |
OpenClaw Gateway (session management, routing, MCP)
    |
MemClaw MCP server (https://memclaw.net/mcp)
    |
fleet_ids array in /recall  <-- governance boundary enforced here
    |
fleet-org-shared / fleet-sales / fleet-legal
    |
AISA LLM gateway
    |
Agent response → user
```

Fleet boundaries are identical to the Python implementation. The `fleet_ids` array in each `/recall` call is the actual enforcement mechanism — OpenClaw routes to it, but MemClaw enforces it.

## Files

```
openclaw/
├── openclaw.json                   — Gateway configuration (models, agents, MCP)
├── agents/
│   ├── sales-agent/
│   │   ├── SOUL.md                 — Sales agent tone and behavioral rules
│   │   └── AGENTS.md              — Sales agent operational instructions
│   ├── legal-agent/
│   │   ├── SOUL.md                 — Legal agent tone and behavioral rules
│   │   └── AGENTS.md              — Legal agent operational instructions
│   └── admin-agent/
│       ├── SOUL.md                 — Admin agent tone and behavioral rules
│       └── AGENTS.md              — Admin agent operational instructions
└── skills/
    └── memclaw-governance.md       — Shared governance skill loaded by all agents
```

## Prerequisites

- Node 24+ installed
- OpenClaw CLI: `npm install -g openclaw@latest`
- AISA account with API key (for LLM inference)
- MemClaw account with API key and `fleet-org-shared`, `fleet-sales`, `fleet-legal` provisioned
- Memories seeded: `python demo/seed_memories.py` from the repo root

## Installation

```bash
# a. Install OpenClaw daemon
openclaw onboard --install-daemon

# b. Store AISA credentials in keychain (not in openclaw.json)
openclaw auth set aisa:default --key "your-aisa-api-key"

# c. Copy Gateway config
cp openclaw/openclaw.json ~/.openclaw/openclaw.json

# d. Copy agent workspaces
cp -r openclaw/agents/sales-agent ~/.openclaw/workspace-sales-agent
cp -r openclaw/agents/legal-agent ~/.openclaw/workspace-legal-agent
cp -r openclaw/agents/admin-agent ~/.openclaw/workspace-admin-agent

# e. Copy shared governance skill to each workspace
cp openclaw/skills/memclaw-governance.md ~/.openclaw/workspace-sales-agent/skills/
cp openclaw/skills/memclaw-governance.md ~/.openclaw/workspace-legal-agent/skills/
cp openclaw/skills/memclaw-governance.md ~/.openclaw/workspace-admin-agent/skills/

# f. Set MEMCLAW_API_KEY in environment (used by openclaw.json via ${MEMCLAW_API_KEY})
export MEMCLAW_API_KEY="your-memclaw-api-key"

# g. Start Gateway
openclaw gateway restart

# h. Verify agents loaded
openclaw agents list --bindings

# i. Open dashboard
openclaw dashboard
# → http://127.0.0.1:18789
```

## Verification

```bash
openclaw doctor
```

Then open http://127.0.0.1:18789 and send a test message to each agent:

**Sales agent:** "What's the renewal status for HealthSystem Inc?"
Expected: surfaces org-shared context. No compliance flags from fleet-legal.

**Legal agent:** "Is there a compliance hold on HealthSystem Inc?"
Expected: surfaces GDPR/legal context from fleet-legal. No discount ceilings from fleet-sales.

**Admin agent:** "Give me the full picture on HealthSystem Inc."
Expected: surfaces all three fleets, flags the conflict between sales pipeline status and legal hold.

## Architecture Note

SOUL.md and AGENTS.md are **behavioral governance** — they define what the agent says when asked about out-of-scope topics. The `fleet_ids` array in MemClaw `/recall` calls is **structural governance** — unauthorized fleet IDs return no results regardless of what the agent says.

Defense-in-depth: structural boundary (MemClaw API) + behavioral rules (SOUL.md/AGENTS.md).

## Troubleshooting

- **Gateway won't start:** run `openclaw doctor` — check for schema errors in openclaw.json
- **Unknown config key errors:** unknown fields cause immediate startup failure; verify against docs at docs.openclaw.ai/gateway/configuration
- **Agent not recalling correctly:** verify `fleet_ids` is an array (`["fleet-a", "fleet-b"]`), not a string
- **Model not found:** verify `deepseek-v3` is in your AISA account's model catalog; update `models[].id` in openclaw.json if the ID differs
- **MCP connection failed:** confirm `MEMCLAW_API_KEY` is exported in the environment where the Gateway runs
