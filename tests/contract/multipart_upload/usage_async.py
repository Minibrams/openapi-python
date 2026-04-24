from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import BodyUploadFileUploadsPost, UploadResult

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    body: BodyUploadFileUploadsPost = {
        "description": "avatar",
        "file": b"content",
    }
    result = await async_client.post("/uploads")(body=body)
    assert_type(result, UploadResult)
    assert_type(result["filename"], str)
    assert_type(result["description"], str)
    assert_type(result["size"], int)
