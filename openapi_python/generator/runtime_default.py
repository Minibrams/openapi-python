from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


def _serialize_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    return value


def _serialize_mapping(values: Mapping[str, object] | None) -> dict[str, object]:
    return {key: _serialize_value(value) for key, value in (values or {}).items()}


class RuntimeDefaultTransport:
    def __init__(self, *, client: httpx.Client | None = None) -> None:
        if client is None:
            import httpx

            client = httpx.Client()
        self._client = client

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
        path_params = _serialize_mapping(params)
        query_dict = {
            key: str(value) for key, value in _serialize_mapping(query).items()
        }
        header_dict = {
            key: str(value) for key, value in _serialize_mapping(headers).items()
        }
        response = self._client.request(
            method=method.upper(),
            url=f"{base_url.rstrip('/')}{route.format(**path_params)}",
            params=query_dict or None,
            headers=header_dict or None,
            json=body,
        )
        response.raise_for_status()
        if response.content:
            return response.json()
        return None
