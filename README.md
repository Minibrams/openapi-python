# openpylit

`openpylit` generates strongly typed Python API clients from OpenAPI specs, with route-literal dispatch and transport decoupling.

## CLI

```bash
uv run openpylit generate --spec ./openapi.json --out ./generated --package my_client
```

For URL specs with self-signed certificates, disable verification explicitly:

```bash
uv run openpylit generate --spec https://example.local/openapi.json --out ./generated --no-ssl
```

## Programmatic API

```python
from pathlib import Path
from openpylit import GenerationRequest, generate_client

result = generate_client(
    GenerationRequest(
        spec_source="./openapi.json",
        output_dir=Path("./generated"),
        package_name="my_client",
        overwrite=True,
        verify_ssl=True,  # set False to ignore SSL certificate verification for URL specs
    )
)
```

## Extensibility

`GeneratorExtensions` exposes two safe hooks:

- `normalize_hooks`: transform the normalized model before rendering.
- `render_context_hooks`: transform rendered file content map before writing.

Invalid extension outputs fail fast with explicit diagnostics.

## Transport Decoupling

Generated clients expose a transport protocol. You can plug in your own transport while keeping route-level typing guarantees.
