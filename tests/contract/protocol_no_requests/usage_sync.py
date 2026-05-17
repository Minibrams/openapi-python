from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import Book

client = Client(base_url="http://testserver")

book = client.get("/books/{book_id}")(
    params={"book_id": "not statically constrained"},
    query={"unexpected": object()},
    headers={"x-test": object()},
)
assert_type(book, Book)
assert_type(book["title"], str)
