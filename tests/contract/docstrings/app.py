from __future__ import annotations

from typing import Annotated, TypedDict

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class MyDTO(BaseModel):
    """This is a descriptive docstring"""

    a: int = Field(description="This is the docstring for a single field")


class CiscoAccessSwitchVLAN(TypedDict):
    vlan_id: int


class CiscoAccessSwitchVLANInterface(TypedDict):
    name: str


class CiscoAccessSwitchInterface(TypedDict):
    name: str


class ISEProfile(TypedDict):
    name: str


class CiscoAccessSwitchTemplateParams(TypedDict):
    hostname: Annotated[str, Field(description="The hostname of the switch")]
    vlans: Annotated[
        list[CiscoAccessSwitchVLAN],
        Field(
            description=(
                "All the VLANs that should be configured on the switch. These are "
                "all the VLANs associated with the location in Nautobot."
            )
        ),
    ]
    vlan_interfaces: Annotated[
        list[CiscoAccessSwitchVLANInterface],
        Field(
            description="All the virtual interfaces on the switch with the tag 'VLAN'."
        ),
    ]
    client_interfaces: Annotated[
        list[CiscoAccessSwitchInterface],
        Field(description="All the client interfaces on the switch."),
    ]
    downlink_interfaces: Annotated[
        list[CiscoAccessSwitchInterface],
        Field(description="All the downlink interfaces on the switch."),
    ]
    uplink_interfaces: Annotated[
        list[CiscoAccessSwitchInterface],
        Field(description="All the uplink interfaces on the switch."),
    ]
    device_mgmt_ip: Annotated[
        str,
        Field(
            description="The IP address assigned to the switch for management purposes."
        ),
    ]
    management_vlan_id: Annotated[
        int,
        Field(
            description=(
                "The VLAN ID of the management VLAN. This is used for the "
                "management interface and default gateway."
            )
        ),
    ]
    management_interface: Annotated[
        str,
        Field(
            description=(
                "The interface on which the management IP is configured. This is "
                "used to determine which interface should be used for out-of-band "
                "management access to the switch."
            )
        ),
    ]
    default_gateway: Annotated[
        str,
        Field(description="The default gateway for the management VLAN."),
    ]
    snmp_contact: Annotated[
        str,
        Field(description="The SNMP contact information for the switch."),
    ]
    snmp_location: Annotated[
        str,
        Field(description="The SNMP location information for the switch."),
    ]
    ise_profile: Annotated[
        ISEProfile,
        Field(description="The ISE profile to use for this switch."),
    ]


@app.get("/dto", response_model=MyDTO)
def get_dto() -> MyDTO:
    return MyDTO(a=1)


@app.get("/switch-template", response_model=CiscoAccessSwitchTemplateParams)
def get_switch_template() -> CiscoAccessSwitchTemplateParams:
    switch_vlan: CiscoAccessSwitchVLAN = {"vlan_id": 10}
    switch_interface: CiscoAccessSwitchInterface = {"name": "GigabitEthernet1/0/1"}
    return {
        "hostname": "switch-01",
        "vlans": [switch_vlan],
        "vlan_interfaces": [{"name": "Vlan10"}],
        "client_interfaces": [switch_interface],
        "downlink_interfaces": [switch_interface],
        "uplink_interfaces": [switch_interface],
        "device_mgmt_ip": "192.0.2.10",
        "management_vlan_id": 10,
        "management_interface": "Vlan10",
        "default_gateway": "192.0.2.1",
        "snmp_contact": "Network Operations",
        "snmp_location": "DC1",
        "ise_profile": {"name": "default"},
    }
