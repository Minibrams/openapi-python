#!/usr/bin/env bash
set -euo pipefail

uv run python tests/generate_client.py
uv run basedpyright -p tests tests
