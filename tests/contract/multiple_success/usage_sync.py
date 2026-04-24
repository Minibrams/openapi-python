from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import CreatedWidget, Widget, WidgetCreate

client = Client(base_url="http://testserver")

body: WidgetCreate = {"name": "alpha"}
result = client.post("/widgets")(body=body)
assert_type(result, Widget | CreatedWidget)
