# MemClaw: Multi-Agent Governance Reference Architecture

A production-quality reference implementation demonstrating how to build secure, multi-agent systems with enterprise-grade governance using [MemClaw](https://memclaw.net).

This repository showcases how MemClaw's server-side, fleet-based memory provides a secure foundation for agentic applications, ensuring that unauthorized data is never exposed to the LLM. It includes two distinct implementation patterns: a direct Python-based runtime and a platform-based deployment using OpenClaw.

---

## Key Features

- **Server-Side Governance**: Fleet-based access control is enforced by the MemClaw API, not the client application.
- **Structural Isolation**: Agents are structurally incapable of accessing memory fleets they are not authorized for.
- **Declarative Policies**: Agent permissions are defined in simple YAML files (`policies/fleet_access.yaml`), allowing for easy updates without code changes.
- **Deterministic Conflict Detection**: Identify and flag conflicts between different data silos (e.g., sales vs. legal) without relying on an LLM.
- **Verifiable Audit Trail**: Every agent interaction is logged with a clear, machine-readable record of which fleets were accessed.
- **Dual Implementation Patterns**: Includes both a simple, terminal-based Python runtime and an advanced OpenClaw deployment for real-world messaging platforms.

---

## Core Principle: Governance Before Reasoning

The foundational security principle of this architecture is that governance is enforced **before** the LLM reasoning step. Unauthorized memories are never retrieved, meaning the LLM is never exposed to forbidden context.

```
User Query
    │
    ▼
GovernanceEngine  ←── policies/fleet_access.yaml
    │  (Validates access before recall)
    ▼
BaseAgent._recall_all()
    │  (Calls only authorized fleet facades)
    ▼
MemClaw REST API (/recall?fleet_id=...)
    │  (Server-side fleet isolation)
    ▼
Authorized Memories Only
    │
    ▼
LLM System Prompt
    │  (LLM only ever sees authorized content)
    ▼
LLM Provider
```

---

## Architecture

This repository is structured to separate the core logic, policies, and agent definitions, making it modular and easy to understand.

```
memclaw-cross-fleet-gov/
│
├── app.py                        # Interactive Python governance runtime
├── config.py                     # Fleet IDs, agent IDs, API credentials
├── client.py                     # MemClaw REST client
│
├── policies/                     # Declarative governance policies
│   ├── fleet_access.yaml         # Agent fleet access rules
│   └── governance_rules.yaml     # Conflict detection patterns
│
├── runtime/                      # Core components for the Python runtime
│
├── agents/                       # Agent implementations (Sales, Legal, Admin)
│
├── fleets/                       # Fleet-specific API facades
│
├── admin/                        # Governance observability tools (Audit, Conflict Detection)
│
├── tests/                        # Pytest suite for verifying governance
│
└── openclaw/                     # OpenClaw deployment layer for messaging platforms
```

---

## Getting Started

Follow these steps to get the application running locally.

### Prerequisites

- Python 3.10+
- `pip` for package management
- [Docker](https://www.docker.com/get-started) (Optional, for containerized deployment)
- A [MemClaw](https://memclaw.net) account with an API Key and Tenant ID.
- (Optional) An AISA account for LLM-enabled features.

### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd memclaw-cross-fleet-gov
    ```

2.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure your environment:**
    Copy the example environment file and fill in your credentials.

    ```bash
    cp .env.example .env
    ```

    Now, edit the `.env` file:
    - `MEMCLAW_API_KEY`: **Required**
    - `MEMCLAW_TENANT_ID`: **Required**
    - `AISA_API_KEY`: Optional, for LLM features.

4.  **Seed the database:**
    This command populates the MemClaw fleets with sample data. It's idempotent, so it's safe to run multiple times.
    ```bash
    python scenarios/seed_memories.py
    ```

---

## Usage

This repository offers two ways to run the agents.

### Option A: Python Interactive Runtime

This is the simplest way to experience the core governance features. It runs a fully interactive terminal application locally.

**Launch the runtime:**

```bash
python app.py
```

The application will present a menu to select an agent. Once an agent is selected, you can query it and observe how its access is restricted to its authorized fleets.

**[Placeholder for Screenshot: Show the agent selection menu and a sample query/response in the terminal.]**

### Option B: OpenClaw Platform Deployment

This pattern uses [OpenClaw](https://openclaw.ai) to deploy the agents to a production-style environment, enabling them to run on platforms like Slack, Discord, or Telegram.

This is an advanced use case that demonstrates how MemClaw's governance can be integrated into a scalable, platform-based architecture.

**For full instructions, please refer to the detailed guide in the OpenClaw directory:**
[**openclaw/README.md**](openclaw/README.md)

---

## Key Components Explained

### Declarative Policies

The governance rules are not hardcoded. They live in simple YAML files, allowing for easy modification.

- [**`policies/fleet_access.yaml`**](policies/fleet_access.yaml): Defines which agent can access which fleets.
- [**`policies/governance_rules.yaml`**](policies/governance_rules.yaml): Defines the keyword patterns for detecting conflicts between fleets.

### Conflict Detection

The `AdminAgent` can see across multiple fleets and use the rules in `governance_rules.yaml` to identify conflicts. For example, if the sales fleet contains information about closing a deal (`"contract"`) while the legal fleet has a compliance hold (`"hipaa"`), the Admin Agent will flag this as a high-priority conflict. This detection is deterministic and does not require an LLM.

### Verifiable Audit Trail

Every action performed by an agent is recorded in `logs/session_audit.log`. Each log entry is a JSON object that includes the agent ID, the query, the fleets accessed, and the number of memories retrieved. This provides a machine-verifiable record of governance enforcement.

```json
{
  "timestamp": "2026-05-12T14:22:31",
  "agent_id": "sales-agent-1",
  "query": "Is HealthSystem ready to close?",
  "fleets_accessed": ["fleet-org-shared", "fleet-sales"],
  "total_memories": 5,
  ...
}
```

---

## Running Tests

To ensure the governance rules and structural boundaries are correctly implemented, you can run the full test suite.

```bash
pytest tests/ -v
```

The most critical test, `test_sales_agent_structural_boundary`, verifies that an agent is structurally incapable of reaching a fleet it is not authorized to access.

---

## Docker Support

You can also run the interactive runtime in a containerized environment using Docker.

1.  Ensure your `.env` file is configured correctly.
2.  Run the following command:
    ```bash
    docker compose -f docker/docker-compose.yml up
    ```
