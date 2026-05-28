"""Multi-agent adapter with shared and role-local memory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_memory import core


DEFAULT_BASE_DIR = ".agent-memory-multi"
SHARED_DIR = "shared"
ROLES_DIR = "roles"
NOTE_FILE = "multi-agent-note.md"

ROLE_KIND_TO_COLLECTION = {
    "fact": "facts",
    "artifact": "artifacts",
    "decision": "decisions",
    "episode": "episodes",
    "open-thread": "open-threads",
}


def resolve_base(path: str | Path = DEFAULT_BASE_DIR) -> Path:
    return Path(path).expanduser().resolve()


def shared_dir(base: str | Path = DEFAULT_BASE_DIR) -> Path:
    return resolve_base(base) / SHARED_DIR


def role_dir(base: str | Path, role: str) -> Path:
    safe_role = role.strip().replace(" ", "-")
    if not safe_role:
        raise ValueError("role cannot be empty")
    return resolve_base(base) / ROLES_DIR / safe_role


def ensure_memory_dir(memory_dir: Path) -> Path:
    if not (memory_dir / core.STATE_FILE).exists():
        state = core.default_state()
        core.write_state(memory_dir, state)
        core.write_packet(memory_dir, state)
    return memory_dir


def ensure_multi_agent_dir(base: str | Path = DEFAULT_BASE_DIR) -> Path:
    base_path = resolve_base(base)
    ensure_memory_dir(base_path / SHARED_DIR)
    (base_path / ROLES_DIR).mkdir(parents=True, exist_ok=True)
    write_orchestration_note(base_path)
    return base_path


def ensure_role(base: str | Path, role: str) -> Path:
    ensure_multi_agent_dir(base)
    memory_dir = role_dir(base, role)
    ensure_memory_dir(memory_dir)
    return memory_dir


def load_state(memory_dir: Path) -> dict[str, Any]:
    return core.load_state(memory_dir)


def validate_or_raise(state: dict[str, Any], memory_dir: Path) -> None:
    errors = core.validate_state(state)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"invalid memory state at {memory_dir / core.STATE_FILE}: {joined}")


def save_state(memory_dir: Path, state: dict[str, Any]) -> None:
    validate_or_raise(state, memory_dir)
    core.write_state(memory_dir, state)
    core.write_packet(memory_dir, state)


def role_names(base: str | Path) -> list[str]:
    roles_path = resolve_base(base) / ROLES_DIR
    if not roles_path.exists():
        return []
    return sorted(path.name for path in roles_path.iterdir() if (path / core.STATE_FILE).exists())


def record_shared_decision(
    base: str | Path,
    *,
    record_id: str,
    text: str,
    evidence: str = "",
    confidence: str = "medium",
    salience: int = 4,
    role: str | None = None,
) -> dict[str, Any]:
    base_path = ensure_multi_agent_dir(base)
    memory_dir = base_path / SHARED_DIR
    state = load_state(memory_dir)
    tags = ["shared"]
    if role:
        tags.append(f"role:{role}")
    record = core.add_record(
        state,
        collection="decisions",
        record_id=record_id,
        text=text,
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=tags,
        source="agent",
        scope="organization",
    )
    save_state(memory_dir, state)
    write_orchestration_note(base_path)
    return record


def record_role_memory(
    base: str | Path,
    *,
    role: str,
    kind: str,
    record_id: str,
    text: str,
    evidence: str = "",
    confidence: str = "medium",
    salience: int = 3,
) -> dict[str, Any]:
    if kind not in ROLE_KIND_TO_COLLECTION:
        choices = ", ".join(sorted(ROLE_KIND_TO_COLLECTION))
        raise ValueError(f"unknown role memory kind: {kind}; choose one of: {choices}")
    memory_dir = ensure_role(base, role)
    state = load_state(memory_dir)
    record = core.add_record(
        state,
        collection=ROLE_KIND_TO_COLLECTION[kind],
        record_id=record_id,
        text=text,
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=[f"role:{role}", kind],
        source="agent",
        scope="role",
    )
    save_state(memory_dir, state)
    write_orchestration_note(resolve_base(base))
    return record


def checkpoint_shared(
    base: str | Path,
    *,
    objective: str | None = None,
    summary: str | None = None,
    next_actions: list[str] | None = None,
    risks: list[str] | None = None,
    handoff_notes: list[str] | None = None,
    handoff: bool = False,
    strict: bool = False,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
) -> Path:
    base_path = ensure_multi_agent_dir(base)
    memory_dir = base_path / SHARED_DIR
    state = load_state(memory_dir)
    core.update_meta(
        state,
        objective=objective,
        summary=summary,
        next_actions=next_actions,
        risks=risks,
        handoff_notes=handoff_notes,
    )
    save_state(memory_dir, state)
    write_orchestration_note(base_path)
    if handoff:
        report = prepare_handoff(
            base_path,
            max_records=max_records,
            include_stale=include_stale,
            include_untrusted=include_untrusted,
            strict=strict,
        )
        if not report["ready"]:
            raise ValueError("multi-agent memory is not handoff-ready:\n" + core.format_issues(report["issues"]))
    return memory_dir


def compact_records(records: list[Any], limit: int = 5) -> list[Any]:
    return core.sort_records(records)[:limit]


def build_orchestration_note(base: str | Path = DEFAULT_BASE_DIR, max_chars: int = 8000) -> str:
    base_path = resolve_base(base)
    shared_memory = base_path / SHARED_DIR
    if not (shared_memory / core.STATE_FILE).exists():
        raise FileNotFoundError(f"no shared memory found at {shared_memory / core.STATE_FILE}")
    shared_state = load_state(shared_memory)
    validate_or_raise(shared_state, shared_memory)

    project = shared_state.get("project", {})
    migration = shared_state.get("migration", {})
    lines = [
        "# Multi-Agent Orchestration Note",
        "",
        "Use this to hand off a multi-agent run without mixing shared decisions and role-local findings.",
        "",
        "## Shared Objective",
        "",
        project.get("objective", "None") if isinstance(project, dict) else "None",
        "",
        "## Shared Summary",
        "",
        migration.get("summary", "None") if isinstance(migration, dict) else "None",
        "",
        "## Shared Decisions",
        "",
        core.bullet_list(compact_records(shared_state.get("decisions", []))),
        "",
        "## Shared Next Actions",
        "",
        core.bullet_list(migration.get("next_actions", []) if isinstance(migration, dict) else []),
        "",
        "## Shared Risks",
        "",
        core.bullet_list(migration.get("risks", []) if isinstance(migration, dict) else []),
        "",
        "## Role Memories",
        "",
    ]

    for role in role_names(base_path):
        memory_dir = role_dir(base_path, role)
        role_state = load_state(memory_dir)
        validate_or_raise(role_state, memory_dir)
        role_project = role_state.get("project", {})
        role_artifacts = role_project.get("artifacts", []) if isinstance(role_project, dict) else []
        role_facts = role_project.get("facts", []) if isinstance(role_project, dict) else []
        lines.extend(
            [
                f"### {role}",
                "",
                "Facts:",
                core.bullet_list(compact_records(role_facts)),
                "",
                "Artifacts:",
                core.bullet_list(compact_records(role_artifacts)),
                "",
                "Episodes:",
                core.bullet_list(compact_records(role_state.get("episodes", []))),
                "",
            ]
        )

    note = "\n".join(lines).rstrip() + "\n"
    if len(note) <= max_chars:
        return note
    suffix = "\n\n[truncated: read shared/state.json and roles/*/state.json for full memory]\n"
    return note[: max_chars - len(suffix)].rstrip() + suffix


def write_orchestration_note(base: str | Path = DEFAULT_BASE_DIR) -> Path:
    base_path = resolve_base(base)
    output_path = base_path / NOTE_FILE
    core.write_text_atomic(output_path, build_orchestration_note(base_path))
    return output_path


def prefixed_issues(report: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    return [
        {
            "severity": issue["severity"],
            "path": f"{prefix}.{issue['path']}",
            "message": issue["message"],
        }
        for issue in report.get("issues", [])
    ]


def prepare_handoff(
    base: str | Path = DEFAULT_BASE_DIR,
    *,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    base_path = ensure_multi_agent_dir(base)
    shared_memory = base_path / SHARED_DIR
    shared_report = core.prepare_handoff_artifacts(
        shared_memory,
        load_state(shared_memory),
        max_records=max_records,
        include_stale=include_stale,
        include_untrusted=include_untrusted,
        strict=strict,
    )
    role_reports = {}
    for role in role_names(base_path):
        memory_dir = role_dir(base_path, role)
        role_reports[role] = core.prepare_handoff_artifacts(
            memory_dir,
            load_state(memory_dir),
            max_records=max_records,
            include_stale=include_stale,
            include_untrusted=include_untrusted,
            strict=strict,
        )
    note_path = write_orchestration_note(base_path)
    issues = prefixed_issues(shared_report, "shared")
    for role, report in role_reports.items():
        issues.extend(prefixed_issues(report, f"roles.{role}"))
    return {
        "base": base_path,
        "note": note_path,
        "shared": shared_report,
        "roles": role_reports,
        "issues": issues,
        "ready": shared_report["ready"] and all(report["ready"] for report in role_reports.values()),
    }


def command_init(args: argparse.Namespace) -> int:
    base = ensure_multi_agent_dir(args.path)
    for role in args.role:
        ensure_role(base, role)
    write_orchestration_note(base)
    print(f"Multi-agent memory: {base}")
    return 0


def command_checkpoint(args: argparse.Namespace) -> int:
    try:
        checkpoint_shared(
            args.path,
            objective=args.objective,
            summary=args.summary,
            next_actions=args.next_action,
            risks=args.risk,
            handoff_notes=args.handoff_note,
            handoff=args.handoff,
            strict=args.strict,
            max_records=args.max_records,
            include_stale=args.include_stale,
            include_untrusted=args.include_untrusted,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"Updated shared multi-agent checkpoint: {resolve_base(args.path)}")
    if args.handoff:
        print(f"Prepared multi-agent handoff: {resolve_base(args.path)}")
    return 0


def command_shared_decision(args: argparse.Namespace) -> int:
    record = record_shared_decision(
        args.path,
        record_id=args.id,
        text=args.text,
        evidence=args.evidence,
        confidence=args.confidence,
        salience=args.salience,
        role=args.role,
    )
    print(f"Recorded shared decision: {record['id']}")
    return 0


def command_role_memory(args: argparse.Namespace) -> int:
    record = record_role_memory(
        args.path,
        role=args.role,
        kind=args.kind,
        record_id=args.id,
        text=args.text,
        evidence=args.evidence,
        confidence=args.confidence,
        salience=args.salience,
    )
    print(f"Recorded {args.role} memory: {record['id']}")
    return 0


def command_note(args: argparse.Namespace) -> int:
    try:
        note = build_orchestration_note(args.path, max_chars=args.max_chars)
        print(note)
        if args.write:
            output_path = write_orchestration_note(args.path)
            print(f"Wrote multi-agent note: {output_path}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
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
    print("Multi-agent handoff artifacts ready:")
    print(f"- Base: {report['base']}")
    print(f"- Note: {report['note']}")
    print(f"- Shared briefing: {report['shared']['briefing']}")
    print(f"- Shared packet: {report['shared']['packet']}")
    for role, role_report in report["roles"].items():
        print(f"- Role {role} briefing: {role_report['briefing']}")
        print(f"- Role {role} packet: {role_report['packet']}")
    if report["issues"]:
        print("")
        print("Memory quality issues:")
        print(core.format_issues(report["issues"]))
    else:
        print("")
        print("No memory quality issues found across shared and role memory")
    return 0 if report["ready"] else 1


def add_record_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--id", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--evidence", default="")
    parser.add_argument("--confidence", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--salience", type=int, choices=range(1, 6), default=3)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Multi-agent shared and role-local memory adapter.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create multi-agent memory")
    init_parser.add_argument("--path", default=DEFAULT_BASE_DIR)
    init_parser.add_argument("--role", action="append", default=[])
    init_parser.set_defaults(func=command_init)

    checkpoint_parser = subparsers.add_parser("checkpoint", help="update shared checkpoint metadata")
    checkpoint_parser.add_argument("--path", default=DEFAULT_BASE_DIR)
    checkpoint_parser.add_argument("--objective")
    checkpoint_parser.add_argument("--summary")
    checkpoint_parser.add_argument("--next-action", action="append", default=[])
    checkpoint_parser.add_argument("--risk", action="append", default=[])
    checkpoint_parser.add_argument("--handoff-note", action="append", default=[])
    checkpoint_parser.add_argument("--handoff", action="store_true", help="also write shared and role handoff artifacts")
    checkpoint_parser.add_argument("--strict", action="store_true", help="fail handoff on warnings")
    checkpoint_parser.add_argument("--max-records", type=int, default=5)
    checkpoint_parser.add_argument("--include-stale", action="store_true")
    checkpoint_parser.add_argument("--include-untrusted", action="store_true")
    checkpoint_parser.set_defaults(func=command_checkpoint)

    decision_parser = subparsers.add_parser("shared-decision", help="record a shared decision")
    decision_parser.add_argument("--path", default=DEFAULT_BASE_DIR)
    add_record_args(decision_parser)
    decision_parser.add_argument("--role")
    decision_parser.set_defaults(func=command_shared_decision)

    role_parser = subparsers.add_parser("role-memory", help="record role-local memory")
    role_parser.add_argument("--path", default=DEFAULT_BASE_DIR)
    role_parser.add_argument("--role", required=True)
    role_parser.add_argument("--kind", required=True, choices=sorted(ROLE_KIND_TO_COLLECTION))
    add_record_args(role_parser)
    role_parser.set_defaults(func=command_role_memory)

    note_parser = subparsers.add_parser("note", help="print multi-agent orchestration note")
    note_parser.add_argument("--path", default=DEFAULT_BASE_DIR)
    note_parser.add_argument("--max-chars", type=int, default=8000)
    note_parser.add_argument("--write", action="store_true")
    note_parser.set_defaults(func=command_note)

    handoff_parser = subparsers.add_parser("handoff", help="write multi-agent handoff artifacts and audit readiness")
    handoff_parser.add_argument("--path", default=DEFAULT_BASE_DIR)
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
