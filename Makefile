PYTHON ?= .venv/bin/python3
HOST ?= 0.0.0.0
PORT ?= 8025

.PHONY: clean-pyc install lint test routes openapi uvicorn check

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
	$(PYTHON) -m pytest

routes:
	$(PYTHON) scripts/list_routes.py

openapi:
	$(PYTHON) scripts/export_openapi.py

uvicorn:
	$(PYTHON) -m uvicorn app.main:app --host $(HOST) --port $(PORT) --reload

check: lint test routes openapi
