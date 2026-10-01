install-dev:
	@echo "Installing local package..."
	uv sync
	uv run prek install
lint:
	@echo "Running linters..."
	uv run ruff check
	uv run ruff format --check
	uv run mypy .
test: lint
	@echo "Running tests..."
	uv run pytest

update-dependencies:
	uv lock --upgrade
update-pre-commit-hooks:
	uv run prek autoupdate --cooldown-days 14
