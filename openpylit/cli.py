from __future__ import annotations

import argparse
import sys
from pathlib import Path

from openpylit.generator import GenerationRequest, try_generate_client


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openpylit")
    subcommands = parser.add_subparsers(dest="command", required=True)

    generate = subcommands.add_parser(
        "generate", help="Generate a typed client from an OpenAPI spec"
    )
    generate.add_argument("--spec", required=True, help="Path or URL to OpenAPI source")
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
        choices=["default-runtime", "external-adapter"],
        default="default-runtime",
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
        spec_source=args.spec,
        output_dir=Path(args.out),
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
