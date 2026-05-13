# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the 15-memory enterprise dataset (idempotent — safe to re-run)
python demo/seed_memories.py

# Run the full pytest suite
pytest tests/ -v

# Run a single test
pytest tests/test_isolation.py::test_sales_recall_contains_no_legal_data -v

# Interactive governance runtime (primary entry point)
python app.py

# Run demos individually (make is not available on Windows — run directly)
# DEMOS REMOVED

# Docker
docker compose -f docker/docker-compose.yml up

# Clean session state
rm -f state/sessions.json
```

## Required Environment Variables

Copy `.env.example` to `.env` and populate:

- `MEMCLAW_API_KEY` — from memclaw.net dashboard
- `MEMCLAW_TENANT_ID` — tenant identifier
- `MEMCLAW_BASE_URL` — default `https://memclaw.net/api/v1`
- `AISA_API_KEY` — required only for LLM demos and the skipped test; check your AISA dashboard for valid model names before setting `AISA_MODEL`

## Architecture

### Core Principle: Governance Before Reasoning

Fleet recall happens **before** the LLM call. The LLM prompt is constructed exclusively from memories returned by authorized fleet calls. No user input can expand fleet access at runtime.

### Layer Stack

```
User query
    |
Agent (sales_agent.py / legal_agent.py)
    |
BaseAgent._recall_all()  <-- fixed fleet callables set at construction
    |
Fleet facades (fleets/sales_fleet.py, fleets/legal_fleet.py)
    |
MemClawClient (client.py)  <-- REST calls to MemClaw API
    |
MemClaw fleet namespace (fleet-org-shared / fleet-sales / fleet-legal)
    |
BaseAgent._build_system_prompt()  <-- only authorized memories reach here
    |
LLMProvider.complete()  <-- AISA gateway (OpenAI SDK)
    |
Response + AuditLogger.record()
```

### Access Matrix

| Agent         | fleet-org-shared | fleet-sales | fleet-legal |
| ------------- | ---------------- | ----------- | ----------- |
| sales-agent-1 | READ/WRITE       | READ/WRITE  | BLOCKED     |
| legal-agent-1 | READ/WRITE       | BLOCKED     | READ/WRITE  |
| admin-agent   | READ/WRITE       | READ        | READ        |

### Key Files

- **`config.py`** — all fleet IDs, agent IDs, and API credentials via `os.getenv`. Single source of truth for constants.
- **`client.py`** — `MemClawClient`: thin REST wrapper. `generate_insights()` accepts optional `fleet_id` to scope findings per fleet.
- **`agents/base_agent.py`** — `BaseAgent`: the governance loop. `_fleet_recall_map` is a fixed dict of `{fleet_id: callable}` set at `__init__` — nothing can add to it at runtime. `_recall_all()` only iterates this map.
- **`agents/llm_provider.py`** — `LLMProvider`: OpenAI SDK targeting AISA gateway. Lazy client init; raises `RuntimeError` if key is missing or model not found.
- **`fleets/`** — `SalesFleet`, `LegalFleet`, and `AdminFleet` wrap `MemClawClient` per agent context. `AdminFleet` exposes `recall_shared()`, `recall_sales()`, `recall_legal()` — READ only, no private fleet writes.
- **`admin/audit.py`** — `AuditLogger`: session-local event store (the MemClaw `/audit` endpoint returns 404). Injected into agents; `governance_summary()` proves which fleets each agent actually accessed.
- **`admin/governance_matrix.py`** — static `MATRIX` dict + `print_matrix()` using `rich` Table. Import `get_allowed_fleets()` / `get_blocked_fleets()` for agent construction.
- **`admin/insights.py`** — `AdminInsights`: wraps `generate_insights()` calls per fleet for the admin agent (trust level 3).
- **`scenarios/enterprise_scenario.py`** — exports `MEMORIES` (15 records) and `DEDUP_QUERIES` (used by seed to prevent duplicates). 5 clients × 3 fleets each.

### Admin Agent

`AdminAgent` (`agents/admin_agent.py`) subclasses `BaseAgent` with all 3 fleets in its `fleet_recall_map`. It overrides `_build_system_prompt()` to include conflict-detection instructions — when sales and legal data contradict, it must surface the conflict and recommend escalation. It is a governance observer only: no write access to private fleets, no authority to approve deals or lift holds.

### Structural Boundary Enforcement

