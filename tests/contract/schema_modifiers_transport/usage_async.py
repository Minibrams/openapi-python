from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import (
    Edge,
    EdgeInlineUnionVariant1,
    EdgeInlineUnionVariant2,
    NamedThing,
    POST_Files_NameBody,
    POST_Files_NameResponse,
)

client = AsyncClient()


async def use_async_client() -> None:
    edge = await client.get("/edge")()
    assert_type(edge, Edge)
    assert_type(
        edge["inline_union"],
        EdgeInlineUnionVariant1 | EdgeInlineUnionVariant2 | None,
    )
    assert_type(edge["ref_nullable"], NamedThing | None)

    body: POST_Files_NameBody = {"description": "avatar", "file": b"content"}
    uploaded = await client.post("/files/{name}")(
        params={"name": "avatar.png"},
        query={"tag": ["profile"], "enabled": True},
        body=body,
    )
    assert_type(uploaded, POST_Files_NameResponse)

    plain = await client.get("/plain")()
    assert_type(plain, str)
