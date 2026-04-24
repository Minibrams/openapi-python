from __future__ import annotations

from typing import assert_type

from generated.my_client import Client
from generated.my_client.types import TreeNode

client = Client(base_url="http://testserver")

tree = client.get("/tree")()
assert_type(tree, TreeNode)
assert_type(tree["name"], str)
children = tree.get("children")
if children is not None:
    assert_type(children[0]["name"], str)
