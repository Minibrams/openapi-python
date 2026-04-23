from __future__ import annotations

from pathlib import Path

from .diagnostics import io_failure
from .model import GeneratedArtifact


def write_artifacts(
    *, output_dir: Path, artifacts: list[GeneratedArtifact], overwrite: bool
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for artifact in sorted(artifacts, key=lambda item: item.relative_path):
        target = output_dir / artifact.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            raise io_failure(
                "Target file already exists; use overwrite to replace", str(target)
            )
        target.write_text(artifact.content, encoding="utf-8")
        written.append(target)

    return written
