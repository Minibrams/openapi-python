from __future__ import annotations

from fastapi import FastAPI, Response, status

app = FastAPI()


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int) -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/jobs/{job_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
def cancel_job(job_id: int) -> None:
    return None
