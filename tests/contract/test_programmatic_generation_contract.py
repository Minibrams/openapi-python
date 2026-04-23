from __future__ import annotations

from pathlib import Path

from openpylit.generator import GenerationRequest, generate_client


def test_programmatic_generation_contract(
    fixture_openapi_file: Path, tmp_path: Path
) -> None:
    result = generate_client(
        GenerationRequest(
            spec_source=str(fixture_openapi_file),
            output_dir=tmp_path / "out",
            package_name="my_client",
            overwrite=True,
        )
    )
    assert result.success
    assert result.operations >= 1
    assert result.type_definitions >= 1
    assert any(path.name == "client.py" for path in result.written_files)
