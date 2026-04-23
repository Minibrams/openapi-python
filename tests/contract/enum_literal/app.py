from __future__ import annotations

from enum import Enum
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Status(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class Article(BaseModel):
    id: int
    status: Status
    visibility: Literal["public", "private"]


class ArticleUpdate(BaseModel):
    status: Status
    visibility: Literal["public", "private"]


@app.get("/articles/{article_id}", response_model=Article)
def get_article(article_id: int) -> Article:
    return Article(id=article_id, status=Status.published, visibility="public")


@app.patch("/articles/{article_id}", response_model=Article)
def update_article(article_id: int, body: ArticleUpdate) -> Article:
    return Article(id=article_id, status=body.status, visibility=body.visibility)
