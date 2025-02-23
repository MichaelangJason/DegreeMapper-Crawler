fetch:
  uv run main.py

lint:
  uv run ruff check
  mypy .

lint-fix:
  uv run ruff check --fix
