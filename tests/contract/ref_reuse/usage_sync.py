from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import Team, TeamEnvelope, User

client = Client(base_url="http://testserver")

user = client.get("/users/{user_id}")(params={"user_id": 1})
assert_type(user, User)
assert_type(user["id"], int)

team = client.get("/teams/{team_id}")(params={"team_id": 1})
assert_type(team, Team)
assert_type(team["owner"], User)
assert_type(team["members"], list[User])

envelope = client.get("/teams/{team_id}/envelope")(params={"team_id": 1})
assert_type(envelope, TeamEnvelope)
assert_type(envelope["data"], Team)
assert_type(envelope["data"]["owner"], User)
assert_type(envelope["requested_by"], User)
