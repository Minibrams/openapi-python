from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, Protocol, overload

from .transport import DefaultTransport, Transport
from .types import *  # noqa: F403

$protocol_blocks

class Client:
    def __init__(self, *, base_url: str, transport: Transport | None = None) -> None:
        self._base_url = base_url
        self._transport = transport or DefaultTransport()

$method_blocks
