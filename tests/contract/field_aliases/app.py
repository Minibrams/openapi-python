from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI()


class AliasRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    request_id: str = Field(alias="requestId")
    trace_id: str = Field(alias="traceId")


@app.get("/aliases/{record_id}", response_model=AliasRecord)
def get_alias_record(record_id: int) -> AliasRecord:
    return AliasRecord.model_validate(
        {"requestId": f"req_{record_id}", "traceId": "trace_123"}
    )


@app.post("/aliases", response_model=AliasRecord)
def create_alias_record(body: AliasRecord) -> AliasRecord:
    return body
