from __future__ import annotations

from my_client import Client


class BadAdapter:
    def request(self, route):
        return None


Client(base_url="http://example", transport=BadAdapter())
