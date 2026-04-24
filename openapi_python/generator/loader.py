from __future__ import annotations

import json
import ssl
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .diagnostics import invalid_spec

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


def _load_text_from_url(url: str, *, verify_ssl: bool) -> str:
    request = Request(
        url=url, headers={"Accept": "application/json, application/yaml, text/yaml"}
    )
    context = None
    if not verify_ssl:
        context = ssl._create_unverified_context()
    with urlopen(request, timeout=30, context=context) as response:  # nosec B310 - URL is user input by design
        return response.read().decode("utf-8")


def _parse_document(raw: str, source: str) -> dict:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    if yaml is not None:
        data = yaml.safe_load(raw)
        if isinstance(data, dict):
            return data

    raise invalid_spec("Could not parse OpenAPI source as JSON or YAML", source)


def _validate_openapi_document(document: dict, source: str) -> dict:
    if "openapi" not in document:
        raise invalid_spec("Missing required 'openapi' field", source)
    if not isinstance(document.get("paths"), dict) or not document.get("paths"):
        raise invalid_spec("Missing or empty 'paths' object", source)
    return document


def load_openapi(source: str, *, verify_ssl: bool = True) -> dict:
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        raw = _load_text_from_url(source, verify_ssl=verify_ssl)
    else:
        path = Path(source)
        if not path.exists():
            raise invalid_spec("OpenAPI source does not exist", str(path))
        raw = path.read_text(encoding="utf-8")

    document = _parse_document(raw, source)
    return _validate_openapi_document(document, source)


def load_openapi_json(raw: str, *, source: str = "<json string>") -> dict:
    document = json.loads(raw)
    return _validate_openapi_document(document, source)
