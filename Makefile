.PHONY: code
code:
	code .vscode/ajera.code-workspace

.PHONY: clean
clean:
	rm -rf dist
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	find . -type d -name '__pycache__' -exec rm -rf {} +

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

.PHONY: test
test:
	uv run pytest 

.PHONY: coverage
coverage:
	uv run coverage run -m pytest
	uv run coverage xml -o coverage.xml
	uv run coverage report -m --fail-under=95

.PHONY: build
build:
	@rm -rf dist
	uv build
