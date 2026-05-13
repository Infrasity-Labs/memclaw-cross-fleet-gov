from client import MemClawClient

c = MemClawClient()

print("=== RECALL PER FLEET (actual contents) ===")
for f, a in [
    (['fleet-org-shared'], 'sales-agent-1'),
    (['fleet-sales'], 'sales-agent-1'),
    (['fleet-legal'], 'legal-agent-1'),
]:
    result = c.recall(f, a, 'Client X account renewal', top_k=10)
    memories = result.get('memories', [])
    print(f"\nfleet={f}  count={len(memories)}")
    for m in memories:
        print(f"  [{m.get('fleet_id')}] {m.get('content','')[:80]}")