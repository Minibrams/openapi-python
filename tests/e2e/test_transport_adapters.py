from __future__ import annotations

from fastapi.testclient import TestClient

from tests.e2e.fixture_app import app


class AdapterA:
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
            return response.json() if response.content else None


class AdapterB(AdapterA):
    pass


def test_transport_adapters_work(generated_client_module) -> None:
    client_a = generated_client_module.Client(
        base_url="http://test", transport=AdapterA()
    )
    client_b = generated_client_module.Client(
        base_url="http://test", transport=AdapterB()
    )

    user_a = client_a.put("/api/v1/users/{id}")(
        params={"id": "2"}, body={"name": "B", "address": "x", "isActive": True}
    )
    user_b = client_b.get("/api/v1/users/{id}")(params={"id": "2"})

    assert user_a["id"] == "2"
    assert user_b["id"] == "2"
