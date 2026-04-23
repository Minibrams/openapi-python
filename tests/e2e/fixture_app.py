from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="OpenPylit Fixture")


class User(BaseModel):
    id: str
    name: str
    address: str
    isActive: bool


class UserUpdate(BaseModel):
    name: str
    address: str
    isActive: bool


class TokenCreate(BaseModel):
    reason: str


_FAKE_DB = {
    "1": User(id="1", name="Alice", address="A street", isActive=True),
}


@app.get("/api/v1/users/{id}", response_model=User)
def get_user(id: str) -> User:
    user = _FAKE_DB.get(id)
    if user is None:
        raise HTTPException(status_code=404, detail="Not found")
    return user


@app.put("/api/v1/users/{id}", response_model=User)
def put_user(id: str, body: UserUpdate) -> User:
    user = User(id=id, name=body.name, address=body.address, isActive=body.isActive)
    _FAKE_DB[id] = user
    return user


@app.get("/api/v1/search", response_model=list[User])
def search_users(q: str, limit: int = 10) -> list[User]:
    matches = [user for user in _FAKE_DB.values() if q.lower() in user.name.lower()]
    return matches[:limit]


@app.post("/api/v1/tokens")
def create_token(
    body: TokenCreate, x_api_key: str = Header(alias="X-Api-Key")
) -> dict[str, str]:
    if x_api_key != "secret":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"token": f"token-for-{body.reason}"}
