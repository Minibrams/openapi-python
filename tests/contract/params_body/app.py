from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    id: int
    name: str
    tags: list[str]


class SearchFilters(BaseModel):
    term: str
    tags: list[str]
    min_score: float | None = None


class SearchRequest(BaseModel):
    filters: SearchFilters
    limit: int


class SearchResult(BaseModel):
    items: list[Item]
    total: int
    applied: SearchRequest


@app.get("/items", response_model=list[Item])
def list_items(
    tenant: str,
    limit: int = 10,
    q: str | None = None,
    tags: Annotated[list[str], Query()] = [],
) -> list[Item]:
    return [Item(id=1, name=q or "alpha", tags=tags)][:limit]


@app.post("/items/search", response_model=SearchResult)
def search_items(body: SearchRequest) -> SearchResult:
    return SearchResult(
        items=[Item(id=1, name=body.filters.term, tags=body.filters.tags)],
        total=1,
        applied=body,
    )
