"""Conversation adapter for ordinary AI chat assistants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_memory import core


DEFAULT_MEMORY_DIR = ".agent-memory"
NOTE_FILE = "chat-memory-note.md"

KIND_TO_COLLECTION = {
    "preference": "preferences",
    "working-style": "working-style",
    "avoid": "avoid",
    "fact": "facts",
    "decision": "decisions",
    "episode": "episodes",
    "artifact": "artifacts",
    "open-thread": "open-threads",
}


def resolve_memory_dir(path: str | Path = DEFAULT_MEMORY_DIR) -> Path:
    return Path(path).expanduser().resolve()


def ensure_memory_dir(path: str | Path = DEFAULT_MEMORY_DIR) -> Path:
    memory_dir = resolve_memory_dir(path)
    if not (memory_dir / core.STATE_FILE).exists():
        state = core.default_state()
        core.write_state(memory_dir, state)
        core.write_packet(memory_dir, state)
        write_note(memory_dir, state)
    return memory_dir


def load_chat_state(path: str | Path = DEFAULT_MEMORY_DIR) -> tuple[Path, dict[str, Any]]:
    memory_dir = resolve_memory_dir(path)
    if not (memory_dir / core.STATE_FILE).exists():
        raise FileNotFoundError(f"no chat memory state found at {memory_dir / core.STATE_FILE}")
    return memory_dir, core.load_state(memory_dir)


def validate_or_raise(state: dict[str, Any], memory_dir: Path) -> None:
    errors = core.validate_state(state)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"invalid memory state at {memory_dir / core.STATE_FILE}: {joined}")


def active_text(state: dict[str, Any]) -> str:
    active = state.get("threads", {}).get("active")
    return core.record_text(active)


def high_signal_records(records: list[Any], limit: int = 6) -> list[Any]:
    return core.sort_records(records)[:limit]


def section(title: str, items: list[Any] | str | None) -> list[str]:
    lines = [f"## {title}", ""]
    if isinstance(items, str):
        lines.append(items or "- None")
    else:
        lines.append(core.bullet_list(items or []))
    lines.append("")
    return lines


def build_note_from_state(memory_dir: Path, state: dict[str, Any], max_chars: int = 5000) -> str:
    user_profile = state.get("user_profile", {})
    threads = state.get("threads", {})
    migration = state.get("migration", {})

    preferences = []
    if isinstance(user_profile, dict):
        preferences.extend(user_profile.get("preferences", []))
        preferences.extend(user_profile.get("working_style", []))
        preferences.extend(user_profile.get("avoid", []))

    lines = [
        "# Chat Memory Note",
        "",
        "Use this as curated operating memory, not as a transcript.",
        "",
    ]
    lines.extend(section("User Preferences", high_signal_records(preferences)))
    lines.extend(section("Active Topic", f"- {active_text(state)}"))
    lines.extend(section("Parked Topics", high_signal_records(threads.get("parked", []))))
    lines.extend(section("Side Episodes", high_signal_records(state.get("episodes", []))))
    lines.extend(section("Decisions", high_signal_records(state.get("decisions", []))))
    lines.extend(section("Next Actions", migration.get("next_actions", [])))
    lines.extend(section("Risks And Avoid", migration.get("risks", [])))

    note = "\n".join(lines).rstrip() + "\n"
    if len(note) <= max_chars:
        return note
    suffix = "\n\n[truncated: read state.json or migration-packet.md for full memory]\n"
    return note[: max_chars - len(suffix)].rstrip() + suffix


def build_note(path: str | Path = DEFAULT_MEMORY_DIR, max_chars: int = 5000) -> str:
    """Build a user-visible memory note for a conversation assistant."""

    memory_dir, state = load_chat_state(path)
    validate_or_raise(state, memory_dir)
    return build_note_from_state(memory_dir, state, max_chars=max_chars)


def write_note(memory_dir: Path, state: dict[str, Any] | None = None) -> Path:
    if state is None:
        state = core.load_state(memory_dir)
    note = build_note_from_state(memory_dir, state)
    output_path = memory_dir / NOTE_FILE
    core.write_text_atomic(output_path, note)
    return output_path


def prepare_handoff(
    path: str | Path = DEFAULT_MEMORY_DIR,
    *,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    memory_dir, state = load_chat_state(path)
    validate_or_raise(state, memory_dir)
    note_path = write_note(memory_dir, state)
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
        write_note(memory_dir, state)


def remember(
    path: str | Path,
    *,
    kind: str,
    record_id: str,
    text: str,
    evidence: str = "",
    confidence: str = "medium",
    salience: int = 3,
    tags: list[str] | None = None,
    render: bool = True,
    note: bool = True,
) -> dict[str, Any]:
    memory_dir = ensure_memory_dir(path)
    state = core.load_state(memory_dir)
    if kind not in KIND_TO_COLLECTION:
        choices = ", ".join(sorted(KIND_TO_COLLECTION))
        raise ValueError(f"unknown memory kind: {kind}; choose one of: {choices}")
    scope = "user" if kind in {"preference", "working-style", "avoid"} else "project"
    record = core.add_record(
        state,
        collection=KIND_TO_COLLECTION[kind],
        record_id=record_id,
        text=text,
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=tags,
        source="user",
        scope=scope,
    )
    save_state(memory_dir, state, render=render, note=note)
    return record


def set_topic(
    path: str | Path,
    *,
    thread_id: str,
    text: str,
    evidence: str = "",
    confidence: str = "medium",
    salience: int = 3,
    tags: list[str] | None = None,
    park_current: bool = False,
    render: bool = True,
    note: bool = True,
) -> dict[str, Any]:
    memory_dir = ensure_memory_dir(path)
    state = core.load_state(memory_dir)
    thread = core.set_active_thread(
        state,
        record_id=thread_id,
        text=text,
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=tags,
        park_current=park_current,
    )
    save_state(memory_dir, state, render=render, note=note)
    return thread


def side_topic(
    path: str | Path,
    *,
    episode_id: str,
    episode_text: str,
    thread_id: str,
    thread_text: str,
    evidence: str = "",
    confidence: str = "medium",
    salience: int = 4,
    tags: list[str] | None = None,
    render: bool = True,
    note: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    memory_dir = ensure_memory_dir(path)
    state = core.load_state(memory_dir)
    episode, thread = core.interrupt_thread(
        state,
        episode_id=episode_id,
        episode_text=episode_text,
        thread_id=thread_id,
        thread_text=thread_text,
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=tags,
    )
    save_state(memory_dir, state, render=render, note=note)
    return episode, thread


def resume_topic(
    path: str | Path,
    *,
    current_destination: str = "closed",
    render: bool = True,
    note: bool = True,
) -> dict[str, Any]:
    memory_dir = ensure_memory_dir(path)
    state = core.load_state(memory_dir)
    thread = core.resume_thread(state, current_destination=current_destination)
    save_state(memory_dir, state, render=render, note=note)
    return thread


def command_init(args: argparse.Namespace) -> int:
    memory_dir = ensure_memory_dir(args.path)
    print(f"Chat memory: {memory_dir}")
    return 0


def command_note(args: argparse.Namespace) -> int:
    try:
        note = build_note(args.path, max_chars=args.max_chars)
        print(note)
        if args.write:
            memory_dir, state = load_chat_state(args.path)
            validate_or_raise(state, memory_dir)
            output_path = write_note(memory_dir, state)
            print(f"Wrote chat memory note: {output_path}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


def command_remember(args: argparse.Namespace) -> int:
    try:
        record = remember(
            args.path,
            kind=args.kind,
            record_id=args.id,
            text=args.text,
            evidence=args.evidence,
            confidence=args.confidence,
            salience=args.salience,
            tags=args.tag,
            render=args.render,
            note=args.note,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Remembered {record['id']} as {args.kind}")
    return 0


def command_set_topic(args: argparse.Namespace) -> int:
    thread = set_topic(
        args.path,
        thread_id=args.id,
        text=args.text,
        evidence=args.evidence,
        confidence=args.confidence,
        salience=args.salience,
        tags=args.tag,
        park_current=args.park_current,
        render=args.render,
        note=args.note,
    )
    print(f"Set active chat topic: {thread['id']}")
    return 0


def command_side_topic(args: argparse.Namespace) -> int:
    episode, thread = side_topic(
        args.path,
        episode_id=args.episode_id,
        episode_text=args.episode_text,
        thread_id=args.thread_id,
        thread_text=args.thread_text,
        evidence=args.evidence,
        confidence=args.confidence,
        salience=args.salience,
        tags=args.tag,
        render=args.render,
        note=args.note,
    )
    print(f"Captured side topic {episode['id']} and active topic {thread['id']}")
    return 0


def command_resume(args: argparse.Namespace) -> int:
    try:
        thread = resume_topic(
            args.path,
            current_destination=args.current_destination,
            render=args.render,
            note=args.note,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Resumed chat topic: {thread['id']}")
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
    print("Chat handoff artifacts ready:")
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


def add_memory_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--id", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--evidence", default="")
    parser.add_argument("--confidence", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--salience", type=int, choices=range(1, 6), default=3)
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--note", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conversation adapter for Agent Memory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create chat memory")
    init_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    init_parser.set_defaults(func=command_init)

    note_parser = subparsers.add_parser("note", help="print a user-visible memory note")
    note_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    note_parser.add_argument("--max-chars", type=int, default=5000)
    note_parser.add_argument("--write", action="store_true")
    note_parser.set_defaults(func=command_note)

    remember_parser = subparsers.add_parser("remember", help="store a chat memory record")
    remember_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    remember_parser.add_argument("--kind", required=True, choices=sorted(KIND_TO_COLLECTION))
    add_memory_args(remember_parser)
    remember_parser.set_defaults(func=command_remember)

    topic_parser = subparsers.add_parser("set-topic", help="set the active chat topic")
    topic_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    add_memory_args(topic_parser)
    topic_parser.add_argument("--park-current", action="store_true")
    topic_parser.set_defaults(func=command_set_topic)

    side_parser = subparsers.add_parser("side-topic", help="capture a side topic and park the current one")
    side_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    side_parser.add_argument("--episode-id", required=True)
    side_parser.add_argument("--episode-text", required=True)
    side_parser.add_argument("--thread-id", required=True)
    side_parser.add_argument("--thread-text", required=True)
    side_parser.add_argument("--evidence", default="")
    side_parser.add_argument("--confidence", choices=["low", "medium", "high"], default="medium")
    side_parser.add_argument("--salience", type=int, choices=range(1, 6), default=4)
    side_parser.add_argument("--tag", action="append", default=[])
    side_parser.add_argument("--render", action="store_true")
    side_parser.add_argument("--note", action="store_true")
    side_parser.set_defaults(func=command_side_topic)

    resume_parser = subparsers.add_parser("resume", help="resume the most recently parked chat topic")
    resume_parser.add_argument("--path", default=DEFAULT_MEMORY_DIR)
    resume_parser.add_argument("--current-destination", choices=["closed", "open", "parked", "drop"], default="closed")
    resume_parser.add_argument("--render", action="store_true")
    resume_parser.add_argument("--note", action="store_true")
    resume_parser.set_defaults(func=command_resume)

    handoff_parser = subparsers.add_parser("handoff", help="write chat handoff artifacts and audit readiness")
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
