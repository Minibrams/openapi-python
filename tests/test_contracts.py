from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _contract_dirs() -> list[Path]:
    return sorted(
        path
        for path in (Path(__file__).parent / "contract").iterdir()
        if path.is_dir() and (path / "generate.py").is_file()
    )


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def _output(result: subprocess.CompletedProcess[str]) -> str:
    parts = [
        f"command: {' '.join(result.args)}",
        f"exit code: {result.returncode}",
    ]
    if result.stdout:
        parts.extend(["stdout:", result.stdout])
    if result.stderr:
        parts.extend(["stderr:", result.stderr])
    return "\n".join(parts)


@pytest.mark.parametrize("contract_dir", _contract_dirs(), ids=lambda path: path.name)
def test_contract_types(contract_dir: Path) -> None:
    generate = _run(["python", "generate.py"], cwd=contract_dir)
    assert generate.returncode == 0, _output(generate)

    typecheck = _run(
        ["ty", "check", ".", "--exclude", "generated", "--python-version", "3.12"],
        cwd=contract_dir,
    )
    assert typecheck.returncode == 0, _output(typecheck)

    generated_types = _run(
        ["ty", "check", "generated/my_client/types.py", "--python-version", "3.12"],
        cwd=contract_dir,
    )
    assert generated_types.returncode == 0, _output(generated_types)
