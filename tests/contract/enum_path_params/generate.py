from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, cast

from app import app

from openapi_python.generator import GenerationRequest, generate_client


class _Response:
    content = b"{}"

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict[str, object]:
        return {}


class _HttpClient:
    def __init__(self) -> None:
        self.url = ""

    def request(self, **kwargs: Any) -> _Response:
        self.url = str(kwargs["url"])
        return _Response()


def main() -> None:
    generate_client(
        GenerationRequest(
            output_dir=Path(__file__).parent / "generated",
            spec_json=json.dumps(app.openapi()),
            overwrite=True,
        )
    )
    types = importlib.import_module("generated.my_client.types")
    transport_module = importlib.import_module("generated.my_client.transport")
    http_client = _HttpClient()
    transport = transport_module.DefaultTransport(client=cast(Any, http_client))

    transport.request(
        method="get",
        route="/api/v1/pipelines/{name}/executions/{id}",
        base_url="http://testserver",
        params={
            "name": types.PipelineName.DEPLOY_CISCO_ACCESS_SWITCH,
            "id": 1,
        },
        query=None,
        headers=None,
        request_media_type=None,
        body=None,
        response_media_type=None,
    )
    assert (
        http_client.url
        == "http://testserver/api/v1/pipelines/deploy-cisco-access-switch/executions/1"
    )


if __name__ == "__main__":
    main()
