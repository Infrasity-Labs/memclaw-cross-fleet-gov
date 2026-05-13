# MemClaw + OpenClaw: Governed Agent Deployment

This repository provides the configuration and agent workspaces for running a multi-agent system on the [OpenClaw](https://openclaw.ai) platform, using [MemClaw](https://memclaw.net) as the secure, governed memory backend.

It demonstrates how to enforce enterprise-grade data governance at the API layer, ensuring that agents deployed on any platform can only access the information they are explicitly authorized to see.

## Architecture

This setup uses OpenClaw as the agent runtime and messaging gateway, while MemClaw provides the core governance and memory services.

```
User message (Slack / Telegram / Discord)
    |
OpenClaw Gateway (session management, routing)
    |
MemClaw MCP Server (via OpenClaw skill)
    |
fleet_ids array in /recall  <-- Governance boundary enforced here
    |
fleet-org-shared / fleet-sales / fleet-legal
    |
AISA LLM Gateway
    |
Agent response → user
```

The `fleet_ids` array in each `/recall` call is the actual enforcement mechanism. OpenClaw routes the request, but MemClaw enforces the data boundary.

## Repository Structure

```
.
├── openclaw.json                   — Gateway configuration (models, agents, MCP)
├── agents/
│   ├── sales-agent/
│   │   ├── SOUL.md                 — Sales agent tone and behavioral rules
│   │   └── AGENTS.md               — Sales agent operational instructions
│   ├── legal-agent/
│   │   ├── SOUL.md                 — Legal agent tone and behavioral rules
│   │   └── AGENTS.md               — Legal agent operational instructions
│   └── admin-agent/
│       ├── SOUL.md                 — Admin agent tone and behavioral rules
│       └── AGENTS.md               — Admin agent operational instructions
└── skills/
    └── memclaw-governance.md       — Shared governance skill loaded by all agents
```

## Prerequisites

- Node 24+ installed
- OpenClaw CLI: `npm install -g openclaw@latest`
- An AISA account with an API key for LLM inference.
- A MemClaw account with an API key and the following fleets provisioned: `fleet-org-shared`, `fleet-sales`, `fleet-legal`.

## Installation

1.  **Install OpenClaw Daemon:**

    ```bash
    openclaw onboard --install-daemon
    ```

2.  **Store AISA Credentials:**
    Store your AISA API key in the secure keychain.

    ```bash
    openclaw auth set aisa:default --key "your-aisa-api-key"
    ```

3.  **Copy Gateway Configuration:**

    ```bash
    # On macOS/Linux
    cp openclaw.json ~/.openclaw/openclaw.json

    # On Windows (using PowerShell)
    Copy-Item -Path "openclaw.json" -Destination "$HOME\.openclaw\openclaw.json"
    ```

4.  **Copy Agent Workspaces:**

    ```bash
    # On macOS/Linux
    cp -r agents/sales-agent ~/.openclaw/workspace-sales-agent
    cp -r agents/legal-agent ~/.openclaw/workspace-legal-agent
    cp -r agents/admin-agent ~/.openclaw/workspace-admin-agent

    # On Windows (using PowerShell)
    Copy-Item -Path "agents\sales-agent" -Destination "$HOME\.openclaw\workspace-sales-agent" -Recurse
    Copy-Item -Path "agents\legal-agent" -Destination "$HOME\.openclaw\workspace-legal-agent" -Recurse
    Copy-Item -Path "agents\admin-agent" -Destination "$HOME\.openclaw\workspace-admin-agent" -Recurse
    ```

5.  **Copy Shared Governance Skill:**
    This skill must be copied into each agent's workspace.

    ```bash
    # On macOS/Linux
    cp skills/memclaw-governance.md ~/.openclaw/workspace-sales-agent/skills/
    cp skills/memclaw-governance.md ~/.openclaw/workspace-legal-agent/skills/
    cp skills/memclaw-governance.md ~/.openclaw/workspace-admin-agent/skills/

    # On Windows (using PowerShell)
    New-Item -ItemType Directory -Force -Path "$HOME\.openclaw\workspace-sales-agent\skills\"
    Copy-Item -Path "skills\memclaw-governance.md" -Destination "$HOME\.openclaw\workspace-sales-agent\skills\"
    New-Item -ItemType Directory -Force -Path "$HOME\.openclaw\workspace-legal-agent\skills\"
    Copy-Item -Path "skills\memclaw-governance.md" -Destination "$HOME\.openclaw\workspace-legal-agent\skills\"
    New-Item -ItemType Directory -Force -Path "$HOME\.openclaw\workspace-admin-agent\skills\"
    Copy-Item -Path "skills\memclaw-governance.md" -Destination "$HOME\.openclaw\workspace-admin-agent\skills\"
    ```

6.  **Set MemClaw API Key:**
    The `openclaw.json` configuration uses an environment variable to access your MemClaw API key.

    ```bash
    # On macOS/Linux
    export MEMCLAW_API_KEY="your-memclaw-api-key"

    # On Windows (using PowerShell)
    $env:MEMCLAW_API_KEY="your-memclaw-api-key"
    ```

    _Note: For persistent storage on Windows, you may need to set this in your System Environment Variables._

7.  **Start the OpenClaw Gateway:**

    ```bash
    openclaw gateway restart
    ```

8.  **Verify Agents and Open Dashboard:**
    ```bash
    openclaw agents list --bindings
    openclaw dashboard
    ```
    Your browser should open to the OpenClaw dashboard at `http://127.0.0.1:18789`.

## Verification

Once the dashboard is open, you can send test messages to each agent to verify the setup:

- **Sales agent:** "What's the renewal status for HealthSystem Inc?"
  - _Expected:_ Surfaces org-shared context. No compliance flags from `fleet-legal`.

- **Legal agent:** "Is there a compliance hold on HealthSystem Inc?"
  - _Expected:_ Surfaces GDPR/legal context from `fleet-legal`. No discount ceilings from `fleet-sales`.

- **Admin agent:** "Give me the full picture on HealthSystem Inc."
  - _Expected:_ Surfaces context from all three fleets and flags the conflict between sales pipeline status and the legal hold.

## Troubleshooting

- **Gateway won't start:** Run `openclaw doctor` to check for schema errors in `openclaw.json`.
- **Agent not recalling correctly:** Verify that `fleet_ids` in the skill file is an array (e.g., `["fleet-a", "fleet-b"]`), not a string.
- **Model not found:** Verify the model ID in `openclaw.json` is available in your AISA account's model catalog.
- **MCP connection failed:** Confirm that `MEMCLAW_API_KEY` is set correctly in the environment where the Gateway is running.
