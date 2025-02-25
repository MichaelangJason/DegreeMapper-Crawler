fetch:
  uv run main.py

lint:
  uv run ruff check || true
  mypy . || true

lint-fix:
  uv run ruff check --fix
