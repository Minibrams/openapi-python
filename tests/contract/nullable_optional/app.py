from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class NullableRecord(BaseModel):
    id: int
    required_nullable: str | None
    optional_note: str | None = None
    optional_count: int | None = None
    tags: list[str] | None = None


@app.get("/records/{record_id}", response_model=NullableRecord)
def get_record(record_id: int) -> NullableRecord:
    return NullableRecord(
        id=record_id,
        required_nullable=None,
        optional_note=None,
        optional_count=3,
        tags=["typed"],
    )
