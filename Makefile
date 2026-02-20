.PHONY: install run test health smoke logs verify triage

install:
	uv sync --extra dev

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest -v

health:
	@curl -s http://localhost:8000/health | python3 -m json.tool

smoke:
	@echo "=== Smoke test: live endpoints ==="
	@echo ""
	@echo "--- GET /health ---"
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@echo ""
	@echo "--- GET /api/variants ---"
	@curl -s http://localhost:8000/api/variants | python3 -m json.tool
	@echo ""
	@echo "--- POST /api/session (both variants) ---"
	@STATUS=$$(curl -s -o /tmp/smoke_session.json -w "%{http_code}" -X POST http://localhost:8000/api/session -H "Content-Type: application/json" -d '{"selections":[{"name":"baseline","ending_strategy":"none"},{"name":"harness","ending_strategy":"harness"}]}'); \
	echo "HTTP $$STATUS"; \
	python3 -c "import json; d=json.load(open('/tmp/smoke_session.json')); gens=d.get('generations',[]); print(json.dumps({'session_id':d.get('session_id'),'generation_count':len(gens),'generations':[{'generation_id':g.get('generation_id'),'condition':g.get('condition'),'body_preview':(g.get('body') or [''])[0][:80]+'...'} for g in gens],'detail':d.get('detail')},indent=2))"
	@echo ""
	@echo "--- POST /api/feedback (rate first generation if session succeeded) ---"
	@GEN_ID=$$(python3 -c "import json; d=json.load(open('/tmp/smoke_session.json')); gens=d.get('generations',[]); print(gens[0]['generation_id'] if gens else '')" 2>/dev/null); \
	if [ -n "$$GEN_ID" ]; then \
	  curl -s -X POST http://localhost:8000/api/feedback \
	    -H "Content-Type: application/json" \
	    -d "{\"generation_id\":$$GEN_ID,\"rating\":4,\"tag\":\"smoke-test\"}" | python3 -m json.tool; \
	else \
	  echo "(skipped — no generations returned, LM Studio likely down)"; \
	fi
	@echo ""
	@echo "--- smoke complete ---"
	@echo "HTTP 200 + generations array on /api/session = fully working."
	@echo "HTTP 503 on /api/session = LM Studio not running (start it, then re-run smoke)."

logs:
	@tail -f logs/app.log

verify: test smoke
	@echo ""
	@echo "--- verify complete ---"
	@echo "Log any observations to docs/exec-plans/tech-debt-tracker.md before moving on."

triage:
	@echo "=== Recent errors (logs/app.log) ==="
	@tail -20 logs/app.log 2>/dev/null || echo "(no log file)"
	@echo ""
	@echo "=== Open tech debt ==="
	@grep -v "^|.*~~" docs/exec-plans/tech-debt-tracker.md | grep "^| TD-"
