from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


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
        query_dict = {key: str(value) for key, value in (query or {}).items()}
        header_dict = {key: str(value) for key, value in (headers or {}).items()}
        response = self._client.request(
            method=method.upper(),
            url=f"{base_url.rstrip('/')}{route.format(**(params or {}))}",
            params=query_dict or None,
            headers=header_dict or None,
            json=body,
        )
        response.raise_for_status()
        if response.content:
            return response.json()
        return None
