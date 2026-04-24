from __future__ import annotations

import json
from pathlib import Path

from app import app

from openapi_python.generator import GenerationRequest, generate_client


def main() -> None:
    generate_client(
        GenerationRequest(
            output_dir=Path(__file__).parent / "generated",
            spec_json=json.dumps(app.openapi()),
            overwrite=True,
        )
    )


if __name__ == "__main__":
    main()
