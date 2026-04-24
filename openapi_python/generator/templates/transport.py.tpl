from __future__ import annotations

from collections.abc import Mapping
from typing import $typing_imports

$httpx_type_checking
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


class AsyncTransport(Protocol):
    async def request(
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

$default_transport_block
