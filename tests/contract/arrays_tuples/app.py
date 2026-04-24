from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    id: int
    name: str


class ArrayShapes(BaseModel):
    tags: list[str]
    matrix: list[list[int]]
    items: list[Item]
    pair: tuple[str, int]


@app.get("/array-shapes", response_model=ArrayShapes)
def get_array_shapes() -> ArrayShapes:
    return ArrayShapes(
        tags=["alpha", "beta"],
        matrix=[[1, 2], [3, 4]],
        items=[Item(id=1, name="alpha")],
        pair=("left", 1),
    )
