from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class User(BaseModel):
    id: int
    name: str


class Team(BaseModel):
    id: int
    name: str
    owner: User
    members: list[User]


class TeamEnvelope(BaseModel):
    data: Team
    requested_by: User


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int) -> User:
    return User(id=user_id, name="Ada")


@app.get("/teams/{team_id}", response_model=Team)
def get_team(team_id: int) -> Team:
    owner = User(id=1, name="Ada")
    return Team(id=team_id, name="Core", owner=owner, members=[owner])


@app.get("/teams/{team_id}/envelope", response_model=TeamEnvelope)
def get_team_envelope(team_id: int) -> TeamEnvelope:
    owner = User(id=1, name="Ada")
    team = Team(id=team_id, name="Core", owner=owner, members=[owner])
    return TeamEnvelope(data=team, requested_by=owner)
