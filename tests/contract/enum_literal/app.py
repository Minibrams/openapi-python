from __future__ import annotations

from enum import Enum, IntEnum
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Status(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class Rating(IntEnum):
    low = 1
    medium = 2
    high = 3


class Article(BaseModel):
    id: int
    status: Status
    rating: Rating
    visibility: Literal["public", "private"]


class ArticleUpdate(BaseModel):
    status: Status
    rating: Rating
    visibility: Literal["public", "private"]


@app.get("/articles/{article_id}", response_model=Article)
def get_article(article_id: int) -> Article:
    return Article(
        id=article_id,
        status=Status.published,
        rating=Rating.high,
        visibility="public",
    )


@app.patch("/articles/{article_id}", response_model=Article)
def update_article(article_id: int, body: ArticleUpdate) -> Article:
    return Article(
        id=article_id,
        status=body.status,
        rating=body.rating,
        visibility=body.visibility,
    )
