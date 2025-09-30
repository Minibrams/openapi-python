from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

import httpx
import yaml  # type: ignore

from openpylit.generate.generator import generate_from_dict


def _load_spec_from_path(p: Path) -> Dict[str, Any]:
    txt = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(txt)
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return yaml.safe_load(txt)


def _load_spec_from_url(url: str, *, no_ssl: bool) -> Dict[str, Any]:
    with httpx.Client(verify=not no_ssl, follow_redirects=True, timeout=30.0) as client:
        r = client.get(url)
        r.raise_for_status()
        ctype = (r.headers.get("content-type") or "").lower()
        text = r.text

    if "yaml" in ctype or "yml" in ctype:
        return yaml.safe_load(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return yaml.safe_load(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sit-http")
    sub = parser.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="Generate a typed client from an OpenAPI spec")
    g.add_argument(
        "--spec", required=True, help="Path or URL to the OpenAPI spec (.json/.yaml)"
    )
    g.add_argument(
        "--out", required=True, help="Output directory for generated package"
    )
    g.add_argument(
        "--package", default="api_client", help="Generated package name (module-safe)"
    )
    g.add_argument(
        "--no-ssl",
        action="store_true",
        help="Ignore SSL certificate errors when fetching spec",
    )

    args = parser.parse_args(argv)

    if args.cmd == "generate":
        spec_src: str = args.spec
        out_dir = Path(args.out)
        pkg = args.package

        parsed = urlparse(spec_src)
        if parsed.scheme in ("http", "https"):
            spec = _load_spec_from_url(spec_src, no_ssl=args.no_ssl)
            generate_from_dict(spec, out_dir, pkg)
        else:
            p = Path(spec_src)
            if not p.exists():
                print(f"[sit-http] Spec file not found: {p}", file=sys.stderr)
                return 2

            spec = _load_spec_from_path(p)
            generate_from_dict(spec, out_dir, pkg)

        print(f"[sit-http] Generated client in {out_dir}/{pkg}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
