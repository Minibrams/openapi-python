from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import Article, ArticleUpdate, ArticleVisibility, Status

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    article = await async_client.get("/articles/{article_id}")(params={"article_id": 1})
    assert_type(article, Article)
    assert_type(article["status"], Status)
    assert_type(article["visibility"], ArticleVisibility)

    body: ArticleUpdate = {"status": Status.ARCHIVED, "visibility": "private"}
    assert_type(body["status"], Status)
    assert_type(body["visibility"], ArticleVisibility)
    updated = await async_client.patch("/articles/{article_id}")(
        params={"article_id": 1},
        body=body,
    )
    assert_type(updated, Article)
    assert_type(updated["status"], Status)
    assert_type(updated["visibility"], ArticleVisibility)
