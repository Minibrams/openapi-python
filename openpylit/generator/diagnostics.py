from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationError(Exception):
    code: str
    message: str
    details: str | None = None

    def __str__(self) -> str:
        if self.details:
            return f"[{self.code}] {self.message}: {self.details}"
        return f"[{self.code}] {self.message}"


def invalid_spec(message: str, details: str | None = None) -> GenerationError:
    return GenerationError("INVALID_SPEC", message, details)


def invalid_request(message: str, details: str | None = None) -> GenerationError:
    return GenerationError("INVALID_REQUEST", message, details)


def invalid_extension(message: str, details: str | None = None) -> GenerationError:
    return GenerationError("INVALID_EXTENSION", message, details)


def io_failure(message: str, details: str | None = None) -> GenerationError:
    return GenerationError("IO_FAILURE", message, details)
