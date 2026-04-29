.PHONY: setup dev crawl-popular crawl-rankings stats serve test lint clean

setup:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"
	cp -n .env.example .env 2>/dev/null || true
	@echo "Setup complete. Run: source .venv/bin/activate"

dev: serve

crawl-popular:
	.venv/bin/python -m video_crawler crawl-popular

crawl-rankings:
	.venv/bin/python -m video_crawler crawl-rankings

stats:
	.venv/bin/python -m video_crawler show-stats

serve:
	.venv/bin/python -m video_crawler serve

test:
	.venv/bin/pytest -v

lint:
	.venv/bin/ruff check src/ tests/
	.venv/bin/ruff format --check src/ tests/

format:
	.venv/bin/ruff check --fix src/ tests/
	.venv/bin/ruff format src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache *.egg-info dist build
