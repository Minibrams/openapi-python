from __future__ import annotations

from pathlib import Path

import pytest

from openpylit.generator import GenerationRequest, generate_client
from openpylit.generator.extensions import GeneratorExtensions


def test_invalid_extension_contract_raises(
    fixture_openapi_file: Path, tmp_path: Path
) -> None:
    def bad_hook(spec):
        return "not-a-spec"

    with pytest.raises(Exception):
        generate_client(
            GenerationRequest(
                spec_source=str(fixture_openapi_file),
                output_dir=tmp_path / "out",
                package_name="my_client",
                overwrite=True,
                extensions=GeneratorExtensions(normalize_hooks=(bad_hook,)),
            )
        )
