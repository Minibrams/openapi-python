from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import Book

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    book = await async_client.get("/books/{book_id}")(params={"book_id": 1})
    assert_type(book, Book)
    assert_type(book["id"], int)
    assert_type(book["title"], str)
    assert_type(book["in_print"], bool)
    assert_type(book["tags"], list[str])

    books = await async_client.get("/books")(query={"limit": 5})
    assert_type(books, list[Book])
    assert_type(books[0]["title"], str)

    created = await async_client.post("/books")(body={"title": "Dawn", "tags": ["sf"]})
    assert_type(created, Book)
    assert_type(created["tags"], list[str])
