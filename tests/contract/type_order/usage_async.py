from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import Owner, Person, Team

async_client = AsyncClient(base_url="http://testserver")


async def use_async_client() -> None:
    person: Person = {"name": "Ada"}
    team: Team = {"slug": "core"}

    assert_type(person, Person)
    assert_type(team, Team)
    assert_type(await async_client.get("/owners")(), Owner)
