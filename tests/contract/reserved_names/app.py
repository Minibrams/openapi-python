from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI()


class OddNames(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    class_: str = Field(alias="class")
    from_: str = Field(alias="from")
    user_id: int = Field(alias="user-id")
    value_123: bool = Field(alias="123value")


@app.get("/odd-names", response_model=OddNames)
def get_odd_names() -> OddNames:
    return OddNames.model_validate(
        {
            "class": "primary",
            "from": "service",
            "user-id": 123,
            "123value": True,
        }
    )


@app.post("/odd-names", response_model=OddNames)
def create_odd_names(body: OddNames) -> OddNames:
    return body
