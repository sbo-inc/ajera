PYTEST_ARGS ?= --capture=no

.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

.PHONY: help install lock upgrade outdated check format test test-integration coverage build code clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Sync the locked environment
	uv sync --frozen

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

test-integration: ## Run integration tests
	uv run pytest -m integration $(PYTEST_ARGS)

coverage: ## Run tests with coverage reporting
	uv run coverage run -m pytest
	uv run coverage xml -o coverage.xml
	uv run coverage report -m --fail-under=95

build: ## Build distribution artifacts
	rm -rf dist
	uv build

code: ## Open the VS Code workspace
	code .vscode/ajera.code-workspace

clean: ## Remove build and cache artifacts
	rm -rf dist .mypy_cache .ruff_cache .pytest_cache
	find . -type d -name '__pycache__' -exec rm -rf {} +
