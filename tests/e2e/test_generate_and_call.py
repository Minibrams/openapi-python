from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from tests.e2e.fixture_app import app


class AppTransport:
    def request(
        self, *, method: str, route: str, base_url: str, params, query, headers, body
    ):
        with TestClient(app, base_url=base_url) as client:
            response = client.request(
                method=method.upper(),
                url=route.format(**(params or {})),
                params=query,
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            if response.content:
                return response.json()
            return None


def test_generate_and_call(
    generated_client_module, generated_package_dir: Path
) -> None:
    client = generated_client_module.Client(
        base_url="http://test", transport=AppTransport()
    )

    put_result = client.put("/api/v1/users/{id}")(
        params={"id": "9182773"},
        body={"name": "anb", "address": "someaddress", "isActive": True},
    )
    assert put_result["id"] == "9182773"

    get_result = client.get("/api/v1/users/{id}")(params={"id": "9182773"})
    assert get_result["name"] == "anb"

    search_result = client.get("/api/v1/search")(query={"q": "an", "limit": 5})
    assert isinstance(search_result, list)
