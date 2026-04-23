from __future__ import annotations

from pathlib import Path

import pytest

from openpylit.generator import GenerationRequest, generate_client


def test_regeneration_requires_overwrite_flag(
    fixture_openapi_file: Path, tmp_path: Path
) -> None:
    out_dir = tmp_path / "out"
    generate_client(
        GenerationRequest(
            spec_source=str(fixture_openapi_file),
            output_dir=out_dir,
            package_name="my_client",
            overwrite=True,
        )
    )

    with pytest.raises(Exception):
        generate_client(
            GenerationRequest(
                spec_source=str(fixture_openapi_file),
                output_dir=out_dir,
                package_name="my_client",
                overwrite=False,
            )
        )
