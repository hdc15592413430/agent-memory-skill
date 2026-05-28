"""Command line interface for Agent Memory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .schema import state_schema
from .core import (
    BRIEFING_FILE,
    BUNDLE_FILE,
    COLLECTIONS,
    KNOWN_STATUSES,
    MemoryWriteConflict,
    KNOWN_SCOPES,
    KNOWN_SOURCES,
    PACKET_FILE,
    PLAN_DIR,
    STATE_FILE,
    add_record,
    apply_compaction_plan,
    audit_state,
    build_memory_bundle,
    capture_plan_artifact,
    compact_state_plan,
    default_state,
    delete_record,
    detect_topic_cue,
    format_issues,
    handoff_exit_code,
    interrupt_thread,
    load_state,
    prepare_handoff_artifacts,
    promote_memory_record,
    propose_memory_record,
    redact_record,
    render_briefing,
    render_compaction_plan,
    render_integration_mode,
    render_packet,
    render_selected_records,
    render_session_health,
    recommend_integration_mode,
    resume_thread,
    assess_session_health,
    serialize_handoff_report,
    set_active_thread,
    select_memory_records,
    state_from_memory_bundle,
    supersede_record,
    update_record,
    update_meta,
    validate_state,
    write_briefing,
    write_packet,
    write_state,
    write_text_atomic,
)


def maybe_render(memory_dir: Path, state: dict, should_render: bool) -> None:
    if should_render:
        write_packet(memory_dir, state)


def print_errors(errors: list[str]) -> None:
    for error in errors:
        print(f"ERROR: {error}")


def write_error(exc: Exception) -> int:
    print(f"ERROR: {exc}")
    return 1


def save_valid_state(memory_dir: Path, state: dict, *, render: bool = False, check_revision: bool = True) -> int:
    errors = validate_state(state)
    if errors:
        print_errors(errors)
        return 1
    try:
        write_state(memory_dir, state, check_revision=check_revision)
        maybe_render(memory_dir, state, render)
    except (MemoryWriteConflict, TimeoutError, OSError) as exc:
        return write_error(exc)
    return 0


def save_state_and_handoff_artifacts(memory_dir: Path, state: dict, *, check_revision: bool = True) -> int:
    errors = validate_state(state)
    if errors:
        print_errors(errors)
        return 1
    try:
        write_state(memory_dir, state, check_revision=check_revision)
        write_briefing(memory_dir, state)
        write_packet(memory_dir, state)
    except (MemoryWriteConflict, TimeoutError, OSError) as exc:
        return write_error(exc)
    return 0


def command_init(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state_path = memory_dir / STATE_FILE
    if state_path.exists() and not args.force:
        print(f"Already exists: {state_path}")
        return 0
    state = default_state()
    try:
        write_state(memory_dir, state, check_revision=False)
        write_packet(memory_dir, state)
    except (MemoryWriteConflict, TimeoutError, OSError) as exc:
        return write_error(exc)
    print(f"Initialized memory state at {state_path}")
    print(f"Rendered migration packet at {memory_dir / PACKET_FILE}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    errors = validate_state(state)
    if errors:
        print_errors(errors)
        return 1
    print(f"Valid memory state: {memory_dir / STATE_FILE}")
    return 0


def command_render(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    errors = validate_state(state)
    if errors:
        print_errors(errors)
        return 1
    if args.output:
        output_path = Path(args.output)
        write_text_atomic(output_path, render_packet(state))
    else:
        output_path = memory_dir / PACKET_FILE
        write_packet(memory_dir, state)
    print(f"Rendered migration packet at {output_path}")
    return 0


def command_brief(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    errors = validate_state(state)
    if errors:
        print_errors(errors)
        return 1
    briefing = render_briefing(
        state,
        max_records=args.max_records,
        include_stale=args.include_stale,
        include_untrusted=args.include_untrusted,
    )
    if args.write:
        write_briefing(
            memory_dir,
            state,
            max_records=args.max_records,
            include_stale=args.include_stale,
            include_untrusted=args.include_untrusted,
        )
        print(f"Rendered memory briefing at {memory_dir / BRIEFING_FILE}")
    elif args.output:
        output_path = Path(args.output)
        write_text_atomic(output_path, briefing)
        print(f"Rendered memory briefing at {output_path}")
    else:
        print(briefing)
    return 0


def print_issues(issues: list[dict[str, str]]) -> None:
    print(format_issues(issues))


def command_handoff(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        summary = prepare_handoff_artifacts(
            memory_dir,
            state,
            max_records=args.max_records,
            include_stale=args.include_stale,
            include_untrusted=args.include_untrusted,
            strict=args.strict,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    issues = summary["issues"]
    exit_code = 0 if summary["ready"] else 1
    if args.json:
        print(json.dumps(serialize_handoff_report(summary), ensure_ascii=False, indent=2))
        return exit_code

    print("Handoff artifacts ready:")
    print(f"- State: {summary['state']}")
    print(f"- Briefing: {summary['briefing']}")
    print(f"- Packet: {summary['packet']}")
    if issues:
        print("")
        print("Memory quality issues:")
        print_issues(issues)
    else:
        print("")
        print(f"No memory quality issues found: {memory_dir / STATE_FILE}")
    return exit_code


def command_schema(args: argparse.Namespace) -> int:
    schema_text = json.dumps(state_schema(), ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        write_text_atomic(output_path, schema_text + "\n")
        print(f"Wrote schema: {output_path}")
    else:
        print(schema_text)
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    issues = audit_state(state)
    if not issues:
        print(f"No memory quality issues found: {memory_dir / STATE_FILE}")
        return 0
    print_issues(issues)
    return handoff_exit_code(issues, strict=args.strict)


def command_integration_mode(args: argparse.Namespace) -> int:
    report = recommend_integration_mode(
        agent_memory_exists=args.agent_memory_exists,
        existing_memory_exists=args.existing_memory_exists,
        trust_unclear=args.trust_unclear,
        audit_only=args.audit_only,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_integration_mode(report))
    return 0


def command_session_health(args: argparse.Namespace) -> int:
    report = assess_session_health(
        message_count=args.messages,
        session_bytes=args.session_bytes,
        context_bytes=args.context_bytes,
        handoff_age_hours=args.handoff_age_hours,
        warning_messages=args.warning_messages,
        critical_messages=args.critical_messages,
        warning_session_bytes=args.warning_session_bytes,
        critical_session_bytes=args.critical_session_bytes,
        warning_context_bytes=args.warning_context_bytes,
        critical_context_bytes=args.critical_context_bytes,
        warning_handoff_age_hours=args.warning_handoff_age_hours,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_session_health(report))
    return 0 if report["status"] == "ok" or not args.strict else 1


def command_export(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        bundle = build_memory_bundle(
            state,
            max_records=args.max_records,
            include_stale=args.include_stale,
            include_untrusted=args.include_untrusted,
            strict=args.strict,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    issues = bundle["audit"]["issues"]
    if args.strict and handoff_exit_code(issues, strict=True):
        print("ERROR: memory is not strict-export-ready")
        if issues:
            print_issues(issues)
        return 1
    output_path = Path(args.output) if args.output else memory_dir / BUNDLE_FILE
    write_text_atomic(output_path, json.dumps(bundle, ensure_ascii=False, indent=2) + "\n")
    print(f"Exported memory bundle at {output_path}")
    return 0


def command_import(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state_path = memory_dir / STATE_FILE
    if state_path.exists() and not args.force:
        print(f"Already exists: {state_path}; pass --force to overwrite")
        return 1
    try:
        bundle = json.loads(Path(args.input).read_text(encoding="utf-8"))
        state = state_from_memory_bundle(bundle)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    result = save_state_and_handoff_artifacts(memory_dir, state, check_revision=False)
    if result != 0:
        return result
    print(f"Imported memory bundle into {memory_dir}")
    print(f"Rendered memory briefing at {memory_dir / BRIEFING_FILE}")
    print(f"Rendered migration packet at {memory_dir / PACKET_FILE}")
    return 0


def command_select(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    errors = validate_state(state)
    if errors:
        print_errors(errors)
        return 1
    results = select_memory_records(
        state,
        query=args.query,
        collections=args.collection,
        record_types=args.record_type,
        tags=args.tag,
        statuses=args.status,
        sources=args.source,
        scopes=args.scope,
        min_salience=args.min_salience,
        limit=args.limit,
        include_stale=args.include_stale,
        include_candidates=args.include_candidates,
        include_untrusted=args.include_untrusted,
    )
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(render_selected_records(results))
    return 0


def command_compact(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        plan = compact_state_plan(
            state,
            min_salience=args.min_salience,
            include_active_thread=args.include_active_thread,
            max_closed_recently=args.max_closed_recently,
            max_episodes=args.max_episodes,
            max_artifacts=args.max_artifacts,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    if not args.apply:
        if args.json:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
        else:
            print(render_compaction_plan(plan))
        return 0

    try:
        result = apply_compaction_plan(state, plan)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    save_result = save_state_and_handoff_artifacts(memory_dir, state)
    if save_result != 0:
        return save_result
    if args.json:
        print(json.dumps({"plan": plan, "result": result}, ensure_ascii=False, indent=2))
    else:
        print(render_compaction_plan(plan))
        print(f"Applied compaction suggestions: {len(result['applied'])}")
        if result["skipped"]:
            print(f"Skipped suggestions: {len(result['skipped'])}")
        print(f"Rendered memory briefing at {memory_dir / BRIEFING_FILE}")
        print(f"Rendered migration packet at {memory_dir / PACKET_FILE}")
    return 0


def command_plan(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        body = Path(args.input).read_text(encoding="utf-8") if args.input else args.body
        result = capture_plan_artifact(
            memory_dir,
            state,
            plan_id=args.id,
            title=args.title,
            body=body,
            evidence=args.evidence,
            tags=args.tag,
            source=args.source,
            scope=args.scope,
            confidence=args.confidence,
            salience=args.salience,
            next_actions=args.next_action,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    save_result = save_state_and_handoff_artifacts(memory_dir, state)
    if save_result != 0:
        return save_result
    print(f"Captured plan artifact {result['record']['id']} at {result['path']}")
    print(f"Recorded plan memory in project artifacts")
    print(f"Rendered memory briefing at {memory_dir / BRIEFING_FILE}")
    print(f"Rendered migration packet at {memory_dir / PACKET_FILE}")
    return 0


def command_meta(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    changed = update_meta(
        state,
        project_name=args.project_name,
        objective=args.objective,
        summary=args.summary,
        next_actions=args.next_action,
        risks=args.risk,
        handoff_notes=args.handoff_note,
    )
    if not changed:
        print("No metadata changes requested")
        return 0
    result = save_valid_state(memory_dir, state, render=args.render)
    if result == 0:
        print(f"Updated memory metadata at {memory_dir / STATE_FILE}")
    return result


def command_add(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        record = add_record(
            state,
            collection=args.collection,
            record_id=args.id,
            text=args.text,
            record_type=args.type,
            status=args.status,
            confidence=args.confidence,
            salience=args.salience,
            evidence=args.evidence,
            tags=args.tag,
            source=args.source,
            scope=args.scope,
            expires_at=args.expires_at,
            supersedes=args.supersedes,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    result = save_valid_state(memory_dir, state, render=args.render)
    if result == 0:
        print(f"Added {record['id']} to {args.collection}")
    return result


def command_propose(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        record = propose_memory_record(
            state,
            collection=args.collection,
            record_id=args.id,
            text=args.text,
            record_type=args.type,
            confidence=args.confidence,
            salience=args.salience,
            evidence=args.evidence,
            tags=args.tag,
            source=args.source,
            scope=args.scope,
            expires_at=args.expires_at,
            supersedes=args.supersedes,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    result = save_valid_state(memory_dir, state, render=args.render)
    if result == 0:
        print(f"Proposed candidate memory {record['id']} in {args.collection}")
        print("Candidate memory is excluded from briefing until promoted")
    return result


def command_promote(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        path, record = promote_memory_record(
            state,
            record_id=args.id,
            status=args.status,
            reviewed=not args.no_reviewed,
            trusted=args.trusted,
            old_status=args.old_status,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    result = save_state_and_handoff_artifacts(memory_dir, state)
    if result != 0:
        return result
    print(f"Promoted memory record {record['id']} at {path} to {record['status']}")
    print(f"Rendered memory briefing at {memory_dir / BRIEFING_FILE}")
    print(f"Rendered migration packet at {memory_dir / PACKET_FILE}")
    return 0


def command_supersede(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        record = supersede_record(
            state,
            collection=args.collection,
            record_id=args.id,
            text=args.text,
            replaces=args.replaces,
            record_type=args.type,
            status=args.status,
            confidence=args.confidence,
            salience=args.salience,
            evidence=args.evidence,
            tags=args.tag,
            source=args.source,
            scope=args.scope,
            expires_at=args.expires_at,
            old_status=args.old_status,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    result = save_state_and_handoff_artifacts(memory_dir, state)
    if result != 0:
        return result
    replaced = ", ".join(args.replaces)
    print(f"Added replacement memory {record['id']} to {args.collection}")
    print(f"Marked replaced memory as {args.old_status}: {replaced}")
    print(f"Rendered memory briefing at {memory_dir / BRIEFING_FILE}")
    print(f"Rendered migration packet at {memory_dir / PACKET_FILE}")
    return 0


def command_set_active(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    set_active_thread(
        state,
        record_id=args.id,
        text=args.text,
        confidence=args.confidence,
        salience=args.salience,
        evidence=args.evidence,
        tags=args.tag,
        source=args.source,
        scope=args.scope,
        expires_at=args.expires_at,
        supersedes=args.supersedes,
        park_current=args.park_current,
    )
    result = save_valid_state(memory_dir, state, render=args.render)
    if result == 0:
        print(f"Set active thread: {args.id}")
    return result


def command_interrupt(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    interrupt_thread(
        state,
        episode_id=args.episode_id,
        episode_text=args.episode_text,
        thread_id=args.thread_id,
        thread_text=args.thread_text,
        confidence=args.confidence,
        salience=args.salience,
        evidence=args.evidence,
        tags=args.tag,
        source=args.source,
        scope=args.scope,
        expires_at=args.expires_at,
        supersedes=args.supersedes,
    )
    result = save_valid_state(memory_dir, state, render=args.render)
    if result == 0:
        print(f"Captured interruption episode {args.episode_id} and set active thread {args.thread_id}")
    return result


def command_resume(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        resumed = resume_thread(state, current_destination=args.current_destination)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    result = save_valid_state(memory_dir, state, render=args.render)
    if result == 0:
        print(f"Resumed active thread: {resumed.get('id', 'unknown')}")
    return result


def command_review(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    add_tags = list(args.tag or [])
    remove_tags = list(args.remove_tag or [])
    if args.reviewed:
        add_tags.append("reviewed")
    if args.trusted:
        remove_tags.append("untrusted")
    try:
        path, record = update_record(
            state,
            record_id=args.id,
            text=args.text,
            record_type=args.type,
            status=args.status,
            confidence=args.confidence,
            salience=args.salience,
            evidence=args.evidence,
            source=args.source,
            scope=args.scope,
            expires_at=args.expires_at,
            clear_expires_at=args.clear_expires_at,
            add_tags=add_tags,
            remove_tags=remove_tags,
            add_supersedes=args.supersedes,
            remove_supersedes=args.remove_supersedes,
            clear_supersedes=args.clear_supersedes,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    result = save_valid_state(memory_dir, state, render=args.render)
    if result == 0:
        print(f"Reviewed memory record {record['id']} at {path}")
    return result


def command_redact(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        path, record = redact_record(
            state,
            record_id=args.id,
            replacement=args.replacement,
            evidence=args.evidence,
            status=args.status,
            confidence=args.confidence,
            salience=args.salience,
            add_tags=args.tag,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    result = save_state_and_handoff_artifacts(memory_dir, state)
    if result != 0:
        return result
    print(f"Redacted memory record {record['id']} at {path}")
    print(f"Rendered memory briefing at {memory_dir / BRIEFING_FILE}")
    print(f"Rendered migration packet at {memory_dir / PACKET_FILE}")
    return 0


def command_forget(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    try:
        path, record = delete_record(state, args.id)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    result = save_state_and_handoff_artifacts(memory_dir, state)
    if result != 0:
        return result
    print(f"Forgot memory record {record['id']} from {path}")
    print(f"Rendered memory briefing at {memory_dir / BRIEFING_FILE}")
    print(f"Rendered migration packet at {memory_dir / PACKET_FILE}")
    return 0


def print_topic_decision(decision: dict[str, str], *, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(decision, ensure_ascii=False, indent=2))
        return
    print(f"ACTION: {decision['action']}")
    print(f"CONFIDENCE: {decision['confidence']}")
    print(f"REASON: {decision['reason']}")
    print(f"ACTIVE: {decision['active']}")
    print(f"RESUME_CANDIDATE: {decision['resume_candidate']}")


def command_cue(args: argparse.Namespace) -> int:
    memory_dir = Path(args.path)
    state = load_state(memory_dir)
    errors = validate_state(state)
    if errors:
        print_errors(errors)
        return 1
    decision = detect_topic_cue(state, args.text)
    if not args.auto_resume:
        print_topic_decision(decision, as_json=args.json)
        return 0
    if decision["action"] != "resume":
        decision = dict(decision)
        decision["auto_resume"] = "skipped"
        print_topic_decision(decision, as_json=args.json)
        return 0
    try:
        resumed = resume_thread(state, current_destination=args.current_destination)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    result = save_valid_state(memory_dir, state, render=args.render)
    if result != 0:
        return result
    decision = dict(decision)
    decision["auto_resume"] = "applied"
    decision["resumed"] = resumed.get("id", "unknown")
    print_topic_decision(decision, as_json=args.json)
    return 0


def add_record_args(parser: argparse.ArgumentParser, *, source_default: str = "user") -> None:
    parser.add_argument("--id", required=True, help="record id")
    parser.add_argument("--text", required=True, help="record text")
    parser.add_argument("--confidence", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--salience", type=int, choices=range(1, 6), default=3)
    parser.add_argument("--evidence", default="", help="source or evidence for the memory")
    parser.add_argument("--source", choices=sorted(KNOWN_SOURCES), default=source_default, help="origin of the memory")
    parser.add_argument("--scope", choices=sorted(KNOWN_SCOPES), default="project", help="visibility or ownership scope")
    parser.add_argument("--expires-at", help="ISO timestamp after which active memory should be reviewed")
    parser.add_argument("--supersedes", action="append", default=[], help="record id this memory replaces")
    parser.add_argument("--tag", action="append", default=[], help="repeatable tag")
    parser.add_argument("--render", action="store_true", help="render migration-packet.md after updating state")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize, update, validate, and render agent memory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create a memory state directory")
    init_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    init_parser.add_argument("--force", action="store_true", help="overwrite existing state.json")
    init_parser.set_defaults(func=command_init)

    validate_parser = subparsers.add_parser("validate", help="validate state.json")
    validate_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    validate_parser.set_defaults(func=command_validate)

    render_parser = subparsers.add_parser("render", help="render migration-packet.md")
    render_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    render_parser.add_argument("--output", help="output markdown file")
    render_parser.set_defaults(func=command_render)

    brief_parser = subparsers.add_parser("brief", help="print or write a short startup memory briefing")
    brief_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    brief_parser.add_argument("--max-records", type=int, default=5, help="maximum records per briefing section")
    brief_parser.add_argument("--include-stale", action="store_true", help="include stale or superseded records")
    brief_parser.add_argument("--include-untrusted", action="store_true", help="include records tagged untrusted")
    brief_parser.add_argument("--output", help="output markdown file")
    brief_parser.add_argument("--write", action="store_true", help=f"write {BRIEFING_FILE} in the memory directory")
    brief_parser.set_defaults(func=command_brief)

    handoff_parser = subparsers.add_parser("handoff", help="write briefing and migration packet, then audit readiness")
    handoff_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    handoff_parser.add_argument("--max-records", type=int, default=5, help="maximum records per briefing section")
    handoff_parser.add_argument("--include-stale", action="store_true", help="include stale or superseded records")
    handoff_parser.add_argument("--include-untrusted", action="store_true", help="include records tagged untrusted")
    handoff_parser.add_argument("--strict", action="store_true", help="exit non-zero on warnings")
    handoff_parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    handoff_parser.set_defaults(func=command_handoff)

    schema_parser = subparsers.add_parser("schema", help="print the JSON Schema for state.json")
    schema_parser.add_argument("--output", help="write schema to a file")
    schema_parser.set_defaults(func=command_schema)

    doctor_parser = subparsers.add_parser("doctor", help="audit memory quality for handoff readiness")
    doctor_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    doctor_parser.add_argument("--strict", action="store_true", help="exit non-zero on warnings")
    doctor_parser.set_defaults(func=command_doctor)

    mode_parser = subparsers.add_parser("integration-mode", help="recommend bootstrap, augment, or audit memory integration")
    mode_parser.add_argument("--agent-memory-exists", action="store_true", help="an Agent Memory state already exists")
    mode_parser.add_argument("--existing-memory-exists", action="store_true", help="another memory system already exists")
    mode_parser.add_argument("--trust-unclear", action="store_true", help="existing memory trust, scope, or freshness is unclear")
    mode_parser.add_argument("--audit-only", action="store_true", help="do not recommend durable writes")
    mode_parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    mode_parser.set_defaults(func=command_integration_mode)

    health_parser = subparsers.add_parser("session-health", help="assess session size and handoff pressure")
    health_parser.add_argument("--messages", type=int, help="number of messages in the current session")
    health_parser.add_argument("--session-bytes", type=int, help="session transcript size in bytes")
    health_parser.add_argument("--context-bytes", type=int, help="startup or injected context size in bytes")
    health_parser.add_argument("--handoff-age-hours", type=float, help="hours since the last handoff artifacts were refreshed")
    health_parser.add_argument("--warning-messages", type=int, default=150)
    health_parser.add_argument("--critical-messages", type=int, default=300)
    health_parser.add_argument("--warning-session-bytes", type=int, default=750_000)
    health_parser.add_argument("--critical-session-bytes", type=int, default=1_500_000)
    health_parser.add_argument("--warning-context-bytes", type=int, default=50_000)
    health_parser.add_argument("--critical-context-bytes", type=int, default=150_000)
    health_parser.add_argument("--warning-handoff-age-hours", type=float, default=24.0)
    health_parser.add_argument("--strict", action="store_true", help="exit non-zero when handoff is recommended")
    health_parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    health_parser.set_defaults(func=command_session_health)

    export_parser = subparsers.add_parser("export", help="write a portable memory bundle for migration")
    export_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    export_parser.add_argument("--output", help=f"output JSON bundle path, default: {BUNDLE_FILE}")
    export_parser.add_argument("--max-records", type=int, default=5, help="maximum records per bundled briefing section")
    export_parser.add_argument("--include-stale", action="store_true", help="include stale or superseded records in bundled briefing")
    export_parser.add_argument("--include-untrusted", action="store_true", help="include records tagged untrusted in bundled briefing")
    export_parser.add_argument("--strict", action="store_true", help="fail when doctor reports warnings")
    export_parser.set_defaults(func=command_export)

    import_parser = subparsers.add_parser("import", help="restore a portable memory bundle into a memory directory")
    import_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    import_parser.add_argument("--input", required=True, help="input JSON bundle path")
    import_parser.add_argument("--force", action="store_true", help="overwrite existing state.json")
    import_parser.set_defaults(func=command_import)

    select_parser = subparsers.add_parser("select", help="select targeted high-signal memory records")
    select_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    select_parser.add_argument("--query", help="keyword or phrase to match across record fields")
    select_parser.add_argument("--collection", action="append", default=[], help="filter by collection or path fragment")
    select_parser.add_argument("--type", dest="record_type", action="append", default=[], help="filter by record type")
    select_parser.add_argument("--tag", action="append", default=[], help="require repeatable tag")
    select_parser.add_argument("--status", choices=sorted(KNOWN_STATUSES), action="append", default=[], help="filter by status")
    select_parser.add_argument("--source", choices=sorted(KNOWN_SOURCES), action="append", default=[], help="filter by source")
    select_parser.add_argument("--scope", choices=sorted(KNOWN_SCOPES), action="append", default=[], help="filter by scope")
    select_parser.add_argument("--min-salience", type=int, choices=range(1, 6), default=1)
    select_parser.add_argument("--limit", type=int, default=10)
    select_parser.add_argument("--include-stale", action="store_true", help="include stale or superseded records")
    select_parser.add_argument("--include-candidates", action="store_true", help="include unpromoted candidate records")
    select_parser.add_argument("--include-untrusted", action="store_true", help="include records tagged untrusted")
    select_parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    select_parser.set_defaults(func=command_select)

    compact_parser = subparsers.add_parser("compact", help="plan or apply conservative memory compaction")
    compact_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    compact_parser.add_argument("--min-salience", type=int, choices=range(1, 6), default=3)
    compact_parser.add_argument(
        "--include-active-thread",
        action="store_true",
        help="allow the current active thread to be considered for auto compaction",
    )
    compact_parser.add_argument(
        "--max-closed-recently",
        type=int,
        default=10,
        help="review older closed threads when the collection exceeds this count",
    )
    compact_parser.add_argument(
        "--max-episodes",
        type=int,
        default=20,
        help="review older episodes when the collection exceeds this count",
    )
    compact_parser.add_argument(
        "--max-artifacts",
        type=int,
        default=20,
        help="review older artifacts when the collection exceeds this count",
    )
    compact_parser.add_argument("--apply", action="store_true", help="mark auto-applicable suggestions stale")
    compact_parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    compact_parser.set_defaults(func=command_compact)

    plan_parser = subparsers.add_parser("plan", help=f"capture an opening or phase plan in {PLAN_DIR}/")
    plan_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    plan_parser.add_argument("--id", required=True, help="plan artifact record id")
    plan_parser.add_argument("--title", required=True, help="plan title")
    plan_body = plan_parser.add_mutually_exclusive_group(required=True)
    plan_body.add_argument("--input", help="markdown plan file to capture")
    plan_body.add_argument("--body", help="inline markdown plan body to capture")
    plan_parser.add_argument("--evidence", default="", help="source or evidence for the plan")
    plan_parser.add_argument("--source", choices=sorted(KNOWN_SOURCES), default="user", help="origin of the plan")
    plan_parser.add_argument("--scope", choices=sorted(KNOWN_SCOPES), default="project", help="visibility or ownership scope")
    plan_parser.add_argument("--confidence", choices=["low", "medium", "high"], default="high")
    plan_parser.add_argument("--salience", type=int, choices=range(1, 6), default=5)
    plan_parser.add_argument("--tag", action="append", default=[], help="repeatable tag")
    plan_parser.add_argument("--next-action", action="append", default=[], help="next action tied to this plan")
    plan_parser.set_defaults(func=command_plan)

    meta_parser = subparsers.add_parser("meta", help="update project and migration metadata")
    meta_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    meta_parser.add_argument("--project-name")
    meta_parser.add_argument("--objective")
    meta_parser.add_argument("--summary")
    meta_parser.add_argument("--next-action", action="append", default=[])
    meta_parser.add_argument("--risk", action="append", default=[])
    meta_parser.add_argument("--handoff-note", action="append", default=[])
    meta_parser.add_argument("--render", action="store_true", help="render migration-packet.md after updating state")
    meta_parser.set_defaults(func=command_meta)

    add_parser = subparsers.add_parser("add", help="add a memory record")
    add_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    add_parser.add_argument("--collection", required=True, choices=sorted(COLLECTIONS))
    add_record_args(add_parser)
    add_parser.add_argument("--type", help="override record type")
    add_parser.add_argument("--status", default="active")
    add_parser.set_defaults(func=command_add)

    propose_parser = subparsers.add_parser("propose", help="propose a candidate memory for later review")
    propose_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    propose_parser.add_argument("--collection", required=True, choices=sorted(COLLECTIONS))
    add_record_args(propose_parser, source_default="agent")
    propose_parser.add_argument("--type", help="override record type")
    propose_parser.set_defaults(func=command_propose)

    promote_parser = subparsers.add_parser("promote", help="promote a candidate memory into startup context")
    promote_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    promote_parser.add_argument("--id", required=True, help="candidate record id to promote")
    promote_parser.add_argument("--status", choices=["active", "tentative"], default="active")
    promote_parser.add_argument("--trusted", action="store_true", help="remove untrusted tag while promoting")
    promote_parser.add_argument("--no-reviewed", action="store_true", help="do not add reviewed tag while promoting")
    promote_parser.add_argument("--old-status", choices=["superseded", "stale"], default="superseded")
    promote_parser.set_defaults(func=command_promote)

    supersede_parser = subparsers.add_parser(
        "supersede",
        help="add a replacement memory and mark old records superseded",
    )
    supersede_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    supersede_parser.add_argument("--collection", required=True, choices=sorted(COLLECTIONS))
    supersede_parser.add_argument("--id", required=True, help="replacement record id")
    supersede_parser.add_argument("--text", required=True, help="replacement record text")
    supersede_parser.add_argument("--type", help="override replacement record type")
    supersede_parser.add_argument("--status", choices=sorted(KNOWN_STATUSES), default="active")
    supersede_parser.add_argument("--confidence", choices=["low", "medium", "high"], default="medium")
    supersede_parser.add_argument("--salience", type=int, choices=range(1, 6), default=3)
    supersede_parser.add_argument("--evidence", default="", help="source or evidence for the replacement memory")
    supersede_parser.add_argument("--source", choices=sorted(KNOWN_SOURCES), default="user", help="origin of the memory")
    supersede_parser.add_argument("--scope", choices=sorted(KNOWN_SCOPES), default="project", help="visibility or ownership scope")
    supersede_parser.add_argument("--expires-at", help="ISO timestamp after which active memory should be reviewed")
    supersede_parser.add_argument("--tag", action="append", default=[], help="repeatable tag")
    supersede_parser.add_argument(
        "--replaces",
        action="append",
        required=True,
        help="old record id replaced by this memory; repeat for multiple records",
    )
    supersede_parser.add_argument(
        "--old-status",
        choices=["superseded", "stale"],
        default="superseded",
        help="status to apply to replaced records",
    )
    supersede_parser.set_defaults(func=command_supersede)

    active_parser = subparsers.add_parser("set-active", help="set the active topic thread")
    active_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    add_record_args(active_parser)
    active_parser.add_argument("--park-current", action="store_true", help="move current active thread to parked")
    active_parser.set_defaults(func=command_set_active)

    interrupt_parser = subparsers.add_parser("interrupt", help="park the current topic and capture a side episode")
    interrupt_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    interrupt_parser.add_argument("--episode-id", required=True)
    interrupt_parser.add_argument("--episode-text", required=True)
    interrupt_parser.add_argument("--thread-id", required=True)
    interrupt_parser.add_argument("--thread-text", required=True)
    interrupt_parser.add_argument("--confidence", choices=["low", "medium", "high"], default="medium")
    interrupt_parser.add_argument("--salience", type=int, choices=range(1, 6), default=4)
    interrupt_parser.add_argument("--evidence", default="", help="source or evidence for the interruption")
    interrupt_parser.add_argument("--source", choices=sorted(KNOWN_SOURCES), default="user", help="origin of the memory")
    interrupt_parser.add_argument("--scope", choices=sorted(KNOWN_SCOPES), default="project", help="visibility or ownership scope")
    interrupt_parser.add_argument("--expires-at", help="ISO timestamp after which active memory should be reviewed")
    interrupt_parser.add_argument("--supersedes", action="append", default=[], help="record id this memory replaces")
    interrupt_parser.add_argument("--tag", action="append", default=[], help="repeatable tag")
    interrupt_parser.add_argument("--render", action="store_true", help="render migration-packet.md after updating state")
    interrupt_parser.set_defaults(func=command_interrupt)

    resume_parser = subparsers.add_parser("resume", help="resume the most recently parked topic")
    resume_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    resume_parser.add_argument(
        "--current-destination",
        choices=["closed", "open", "parked", "drop"],
        default="closed",
        help="where to move the currently active interruption thread",
    )
    resume_parser.add_argument("--render", action="store_true", help="render migration-packet.md after updating state")
    resume_parser.set_defaults(func=command_resume)

    cue_parser = subparsers.add_parser("cue", help="detect whether a message should resume a parked topic")
    cue_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    cue_parser.add_argument("--text", required=True, help="latest user message or closure cue text")
    cue_parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    cue_parser.add_argument("--auto-resume", action="store_true", help="resume the parked topic when action is resume")
    cue_parser.add_argument(
        "--current-destination",
        choices=["closed", "open", "parked", "drop"],
        default="closed",
        help="where to move the currently active interruption thread when auto-resuming",
    )
    cue_parser.add_argument("--render", action="store_true", help="render migration-packet.md after auto-resume")
    cue_parser.set_defaults(func=command_cue)

    review_parser = subparsers.add_parser("review", help="review or update an existing memory record")
    review_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    review_parser.add_argument("--id", required=True, help="record id to review")
    review_parser.add_argument("--text", help="replace record text")
    review_parser.add_argument("--type", help="replace record type")
    review_parser.add_argument("--status", choices=sorted(KNOWN_STATUSES), help="replace record status")
    review_parser.add_argument("--confidence", choices=["low", "medium", "high"], help="replace confidence")
    review_parser.add_argument("--salience", type=int, choices=range(1, 6), help="replace salience")
    review_parser.add_argument("--evidence", help="replace evidence")
    review_parser.add_argument("--source", choices=sorted(KNOWN_SOURCES), help="replace source")
    review_parser.add_argument("--scope", choices=sorted(KNOWN_SCOPES), help="replace scope")
    review_parser.add_argument("--expires-at", help="set ISO expiry timestamp")
    review_parser.add_argument("--clear-expires-at", action="store_true", help="remove expiry timestamp")
    review_parser.add_argument("--supersedes", action="append", default=[], help="add superseded record id")
    review_parser.add_argument("--remove-supersedes", action="append", default=[], help="remove superseded record id")
    review_parser.add_argument("--clear-supersedes", action="store_true", help="remove all superseded record ids")
    review_parser.add_argument("--tag", action="append", default=[], help="add repeatable tag")
    review_parser.add_argument("--remove-tag", action="append", default=[], help="remove repeatable tag")
    review_parser.add_argument("--reviewed", action="store_true", help="add reviewed tag")
    review_parser.add_argument("--trusted", action="store_true", help="remove untrusted tag")
    review_parser.add_argument("--render", action="store_true", help="render migration-packet.md after updating state")
    review_parser.set_defaults(func=command_review)

    redact_parser = subparsers.add_parser(
        "redact",
        help="replace sensitive record text and refresh handoff artifacts",
    )
    redact_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    redact_parser.add_argument("--id", required=True, help="record id to redact")
    redact_parser.add_argument(
        "--replacement",
        default="[redacted sensitive memory]",
        help="safe replacement text for the memory record",
    )
    redact_parser.add_argument("--evidence", default="Sensitive memory redacted.", help="safe replacement evidence")
    redact_parser.add_argument("--status", choices=sorted(KNOWN_STATUSES), default="stale")
    redact_parser.add_argument("--confidence", choices=["low", "medium", "high"], default="low")
    redact_parser.add_argument("--salience", type=int, choices=range(1, 6), default=1)
    redact_parser.add_argument("--tag", action="append", default=[], help="add repeatable tag after redaction")
    redact_parser.set_defaults(func=command_redact)

    forget_parser = subparsers.add_parser(
        "forget",
        help="remove a memory record and refresh handoff artifacts",
    )
    forget_parser.add_argument("--path", default=".agent-memory", help="memory directory path")
    forget_parser.add_argument("--id", required=True, help="record id to forget")
    forget_parser.set_defaults(func=command_forget)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
