from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.e2e.fixture_app import app


@pytest.fixture
def fixture_openapi_file(tmp_path: Path) -> Path:
    path = tmp_path / "openapi.json"
    path.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    return path
