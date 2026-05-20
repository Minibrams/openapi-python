from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

from app import app

from openapi_python.generator import GenerationRequest, generate_client


def main() -> None:
    output_dir = Path(__file__).parent / "generated"
    generate_client(
        GenerationRequest(
            output_dir=output_dir,
            spec_json=json.dumps(app.openapi()),
            overwrite=True,
        )
    )

    source = (output_dir / "my_client" / "types.py").read_text()
    module = ast.parse(source)
    dto = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "MyDTO"
    )
    generated_types = importlib.import_module("generated.my_client.types")

    assert ast.get_docstring(dto) == "This is a descriptive docstring"
    assert generated_types.MyDTO.__doc__ == "This is a descriptive docstring"
    assert "This is the docstring for a single field" in source


if __name__ == "__main__":
    main()
