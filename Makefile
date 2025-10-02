.PHONY: code
code:
	code .vscode/ajera.code-workspace

.PHONY: install
install:
	uv sync --all-extras --all-packages --group dev

.PHONY: check
check: 
	uv run ruff check
	uv run ruff format --check
	uv run mypy . --exclude site

.PHONY: format
format: 
	uv run ruff format
	uv run ruff check --fix

.PHONY: tests
tests: 
	uv run pytest 

.PHONY: coverage
coverage:
	uv run coverage run -m pytest
	uv run coverage xml -o coverage.xml
	uv run coverage report -m --fail-under=95

