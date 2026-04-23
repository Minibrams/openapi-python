from __future__ import annotations

from pathlib import Path

from openpylit.cli import main


def test_cli_generate_contract(fixture_openapi_file: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    code = main(
        [
            "generate",
            "--spec",
            str(fixture_openapi_file),
            "--out",
            str(out_dir),
            "--package",
            "my_client",
        ]
    )
    assert code == 0
    assert (out_dir / "my_client" / "client.py").exists()
    assert (out_dir / "my_client" / "types.py").exists()
