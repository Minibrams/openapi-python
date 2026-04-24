from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class TreeNode(BaseModel):
    name: str
    children: list[TreeNode] = Field(default_factory=list)


@app.get("/tree", response_model=TreeNode)
def get_tree() -> TreeNode:
    return TreeNode(
        name="root",
        children=[TreeNode(name="leaf")],
    )
