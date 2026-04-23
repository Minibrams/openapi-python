from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .diagnostics import GenerationError, invalid_extension, invalid_request
from .extensions import GeneratorExtensions
from .loader import load_openapi
from .model import NormalizedSpec
from .normalize import normalize_openapi
from .render import render_package
from .write import write_artifacts


@dataclass(frozen=True)
class GenerationRequest:
    spec_source: str
    output_dir: Path
    package_name: str = "my_client"
    overwrite: bool = False
    verify_ssl: bool = True
    transport_mode: str = "default-runtime"
    extensions: GeneratorExtensions | None = None


@dataclass(frozen=True)
class GenerationResult:
    success: bool
    written_files: tuple[Path, ...] = ()
    operations: int = 0
    type_definitions: int = 0
    diagnostics: tuple[str, ...] = ()


@dataclass
class _GenerationContext:
    normalized: NormalizedSpec
    warnings: list[str] = field(default_factory=list)


def generate_client(request: GenerationRequest) -> GenerationResult:
    if not request.spec_source:
        raise invalid_request("spec_source is required")
    if not request.package_name:
        raise invalid_request("package_name is required")
    if request.transport_mode not in {"default-runtime", "external-adapter"}:
        raise invalid_request(
            "transport_mode must be 'default-runtime' or 'external-adapter'"
        )

    document = load_openapi(request.spec_source, verify_ssl=request.verify_ssl)
    normalized = normalize_openapi(document, request.package_name)

    if request.extensions:
        for hook in request.extensions.normalize_hooks:
            candidate = hook(normalized)
            if not isinstance(candidate, NormalizedSpec):
                raise invalid_extension("normalize hook must return NormalizedSpec")
            normalized = candidate

    artifacts = render_package(normalized, request.extensions)
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
