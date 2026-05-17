from __future__ import annotations

from typing import Any, assert_type

from generated.my_client import Client

client = Client(base_url="http://testserver")

book = client.get("/books/{book_id}")(params={"book_id": 1})
assert_type(book, Any)
