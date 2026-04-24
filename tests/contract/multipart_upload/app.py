from __future__ import annotations

from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel

app = FastAPI()


class UploadResult(BaseModel):
    filename: str
    description: str
    size: int


@app.post("/uploads", response_model=UploadResult)
async def upload_file(
    description: str = Form(),
    file: UploadFile = File(),
) -> UploadResult:
    content = await file.read()
    return UploadResult(
        filename=file.filename or "",
        description=description,
        size=len(content),
    )
