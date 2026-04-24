from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import BodyUploadFileUploadsPost, UploadResult

client = Client(base_url="http://testserver")

body: BodyUploadFileUploadsPost = {
    "description": "avatar",
    "file": b"content",
}
result = client.post("/uploads")(body=body)
assert_type(result, UploadResult)
assert_type(result["filename"], str)
assert_type(result["description"], str)
assert_type(result["size"], int)
