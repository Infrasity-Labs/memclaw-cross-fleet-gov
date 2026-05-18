# MemClaw Governance Skill

## Core Principle
Retrieval before reasoning. Never answer account questions from
memory alone — always call memclaw_recall first.

## Fleet Scoping
Pass only your authorized fleet_ids to every recall call.
The fleet_ids parameter is an array: ["fleet-a", "fleet-b"]
Unauthorized fleet_ids will return no results — this is by design.

## Retrieval Protocol
1. Receive account query
2. Call memclaw_recall with authorized fleet_ids
3. Label each returned memory by its source fleet_id
4. Reason only over retrieved memories
5. If no memories returned: state that explicitly, do not speculate

## Conflict Reporting
When retrieved memories contain contradictory status for the same
account across different fleets:
- Surface both perspectives with explicit fleet labels
- Do not resolve the contradiction
- Escalate to admin-agent or human decision-maker

## Compliance Hold Priority
Active compliance holds (HIPAA, GDPR, regulatory flags) always
override commercial considerations. If a compliance hold exists
in fleet-legal and is visible via org-shared, deal progression stops.

## Escalation Triggers
- Compliance question to Sales agent → escalate to Legal Agent
- Governance conflict detected → escalate to Admin Agent
- Active hold conflicts with deal momentum → human escalation required

## Admin Observability
Admin agent uses memclaw_insights with focus=discover to generate
cross-fleet knowledge maps. All significant account status changes
should be written to fleet-org-shared for cross-fleet visibility.
