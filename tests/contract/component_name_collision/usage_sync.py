from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import FooBar, FooBar2

client = Client(base_url="http://testserver")

hyphen = client.get("/hyphen")()
assert_type(hyphen, FooBar)
assert_type(hyphen["hyphen"], str)

underscore = client.get("/underscore")()
assert_type(underscore, FooBar2)
assert_type(underscore["underscore"], int)
