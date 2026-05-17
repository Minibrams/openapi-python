set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default:
    @just --list

sync:
    uv sync --locked --all-packages

format:
    uv run ruff check --select I --fix .
    uv run ruff format .

format-check:
    uv run ruff check --select I .
    uv run ruff format --check .

typecheck:
    uv run ty check .

test *args:
    uv run pytest -n auto {{args}}

check: format-check typecheck test

build:
    uv build

release version="":
    if [ -n "{{version}}" ]; then \
        uv run python scripts/release.py --version "{{version}}"; \
    else \
        uv run python scripts/release.py; \
    fi
