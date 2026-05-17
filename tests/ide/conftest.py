from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

CURSOR = "<CURSOR>"


class TyServer:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.process = subprocess.Popen(
            ["ty", "server"],
            cwd=self.workspace,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        stdin = self.process.stdin
        stdout = self.process.stdout
        if stdin is None or stdout is None:
            raise RuntimeError("failed to start ty server")

        self.stdin = stdin
        self.stdout = stdout
        self._next_id = 1
        self._request(
            "initialize",
            {
                "processId": None,
                "rootUri": self.workspace.as_uri(),
                "capabilities": {},
            },
        )
        self._notify("initialized", {})

    def close(self) -> None:
        if self.process.poll() is not None:
            return
        try:
            self._request("shutdown", None)
            self._notify("exit", {})
            self.process.wait(timeout=5)
        finally:
            if self.process.poll() is None:
                self.process.kill()
                self.process.wait(timeout=5)

    def completion_labels(self, source: str) -> set[str]:
        if source.count(CURSOR) != 1:
            raise ValueError(f"source must contain exactly one {CURSOR!r} marker")

        before, after = source.split(CURSOR)
        text = before + after
        uri = (self.workspace / "__ty_completion_probe.py").as_uri()

        self._notify(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": "python",
                    "version": 1,
                    "text": text,
                }
            },
        )
        try:
            response = self._request(
                "textDocument/completion",
                {
                    "textDocument": {"uri": uri},
                    "position": _position(before),
                    "context": {"triggerKind": 1},
                },
            )
            result = response.get("result")
            if result is None:
                return set()
            items = result if isinstance(result, list) else result.get("items", [])
            return {
                str(item["label"])
                for item in items
                if isinstance(item, dict) and "label" in item
            }
        finally:
            self._notify("textDocument/didClose", {"textDocument": {"uri": uri}})

    def _request(self, method: str, params: object) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self._send(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        )
        while True:
            message = self._read_message()
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise AssertionError(
                    f"ty server returned an error for {method}: {message['error']}"
                )
            return message

    def _notify(self, method: str, params: object) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _send(self, message: dict[str, object]) -> None:
        payload = json.dumps(message).encode()
        self.stdin.write(f"Content-Length: {len(payload)}\r\n\r\n".encode() + payload)
        self.stdin.flush()

    def _read_message(self) -> dict[str, Any]:
        header = bytearray()
        while b"\r\n\r\n" not in header:
            header.extend(self._read_exact(1))

        content_length = None
        for line in bytes(header).split(b"\r\n"):
            if line.lower().startswith(b"content-length:"):
                content_length = int(line.split(b":", 1)[1].strip())
                break
        if content_length is None:
            raise AssertionError(f"ty server sent invalid LSP headers: {header!r}")

        payload = self._read_exact(content_length)
        return json.loads(payload)

    def _read_exact(self, length: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self.stdout.read(length - len(chunks))
            if not chunk:
                raise RuntimeError("ty server exited unexpectedly")
            chunks.extend(chunk)
        return bytes(chunks)


def _position(text_before_cursor: str) -> dict[str, int]:
    current_line = text_before_cursor.rsplit("\n", 1)[-1]
    return {
        "line": text_before_cursor.count("\n"),
        "character": len(current_line.encode("utf-16-le")) // 2,
    }


@pytest.fixture(scope="module")
def ty_server(ide_workspace: Path) -> Iterator[TyServer]:
    server = TyServer(ide_workspace)
    try:
        yield server
    finally:
        server.close()
