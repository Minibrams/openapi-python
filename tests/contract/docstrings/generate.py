from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

from app import app
from fastapi import FastAPI

from openapi_python.generator import GenerationRequest, generate_client

SWITCH_TEMPLATE_FIELD_DOCSTRINGS = {
    "hostname": "The hostname of the switch",
    "vlans": (
        "All the VLANs that should be configured on the switch. These are all "
        "the VLANs associated with the location in Nautobot."
    ),
    "vlan_interfaces": "All the virtual interfaces on the switch with the tag 'VLAN'.",
    "client_interfaces": "All the client interfaces on the switch.",
    "downlink_interfaces": "All the downlink interfaces on the switch.",
    "uplink_interfaces": "All the uplink interfaces on the switch.",
    "device_mgmt_ip": "The IP address assigned to the switch for management purposes.",
    "management_vlan_id": (
        "The VLAN ID of the management VLAN. This is used for the management "
        "interface and default gateway."
    ),
    "management_interface": (
        "The interface on which the management IP is configured. This is used "
        "to determine which interface should be used for out-of-band management "
        "access to the switch."
    ),
    "default_gateway": "The default gateway for the management VLAN.",
    "snmp_contact": "The SNMP contact information for the switch.",
    "snmp_location": "The SNMP location information for the switch.",
    "ise_profile": "The ISE profile to use for this switch.",
}


def _class_def(module: ast.Module, name: str) -> ast.ClassDef:
    return next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == name
    )


def _field_docstrings(class_def: ast.ClassDef) -> dict[str, str]:
    docs: dict[str, str] = {}
    for field, docstring in zip(class_def.body, class_def.body[1:], strict=False):
        if not isinstance(field, ast.AnnAssign) or not isinstance(
            field.target, ast.Name
        ):
            continue
        if not isinstance(docstring, ast.Expr) or not isinstance(
            docstring.value, ast.Constant
        ):
            continue
        if isinstance(docstring.value.value, str):
            docs[field.target.id] = docstring.value.value
    return docs


def _schema_property_descriptions(schema: dict) -> dict[str, str]:
    properties = schema["properties"]
    return {
        name: prop["description"]
        for name, prop in properties.items()
        if "description" in prop
    }


def main() -> None:
    output_dir = Path(__file__).parent / "generated"
    generate_client(
        GenerationRequest(
            output_dir=output_dir,
            spec_json=json.dumps(app.openapi()),
            overwrite=True,
        )
    )

    source = (output_dir / "my_client" / "types.py").read_text()
    module = ast.parse(source)
    dto = _class_def(module, "MyDTO")
    switch_template = _class_def(module, "CiscoAccessSwitchTemplateParams")
    generated_types = importlib.import_module("generated.my_client.types")

    assert ast.get_docstring(dto) == "This is a descriptive docstring"
    assert generated_types.MyDTO.__doc__ == "This is a descriptive docstring"
    assert "This is the docstring for a single field" in source
    assert _field_docstrings(switch_template) == SWITCH_TEMPLATE_FIELD_DOCSTRINGS

    api_b = FastAPI()

    def get_switch_template() -> object:
        return {}

    api_b.get(
        "/switch-template",
        response_model=generated_types.CiscoAccessSwitchTemplateParams,
    )(get_switch_template)
    schema = api_b.openapi()["components"]["schemas"]["CiscoAccessSwitchTemplateParams"]
    assert _schema_property_descriptions(schema) == SWITCH_TEMPLATE_FIELD_DOCSTRINGS


if __name__ == "__main__":
    main()
