# openapi-python

`openapi-python` generates strongly typed Python API clients from OpenAPI specs, with route-literal dispatch and transport decoupling.

## Installation

For protocol-only generated clients where you provide the transport:

```bash
uv add openapi-python
```

For generated clients that use the built-in `httpx` transport:

```bash
uv add "openapi-python[httpx]"
```

## CLI

```bash
uv run openapi-python generate --spec ./openapi.json --out ./generated --package my_client
```

You can also pass the OpenAPI document directly as JSON:

```bash
uv run openapi-python generate --spec-json "$OPENAPI_JSON" --out ./generated --package my_client
```

For URL specs with self-signed certificates, disable verification explicitly:

```bash
uv run openapi-python generate --spec https://example.local/openapi.json --out ./generated --no-ssl
```

## Programmatic API

```python
from pathlib import Path
from openapi_python import GenerationRequest, generate_client

result = generate_client(
    GenerationRequest(
        spec_source="./openapi.json",
        output_dir=Path("./generated"),
        package_name="my_client",
        overwrite=True,
    )
)
```

To generate from an in-memory OpenAPI document, pass a JSON string instead of `spec_source`:

```python
import json
from pathlib import Path

from openapi_python import GenerationRequest, generate_client

result = generate_client(
    GenerationRequest(
        output_dir=Path("./generated"),
        spec_json=json.dumps(app.openapi()),
        package_name="my_client",
        overwrite=True,
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

Use `--transport-mode protocol-only` to generate clients that require a supplied transport and do not emit the built-in `httpx` transport classes. The default `--transport-mode default-runtime` includes `DefaultTransport` and `DefaultAsyncTransport`, which require the `httpx` extra when instantiated.

### Built-in `httpx` transport

Install the `httpx` extra and generate with the default transport mode:

```bash
uv add "openapi-python[httpx]"
uv run openapi-python generate --spec ./openapi.json --out ./generated --package my_client
```

The generated `Client` can create its own default transport:

```python
from generated.my_client import Client

client = Client(base_url="https://api.example.com")
book = client.get("/books/{book_id}")(params={"book_id": 1})
```

You can also supply preconfigured `httpx` clients:

```python
import httpx

from generated.my_client import AsyncClient, Client, DefaultAsyncTransport, DefaultTransport

sync_http = httpx.Client(headers={"authorization": "Bearer token"})
async_http = httpx.AsyncClient(headers={"authorization": "Bearer token"})

client = Client(
    base_url="https://api.example.com",
    transport=DefaultTransport(client=sync_http),
)
async_client = AsyncClient(
    base_url="https://api.example.com",
    transport=DefaultAsyncTransport(client=async_http),
)
```

### Custom transport

Install `openapi-python` without extras and generate protocol-only code:

```bash
uv add openapi-python requests
uv run openapi-python generate \
  --spec ./openapi.json \
  --out ./generated \
  --package my_client \
  --transport-mode protocol-only
```

Then provide an object that satisfies the generated `Transport` protocol:

```python
from collections.abc import Mapping

import requests

from generated.my_client import Client


class RequestsTransport:
    def request(
        self,
        *,
        method: str,
        route: str,
        base_url: str,
        params: Mapping[str, object] | None,
        query: Mapping[str, object] | None,
        headers: Mapping[str, object] | None,
        body: object | None,
    ) -> object:
        response = requests.request(
            method=method.upper(),
            url=f"{base_url.rstrip('/')}{route.format(**(params or {}))}",
            params={key: str(value) for key, value in (query or {}).items()} or None,
            headers={key: str(value) for key, value in (headers or {}).items()} or None,
            json=body,
        )
        response.raise_for_status()
        if response.content:
            return response.json()
        return None


client = Client(
    base_url="https://api.example.com",
    transport=RequestsTransport(),
)
book = client.get("/books/{book_id}")(params={"book_id": 1})
```
