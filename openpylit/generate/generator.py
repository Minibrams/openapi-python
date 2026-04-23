"""Legacy compatibility shim.

Use `openpylit.generator.generate_client` for new code.
"""

from pathlib import Path
from typing import Any

from openpylit.generator import GenerationRequest, generate_client


def generate_from_dict(spec: dict[str, Any], out_dir: Path, package_name: str) -> None:
    """Generate a client package from an in-memory OpenAPI document."""
    import json
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        spec_path = Path(tmp) / "openapi.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        generate_client(
            GenerationRequest(
                spec_source=str(spec_path),
                output_dir=out_dir,
                package_name=package_name,
                overwrite=True,
            )
        )
