from __future__ import annotations

from openpylit.generator import loader


class _Response:
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload.encode("utf-8")


def test_load_openapi_uses_verified_ssl_by_default(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout, context=None):
        captured["context"] = context
        return _Response(
            '{"openapi":"3.1.0","paths":{"/x":{"get":{"responses":{"200":{"description":"ok"}}}}}}'
        )

    monkeypatch.setattr(loader, "urlopen", fake_urlopen)

    document = loader.load_openapi("https://example.com/openapi.json")

    assert document["openapi"] == "3.1.0"
    assert captured["context"] is None


def test_load_openapi_can_disable_ssl_verification(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout, context=None):
        captured["context"] = context
        return _Response(
            '{"openapi":"3.1.0","paths":{"/x":{"get":{"responses":{"200":{"description":"ok"}}}}}}'
        )

    monkeypatch.setattr(loader, "urlopen", fake_urlopen)

    document = loader.load_openapi("https://example.com/openapi.json", verify_ssl=False)

    assert document["openapi"] == "3.1.0"
    assert captured["context"] is not None
