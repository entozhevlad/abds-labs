COMPOSE = docker compose --env-file .env.local
UV ?= uv
ifneq ($(shell command -v $(UV) 2>/dev/null),)
PYTHON = $(UV) run --locked python
else
PYTHON = $(COMPOSE) run --rm --no-deps --build -v "$(CURDIR):/workspace" -w /workspace -e UV_PROJECT_ENVIRONMENT=/service/.venv app uv run --locked --no-sync python
endif
.DEFAULT_GOAL := run
.PHONY: run rund services stop clean gen schema load setup teardown test check lint format mypy

# Runs all services in detached mode.
run:
	$(COMPOSE) up -d --build --wait

# Runs all services without detached mode (for debugging).
rund:
	$(COMPOSE) up --build

# Shows all service statuses.
services:
	$(COMPOSE) ps

# Stops all running services.
stop:
	$(COMPOSE) down

# Cleans up all resources including volumes.
clean:
	$(COMPOSE) down -v

gen:
	$(PYTHON) -m app.manage gen
schema:
	$(PYTHON) -m app.manage schema
load:
	$(PYTHON) -m app.manage load
setup:
	$(PYTHON) -m app.manage setup
teardown:
	$(PYTHON) -m app.manage teardown
test:
	$(PYTHON) -m unittest discover -s tests -v
check:
	$(PYTHON) -m tests.integration
lint:
	$(PYTHON) -m ruff check app tests
	$(PYTHON) -m ruff format --check app tests
format:
	$(PYTHON) -m ruff format app tests
	$(PYTHON) -m ruff check --fix app tests
	$(PYTHON) -m ruff format app tests
mypy:
	$(PYTHON) -m mypy
