from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run_pyright(file_path: Path, generated_root: Path) -> list[str]:
    config_path = file_path.parent / "pyrightconfig.json"
    config_path.write_text(
        json.dumps(
            {
                "typeCheckingMode": "standard",
                "reportMissingImports": True,
                "extraPaths": [str(generated_root)],
            }
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        ["uv", "run", "pyright", "--outputjson", str(file_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(file_path.parent),
    )
    payload = json.loads(proc.stdout or "{}")
    diagnostics = payload.get("generalDiagnostics") or []
    config_path.unlink(missing_ok=True)
    return [diag.get("message", "") for diag in diagnostics]


def assert_expected_patterns(messages: list[str], expected_file: Path) -> None:
    expected = [
        line.strip()
        for line in expected_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for pattern in expected:
        if not any(pattern in message for message in messages):
            raise AssertionError(
                f"Missing expected diagnostic pattern: {pattern}\nMessages: {messages}"
            )
