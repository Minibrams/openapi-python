from __future__ import annotations

from typing import TypeVar, overload

_T = TypeVar("_T")


@overload
def safe_get(obj: object, *path: str | int) -> object | None: ...


@overload
def safe_get(obj: object, *path: str | int, type: type[_T]) -> _T | None: ...


def safe_get(
    obj: object, *path: str | int, type: type[object] | None = None
) -> object | None:
    current = obj
    for part in path:
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
            continue

        if isinstance(current, list) and isinstance(part, int):
            if not -len(current) <= part < len(current):
                return None
            current = current[part]
            continue

        return None

    if type is not None and not isinstance(current, type):
        return None
    return current
