from __future__ import annotations

import time
from pathlib import Path

from openpylit.generator import GenerationRequest, generate_client


def test_generation_performance_smoke(
    fixture_openapi_file: Path, tmp_path: Path
) -> None:
    start = time.perf_counter()
    generate_client(
        GenerationRequest(
            spec_source=str(fixture_openapi_file),
            output_dir=tmp_path / "out",
            package_name="my_client",
            overwrite=True,
        )
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 30
