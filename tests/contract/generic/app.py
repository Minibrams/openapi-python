from __future__ import annotations

from typing import Generic, TypeVar

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

T = TypeVar("T")


class Item(BaseModel):
    id: int
    name: str


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int


class Envelope(BaseModel, Generic[T]):
    data: T
    request_id: str


class SearchRequest(BaseModel, Generic[T]):
    filters: T
    limit: int


@app.get("/items", response_model=Page[Item])
def list_items() -> Page[Item]:
    return Page(items=[Item(id=1, name="alpha")], total=1)


@app.get("/items/{item_id}", response_model=Envelope[Item])
def get_item(item_id: int) -> Envelope[Item]:
    return Envelope(data=Item(id=item_id, name="alpha"), request_id="req_123")


@app.post("/items/search", response_model=Envelope[Page[Item]])
def search_items(body: SearchRequest[Item]) -> Envelope[Page[Item]]:
    return Envelope(
        data=Page(items=[body.filters], total=1),
        request_id="req_456",
    )
