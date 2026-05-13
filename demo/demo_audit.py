"""
Demo Moment 4 — Audit Log.

Instantiates AdminInsights (sets AGENT_ADMIN trust=3), calls get_audit_log,
then prints recent entries grouped by operation type.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from admin.insights import AdminInsights

DIVIDER = "=" * 60
OP_ORDER = ["write", "recall", "search", "insights", "trust"]


def _parse_entries(result):
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        for key in ("entries", "events", "logs", "data", "results", "audit"):
            val = result.get(key)
            if isinstance(val, list):
                return val
    return []


def _op_key(entry):
    if isinstance(entry, dict):
        return (
            entry.get("operation")
            or entry.get("action")
            or entry.get("type")
            or entry.get("event_type")
            or "unknown"
        ).lower()
    return "unknown"


def _format_entry(entry):
    if not isinstance(entry, dict):
        return f"    {str(entry)[:120]}"
    agent = entry.get("agent_id") or entry.get("agent") or "-"
    fleet = entry.get("fleet_id") or entry.get("fleet") or "-"
    ts = entry.get("timestamp") or entry.get("created_at") or entry.get("time") or "-"
    detail = (
        entry.get("content_preview")
        or entry.get("query")
        or entry.get("detail")
        or entry.get("summary")
        or ""
    )
    line = f"    agent={agent!r}  fleet={fleet!r}  ts={ts}"
    if detail:
        line += f"\n      {str(detail)[:100]}"
    return line


def main():
    print("\n=== Demo Moment 4: Audit Log ===")
    print("Agent     : admin-agent  (trust level 3 / admin)")
    print()

    admin = AdminInsights()
    print("Trust level set. Fetching audit log...\n")

    try:
        result = admin.get_audit_log()
    except RuntimeError as exc:
        err = str(exc)
        if "404" in err or "405" in err:
            print(DIVIDER)
            print("Audit endpoint unavailable.")
            print("Check the correct path in Swagger at memclaw.net/api/docs")
            print(f"Error: {err[:300]}")
            print(DIVIDER)
            return
        raise

    entries = _parse_entries(result)

    print(DIVIDER)
    print(f"AUDIT LOG  ({len(entries)} entries)")
    print(DIVIDER)

    if not entries:
        print("\n  (No entries returned — printing raw response)\n")
        print(f"  {result}")
        print()
        print(DIVIDER)
        return

    grouped = {}
    for entry in entries:
        key = _op_key(entry)
        grouped.setdefault(key, []).append(entry)

    ordered_keys = [k for k in OP_ORDER if k in grouped]
    ordered_keys += [k for k in grouped if k not in OP_ORDER]

    for op in ordered_keys:
        items = grouped[op]
        print(f"\n  [{op.upper()}]  ({len(items)} entries)")
        for entry in items[:10]:
            print(_format_entry(entry))
        if len(items) > 10:
            print(f"    ... and {len(items) - 10} more")

    print()
    print(DIVIDER)
    print()


if __name__ == "__main__":
    main()
