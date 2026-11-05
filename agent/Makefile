.PHONY: sync index dev test
sync:
	uv sync
index:
	uv run python -m brain.index
dev:
	uv run uvicorn brain.app:app --port $${PORT:-8008} --reload
test:
	uv run pytest -n auto
