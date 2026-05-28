"""Workspace adapter for Codex-style agents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent_memory import core


DEFAULT_MEMORY_DIR = ".agent-memory"
MEMORY_DIR_CANDIDATES = (".agent-memory", "memory")


def resolve_workspace(workspace: str | Path) -> Path:
    return Path(workspace).expanduser().resolve()


def find_memory_dir(workspace: str | Path) -> Path | None:
    """Find a memory directory in or above a workspace."""

    current = resolve_workspace(workspace)
    if current.is_file():
        current = current.parent
    if (current / core.STATE_FILE).exists():
        return current
    for parent in (current, *current.parents):
        for name in MEMORY_DIR_CANDIDATES:
            candidate = parent / name
            if (candidate / core.STATE_FILE).exists():
                return candidate
    return None


def ensure_memory_dir(workspace: str | Path, memory_dir_name: str = DEFAULT_MEMORY_DIR) -> Path:
    """Create a workspace memory directory if one does not already exist."""

    workspace_path = resolve_workspace(workspace)
    existing = find_memory_dir(workspace_path)
    if existing is not None:
        return existing
    memory_dir = workspace_path / memory_dir_name
    state = core.default_state()
    core.write_state(memory_dir, state)
    core.write_packet(memory_dir, state)
    return memory_dir


def load_workspace_state(workspace: str | Path) -> tuple[Path, dict]:
    memory_dir = find_memory_dir(workspace)
    if memory_dir is None:
        raise FileNotFoundError("no agent memory directory found")
    return memory_dir, core.load_state(memory_dir)


def build_context(
    workspace: str | Path,
    max_chars: int = 6000,
    *,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
) -> str:
    """Build concise memory context for injection into a Codex-style agent prompt."""

    memory_dir, state = load_workspace_state(workspace)
    errors = core.validate_state(state)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"invalid memory state at {memory_dir / core.STATE_FILE}: {joined}")
    briefing = core.render_briefing(
        state,
        max_records=max_records,
        include_stale=include_stale,
        include_untrusted=include_untrusted,
    ).strip()
    context = (
        "# Agent Memory Context\n\n"
        f"Source: {memory_dir}\n"
        f"Full detail: {memory_dir / core.PACKET_FILE}\n\n"
        f"{briefing}\n"
    )
    if len(context) <= max_chars:
        return context
    suffix = "\n\n[truncated: read migration-packet.md or state.json for full memory]\n"
    return context[: max_chars - len(suffix)].rstrip() + suffix


def prepare_handoff(
    workspace: str | Path,
    *,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
    strict: bool = False,
) -> dict:
    """Write handoff artifacts and return an audit report for a workspace."""

    memory_dir, state = load_workspace_state(workspace)
    return core.prepare_handoff_artifacts(
        memory_dir,
        state,
        max_records=max_records,
        include_stale=include_stale,
        include_untrusted=include_untrusted,
        strict=strict,
    )


def checkpoint(
    workspace: str | Path,
    *,
    summary: str | None = None,
    next_actions: list[str] | None = None,
    risks: list[str] | None = None,
    handoff_notes: list[str] | None = None,
    render: bool = True,
    handoff: bool = False,
    strict: bool = False,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
) -> Path:
    """Update migration metadata for a workspace checkpoint."""

    memory_dir = ensure_memory_dir(workspace)
    state = core.load_state(memory_dir)
    core.update_meta(
        state,
        summary=summary,
        next_actions=next_actions,
        risks=risks,
        handoff_notes=handoff_notes,
    )
    errors = core.validate_state(state)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"invalid memory state at {memory_dir / core.STATE_FILE}: {joined}")
    core.write_state(memory_dir, state)
    if handoff:
        report = core.prepare_handoff_artifacts(
            memory_dir,
            state,
            max_records=max_records,
            include_stale=include_stale,
            include_untrusted=include_untrusted,
            strict=strict,
        )
        if not report["ready"]:
            raise ValueError("memory is not handoff-ready:\n" + core.format_issues(report["issues"]))
    elif render:
        core.write_packet(memory_dir, state)
    return memory_dir


def command_init(args: argparse.Namespace) -> int:
    memory_dir = ensure_memory_dir(args.workspace, args.memory_dir)
    print(f"Workspace memory: {memory_dir}")
    return 0


def command_context(args: argparse.Namespace) -> int:
    try:
        print(
            build_context(
                args.workspace,
                max_chars=args.max_chars,
                max_records=args.max_records,
                include_stale=args.include_stale,
                include_untrusted=args.include_untrusted,
            )
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


def command_checkpoint(args: argparse.Namespace) -> int:
    try:
        memory_dir = checkpoint(
            args.workspace,
            summary=args.summary,
            next_actions=args.next_action,
            risks=args.risk,
            handoff_notes=args.handoff_note,
            render=args.render,
            handoff=args.handoff,
            strict=args.strict,
            max_records=args.max_records,
            include_stale=args.include_stale,
            include_untrusted=args.include_untrusted,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Updated workspace checkpoint: {memory_dir}")
    if args.handoff:
        print(f"Prepared workspace handoff: {memory_dir / core.BRIEFING_FILE}, {memory_dir / core.PACKET_FILE}")
    return 0


def command_handoff(args: argparse.Namespace) -> int:
    try:
        report = prepare_handoff(
            args.workspace,
            max_records=args.max_records,
            include_stale=args.include_stale,
            include_untrusted=args.include_untrusted,
            strict=args.strict,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    if args.json:
        print(json.dumps(core.serialize_handoff_report(report), ensure_ascii=False, indent=2))
        return 0 if report["ready"] else 1
    print("Workspace handoff artifacts ready:")
    print(f"- State: {report['state']}")
    print(f"- Briefing: {report['briefing']}")
    print(f"- Packet: {report['packet']}")
    issues = report["issues"]
    if issues:
        print("")
        print("Memory quality issues:")
        print(core.format_issues(issues))
    else:
        print("")
        print(f"No memory quality issues found: {report['state']}")
    return 0 if report["ready"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex-style workspace adapter for Agent Memory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create or find workspace memory")
    init_parser.add_argument("--workspace", default=".")
    init_parser.add_argument("--memory-dir", default=DEFAULT_MEMORY_DIR)
    init_parser.set_defaults(func=command_init)

    context_parser = subparsers.add_parser("context", help="print memory context for prompt injection")
    context_parser.add_argument("--workspace", default=".")
    context_parser.add_argument("--max-chars", type=int, default=6000)
    context_parser.add_argument("--max-records", type=int, default=5)
    context_parser.add_argument("--include-stale", action="store_true")
    context_parser.add_argument("--include-untrusted", action="store_true")
    context_parser.set_defaults(func=command_context)

    checkpoint_parser = subparsers.add_parser("checkpoint", help="update migration checkpoint metadata")
    checkpoint_parser.add_argument("--workspace", default=".")
    checkpoint_parser.add_argument("--summary")
    checkpoint_parser.add_argument("--next-action", action="append", default=[])
    checkpoint_parser.add_argument("--risk", action="append", default=[])
    checkpoint_parser.add_argument("--handoff-note", action="append", default=[])
    checkpoint_parser.add_argument("--render", action="store_true")
    checkpoint_parser.add_argument("--handoff", action="store_true", help="also write briefing, packet, and audit readiness")
    checkpoint_parser.add_argument("--strict", action="store_true", help="fail handoff on warnings")
    checkpoint_parser.add_argument("--max-records", type=int, default=5)
    checkpoint_parser.add_argument("--include-stale", action="store_true")
    checkpoint_parser.add_argument("--include-untrusted", action="store_true")
    checkpoint_parser.set_defaults(func=command_checkpoint)

    handoff_parser = subparsers.add_parser("handoff", help="write workspace handoff artifacts and audit readiness")
    handoff_parser.add_argument("--workspace", default=".")
    handoff_parser.add_argument("--max-records", type=int, default=5)
    handoff_parser.add_argument("--include-stale", action="store_true")
    handoff_parser.add_argument("--include-untrusted", action="store_true")
    handoff_parser.add_argument("--strict", action="store_true")
    handoff_parser.add_argument("--json", action="store_true")
    handoff_parser.set_defaults(func=command_handoff)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
