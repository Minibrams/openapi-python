from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal, Protocol, overload

from .transport import AsyncTransport, DefaultAsyncTransport, DefaultTransport, Transport
from .types import *  # noqa: F403

$protocol_blocks
$async_protocol_blocks

class Client:
    def __init__(self, *, base_url: str, transport: Transport | None = None) -> None:
        self._base_url = base_url
        self._transport = transport or DefaultTransport()

$method_blocks

class AsyncClient:
    def __init__(
        self, *, base_url: str, transport: AsyncTransport | None = None
    ) -> None:
        self._base_url = base_url
        self._transport = transport or DefaultAsyncTransport()

$async_method_blocks
