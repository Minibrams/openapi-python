from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

from openpylit.generator import GenerationRequest, generate_client
from tests.e2e.fixture_app import app


@pytest.fixture
def fixture_openapi_file(tmp_path: Path) -> Path:
    path = tmp_path / "openapi.json"
    path.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    return path


@pytest.fixture
def generated_package_dir(tmp_path: Path, fixture_openapi_file: Path) -> Path:
    out_dir = tmp_path / "generated"
    result = generate_client(
        GenerationRequest(
            spec_source=str(fixture_openapi_file),
            output_dir=out_dir,
            package_name="my_client",
            overwrite=True,
        )
    )
    assert result.success
    return out_dir


@pytest.fixture
def generated_client_module(generated_package_dir: Path):
    sys.path.insert(0, str(generated_package_dir))
    try:
        yield importlib.import_module("my_client")
    finally:
        sys.path.remove(str(generated_package_dir))
        sys.modules.pop("my_client", None)
        sys.modules.pop("my_client.client", None)
        sys.modules.pop("my_client.transport", None)
        sys.modules.pop("my_client.types", None)
