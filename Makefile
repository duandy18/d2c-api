PYTHON ?= .venv/bin/python3
ALEMBIC ?= .venv/bin/alembic
TESTS ?= tests

DEV_DB_DSN ?= postgresql+psycopg://d2c:d2c@127.0.0.1:5433/d2c
DEV_TEST_DB_DSN ?= postgresql+psycopg://d2c:d2c@127.0.0.1:5433/d2c_test
D2C_ENV ?= local

HOST ?= 0.0.0.0
PORT ?= 8025
PID_FILE ?= /tmp/d2c_api_8025.pid
LOG_FILE ?= /tmp/d2c_api_8025.log
HEALTH_URL ?= http://127.0.0.1:$(PORT)/health

DEV_ENV := D2C_ENVIRONMENT="$(D2C_ENV)" D2C_DATABASE_URL="$(DEV_DB_DSN)" D2C_TEST_DATABASE_URL="$(DEV_DB_DSN)" PYTHONPATH=.
TEST_ENV := D2C_ENVIRONMENT=test D2C_DATABASE_URL="$(DEV_TEST_DB_DSN)" D2C_TEST_DATABASE_URL="$(DEV_TEST_DB_DSN)" PYTHONPATH=.

.PHONY: clean-pyc install lint test routes openapi check
.PHONY: upgrade-dev alembic-check alembic-current alembic-history revision
.PHONY: uvicorn uvicorn-up uvicorn-down uvicorn-restart uvicorn-status uvicorn-logs
.PHONY: up down restart status logs

clean-pyc:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

lint: clean-pyc
	$(PYTHON) -m ruff check .

test: clean-pyc
	$(PYTHON) -m pytest $(TESTS)

routes:
	$(PYTHON) scripts/list_routes.py

openapi:
	$(PYTHON) scripts/export_openapi.py

check: lint test routes openapi

upgrade-dev:
	@echo ">>> Alembic upgrade head on DEV_DB_DSN ($(DEV_DB_DSN))"
	$(DEV_ENV) $(ALEMBIC) upgrade head

alembic-check:
	@echo ">>> Alembic check on DEV_DB_DSN ($(DEV_DB_DSN))"
	$(DEV_ENV) $(ALEMBIC) check

alembic-current:
	@echo ">>> Alembic current on DEV_DB_DSN ($(DEV_DB_DSN))"
	$(DEV_ENV) $(ALEMBIC) current

alembic-history:
	@echo ">>> Alembic history on DEV_DB_DSN ($(DEV_DB_DSN))"
	$(DEV_ENV) $(ALEMBIC) history | tail -n 30

revision:
	@if [ -z "$(MESSAGE)" ]; then \
		echo "usage: make revision MESSAGE=\"describe change\""; \
	else \
		$(DEV_ENV) $(ALEMBIC) revision --autogenerate -m "$(MESSAGE)"; \
	fi

uvicorn:
	$(PYTHON) -m uvicorn app.main:app --host $(HOST) --port $(PORT) --reload

uvicorn-up:
	@if curl -fsS "$(HEALTH_URL)" >/dev/null 2>&1; then \
		echo "d2c-api already running: $(HEALTH_URL)"; \
	else \
		echo "starting d2c-api on $(HOST):$(PORT)"; \
		nohup $(PYTHON) -m uvicorn app.main:app --host $(HOST) --port $(PORT) --reload >"$(LOG_FILE)" 2>&1 & \
		echo $$! >"$(PID_FILE)"; \
		echo "pid file: $(PID_FILE)"; \
		echo "log file: $(LOG_FILE)"; \
		for i in 1 2 3 4 5 6 7 8 9 10; do \
			if curl -fsS "$(HEALTH_URL)" >/dev/null 2>&1; then \
				echo "d2c-api ready: $(HEALTH_URL)"; \
				break; \
			fi; \
			echo "waiting d2c-api attempt $$i"; \
			sleep 1; \
		done; \
	fi

uvicorn-down:
	@if [ -f "$(PID_FILE)" ]; then \
		OLD_PID="$$(cat "$(PID_FILE)")"; \
		echo "stopping d2c-api pid: $$OLD_PID"; \
		kill "$$OLD_PID" 2>/dev/null || true; \
		sleep 2; \
	else \
		echo "pid file not found: $(PID_FILE)"; \
	fi
	@if ss -ltnp 2>/dev/null | grep ":$(PORT)" >/dev/null; then \
		echo "port $(PORT) still occupied, fallback stop uvicorn"; \
		pkill -f "uvicorn app.main:app --host $(HOST) --port $(PORT)" 2>/dev/null || true; \
		sleep 2; \
	fi
	@rm -f "$(PID_FILE)"
	@echo "d2c-api stopped if it was running"

uvicorn-restart: uvicorn-down uvicorn-up

uvicorn-status:
	@echo "===== listener on port $(PORT) ====="
	@ss -ltnp 2>/dev/null | grep ":$(PORT)" || true
	@echo
	@echo "===== health ====="
	@curl -fsS "$(HEALTH_URL)" | python3 -m json.tool || true

uvicorn-logs:
	@tail -n 80 "$(LOG_FILE)" 2>/dev/null || true

up: uvicorn-up
down: uvicorn-down
restart: uvicorn-restart
status: uvicorn-status
logs: uvicorn-logs
