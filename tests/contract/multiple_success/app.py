from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Widget(BaseModel):
    id: int
    name: str


class CreatedWidget(BaseModel):
    widget: Widget
    created: bool


class WidgetCreate(BaseModel):
    name: str


@app.post(
    "/widgets",
    response_model=Widget,
    responses={201: {"model": CreatedWidget}},
)
def create_widget(body: WidgetCreate) -> Widget:
    return Widget(id=1, name=body.name)
