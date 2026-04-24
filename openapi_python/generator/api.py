from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .diagnostics import GenerationError, invalid_extension, invalid_request
from .extensions import GeneratorExtensions
from .loader import load_openapi, load_openapi_json
from .model import NormalizedSpec
from .normalize import normalize_openapi
from .render import render_package
from .write import write_artifacts


@dataclass(frozen=True)
class GenerationRequest:
    output_dir: Path
    spec_source: str | None = None
    package_name: str = "my_client"
    overwrite: bool = False
    verify_ssl: bool = True
    transport_mode: str = "default"
    extensions: GeneratorExtensions | None = None
    spec_json: str | None = None


@dataclass(frozen=True)
class GenerationResult:
    success: bool
    written_files: tuple[Path, ...] = ()
    operations: int = 0
    type_definitions: int = 0
    diagnostics: tuple[str, ...] = ()


def generate_client(request: GenerationRequest) -> GenerationResult:
    if bool(request.spec_source) == bool(request.spec_json):
        raise invalid_request("Exactly one of spec_source or spec_json is required")
    if not request.package_name:
        raise invalid_request("package_name is required")
    if request.transport_mode not in {"default", "protocol-only"}:
        raise invalid_request("transport_mode must be 'default' or 'protocol-only'")

    if request.spec_json is not None:
        document = load_openapi_json(request.spec_json)
    else:
        document = load_openapi(
            request.spec_source or "", verify_ssl=request.verify_ssl
        )
    normalized = normalize_openapi(document, request.package_name)

    if request.extensions:
        for hook in request.extensions.normalize_hooks:
            candidate = hook(normalized)
            if not isinstance(candidate, NormalizedSpec):
                raise invalid_extension("normalize hook must return NormalizedSpec")
            normalized = candidate

    artifacts = render_package(
        normalized, request.extensions, transport_mode=request.transport_mode
    )
    written = write_artifacts(
        output_dir=request.output_dir, artifacts=artifacts, overwrite=request.overwrite
    )

    return GenerationResult(
        success=True,
        written_files=tuple(written),
        operations=len(normalized.operations),
        type_definitions=len(normalized.aliases) + len(normalized.typed_dicts),
        diagnostics=(),
    )


def try_generate_client(request: GenerationRequest) -> GenerationResult:
    try:
        return generate_client(request)
    except GenerationError as exc:
        return GenerationResult(success=False, diagnostics=(str(exc),))
