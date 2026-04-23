from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="OpenPylit Static Type Fixture")


class Book(BaseModel):
    id: int
    title: str
    in_print: bool
    tags: list[str]


class BookCreate(BaseModel):
    title: str
    tags: list[str]


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int) -> Book:
    return Book(
        id=book_id, title="The Left Hand of Darkness", in_print=True, tags=["sf"]
    )


@app.get("/books", response_model=list[Book])
def list_books(limit: int = 10) -> list[Book]:
    return [
        Book(id=1, title="Kindred", in_print=True, tags=["sf", "classic"]),
    ][:limit]


@app.post("/books", response_model=Book)
def create_book(body: BookCreate) -> Book:
    return Book(id=2, title=body.title, in_print=True, tags=body.tags)
