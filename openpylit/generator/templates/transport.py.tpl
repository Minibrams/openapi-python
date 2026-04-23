from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, Protocol

import httpx

RouteLiteral = Literal[
$route_literals
]


class Transport(Protocol):
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
    ) -> object: ...


class DefaultTransport:
    def __init__(self, *, timeout: float = 30.0) -> None:
        self._client = httpx.Client(timeout=timeout)

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
        formatted_route = route.format(**(params or {}))
        query_dict = {key: str(value) for key, value in (query or {}).items()}
        header_dict = {key: str(value) for key, value in (headers or {}).items()}
        response = self._client.request(
            method=method.upper(),
            url=f"{base_url.rstrip('/')}{formatted_route}",
            params=query_dict or None,
            headers=header_dict or None,
            json=body,
        )
        response.raise_for_status()
        if response.content:
            return response.json()
        return None
