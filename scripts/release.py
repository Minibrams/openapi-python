from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(
    r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:(?P<stage>a|b|rc)(?P<stage_number>\d+))?"
)
STAGE_ORDER = {"a": 0, "b": 1, "rc": 2, None: 3}


class Version(NamedTuple):
    major: int
    minor: int
    patch: int
    stage: int
    stage_number: int


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


def parse_version(version: str) -> Version | None:
    match = VERSION_PATTERN.fullmatch(version)
    if not match:
        return None
    stage = match.group("stage")
    stage_number = match.group("stage_number")
    return Version(
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        STAGE_ORDER[stage],
        int(stage_number or 0),
    )


def require_supported_version(version: str) -> Version:
    parsed = parse_version(version)
    if parsed is None:
        print(f"Unsupported release version: {version!r}")
        print("Expected X.Y.Z, X.Y.ZaN, X.Y.ZbN, or X.Y.ZrcN.")
        sys.exit(1)
    return parsed


def require_next_version(current: str, next_version: str) -> None:
    if require_supported_version(next_version) <= require_supported_version(current):
        print(
            f"Next version must be higher than the current version: "
            f"{next_version} <= {current}."
        )
        sys.exit(1)


def require_clean_worktree() -> None:
    status = run(["git", "status", "--porcelain"], capture=True).stdout.strip()
    if status:
        print(
            "Release requires a clean git worktree. Commit or stash these changes first:"
        )
        print(status)
        sys.exit(1)


def require_branch(branch: str) -> None:
    current = run(["git", "branch", "--show-current"], capture=True).stdout.strip()
    if current != branch:
        print(
            f"Release must be run from {branch!r}, but current branch is {current!r}."
        )
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


def commit_version_bump(tag: str) -> None:
    run(["git", "add", "pyproject.toml", "uv.lock"])
    staged = run(["git", "diff", "--cached", "--name-only"], capture=True).stdout
    if not staged.strip():
        print("Version bump did not change pyproject.toml or uv.lock.")
        sys.exit(1)
    run(["git", "commit", "-m", f"Release {tag}"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run local checks and build distributions before releasing."
    )
    parser.add_argument(
        "--version",
        help="Next release version. Prompts when omitted.",
    )
    args = parser.parse_args()

    current_version = project_version()
    require_supported_version(current_version)
    print(f"Current version: {current_version}")

    next_version = args.version or input("Next version: ").strip()
    if not next_version:
        print("A next version is required.")
        sys.exit(1)

    require_next_version(current_version, next_version)
    tag = f"v{next_version}"

    require_clean_worktree()
    require_branch("main")
    require_tag_available(tag)
    run(["uv", "version", next_version, "--no-sync"])

    dist = ROOT / "dist"
    if dist.exists():
        shutil.rmtree(dist)

    run(["uv", "run", "ruff", "check", "--select", "I", "."])
    run(["uv", "run", "ruff", "format", "--check", "."])
    run(["uv", "run", "ty", "check", "."])
    run(["uv", "run", "pytest", "-n", "auto"])
    run(["uv", "build"])

    commit_version_bump(tag)
    run(["git", "push", "origin", "main"])
    run(["git", "push", "origin", "HEAD:releases"])

    print(f"Release checks passed for {tag}.")
    print("Release pushed to main and releases.")


if __name__ == "__main__":
    main()
