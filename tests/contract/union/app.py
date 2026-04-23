from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class LookupResult(BaseModel):
    value: int | str | dict


@app.get("/lookup/{value}")
def lookup_value(value: int | str) -> LookupResult:
    return LookupResult(value=value)
