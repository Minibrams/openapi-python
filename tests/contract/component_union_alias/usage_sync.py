from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import FGAObjectType, FGARelation, UserFGACheckRequest

client = Client(base_url="http://testserver")

body: UserFGACheckRequest = {
    "relation": "owner",
    "object_type": "sensor",
    "object_id": "sensor-1",
}
relation: FGARelation = body["relation"]
object_type: FGAObjectType = body["object_type"]

response = client.post("/check")(body=body)
assert_type(response, UserFGACheckRequest)
assert_type(response["relation"], FGARelation)
assert_type(response["object_type"], FGAObjectType)
