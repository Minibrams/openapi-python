from __future__ import annotations

from typing import assert_type

from generated.my_client import AsyncClient
from generated.my_client.types import CiscoAccessSwitchTemplateParams, MyDTO

client = AsyncClient(base_url="http://testserver")


async def main() -> None:
    result = await client.get("/dto")()
    assert_type(result, MyDTO)
    assert_type(result["a"], int)

    switch_template = await client.get("/switch-template")()
    assert_type(switch_template, CiscoAccessSwitchTemplateParams)
    assert_type(switch_template["hostname"], str)
    assert_type(switch_template["management_vlan_id"], int)
