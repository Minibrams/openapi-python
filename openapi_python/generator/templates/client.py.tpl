from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal, Protocol, overload

$transport_imports
from .types import *  # noqa: F403

$protocol_blocks
$async_protocol_blocks

class Client:
    def __init__(self, *, base_url: str, transport: $sync_transport_type) -> None:
        self._base_url = base_url
        self._transport = $sync_transport_assignment

$method_blocks

class AsyncClient:
    def __init__(
        self, *, base_url: str, transport: $async_transport_type
    ) -> None:
        self._base_url = base_url
        self._transport = $async_transport_assignment

$async_method_blocks
