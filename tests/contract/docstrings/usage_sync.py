from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import MyDTO

client = Client(base_url="http://testserver")

result = client.get("/dto")()
assert_type(result, MyDTO)
assert_type(result["a"], int)
