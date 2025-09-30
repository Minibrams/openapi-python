from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Union

import httpx

JSONable = Union[dict, list, str, int, float, bool, None]


def _normalize_json(obj: Any) -> Any:  # NEW
    if obj is None:
        return None
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _normalize_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize_json(v) for v in obj]
    return obj


def _normalize_params(
    params: Optional[Mapping[str, Any]],
) -> Optional[Mapping[str, Any]]:  # NEW
    if not params:
        return None
    out = {}
    for k, v in params.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            out[k] = [_normalize_json(x) for x in v]
        else:
            out[k] = _normalize_json(v)
    return out


def _format_path(path_template: str, **path_params: Any) -> str:
    path = path_template
    for k, v in (path_params or {}).items():
        val = _normalize_json(v)  # date->iso, enum->value
        path = path.replace("{" + k + "}", httpx.QueryParams({k: val}).get(k))
    return path


class AsyncBaseClient:
    """
    Minimal async runtime wrapper around httpx.AsyncClient for generated clients.
    """

    def __init__(
        self,
        base_url: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = 30.0,
        client: Optional[httpx.AsyncClient] = None,
        raise_for_status: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers: Dict[str, str] = dict(headers or {})
        self.raise_for_status = raise_for_status
        self._own_client = client is None
        self.client = client or httpx.AsyncClient(timeout=timeout, headers=self.headers)

    async def aclose(self) -> None:
        if self._own_client:
            await self.client.aclose()

    async def _request_json(
        self,
        method: str,
        path_template: str,
        *,
        path_params: Optional[dict] = None,
        query: Optional[Mapping[str, Any]] = None,
        json_body: Optional[JSONable] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> httpx.Response:
        url = self.base_url + _format_path(path_template, **(path_params or {}))
        resp = await self.client.request(
            method,
            url,
            params=(_normalize_params(query) or None),
            json=_normalize_json(json_body),
            headers=headers,
        )
        if self.raise_for_status:
            resp.raise_for_status()
        return resp
