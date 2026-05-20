from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class MyDTO(BaseModel):
    """This is a descriptive docstring"""

    a: int = Field(description="This is the docstring for a single field")


@app.get("/dto", response_model=MyDTO)
def get_dto() -> MyDTO:
    return MyDTO(a=1)
