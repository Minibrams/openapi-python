from __future__ import annotations

from pathlib import Path

from openpylit.generator import GenerationRequest, generate_client


def test_generation_is_deterministic(
    fixture_openapi_file: Path, tmp_path: Path
) -> None:
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"

    generate_client(
        GenerationRequest(
            spec_source=str(fixture_openapi_file),
            output_dir=out_a,
            package_name="my_client",
            overwrite=True,
        )
    )
    generate_client(
        GenerationRequest(
            spec_source=str(fixture_openapi_file),
            output_dir=out_b,
            package_name="my_client",
            overwrite=True,
        )
    )

    a = (out_a / "my_client" / "client.py").read_text(encoding="utf-8")
    b = (out_b / "my_client" / "client.py").read_text(encoding="utf-8")
    assert a == b
