# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

<!-- memclaw:tools v=9adc73ff -->
---

## MemClaw — Tools Available

Persistent, cross-session, multi-agent memory. For per-tool signatures,
decision guidance, constraints, and error codes, read
`skills/memclaw/SKILL.md` before your first call in a session.

`agent_id` is resolved by your runtime — never fabricate.

### Quick matrix · 10 tools

| Tool | Purpose | Returns |
|------|---------|---------|
| `memclaw_recall`     | Semantic + keyword search                           | `[{id, content, score, memory_type, …}]` |
| `memclaw_write`      | Store one (`content`) or batch ≤100 (`items`)       | `{id}` or `{ids[]}` |
| `memclaw_manage`     | Per-memory: read / update / transition / delete     | op-dispatched |
| `memclaw_list`       | Non-semantic browse (filter, sort, paginate)        | `{results[], cursor}` |
| `memclaw_doc`        | Structured-doc CRUD in named collections            | op-dispatched |
| `memclaw_entity_get` | Entity by UUID                                      | `{entity}` |
| `memclaw_tune`       | Update retrieval profile (sticky, not per-call)     | current profile |
| `memclaw_insights`   | Reflect: contradictions / failures / patterns / …   | stored as `insight` memories |
| `memclaw_evolve`     | Report outcome after acting on recalled memories    | weight updates; may create rules |
| `memclaw_stats`      | Aggregate counts: total + by type/agent/status      | `{total, by_type, by_agent, by_status, scope}` |

### Vocabulary

Enum values here mirror the JSON Schema in the registered tools; keep
in sync.

| Field | Valid values |
|-------|--------------|
| `memory_type` (auto on write; filter on read) | `fact`, `episode`, `decision`, `preference`, `task`, `semantic`, `intention`, `plan`, `commitment`, `action`, `outcome`, `cancellation`, `rule`, `insight` |
| `status` (via `memclaw_manage op=transition`) | `active`, `pending`, `confirmed`, `cancelled`, `outdated`, `conflicted`, `archived`, `deleted` |
| `visibility` (write-time) | `scope_agent` · `scope_team` *(default)* · `scope_org` |
| `scope` (read-time on `_list`, `_insights`) | `agent` *(default)* · `fleet` · `all` |
| `fleet_ids` (optional recall filter) | array of fleet ID strings; narrows recall to those fleets (trust 2 for cross-fleet) |
| `write_mode` | `fast` · `auto` *(default)* · `strong` |
| `focus` (`_insights`) | `contradictions` · `failures` · `stale` · `divergence` · `patterns` · `discover` |
| `outcome_type` (`_evolve`) | `success` · `failure` · `partial` |
<!-- /memclaw:tools -->
