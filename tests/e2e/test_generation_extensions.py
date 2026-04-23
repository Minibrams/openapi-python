from __future__ import annotations

from pathlib import Path

from openpylit.generator import GenerationRequest, generate_client
from openpylit.generator.extensions import GeneratorExtensions


def test_extension_customization_changes_output(
    fixture_openapi_file: Path, tmp_path: Path
) -> None:
    def hook(spec):
        return spec

    out_dir = tmp_path / "out"
    generate_client(
        GenerationRequest(
            spec_source=str(fixture_openapi_file),
            output_dir=out_dir,
            package_name="my_client",
            overwrite=True,
            extensions=GeneratorExtensions(normalize_hooks=(hook,)),
        )
    )
    assert (out_dir / "my_client" / "client.py").exists()
