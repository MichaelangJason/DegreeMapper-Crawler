set dotenv-load := true

crawl crawler:
  uv run scrapy crawl {{crawler}} --nolog

fetch:
  uv run main.py

lint:
  uv run ruff check || true
  mypy . || true


default_n := '5'

query query n_results=default_n:
  uv run query.py "{{query}}" {{n_results}}

run-query-api:
  uv run uvicorn queryAPI:app --host ${QUERY_API_HOST} --port ${QUERY_API_PORT} --reload

lint-fix:
  uv run ruff check --fix
