"""Backward-compatible import surface for openapi_python.generate modules."""

from openapi_python.generator import (
    GenerationRequest,
    GenerationResult,
    generate_client,
    try_generate_client,
)

__all__ = [
    "GenerationRequest",
    "GenerationResult",
    "generate_client",
    "try_generate_client",
]
