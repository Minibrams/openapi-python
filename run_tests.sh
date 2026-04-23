#!/usr/bin/env bash
set -euo pipefail

found_contract=0

for contract_dir in tests/contract/*/; do
  [[ -d "$contract_dir" ]] || continue

  generate_file="$contract_dir/generate.py"

  if [[ ! -f "$generate_file" ]]; then
    echo "Missing required file: $generate_file" >&2
    exit 1
  fi

  echo "$contract_dir"

  echo "    Generating contract client..."
  uv run python "$generate_file"

  echo "    Type checking contract..."
  uv run basedpyright -p "$contract_dir"
done
