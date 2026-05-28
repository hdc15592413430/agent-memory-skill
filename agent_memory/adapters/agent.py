"""Autonomous-agent adapter for checkpointing tool runs and failed attempts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_memory import core


DEFAULT_MEMORY_DIR = ".agent-memory"
RUN_NOTE_FILE = "agent-run-note.md"


def resolve_memory_dir(path: str | Path = DEFAULT_MEMORY_DIR) -> Path:
    return Path(path).expanduser().resolve()


def ensure_memory_dir(path: str | Path = DEFAULT_MEMORY_DIR) -> Path:
    memory_dir = resolve_memory_dir(path)
    if not (memory_dir / core.STATE_FILE).exists():
        state = core.default_state()
        core.write_state(memory_dir, state)
        core.write_packet(memory_dir, state)
        write_run_note(memory_dir, state)
    return memory_dir


def load_agent_state(path: str | Path = DEFAULT_MEMORY_DIR) -> tuple[Path, dict[str, Any]]:
    memory_dir = resolve_memory_dir(path)
    if not (memory_dir / core.STATE_FILE).exists():
        raise FileNotFoundError(f"no agent memory state found at {memory_dir / core.STATE_FILE}")
    return memory_dir, core.load_state(memory_dir)


def validate_or_raise(state: dict[str, Any], memory_dir: Path) -> None:
    errors = core.validate_state(state)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"invalid memory state at {memory_dir / core.STATE_FILE}: {joined}")


def high_signal(records: list[Any], limit: int = 8) -> list[Any]:
    return core.sort_records(records)[:limit]


def build_run_note_from_state(state: dict[str, Any], max_chars: int = 6000) -> str:
    project = state.get("project", {})
    threads = state.get("threads", {})
    migration = state.get("migration", {})

    artifacts = [
        record
        for record in state.get("project", {}).get("artifacts", [])
        if isinstance(record, dict)
    ]
    tool_results = [record for record in artifacts if "tool-result" in record.get("tags", [])]
    failed_attempts = [record for record in artifacts if "failed-attempt" in record.get("tags", [])]

    lines = [
        "# Agent Run Note",
        "",
        "Use this before continuing an autonomous agent run.",
        "",
        "## Objective",
        "",
        project.get("objective", "None") if isinstance(project, dict) else "None",
        "",
        "## Active Thread",
        "",
        f"- {core.record_text(threads.get('active')) if isinstance(threads, dict) else 'None'}",
        "",
        "## Next Actions",
        "",
        core.bullet_list(migration.get("next_actions", []) if isinstance(migration, dict) else []),
        "",
        "## Important Tool Results",
        "",
        core.bullet_list(high_signal(tool_results)),
        "",
        "## Failed Attempts",
        "",
        core.bullet_list(high_signal(failed_attempts)),
        "",
        "## Risks And Do-Not-Redo",
        "",
        core.bullet_list(migration.get("risks", []) if isinstance(migration, dict) else []),
        "",
        "## Handoff Notes",
        "",
        core.bullet_list(migration.get("handoff_notes", []) if isinstance(migration, dict) else []),
        "",
    ]
    note = "\n".join(lines)
    if len(note) <= max_chars:
        return note
    suffix = "\n\n[truncated: read state.json or migration-packet.md for full memory]\n"
    return note[: max_chars - len(suffix)].rstrip() + suffix


def build_run_note(path: str | Path = DEFAULT_MEMORY_DIR, max_chars: int = 6000) -> str:
    memory_dir, state = load_agent_state(path)
    validate_or_raise(state, memory_dir)
    return build_run_note_from_state(state, max_chars=max_chars)


def write_run_note(memory_dir: Path, state: dict[str, Any] | None = None) -> Path:
    if state is None:
        state = core.load_state(memory_dir)
    output_path = memory_dir / RUN_NOTE_FILE
    output_path.write_text(build_run_note_from_state(state), encoding="utf-8", newline="\n")
    return output_path


def prepare_handoff(
    path: str | Path = DEFAULT_MEMORY_DIR,
    *,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    memory_dir, state = load_agent_state(path)
    validate_or_raise(state, memory_dir)
    note_path = write_run_note(memory_dir, state)
    report = core.prepare_handoff_artifacts(
        memory_dir,
        state,
        max_records=max_records,
        include_stale=include_stale,
        include_untrusted=include_untrusted,
        strict=strict,
    )
    report["note"] = note_path
    return report


def save_state(memory_dir: Path, state: dict[str, Any], *, render: bool = True, note: bool = True) -> None:
    validate_or_raise(state, memory_dir)
    core.write_state(memory_dir, state)
    if render:
        core.write_packet(memory_dir, state)
    if note:
        write_run_note(memory_dir, state)


def checkpoint(
    path: str | Path,
    *,
    objective: str | None = None,
    summary: str | None = None,
    next_actions: list[str] | None = None,
    risks: list[str] | None = None,
    handoff_notes: list[str] | None = None,
    render: bool = True,
    note: bool = True,
    handoff: bool = False,
    strict: bool = False,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
) -> Path:
    memory_dir = ensure_memory_dir(path)
    state = core.load_state(memory_dir)
    core.update_meta(
        state,
        objective=objective,
        summary=summary,
        next_actions=next_actions,
        risks=risks,
        handoff_notes=handoff_notes,
    )
    save_state(memory_dir, state, render=render, note=note)
    if handoff:
        report = prepare_handoff(
            memory_dir,
            max_records=max_records,
            include_stale=include_stale,
            include_untrusted=include_untrusted,
            strict=strict,
        )
        if not report["ready"]:
            raise ValueError("memory is not handoff-ready:\n" + core.format_issues(report["issues"]))
    return memory_dir


def record_tool_result(
    path: str | Path,
    *,
    record_id: str,
    tool: str,
    result: str,
    evidence: str = "",
    salience: int = 3,
    confidence: str = "medium",
    tags: list[str] | None = None,
    render: bool = True,
    note: bool = True,
) -> dict[str, Any]:
    memory_dir = ensure_memory_dir(path)
    state = core.load_state(memory_dir)
    all_tags = ["tool-result", f"tool:{tool}", *(tags or [])]
    record = core.add_record(
        state,
        collection="artifacts",
        record_id=record_id,
        text=f"{tool}: {result}",
        record_type="artifact",
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=all_tags,
        source="tool",
        scope="project",
    )
    save_state(memory_dir, state, render=render, note=note)
    return record


def record_failed_attempt(
    path: str | Path,
    *,
    record_id: str,
    text: str,
    evidence: str = "",
    do_not_repeat: str | None = None,
    salience: int = 4,
    confidence: str = "medium",
    tags: list[str] | None = None,
    render: bool = True,
    note: bool = True,
) -> dict[str, Any]:
    memory_dir = ensure_memory_dir(path)
    state = core.load_state(memory_dir)
    record = core.add_record(
        state,
        collection="artifacts",
        record_id=record_id,
        text=text,
        record_type="artifact",
        status="closed",
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=["failed-attempt", *(tags or [])],
        source="agent",
        scope="project",
    )
    if do_not_repeat:
        state["migration"]["risks"].append(do_not_repeat)
    save_state(memory_dir, state, render=render, note=note)
    return record


def command_init(args: argparse.Namespace) -> int:
    memory_dir = ensure_memory_dir(args.path)
    print(f"Agent memory: {memory_dir}")
    return 0


def command_note(args: argparse.Namespace) -> int:
    try:
        note = build_run_note(args.path, max_chars=args.max_chars)
        print(note)
        if args.write:
            memory_dir, state = load_agent_state(args.path)
            validate_or_raise(state, memory_dir)
            output_path = write_run_note(memory_dir, state)
            print(f"Wrote agent run note: {output_path}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


def command_checkpoint(args: argparse.Namespace) -> int:
    try:
        checkpoint(
            args.path,
            objective=args.objective,
            summary=args.summary,
            next_actions=args.next_action,
            risks=args.risk,
            handoff_notes=args.handoff_note,
            render=args.render,
            note=args.note,
            handoff=args.handoff,
            strict=args.strict,
            max_records=args.max_records,
            include_stale=args.include_stale,
            include_untrusted=args.include_untrusted,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Updated agent checkpoint: {resolve_memory_dir(args.path)}")
    if args.handoff:
        memory_dir = resolve_memory_dir(args.path)
        print(f"Prepared agent handoff: {memory_dir / core.BRIEFING_FILE}, {memory_dir / core.PACKET_FILE}")
    return 0


def command_tool_result(args: argparse.Namespace) -> int:
    record = record_tool_result(
        args.path,
        record_id=args.id,
        tool=args.tool,
        result=args.result,
        evidence=args.evidence,
        salience=args.salience,
        confidence=args.confidence,
        tags=args.tag,
        render=args.render,
        note=args.note,
    )
    print(f"Recorded tool result: {record['id']}")
    return 0


def command_failed_attempt(args: argparse.Namespace) -> int:
    record = record_failed_attempt(
        args.path,
        record_id=args.id,
        text=args.text,
        evidence=args.evidence,
        do_not_repeat=args.do_not_repeat,
        salience=args.salience,
        confidence=args.confidence,
        tags=args.tag,
        render=args.render,
        note=args.note,
    )
    print(f"Recorded failed attempt: {record['id']}")
    return 0


def command_handoff(args: argparse.Namespace) -> int:
    try:
        report = prepare_handoff(
            args.path,
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
    print("Agent handoff artifacts ready:")
    print(f"- State: {report['state']}")
    print(f"- Note: {report['note']}")
    print(f"- Briefing: {report['briefing']}")
    print(f"- Packet: {report['packet']}")
    if report["issues"]:
        print("")
        print("Memory quality issues:")
        print(core.format_issues(report["issues"]))
    else:
        print("")
        print(f"No memory quality issues found: {report['state']}")
    return 0 if report["ready"] else 1


def add_common_record_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--id", required=True)
    parser.add_argument("--evidence", default="")
    parser.add_argument("--confidence", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--salience", type=int, choices=range(1, 6), default=3)
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--note", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Autonomous-agent adapter for Agent Memory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create agent memory")
    init_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    init_parser.set_defaults(func=command_init)

    note_parser = subparsers.add_parser("note", help="print an agent run note")
    note_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    note_parser.add_argument("--max-chars", type=int, default=6000)
    note_parser.add_argument("--write", action="store_true")
    note_parser.set_defaults(func=command_note)

    checkpoint_parser = subparsers.add_parser("checkpoint", help="update agent checkpoint metadata")
    checkpoint_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    checkpoint_parser.add_argument("--objective")
    checkpoint_parser.add_argument("--summary")
    checkpoint_parser.add_argument("--next-action", action="append", default=[])
    checkpoint_parser.add_argument("--risk", action="append", default=[])
    checkpoint_parser.add_argument("--handoff-note", action="append", default=[])
    checkpoint_parser.add_argument("--render", action="store_true")
    checkpoint_parser.add_argument("--note", action="store_true")
    checkpoint_parser.add_argument("--handoff", action="store_true", help="also write briefing, packet, run note, and audit readiness")
    checkpoint_parser.add_argument("--strict", action="store_true", help="fail handoff on warnings")
    checkpoint_parser.add_argument("--max-records", type=int, default=5)
    checkpoint_parser.add_argument("--include-stale", action="store_true")
    checkpoint_parser.add_argument("--include-untrusted", action="store_true")
    checkpoint_parser.set_defaults(func=command_checkpoint)

    tool_parser = subparsers.add_parser("tool-result", help="record an important tool result")
    tool_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    add_common_record_args(tool_parser)
    tool_parser.add_argument("--tool", required=True)
    tool_parser.add_argument("--result", required=True)
    tool_parser.set_defaults(func=command_tool_result)

    failed_parser = subparsers.add_parser("failed-attempt", help="record a failed attempt and optional do-not-repeat note")
    failed_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    add_common_record_args(failed_parser)
    failed_parser.add_argument("--text", required=True)
    failed_parser.add_argument("--do-not-repeat")
    failed_parser.set_defaults(func=command_failed_attempt)

    handoff_parser = subparsers.add_parser("handoff", help="write agent handoff artifacts and audit readiness")
    handoff_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
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
