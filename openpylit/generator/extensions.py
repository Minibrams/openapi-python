from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .model import NormalizedSpec


class NormalizeHook(Protocol):
    def __call__(self, normalized: NormalizedSpec) -> NormalizedSpec: ...


class RenderContextHook(Protocol):
    def __call__(
        self, normalized: NormalizedSpec, context: dict[str, str]
    ) -> dict[str, str]: ...


@dataclass(frozen=True)
class GeneratorExtensions:
    normalize_hooks: tuple[NormalizeHook, ...] = ()
    render_context_hooks: tuple[RenderContextHook, ...] = ()
