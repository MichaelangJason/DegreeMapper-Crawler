fetch:
  uv run main.py

lint:
  uv run ruff check || true
  mypy . || true


default_n := '5'

query query n_results=default_n:
  uv run query.py "{{query}}" {{n_results}}

lint-fix:
  uv run ruff check --fix
