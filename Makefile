.PHONY: seed demo-shared demo-boundary demo-insights demo-agents demo-audit demo-audit-trail demo-conflict test install all runtime docker-up clean-sessions

install:
	pip install -r requirements.txt

seed:
	python demo/seed_memories.py

demo-shared:
	python demo/demo_shared.py

demo-boundary:
	python demo/demo_boundary.py

demo-insights:
	python demo/demo_insights.py

demo-agents:
	python demo/demo_agent_loop.py

demo-audit:
	python demo/demo_audit.py

demo-audit-trail:
	python demo/demo_audit_trail.py

demo-conflict:
	python demo/demo_conflict.py

test:
	pytest tests/ -v

all: seed demo-shared demo-boundary demo-insights demo-agents demo-audit-trail test

runtime:
	python app.py

docker-up:
	docker compose -f docker/docker-compose.yml up

clean-sessions:
	rm -f state/sessions.json
