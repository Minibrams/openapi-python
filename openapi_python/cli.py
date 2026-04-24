from __future__ import annotations

import argparse
import sys
from pathlib import Path

from openapi_python.generator import GenerationRequest, try_generate_client


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openapi-python")
    subcommands = parser.add_subparsers(dest="command", required=True)

    generate = subcommands.add_parser(
        "generate", help="Generate a typed client from an OpenAPI spec"
    )
    spec_input = generate.add_mutually_exclusive_group(required=True)
    spec_input.add_argument("--spec", help="Path or URL to OpenAPI source")
    spec_input.add_argument("--spec-json", help="OpenAPI source as a JSON string")
    generate.add_argument("--out", required=True, help="Output directory")
    generate.add_argument(
        "--package", default="my_client", help="Generated package name"
    )
    generate.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing generated files"
    )
    generate.add_argument(
        "--no-ssl",
        action="store_true",
        help="Disable SSL certificate verification for URL specs",
    )
    generate.add_argument(
        "--transport-mode",
        choices=["default", "protocol-only"],
        default="default",
        help="Generation mode for transport integration",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "generate":
        parser.print_help()
        return 2

    request = GenerationRequest(
        output_dir=Path(args.out),
        spec_source=args.spec,
        spec_json=args.spec_json,
        package_name=args.package,
        overwrite=args.overwrite,
        verify_ssl=not args.no_ssl,
        transport_mode=args.transport_mode,
    )
    result = try_generate_client(request)

    if not result.success:
        print(result.diagnostics[0], file=sys.stderr)
        return 2

    print(
        f"Generated {len(result.written_files)} files for package '{args.package}' "
        f"({result.operations} operations, {result.type_definitions} type definitions)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
