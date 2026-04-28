from __future__ import annotations

import argparse
import gzip
import json
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


def _load_spec(path: Path) -> str:
    if path.suffix == ".gz":
        return gzip.decompress(path.read_bytes()).decode("utf-8")
    return path.read_text(encoding="utf-8")


def _load_generator(package_path: Path) -> tuple[Any, Any]:
    sys.path.insert(0, str(package_path.resolve()))

    from openapi_python.generator import GenerationRequest, generate_client

    return GenerationRequest, generate_client


def _run_once(
    *,
    generate_client: Any,
    generation_request: Any,
    spec_json: str,
    package_name: str,
) -> tuple[float, Any]:
    output_dir = Path(tempfile.mkdtemp(prefix="openapi-python-benchmark-"))
    try:
        start = time.perf_counter()
        result = generate_client(
            generation_request(
                output_dir=output_dir,
                spec_json=spec_json,
                package_name=package_name,
                overwrite=True,
            )
        )
        elapsed = time.perf_counter() - start
        return elapsed, result
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def run_benchmark(args: argparse.Namespace) -> int:
    spec_json = _load_spec(args.spec)
    generation_request, generate_client = _load_generator(args.package_path)

    result = None
    for _ in range(args.warmup):
        _, result = _run_once(
            generate_client=generate_client,
            generation_request=generation_request,
            spec_json=spec_json,
            package_name=args.package,
        )

    samples = []
    for _ in range(args.repeat):
        elapsed, result = _run_once(
            generate_client=generate_client,
            generation_request=generation_request,
            spec_json=spec_json,
            package_name=args.package,
        )
        samples.append(elapsed)

    if result is None:
        raise RuntimeError("benchmark did not run")

    payload = {
        "best_seconds": min(samples),
        "median_seconds": statistics.median(samples),
        "samples_seconds": samples,
        "operations": result.operations,
        "type_definitions": result.type_definitions,
        "repeat": args.repeat,
        "warmup": args.warmup,
    }

    encoded = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


def compare_benchmarks(args: argparse.Namespace) -> int:
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))

    baseline_seconds = float(baseline["best_seconds"])
    candidate_seconds = float(candidate["best_seconds"])
    allowed_seconds = baseline_seconds * (1 + args.max_regression)
    change = (candidate_seconds - baseline_seconds) / baseline_seconds

    print(f"baseline best:  {baseline_seconds:.6f}s")
    print(f"candidate best: {candidate_seconds:.6f}s")
    print(f"change:         {change:+.2%}")
    print(f"limit:          +{args.max_regression:.2%}")

    if candidate_seconds > allowed_seconds:
        print(
            "generation benchmark regressed beyond the configured limit",
            file=sys.stderr,
        )
        return 1
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="benchmark_generate.py",
        description="Benchmark OpenAPI client generation for a large spec.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    run = subcommands.add_parser("run", help="Run the generation benchmark")
    run.add_argument("--spec", type=Path, required=True)
    run.add_argument("--package-path", type=Path, default=Path.cwd())
    run.add_argument("--package", default="my_client")
    run.add_argument("--repeat", type=int, default=5)
    run.add_argument("--warmup", type=int, default=1)
    run.add_argument("--output", type=Path)
    run.set_defaults(func=run_benchmark)

    compare = subcommands.add_parser("compare", help="Compare two benchmark results")
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--candidate", type=Path, required=True)
    compare.add_argument("--max-regression", type=float, default=0.02)
    compare.set_defaults(func=compare_benchmarks)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
