PYTEST_ARGS ?= --capture=no

# Ajera ODBC. Progress ships the HDP driver for x86_64 Linux and Windows only,
# so ODBC work runs in a linux/amd64 image (docker/odbc/Dockerfile). The driver
# is Deltek's public download, pinned by checksum and never committed.
ODBC_IMAGE ?= ajera-odbc
HDP_URL := https://dsm.deltek.com/DFVE/ODBC/HDPLinuxDriver.zip
HDP_SHA256 := e16e7eb19a113a33c18dfc6b0f2a4af44b842c4356dad2a800efb7cb49e68dea
HDP_DIR := .odbc/download
HDP_ZIP := $(HDP_DIR)/HDPLinuxDriver.zip
ODBC_ENV := AJERA_ODBC_DATASOURCE AJERA_ODBC_USERNAME AJERA_ODBC_PASSWORD \
	AJERA_ODBC_HOST AJERA_ODBC_PORT AJERA_ODBC_DRIVER \
	AJERA_API_URL AJERA_API_USERNAME AJERA_API_PASSWORD
# Credentials pass by name (-e VAR), so their values never reach the command line.
ODBC_RUN = docker run --rm --platform linux/amd64 $(foreach var,$(ODBC_ENV),-e $(var)) \
	-v "$(CURDIR)":/src

.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

.PHONY: help install lock upgrade outdated check format test test-integration coverage build code clean \
	odbc-driver odbc-image odbc-shell test-odbc odbc-catalog odbc-probe odbc-enums odbc-generate odbc-verify

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Sync the locked environment, with every extra (pyodbc included)
	uv sync --frozen --all-extras

lock: ## Update the lock file and re-sync
	uv lock
	$(MAKE) install

upgrade: ## Upgrade dependencies and re-sync
	uv lock --upgrade
	$(MAKE) install

outdated: ## Show available dependency upgrades
	uv lock --upgrade --dry-run

check: ## Run linters and type checks
	uv run ruff check
	uv run ruff format --check
	uv run mypy . --exclude site

format: ## Auto-format and apply lint fixes
	uv run ruff format
	uv run ruff check --fix

test: ## Run unit tests
	uv run pytest -m "not integration" $(PYTEST_ARGS)

test-integration: ## Run integration tests against the REST API
	uv run pytest -m "integration and not odbc" $(PYTEST_ARGS)

odbc-driver: ## Download and verify the HDP ODBC driver
	@mkdir -p $(HDP_DIR)
	@test -f $(HDP_ZIP) || { curl -fsSL -o $(HDP_ZIP).part $(HDP_URL) && mv $(HDP_ZIP).part $(HDP_ZIP); }
	@echo "$(HDP_SHA256)  $(HDP_ZIP)" | shasum -a 256 -c -

odbc-image: odbc-driver ## Build the linux/amd64 image with the HDP ODBC driver
	docker build --platform linux/amd64 --build-context hdp-dist=$(HDP_DIR) \
		-f docker/odbc/Dockerfile -t $(ODBC_IMAGE) .

odbc-shell: ## Open a shell in the ODBC image with this checkout mounted
	$(ODBC_RUN) -it $(ODBC_IMAGE) bash

test-odbc: ## Run integration tests against the ODBC database, in the ODBC image
	$(ODBC_RUN) $(ODBC_IMAGE) uv run --frozen --extra odbc pytest -m odbc $(PYTEST_ARGS)

odbc-catalog: ## Snapshot the live database catalog into scripts/odbc/catalog.json
	$(ODBC_RUN) $(ODBC_IMAGE) uv run --frozen --extra odbc python scripts/odbc/harvest.py

odbc-probe: ## Record which function parameters have no effect (ARGS=function names)
	$(ODBC_RUN) $(ODBC_IMAGE) uv run --frozen --extra odbc python -u scripts/odbc/probe.py $(ARGS)

odbc-enums: ## Extract documented codes from the schema workbook (XLSX=path)
	@test -n "$(XLSX)" || { echo "usage: make odbc-enums XLSX=path/to/AjeraSchema.xlsx"; exit 2; }
	uv run --with openpyxl python scripts/odbc/enums.py "$(XLSX)"

odbc-generate: ## Regenerate the database models from the catalog snapshot
	uv run python scripts/odbc/generate.py

odbc-verify: ## Validate every model against every live row (ARGS=name filter)
	$(ODBC_RUN) $(ODBC_IMAGE) uv run --frozen --extra odbc python -u scripts/odbc/verify.py $(ARGS)

coverage: ## Run unit tests with coverage reporting
	uv run pytest -m "not integration" --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=80 $(PYTEST_ARGS)

build: ## Build distribution artifacts
	rm -rf dist
	uv build

code: ## Open the VS Code workspace
	code .vscode/ajera.code-workspace

clean: ## Remove build and cache artifacts
	rm -rf dist .mypy_cache .ruff_cache .pytest_cache
	find . -type d -name '__pycache__' -exec rm -rf {} +
