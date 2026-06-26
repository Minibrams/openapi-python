from __future__ import annotations

from typing import Literal, assert_type

from generated.my_client import Client
from generated.my_client.types import (
    Edge,
    EdgeInlineUnionVariant1,
    EdgeInlineUnionVariant2,
    EdgeMaybeStatus,
    NamedThing,
    POST_Files_NameBody,
    POST_Files_NameResponse,
)

client = Client()

edge = client.get("/edge")()
assert_type(edge, Edge)
assert_type(edge["maybe_status"], EdgeMaybeStatus | None)
assert_type(
    edge["inline_union"],
    EdgeInlineUnionVariant1 | EdgeInlineUnionVariant2 | None,
)
assert_type(edge["const_nullable"], Literal["fixed"] | None)
assert_type(edge["ref_nullable"], NamedThing | None)

small: EdgeInlineUnionVariant1 = {"kind": "small", "count": 1}
large: EdgeInlineUnionVariant2 = {"kind": "large", "name": "core"}
assert_type(small["kind"], Literal["small"])
assert_type(large["kind"], Literal["large"])

body: POST_Files_NameBody = {"description": "avatar", "file": b"content"}
uploaded = client.post("/files/{name}")(
    params={"name": "avatar.png"},
    query={"tag": ["profile"], "enabled": True},
    body=body,
)
assert_type(uploaded, POST_Files_NameResponse)
assert_type(uploaded["ok"], bool)

plain = client.get("/plain")()
assert_type(plain, str)