`SalesAgent`, `LegalAgent`, and `AdminAgent` pass their fleet recall callables directly to `BaseAgent.__init__`. The callables are closures over the fleet facade — no fleet ID string is ever derived from user input. Adding a new agent means subclassing `BaseAgent` and declaring its `fleet_recall_map` in `__init__`.

### Idempotent Seeding

`seed_memories.py` checks each memory via a dedup query before writing. On a 409 Conflict from the API it continues silently. Re-running seed is always safe.

### Tests

- `test_isolation.py` / `test_scope_enforcement.py` — assert sentinel phrases from one fleet's private data are absent in the other fleet's recall results
- `test_shared_access.py` — assert both agents can recall from `fleet-org-shared`
- `test_agent_visibility.py::test_sales_agent_response_contains_no_legal_phrases` — end-to-end LLM test; **skipped automatically** when `AISA_API_KEY` is not set

### Runtime and State Modules (new)

- **`app.py`** — interactive governance runtime. Entry point: `python app.py`. Loads `GovernanceEngine`, `SessionManager`, `AuditLogger`, `ConflictDetector`, and all 3 agents on startup.
- **`runtime/policy_loader.py`** — `PolicyLoader.load(path)` reads YAML files relative to repo root via `yaml.safe_load`. Used by `GovernanceEngine` and `ConflictDetector`.
- **`runtime/governance_engine.py`** — `GovernanceEngine` provides `get_authorized_fleets(agent_id)` and `get_blocked_fleets(agent_id)` from `policies/fleet_access.yaml`. Agents call this instead of hardcoding fleet lists.
- **`runtime/event_bus.py`** — synchronous pub/sub (`subscribe`, `publish`). Handlers are wrapped in `try/except` — they can never crash the agent loop.
- **`runtime/session_manager.py`** — `SessionManager` creates/retrieves/resets `SessionState` objects; persists to `state/sessions.json` via `save_all()`.
- **`runtime/terminal_ui.py`** — shared Rich UI primitives used by `app.py`: `render_governance_header`, `render_memory_table`, `render_conflict_findings`, `render_audit_event`, `render_agent_selection_menu`.
- **`runtime/live_audit_monitor.py`** — `LiveAuditMonitor` wraps `AuditLogger` and displays only new events (using a `_last_seen` pointer) after each agent turn.
- **`state/session_state.py`** — per-agent conversation history as `list[tuple[str,str]]`. `get_context_summary(max_turns=3)` builds a prior-context string for multi-turn queries.
- **`state/persistence.py`** — `save_sessions()` / `load_sessions()` to/from `state/sessions.json`. Pure stdlib.

### Policy Files

- **`policies/fleet_access.yaml`** — single source of truth for agent fleet access. Edit here to add agents or change access rules; no Python changes needed.
- **`policies/governance_rules.yaml`** — 5 conflict detection rules (HIPAA-001, GDPR-001, GDPR-002, SECURITY-001, PCI-001). Each rule has `sales_signal_patterns` and `legal_signal_patterns` for keyword matching. Add rules here to detect new conflict types.

### Conflict Detector

**`admin/conflict_detector.py`** — `ConflictDetector` loads rules from `governance_rules.yaml`. `detect(memories_by_fleet)` does keyword matching across fleet-sales and fleet-legal content — no LLM, fully deterministic. Returns `[]` when either private fleet is absent (safe to call for non-Admin agents). `format_findings(findings)` returns a plain-text summary.

### Audit Logging

**`admin/audit.py`** — `AuditLogger(log_to_file=True, session_id=None)`. Events are now appended to `logs/session_audit.log` as JSON lines in addition to being stored in-process. Event schema: `timestamp`, `agent_id`, `query`, `fleets_accessed`, `memory_counts`, `total_memories`, `response_preview`, `response_summary`, `session_id`. All existing keys preserved; `response_summary` and `session_id` are new additions.

### Docker

`docker/Dockerfile` — Python 3.11-slim, installs requirements, runs `app.py`.
`docker/docker-compose.yml` — single `governance-runtime` service; `stdin_open: true`, `tty: true`, `env_file: ../.env`, `logs/` volume mounted for audit log persistence.

### OpenClaw Deployment

`openclaw/` is a separate deployment layer for messaging platforms (Slack/Telegram/Discord). It does not replace the Python implementation — it adds OpenClaw runtime routing on top. Fleet scoping is identical; it is enforced at the MemClaw API layer regardless of runtime. See `openclaw/README.md` for deployment steps.
