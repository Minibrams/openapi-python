from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import Owner, Person, Team

client = Client(base_url="http://testserver")

person: Person = {"name": "Ada"}
team: Team = {"slug": "core"}

assert_type(person, Person)
assert_type(team, Team)
assert_type(client.get("/owners")(), Owner)
