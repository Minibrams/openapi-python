from __future__ import annotations

from pathlib import Path

from tests.e2e.typing_cases.assert_diagnostics import (
    assert_expected_patterns,
    run_pyright,
)


def test_valid_usage_typechecks(generated_package_dir: Path) -> None:
    case = Path(__file__).parent / "typing_cases" / "valid_usage.py"
    messages = run_pyright(case, generated_package_dir)
    assert messages == []


def test_invalid_usage_emits_expected_diagnostics(generated_package_dir: Path) -> None:
    root = Path(__file__).parent / "typing_cases"
    messages = run_pyright(root / "invalid_usage.py", generated_package_dir)
    assert_expected_patterns(messages, root / "expected_diagnostics.txt")


def test_invalid_transport_adapter_emits_expected_diagnostics(
    generated_package_dir: Path,
) -> None:
    root = Path(__file__).parent / "typing_cases"
    messages = run_pyright(root / "invalid_transport_adapter.py", generated_package_dir)
    assert_expected_patterns(
        messages, root / "expected_transport_adapter_diagnostics.txt"
    )
