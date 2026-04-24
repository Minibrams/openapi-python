from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]


def run(
    command: list[str], *, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(command))
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as file:
        return tomllib.load(file)["project"]["version"]


def require_supported_version(version: str) -> None:
    if not re.fullmatch(r"\d+\.\d+\.\d+((a|b|rc)\d+)?", version):
        print(f"Unsupported release version: {version!r}")
        print("Expected X.Y.Z, X.Y.ZaN, X.Y.ZbN, or X.Y.ZrcN.")
        sys.exit(1)


def require_clean_worktree() -> None:
    status = run(["git", "status", "--porcelain"], capture=True).stdout.strip()
    if status:
        print(
            "Release requires a clean git worktree. Commit or stash these changes first:"
        )
        print(status)
        sys.exit(1)


def require_tag_available(tag: str) -> None:
    local = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if local.returncode == 0:
        print(f"Tag {tag} already exists locally.")
        sys.exit(1)

    remote = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--tags", "origin", f"refs/tags/{tag}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if remote.returncode == 0:
        print(f"Tag {tag} already exists on origin.")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare and optionally publish from the releases branch."
    )
    parser.add_argument(
        "--version",
        help="Expected version. Defaults to the version in pyproject.toml.",
    )
    parser.add_argument(
        "--push-release-branch",
        action="store_true",
        help="Push the current commit to origin/releases after release checks pass.",
    )
    args = parser.parse_args()

    version = project_version()
    require_supported_version(version)
    if args.version and args.version != version:
        print(
            f"Expected version {args.version}, but pyproject.toml contains {version}."
        )
        sys.exit(1)

    tag = f"v{version}"

    require_clean_worktree()
    require_tag_available(tag)

    dist = ROOT / "dist"
    if dist.exists():
        shutil.rmtree(dist)

    run(["uv", "run", "ruff", "check", "--select", "I", "."])
    run(["uv", "run", "ruff", "format", "--check", "."])
    run(["uv", "run", "basedpyright", "."])
    run(["uv", "run", "pytest", "tests/test_contracts.py", "-n", "auto"])
    run(["uv", "build"])
    run(["uv", "run", "twine", "check", *sorted(str(path) for path in dist.iterdir())])

    if args.push_release_branch:
        run(["git", "push", "origin", "HEAD:releases"])
        print("Pushed current commit to origin/releases.")
        print("GitHub Actions will create the release tag and publish after approval.")
    else:
        print(f"Release checks passed for {tag}.")
        print("Publish with: git push origin HEAD:releases")


if __name__ == "__main__":
    main()
