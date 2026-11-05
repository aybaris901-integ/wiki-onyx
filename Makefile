NODE_BIN := $(HOME)/.nvm/versions/node/v26.13.0/bin
export PATH := $(NODE_BIN):$(PATH)

.PHONY: setup index agent frontend bridge dev test

setup:
	cd agent && uv sync
	cd frontend && npm install
	@test -f frontend/.env.local || echo 'ASK_BACKEND_URL=http://localhost:8000' > frontend/.env.local

index:
	cd agent && uv run python -m brain.index

agent:
	cd agent && uv run uvicorn brain.app:app --port 8000 --reload

frontend:
	cd frontend && npm run dev

bridge:
	uv run triggerware/bridge.py

# Runs agent + frontend + bridge together; Ctrl-C stops all three.
dev:
	@trap 'kill 0' INT TERM; \
	( cd agent && uv run uvicorn brain.app:app --port 8000 ) & \
	( cd frontend && npm run dev ) & \
	( sleep 4 && uv run triggerware/bridge.py ) & \
	wait

test:
	cd agent && uv run pytest -n auto -q
