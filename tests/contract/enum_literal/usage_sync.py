from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import (
    Article,
    ArticleUpdate,
    ArticleVisibility,
    Rating,
    Status,
)

client = Client(base_url="http://testserver")

article = client.get("/articles/{article_id}")(params={"article_id": 1})
assert_type(article, Article)
assert_type(article["status"], Status)
assert_type(article["rating"], Rating)
assert_type(article["visibility"], ArticleVisibility)

body: ArticleUpdate = {
    "status": Status.ARCHIVED,
    "rating": Rating._2,
    "visibility": "private",
}
assert_type(body["status"], Status)
assert_type(body["rating"], Rating)
assert_type(body["visibility"], ArticleVisibility)
updated = client.patch("/articles/{article_id}")(
    params={"article_id": 1},
    body=body,
)
assert_type(updated, Article)
assert_type(updated["status"], Status)
assert_type(updated["rating"], Rating)
assert_type(updated["visibility"], ArticleVisibility)
