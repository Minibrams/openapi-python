from __future__ import annotations

import json
from pathlib import Path

from openpylit.generator import GenerationRequest, generate_client
from tests.fixture_app import app

ROOT = Path(__file__).resolve().parent
GENERATED_ROOT = ROOT / "generated"


def main() -> None:
    generate_client(
        GenerationRequest(
            output_dir=GENERATED_ROOT,
            spec_json=json.dumps(app.openapi()),
            package_name="static_client",
            overwrite=True,
        )
    )


if __name__ == "__main__":
    main()
