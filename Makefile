.PHONY: install run test health logs verify triage

install:
	uv sync --extra dev

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest -v

health:
	@curl -s http://localhost:8000/health | python3 -m json.tool

logs:
	@tail -f logs/app.log

verify: test health
	@echo ""
	@echo "--- verify complete ---"
	@echo "Log any observations to docs/exec-plans/tech-debt-tracker.md before moving on."

triage:
	@echo "=== Recent errors (logs/app.log) ==="
	@tail -20 logs/app.log 2>/dev/null || echo "(no log file)"
	@echo ""
	@echo "=== Open tech debt ==="
	@grep -v "^|.*~~" docs/exec-plans/tech-debt-tracker.md | grep "^| TD-"
