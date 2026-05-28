#!/usr/bin/env python3
"""Install the bundled agent-memory skill into a local Codex skills directory."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "agent-memory"


def default_target_dir() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def validate_source(source: Path) -> None:
    if not source.exists():
        raise ValueError(f"skill source does not exist: {source}")
    if not source.is_dir():
        raise ValueError(f"skill source is not a directory: {source}")
    if not (source / "SKILL.md").exists():
        raise ValueError(f"skill source is missing SKILL.md: {source}")


def install_skill(
    *,
    source: Path = DEFAULT_SOURCE,
    target_dir: Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> Path:
    source = source.expanduser().resolve()
    target_dir = (target_dir or default_target_dir()).expanduser().resolve()
    validate_source(source)

    destination = target_dir / source.name
    if destination.resolve() == source:
        print(f"Source and destination are the same: {destination}")
        return destination

    if dry_run:
        print(f"Would install {source} to {destination}")
        return destination

    if destination.exists():
        if not force:
            raise FileExistsError(f"skill already exists: {destination}; use --force to replace it")
        if destination.is_symlink() or not destination.is_dir():
            raise ValueError(f"refusing to replace non-directory destination: {destination}")
        shutil.rmtree(destination)

    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    print(f"Installed agent-memory skill to {destination}")
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install the bundled agent-memory Codex skill.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="skill source directory")
    parser.add_argument("--target-dir", default=None, help="directory that should contain the installed skill")
    parser.add_argument("--force", action="store_true", help="replace an existing installed skill")
    parser.add_argument("--dry-run", action="store_true", help="print the planned install path without copying files")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        install_skill(
            source=Path(args.source),
            target_dir=Path(args.target_dir) if args.target_dir else None,
            force=args.force,
            dry_run=args.dry_run,
        )
    except (FileExistsError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
