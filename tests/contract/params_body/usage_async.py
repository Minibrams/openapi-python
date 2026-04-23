from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import (
    GET_ItemsQuery,
    Item,
    SearchFilters,
    SearchRequest,
    SearchResult,
)

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    query: GET_ItemsQuery = {
        "tenant": "acme",
        "limit": 5,
        "q": "alp",
        "tags": ["sf", "classic"],
    }
    assert_type(query["tenant"], str)
    assert_type(query["limit"], int)
    assert_type(query.get("q"), str | None)
    assert_type(query["tags"], list[str])

    items = await async_client.get("/items")(query=query)
    assert_type(items, list[Item])
    assert_type(items[0]["id"], int)
    assert_type(items[0]["tags"], list[str])

    filters: SearchFilters = {"term": "alpha", "tags": ["sf"], "min_score": None}
    body: SearchRequest = {"filters": filters, "limit": 10}
    result = await async_client.post("/items/search")(body=body)
    assert_type(result, SearchResult)
    assert_type(result["items"], list[Item])
    assert_type(result["applied"], SearchRequest)
    assert_type(result["applied"]["filters"], SearchFilters)
