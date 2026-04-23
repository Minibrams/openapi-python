from __future__ import annotations

from pathlib import Path

from openpylit import cli
from openpylit.generator import GenerationResult


def test_cli_no_ssl_flag_sets_verify_ssl_false(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def fake_try_generate_client(request):
        captured["verify_ssl"] = request.verify_ssl
        return GenerationResult(
            success=True,
            written_files=(),
            operations=0,
            type_definitions=0,
            diagnostics=(),
        )

    monkeypatch.setattr(cli, "try_generate_client", fake_try_generate_client)

    code = cli.main(
        [
            "generate",
            "--spec",
            "https://example.com/openapi.json",
            "--out",
            str(tmp_path / "out"),
            "--package",
            "my_client",
            "--no-ssl",
        ]
    )

    assert code == 0
    assert captured["verify_ssl"] is False
