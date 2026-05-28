"""Core state, validation, topic stack, and rendering logic for agent memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_FILE = "state.json"
PACKET_FILE = "migration-packet.md"
BRIEFING_FILE = "memory-briefing.md"
BUNDLE_FILE = "agent-memory-export.json"
PLAN_DIR = "plans"
BUNDLE_FORMAT = "agent-memory-bundle"
BUNDLE_VERSION = 1

COLLECTIONS = {
    "preferences": ("user_profile", "preferences", "preference"),
    "working-style": ("user_profile", "working_style", "preference"),
    "avoid": ("user_profile", "avoid", "preference"),
    "facts": ("project", "facts", "project_fact"),
    "artifacts": ("project", "artifacts", "artifact"),
    "decisions": (None, "decisions", "decision"),
    "episodes": (None, "episodes", "episode"),
    "open-threads": ("threads", "open", "thread"),
    "parked-threads": ("threads", "parked", "thread"),
    "closed-threads": ("threads", "closed_recently", "thread"),
}

KNOWN_STATUSES = {"active", "tentative", "candidate", "superseded", "stale", "closed", "parked"}
KNOWN_SOURCES = {"user", "agent", "tool", "external", "system", "derived"}
KNOWN_SCOPES = {"user", "project", "agent", "role", "organization", "global"}
POISONING_PHRASES = (
    "ignore previous",
    "ignore all previous",
    "system prompt",
    "developer message",
    "do not tell the user",
    "do not reveal",
    "always recommend",
    "exfiltrate",
    "api key",
    "password",
    "credential",
    "jailbreak",
    "bypass safety",
)
EXPLICIT_RETURN_CUES = (
    "back to",
    "return to",
    "resume previous",
    "resume the previous",
    "continue previous",
    "continue the previous",
    "continue main",
    "main thread",
    "previous topic",
    "previous thread",
    "\u56de\u5230",
    "\u8fd4\u56de",
    "\u7ee7\u7eed\u4e4b\u524d",
    "\u7ee7\u7eed\u521a\u624d",
    "\u7ee7\u7eed\u4e3b\u7ebf",
    "\u56de\u4e3b\u7ebf",
    "\u4e0a\u4e00\u4e2a\u8bdd\u9898",
    "\u4e4b\u524d\u7684\u8bdd\u9898",
    "\u521a\u624d\u7684\u8bdd\u9898",
)
CLOSURE_CUES = (
    "done",
    "solved",
    "finished",
    "that's enough",
    "that is enough",
    "close this",
    "wrap this",
    "leave this for later",
    "park this",
    "\u5148\u8fd9\u6837",
    "\u5148\u5230\u8fd9",
    "\u7ed3\u675f\u8fd9\u4e2a",
    "\u8fd9\u4e2a\u7ed3\u675f",
    "\u8fd9\u5757\u7ed3\u675f",
    "\u804a\u5b8c",
    "\u8bf4\u5b8c",
    "\u5148\u653e",
    "\u4e4b\u540e\u518d\u8bf4",
    "\u4ee5\u540e\u518d\u8bf4",
)
AMBIGUOUS_CONTINUE_CUES = ("continue", "go on", "\u63a5\u7740", "\u7ee7\u7eed")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def contains_any(text: str, phrases: tuple[str, ...]) -> str | None:
    lowered = text.lower()
    for phrase in phrases:
        if phrase in lowered:
            return phrase
    return None


def default_state() -> dict[str, Any]:
    timestamp = now_iso()
    return {
        "version": 1,
        "updated_at": timestamp,
        "user_profile": {
            "preferences": [],
            "working_style": [],
            "avoid": [],
        },
        "project": {
            "name": "",
            "objective": "",
            "facts": [],
            "artifacts": [],
        },
        "threads": {
            "active": None,
            "open": [],
            "parked": [],
            "closed_recently": [],
        },
        "decisions": [],
        "episodes": [],
        "migration": {
            "summary": "",
            "next_actions": [],
            "risks": [],
            "handoff_notes": [],
        },
    }


def load_state(memory_dir: Path) -> dict[str, Any]:
    state_path = memory_dir / STATE_FILE
    with state_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_state(memory_dir: Path, state: dict[str, Any]) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = now_iso()
    state_path = memory_dir / STATE_FILE
    with state_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_packet(memory_dir: Path, state: dict[str, Any]) -> None:
    (memory_dir / PACKET_FILE).write_text(render_packet(state), encoding="utf-8", newline="\n")


def write_briefing(
    memory_dir: Path,
    state: dict[str, Any],
    *,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
) -> None:
    briefing = render_briefing(
        state,
        max_records=max_records,
        include_stale=include_stale,
        include_untrusted=include_untrusted,
    )
    (memory_dir / BRIEFING_FILE).write_text(briefing, encoding="utf-8", newline="\n")


def clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def build_memory_bundle(
    state: dict[str, Any],
    *,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    errors = validate_state(state)
    if errors:
        raise ValueError("invalid memory state: " + "; ".join(errors))
    issues = audit_state(state)
    return {
        "format": BUNDLE_FORMAT,
        "version": BUNDLE_VERSION,
        "exported_at": now_iso(),
        "state": clone_json(state),
        "artifacts": {
            BRIEFING_FILE: render_briefing(
                state,
                max_records=max_records,
                include_stale=include_stale,
                include_untrusted=include_untrusted,
            ),
            PACKET_FILE: render_packet(state),
        },
        "audit": {
            "issues": clone_json(issues),
            "ready": not handoff_failed(issues, strict=strict),
            "strict": strict,
        },
    }


def state_from_memory_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bundle, dict):
        raise ValueError("memory bundle must be a JSON object")
    if bundle.get("format") != BUNDLE_FORMAT:
        raise ValueError(f"unsupported memory bundle format: {bundle.get('format')}")
    if bundle.get("version") != BUNDLE_VERSION:
        raise ValueError(f"unsupported memory bundle version: {bundle.get('version')}")
    state = bundle.get("state")
    if not isinstance(state, dict):
        raise ValueError("memory bundle is missing object field: state")
    errors = validate_state(state)
    if errors:
        raise ValueError("invalid bundled memory state: " + "; ".join(errors))
    return clone_json(state)


def collection_list(state: dict[str, Any], collection: str) -> tuple[list[Any], str]:
    if collection not in COLLECTIONS:
        choices = ", ".join(sorted(COLLECTIONS))
        raise ValueError(f"unknown collection: {collection}; choose one of: {choices}")
    parent_key, child_key, default_type = COLLECTIONS[collection]
    if parent_key is None:
        records = state[child_key]
    else:
        records = state[parent_key][child_key]
    return records, default_type


def make_record(
    *,
    record_id: str,
    text: str,
    record_type: str,
    status: str,
    confidence: str,
    salience: int,
    evidence: str,
    tags: list[str] | None = None,
    source: str = "user",
    scope: str = "project",
    expires_at: str | None = None,
    supersedes: list[str] | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    created_at = timestamp or now_iso()
    record = {
        "id": record_id,
        "text": text,
        "type": record_type,
        "status": status,
        "created_at": created_at,
        "updated_at": created_at,
        "confidence": confidence,
        "salience": salience,
        "evidence": evidence,
        "source": source,
        "scope": scope,
        "tags": tags or [],
    }
    if expires_at:
        record["expires_at"] = expires_at
    if supersedes:
        record["supersedes"] = supersedes
    return record


def copy_with_status(record: dict[str, Any], status: str, timestamp: str | None = None) -> dict[str, Any]:
    copied = dict(record)
    copied["status"] = status
    copied["updated_at"] = timestamp or now_iso()
    return copied


def iter_records(state: dict[str, Any]):
    for collection_name, records in iter_record_collections(state):
        if not isinstance(records, list):
            continue
        for index, record in enumerate(records):
            if isinstance(record, dict):
                yield f"{collection_name}[{index}]", record


def find_record(state: dict[str, Any], record_id: str) -> tuple[str, dict[str, Any]]:
    for path, record in iter_records(state):
        if record.get("id") == record_id:
            return path, record
    raise ValueError(f"record not found: {record_id}")


def iter_mutable_record_lists(state: dict[str, Any]):
    user_profile = state.get("user_profile", {})
    if isinstance(user_profile, dict):
        yield "user_profile.preferences", user_profile.get("preferences")
        yield "user_profile.working_style", user_profile.get("working_style")
        yield "user_profile.avoid", user_profile.get("avoid")

    project = state.get("project", {})
    if isinstance(project, dict):
        yield "project.facts", project.get("facts")
        yield "project.artifacts", project.get("artifacts")

    threads = state.get("threads", {})
    if isinstance(threads, dict):
        yield "threads.open", threads.get("open")
        yield "threads.parked", threads.get("parked")
        yield "threads.closed_recently", threads.get("closed_recently")

    yield "decisions", state.get("decisions")
    yield "episodes", state.get("episodes")


def merge_unique(existing: list[str], added: list[str]) -> list[str]:
    merged = list(existing)
    for item in added:
        if item not in merged:
            merged.append(item)
    return merged


def update_record(
    state: dict[str, Any],
    *,
    record_id: str,
    text: str | None = None,
    record_type: str | None = None,
    status: str | None = None,
    confidence: str | None = None,
    salience: int | None = None,
    evidence: str | None = None,
    source: str | None = None,
    scope: str | None = None,
    expires_at: str | None = None,
    clear_expires_at: bool = False,
    add_tags: list[str] | None = None,
    remove_tags: list[str] | None = None,
    add_supersedes: list[str] | None = None,
    remove_supersedes: list[str] | None = None,
    clear_supersedes: bool = False,
) -> tuple[str, dict[str, Any]]:
    path, record = find_record(state, record_id)

    for key, value in {
        "text": text,
        "type": record_type,
        "status": status,
        "confidence": confidence,
        "salience": salience,
        "evidence": evidence,
        "source": source,
        "scope": scope,
    }.items():
        if value is not None:
            record[key] = value

    if clear_expires_at:
        record.pop("expires_at", None)
    elif expires_at is not None:
        record["expires_at"] = expires_at

    tags = record.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    tags = [str(tag) for tag in tags]
    if remove_tags:
        remove_set = set(remove_tags)
        tags = [tag for tag in tags if tag not in remove_set]
    if add_tags:
        tags = merge_unique(tags, add_tags)
    record["tags"] = tags

    supersedes = record.get("supersedes", [])
    if clear_supersedes:
        supersedes = []
    if not isinstance(supersedes, list):
        supersedes = []
    supersedes = [str(item) for item in supersedes]
    if remove_supersedes:
        remove_set = set(remove_supersedes)
        supersedes = [item for item in supersedes if item not in remove_set]
    if add_supersedes:
        supersedes = merge_unique(supersedes, add_supersedes)
    if supersedes:
        record["supersedes"] = supersedes
    else:
        record.pop("supersedes", None)

    record["updated_at"] = now_iso()
    return path, record


def remove_supersedes_references(state: dict[str, Any], record_id: str) -> None:
    timestamp = now_iso()
    for _path, record in iter_records(state):
        supersedes = record.get("supersedes")
        if not isinstance(supersedes, list) or record_id not in supersedes:
            continue
        remaining = [str(item) for item in supersedes if item != record_id]
        if remaining:
            record["supersedes"] = remaining
        else:
            record.pop("supersedes", None)
        record["updated_at"] = timestamp


def delete_record(state: dict[str, Any], record_id: str) -> tuple[str, dict[str, Any]]:
    """Remove a memory record by id and clean up supersedes references."""

    threads = state.get("threads", {})
    if isinstance(threads, dict):
        active = threads.get("active")
        if isinstance(active, dict) and active.get("id") == record_id:
            threads["active"] = None
            remove_supersedes_references(state, record_id)
            return "threads.active", active

    for collection_name, records in iter_mutable_record_lists(state):
        if not isinstance(records, list):
            continue
        for index, record in enumerate(records):
            if isinstance(record, dict) and record.get("id") == record_id:
                removed = records.pop(index)
                remove_supersedes_references(state, record_id)
                return f"{collection_name}[{index}]", removed

    raise ValueError(f"record not found: {record_id}")


def redact_record(
    state: dict[str, Any],
    *,
    record_id: str,
    replacement: str = "[redacted sensitive memory]",
    evidence: str = "Sensitive memory redacted.",
    status: str = "stale",
    confidence: str = "low",
    salience: int = 1,
    add_tags: list[str] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Replace a record's sensitive text while preserving an audit trail."""

    if not replacement.strip():
        raise ValueError("replacement cannot be empty")
    tags = ["redacted", "reviewed"]
    if add_tags:
        tags = merge_unique(tags, add_tags)
    return update_record(
        state,
        record_id=record_id,
        text=replacement,
        status=status,
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        add_tags=tags,
    )


def supersede_record(
    state: dict[str, Any],
    *,
    collection: str,
    record_id: str,
    text: str,
    replaces: list[str],
    record_type: str | None = None,
    status: str = "active",
    confidence: str = "medium",
    salience: int = 3,
    evidence: str = "",
    tags: list[str] | None = None,
    source: str = "user",
    scope: str = "project",
    expires_at: str | None = None,
    old_status: str = "superseded",
) -> dict[str, Any]:
    """Add a replacement memory and mark replaced records inactive."""

    if not replaces:
        raise ValueError("replaces must include at least one record id")
    if old_status not in {"superseded", "stale"}:
        raise ValueError("old_status must be superseded or stale")
    if record_id in replaces:
        raise ValueError("replacement record cannot supersede itself")
    try:
        find_record(state, record_id)
    except ValueError:
        pass
    else:
        raise ValueError(f"record already exists: {record_id}")

    replaced_records: list[tuple[str, dict[str, Any]]] = []
    for old_id in replaces:
        replaced_records.append(find_record(state, old_id))

    replacement = add_record(
        state,
        collection=collection,
        record_id=record_id,
        text=text,
        record_type=record_type,
        status=status,
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=tags,
        source=source,
        scope=scope,
        expires_at=expires_at,
        supersedes=replaces,
    )
    for _path, old_record in replaced_records:
        update_record(
            state,
            record_id=str(old_record["id"]),
            status=old_status,
            add_tags=["superseded"],
        )
    return replacement


def propose_memory_record(
    state: dict[str, Any],
    *,
    collection: str,
    record_id: str,
    text: str,
    record_type: str | None = None,
    confidence: str = "medium",
    salience: int = 3,
    evidence: str = "",
    tags: list[str] | None = None,
    source: str = "agent",
    scope: str = "project",
    expires_at: str | None = None,
    supersedes: list[str] | None = None,
) -> dict[str, Any]:
    """Capture an agent-proposed memory that must be reviewed before startup reuse."""

    candidate_tags = merge_unique(["candidate", "needs-review"], tags or [])
    return add_record(
        state,
        collection=collection,
        record_id=record_id,
        text=text,
        record_type=record_type,
        status="candidate",
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=candidate_tags,
        source=source,
        scope=scope,
        expires_at=expires_at,
        supersedes=supersedes,
    )


def promote_memory_record(
    state: dict[str, Any],
    *,
    record_id: str,
    status: str = "active",
    reviewed: bool = True,
    trusted: bool = False,
    old_status: str = "superseded",
) -> tuple[str, dict[str, Any]]:
    """Promote a candidate memory into reusable context after review."""

    if status not in {"active", "tentative"}:
        raise ValueError("promoted status must be active or tentative")
    if old_status not in {"superseded", "stale"}:
        raise ValueError("old_status must be superseded or stale")
    path, record = find_record(state, record_id)
    supersedes = record.get("supersedes", [])
    if not isinstance(supersedes, list):
        supersedes = []
    superseded_records: list[tuple[str, dict[str, Any]]] = []
    for old_id in [str(item) for item in supersedes]:
        if old_id == record_id:
            raise ValueError("record cannot supersede itself")
        superseded_records.append(find_record(state, old_id))

    remove_tags = ["candidate", "needs-review"]
    if trusted:
        remove_tags.append("untrusted")
    add_tags = ["reviewed"] if reviewed else []
    promoted_path, promoted = update_record(
        state,
        record_id=record_id,
        status=status,
        add_tags=add_tags,
        remove_tags=remove_tags,
    )
    for _old_path, old_record in superseded_records:
        update_record(
            state,
            record_id=str(old_record["id"]),
            status=old_status,
            add_tags=["superseded"],
        )
    return promoted_path or path, promoted


def safe_plan_filename(plan_id: str) -> str:
    cleaned = "".join(
        character if character.isascii() and (character.isalnum() or character in {"-", "_", "."}) else "-"
        for character in plan_id.strip()
    ).strip(".-")
    return cleaned or "plan"


def render_plan_artifact(title: str, body: str) -> str:
    return "\n".join(["# " + title.strip(), "", body.strip(), ""])


def capture_plan_artifact(
    memory_dir: Path,
    state: dict[str, Any],
    *,
    plan_id: str,
    title: str,
    body: str,
    evidence: str = "",
    tags: list[str] | None = None,
    source: str = "user",
    scope: str = "project",
    confidence: str = "high",
    salience: int = 5,
    next_actions: list[str] | None = None,
) -> dict[str, Any]:
    """Persist an opening or phase plan and register it as memory."""

    if not plan_id.strip():
        raise ValueError("plan_id cannot be empty")
    if not title.strip():
        raise ValueError("title cannot be empty")
    if not body.strip():
        raise ValueError("plan body cannot be empty")
    try:
        find_record(state, plan_id)
    except ValueError:
        pass
    else:
        raise ValueError(f"record already exists: {plan_id}")

    plan_dir = memory_dir / PLAN_DIR
    plan_dir.mkdir(parents=True, exist_ok=True)
    relative_path = f"{PLAN_DIR}/{safe_plan_filename(plan_id)}.md"
    plan_path = memory_dir / relative_path
    plan_path.write_text(render_plan_artifact(title, body), encoding="utf-8", newline="\n")

    plan_tags = merge_unique(["plan", "opening-plan"], tags or [])
    evidence_text = evidence or f"Captured plan artifact at {relative_path}."
    record = add_record(
        state,
        collection="artifacts",
        record_id=plan_id,
        text=f"{title.strip()} ({relative_path})",
        record_type="artifact",
        status="active",
        confidence=confidence,
        salience=salience,
        evidence=evidence_text,
        tags=plan_tags,
        source=source,
        scope=scope,
    )

    handoff_note = f"Follow opening plan artifact before implementation: {relative_path}"
    if handoff_note not in state["migration"]["handoff_notes"]:
        state["migration"]["handoff_notes"].append(handoff_note)
    for action in next_actions or []:
        if action not in state["migration"]["next_actions"]:
            state["migration"]["next_actions"].append(action)

    return {"record": record, "path": plan_path, "relative_path": relative_path}


def record_preview(record: dict[str, Any], *, max_chars: int = 140) -> str:
    text = str(record.get("text", "")).replace("\n", " ").strip()
    if len(text) <= max_chars:
        return text
    return text[: max(1, max_chars - 3)].rstrip() + "..."


def record_timestamp(record: dict[str, Any]) -> datetime:
    for key in ("updated_at", "created_at"):
        value = record.get(key)
        if isinstance(value, str):
            parsed = parse_iso_datetime(value)
            if parsed is not None:
                return parsed
    return datetime.min.replace(tzinfo=timezone.utc)


def compact_state_plan(
    state: dict[str, Any],
    *,
    min_salience: int = 3,
    include_active_thread: bool = False,
    max_closed_recently: int = 10,
    max_episodes: int = 20,
    max_artifacts: int = 20,
) -> dict[str, Any]:
    """Build a conservative memory compaction plan without mutating state."""

    errors = validate_state(state)
    if errors:
        raise ValueError("invalid memory state: " + "; ".join(errors))

    now = datetime.now(timezone.utc)
    normalized_min_salience = max(1, min(5, int(min_salience)))
    suggestions: list[dict[str, Any]] = []
    seen: dict[tuple[str, str], dict[str, Any]] = {}

    def add_suggestion(
        *,
        action: str,
        path: str,
        record: dict[str, Any],
        reason: str,
        auto_apply: bool,
    ) -> None:
        record_id = str(record.get("id") or path)
        key = (action, record_id)
        if key in seen:
            reasons = seen[key]["reasons"]
            if reason not in reasons:
                reasons.append(reason)
            return
        suggestion = {
            "action": action,
            "id": record_id,
            "path": path,
            "status": record.get("status", "unknown"),
            "salience": record.get("salience", "unknown"),
            "confidence": record.get("confidence", "unknown"),
            "source": record.get("source", "unknown"),
            "scope": record.get("scope", "unknown"),
            "text_preview": record_preview(record),
            "reasons": [reason],
            "auto_apply": auto_apply,
        }
        seen[key] = suggestion
        suggestions.append(suggestion)

    for path, record in iter_records(state):
        if path.startswith("threads.active") and not include_active_thread:
            continue
        status = record.get("status")
        salience = record.get("salience")
        if status in {"active", "tentative"} and isinstance(salience, int) and salience < normalized_min_salience:
            add_suggestion(
                action="mark-stale",
                path=path,
                record=record,
                reason=f"active memory salience {salience} is below compaction threshold {normalized_min_salience}",
                auto_apply=True,
            )
        expires_at = record.get("expires_at")
        if status in {"active", "tentative"} and isinstance(expires_at, str):
            expires = parse_iso_datetime(expires_at)
            if expires is not None and expires <= now:
                add_suggestion(
                    action="mark-stale",
                    path=path,
                    record=record,
                    reason=f"active memory expired at {expires_at}",
                    auto_apply=True,
                )

    collection_limits = {
        "threads.closed_recently": max(0, int(max_closed_recently)),
        "episodes": max(0, int(max_episodes)),
        "project.artifacts": max(0, int(max_artifacts)),
    }
    for collection_name, records in iter_record_collections(state):
        limit = collection_limits.get(collection_name)
        if limit is None or not isinstance(records, list):
            continue
        indexed_records = [
            (index, record)
            for index, record in enumerate(records)
            if isinstance(record, dict)
        ]
        if len(indexed_records) <= limit:
            continue
        ranked = sorted(indexed_records, key=lambda item: record_timestamp(item[1]), reverse=True)
        for index, record in ranked[limit:]:
            add_suggestion(
                action="review-for-forget",
                path=f"{collection_name}[{index}]",
                record=record,
                reason=f"{collection_name} keeps more than {limit} records; review older low-value memory",
                auto_apply=False,
            )

    action_counts: dict[str, int] = {}
    for suggestion in suggestions:
        action = suggestion["action"]
        action_counts[action] = action_counts.get(action, 0) + 1

    return {
        "generated_at": now_iso(),
        "settings": {
            "min_salience": normalized_min_salience,
            "include_active_thread": include_active_thread,
            "max_closed_recently": max(0, int(max_closed_recently)),
            "max_episodes": max(0, int(max_episodes)),
            "max_artifacts": max(0, int(max_artifacts)),
        },
        "summary": {
            "suggestions": len(suggestions),
            "auto_apply": sum(1 for suggestion in suggestions if suggestion.get("auto_apply")),
            "review_only": sum(1 for suggestion in suggestions if not suggestion.get("auto_apply")),
            "actions": action_counts,
        },
        "suggestions": suggestions,
    }


def apply_compaction_plan(state: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    """Apply safe compaction suggestions. Review-only suggestions are never applied."""

    errors = validate_state(state)
    if errors:
        raise ValueError("invalid memory state: " + "; ".join(errors))
    suggestions = plan.get("suggestions", [])
    if not isinstance(suggestions, list):
        raise ValueError("compaction plan suggestions must be a list")

    applied: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    applied_ids: set[str] = set()
    for suggestion in suggestions:
        if not isinstance(suggestion, dict):
            skipped.append({"id": "unknown", "reason": "suggestion is not an object"})
            continue
        record_id = str(suggestion.get("id", ""))
        if not record_id:
            skipped.append({"id": "unknown", "reason": "suggestion is missing id"})
            continue
        if record_id in applied_ids:
            skipped.append({"id": record_id, "reason": "record already compacted by an earlier suggestion"})
            continue
        if suggestion.get("action") != "mark-stale" or not suggestion.get("auto_apply"):
            skipped.append({"id": record_id, "reason": "suggestion requires manual review"})
            continue
        try:
            path, record = find_record(state, record_id)
        except ValueError:
            skipped.append({"id": record_id, "reason": "record no longer exists"})
            continue
        if record.get("status") not in {"active", "tentative"}:
            skipped.append({"id": record_id, "reason": f"record status is already {record.get('status', 'unknown')}"})
            continue
        path, _record = update_record(state, record_id=record_id, status="stale", add_tags=["compacted"])
        applied.append({"id": record_id, "path": path, "action": "mark-stale"})
        applied_ids.add(record_id)

    return {"applied": applied, "skipped": skipped}


def render_compaction_plan(plan: dict[str, Any]) -> str:
    summary = plan.get("summary", {})
    settings = plan.get("settings", {})
    suggestions = plan.get("suggestions", [])
    lines = [
        "# Memory Compaction Plan",
        "",
        f"Generated: {plan.get('generated_at', 'unknown')}",
        (
            f"Suggestions: {summary.get('suggestions', 0)}"
            f" | Auto-applicable: {summary.get('auto_apply', 0)}"
            f" | Review-only: {summary.get('review_only', 0)}"
        ),
        (
            f"Settings: min_salience={settings.get('min_salience', 'unknown')}, "
            f"include_active_thread={settings.get('include_active_thread', False)}"
        ),
        "",
        "Default output is a plan only. Use --apply to mark auto-applicable records stale.",
        "",
    ]
    if not suggestions:
        lines.extend(["- No compaction suggestions.", ""])
        return "\n".join(lines)

    for suggestion in suggestions:
        reasons = "; ".join(str(reason) for reason in suggestion.get("reasons", []))
        mode = "auto" if suggestion.get("auto_apply") else "review"
        lines.extend(
            [
                f"## {suggestion.get('id', 'unknown')}",
                "",
                (
                    f"- Action: {suggestion.get('action', 'unknown')} ({mode})"
                    f" | Path: {suggestion.get('path', 'unknown')}"
                    f" | Status: {suggestion.get('status', 'unknown')}"
                    f" | Salience: {suggestion.get('salience', 'unknown')}"
                ),
                f"- Reason: {reasons or 'None'}",
                f"- Preview: {suggestion.get('text_preview', '')}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def ensure_list(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ["version", "updated_at", "user_profile", "project", "threads", "decisions", "episodes", "migration"]
    for key in required:
        if key not in state:
            errors.append(f"missing top-level key: {key}")

    user_profile = state.get("user_profile", {})
    if isinstance(user_profile, dict):
        for key in ["preferences", "working_style", "avoid"]:
            ensure_list(user_profile.get(key), f"user_profile.{key}", errors)
    else:
        errors.append("user_profile must be an object")

    project = state.get("project", {})
    if isinstance(project, dict):
        for key in ["facts", "artifacts"]:
            ensure_list(project.get(key), f"project.{key}", errors)
    else:
        errors.append("project must be an object")

    threads = state.get("threads", {})
    if isinstance(threads, dict):
        for key in ["open", "parked", "closed_recently"]:
            ensure_list(threads.get(key), f"threads.{key}", errors)
    else:
        errors.append("threads must be an object")

    for key in ["decisions", "episodes"]:
        ensure_list(state.get(key), key, errors)

    migration = state.get("migration", {})
    if isinstance(migration, dict):
        for key in ["next_actions", "risks", "handoff_notes"]:
            ensure_list(migration.get(key), f"migration.{key}", errors)
    else:
        errors.append("migration must be an object")

    for collection_name, records in iter_record_collections(state):
        if not isinstance(records, list):
            continue
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(f"{collection_name}[{index}] must be an object")
                continue
            for field in ["id", "text", "status", "confidence", "salience"]:
                if field not in record:
                    errors.append(f"{collection_name}[{index}] missing field: {field}")
            salience = record.get("salience")
            if not isinstance(salience, int) or salience < 1 or salience > 5:
                errors.append(f"{collection_name}[{index}].salience must be an integer from 1 to 5")
            confidence = record.get("confidence")
            if confidence not in {"low", "medium", "high"}:
                errors.append(f"{collection_name}[{index}].confidence must be low, medium, or high")
            status = record.get("status")
            if status not in KNOWN_STATUSES:
                errors.append(
                    f"{collection_name}[{index}].status must be one of: {', '.join(sorted(KNOWN_STATUSES))}"
                )
            source = record.get("source")
            if source is not None and source not in KNOWN_SOURCES:
                errors.append(f"{collection_name}[{index}].source must be one of: {', '.join(sorted(KNOWN_SOURCES))}")
            scope = record.get("scope")
            if scope is not None and scope not in KNOWN_SCOPES:
                errors.append(f"{collection_name}[{index}].scope must be one of: {', '.join(sorted(KNOWN_SCOPES))}")
            expires_at = record.get("expires_at")
            if expires_at is not None and (not isinstance(expires_at, str) or parse_iso_datetime(expires_at) is None):
                errors.append(f"{collection_name}[{index}].expires_at must be an ISO timestamp")
            supersedes = record.get("supersedes")
            if supersedes is not None and (
                not isinstance(supersedes, list) or any(not isinstance(item, str) for item in supersedes)
            ):
                errors.append(f"{collection_name}[{index}].supersedes must be a list of record ids")

    return errors


def audit_state(state: dict[str, Any]) -> list[dict[str, str]]:
    """Return quality issues that make memory less useful for handoff."""

    issues: list[dict[str, str]] = []
    for error in validate_state(state):
        issues.append({"severity": "error", "path": "schema", "message": error})

    project = state.get("project", {})
    if isinstance(project, dict) and not project.get("objective"):
        issues.append(
            {
                "severity": "warning",
                "path": "project.objective",
                "message": "missing objective makes handoff harder",
            }
        )

    migration = state.get("migration", {})
    if isinstance(migration, dict):
        if not migration.get("summary"):
            issues.append(
                {
                    "severity": "warning",
                    "path": "migration.summary",
                    "message": "missing summary weakens model or agent migration",
                }
            )
        if not migration.get("next_actions"):
            issues.append(
                {
                    "severity": "info",
                    "path": "migration.next_actions",
                    "message": "no next actions recorded",
                }
            )

    seen_ids: dict[str, str] = {}
    records_by_id: dict[str, dict[str, Any]] = {}
    supersedes_checks: list[tuple[str, list[str]]] = []
    for collection_name, records in iter_record_collections(state):
        if not isinstance(records, list):
            continue
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            path = f"{collection_name}[{index}]"
            record_id = str(record.get("id", ""))
            if record_id:
                if record_id in seen_ids:
                    issues.append(
                        {
                            "severity": "error",
                            "path": f"{path}.id",
                            "message": f"duplicate record id also used at {seen_ids[record_id]}",
                        }
                    )
                else:
                    seen_ids[record_id] = path
                    records_by_id[record_id] = record

            text = str(record.get("text", ""))
            evidence = str(record.get("evidence", ""))
            salience = record.get("salience", 0)
            confidence = record.get("confidence", "")
            status = record.get("status", "")
            source = str(record.get("source", "user"))
            expires_at = record.get("expires_at")
            tags = record.get("tags", [])
            if not isinstance(tags, list):
                tags = []
            is_candidate = status == "candidate"

            if status and status not in KNOWN_STATUSES:
                issues.append(
                    {
                        "severity": "warning",
                        "path": f"{path}.status",
                        "message": f"unknown status: {status}",
                    }
                )
            if is_candidate:
                issues.append(
                    {
                        "severity": "info",
                        "path": f"{path}.status",
                        "message": "candidate memory awaiting review",
                    }
                )
            if not is_candidate and isinstance(salience, int) and salience >= 3 and not evidence:
                issues.append(
                    {
                        "severity": "warning",
                        "path": f"{path}.evidence",
                        "message": "salient memory should include evidence",
                    }
                )
            if not is_candidate and isinstance(salience, int) and salience >= 5 and confidence == "low":
                issues.append(
                    {
                        "severity": "warning",
                        "path": f"{path}.confidence",
                        "message": "critical memory has low confidence",
                    }
                )
            if isinstance(salience, int) and salience <= 2 and status == "active":
                issues.append(
                    {
                        "severity": "info",
                        "path": f"{path}.salience",
                        "message": "low-salience active memory may be bloat",
                    }
                )
            if len(text) > 600:
                issues.append(
                    {
                        "severity": "warning",
                        "path": f"{path}.text",
                        "message": "record text is long; summarize instead of storing transcript-like content",
                    }
                )
            if "User:" in text and "Assistant:" in text:
                issues.append(
                    {
                        "severity": "warning",
                        "path": f"{path}.text",
                        "message": "record looks transcript-like; store curated memory instead",
                    }
                )
            lowered_text = text.lower()
            if any(phrase in lowered_text for phrase in POISONING_PHRASES):
                issues.append(
                    {
                        "severity": "warning",
                        "path": f"{path}.text",
                        "message": "record contains instruction-like or secret-handling language; review for memory poisoning",
                    }
                )
            if isinstance(salience, int) and salience >= 4 and source in {"tool", "external", "derived"}:
                if "reviewed" not in tags:
                    issues.append(
                        {
                            "severity": "warning",
                            "path": f"{path}.source",
                            "message": "high-impact memory from a non-user source should be reviewed before reuse",
                        }
                    )
            if "untrusted" in tags and status in {"active", "tentative"}:
                issues.append(
                    {
                        "severity": "warning",
                        "path": f"{path}.tags",
                        "message": "untrusted memory should not remain active without review",
                    }
                )
            if isinstance(expires_at, str):
                parsed_expires_at = parse_iso_datetime(expires_at)
                if parsed_expires_at and parsed_expires_at <= datetime.now(timezone.utc) and status in {
                    "active",
                    "tentative",
                }:
                    issues.append(
                        {
                            "severity": "warning",
                            "path": f"{path}.expires_at",
                            "message": "expired memory remains active",
                        }
                    )
            supersedes = record.get("supersedes")
            if isinstance(supersedes, list):
                supersedes_checks.append((path, [str(item) for item in supersedes]))

    for path, superseded_ids in supersedes_checks:
        for superseded_id in superseded_ids:
            if superseded_id not in seen_ids:
                issues.append(
                    {
                        "severity": "warning",
                        "path": f"{path}.supersedes",
                        "message": f"supersedes unknown record id: {superseded_id}",
                    }
                )
                continue
            superseded_record = records_by_id.get(superseded_id, {})
            superseded_status = superseded_record.get("status")
            if superseded_status not in {"superseded", "stale", "closed"}:
                issues.append(
                    {
                        "severity": "warning",
                        "path": f"{path}.supersedes",
                        "message": f"superseded record should be stale or superseded: {superseded_id}",
                    }
                )

    return issues


def handoff_failed(issues: list[dict[str, str]], *, strict: bool = False) -> bool:
    has_error = any(issue["severity"] == "error" for issue in issues)
    has_warning = any(issue["severity"] == "warning" for issue in issues)
    return has_error or (strict and has_warning)


def handoff_exit_code(issues: list[dict[str, str]], *, strict: bool = False) -> int:
    return 1 if handoff_failed(issues, strict=strict) else 0


def format_issues(issues: list[dict[str, str]]) -> str:
    return "\n".join(f"{issue['severity'].upper()}: {issue['path']}: {issue['message']}" for issue in issues)


def serialize_handoff_report(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: serialize_handoff_report(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_handoff_report(item) for item in value]
    return value


def prepare_handoff_artifacts(
    memory_dir: Path,
    state: dict[str, Any],
    *,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    errors = validate_state(state)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"invalid memory state at {memory_dir / STATE_FILE}: {joined}")
    write_briefing(
        memory_dir,
        state,
        max_records=max_records,
        include_stale=include_stale,
        include_untrusted=include_untrusted,
    )
    write_packet(memory_dir, state)
    issues = audit_state(state)
    return {
        "memory_dir": memory_dir,
        "state": memory_dir / STATE_FILE,
        "briefing": memory_dir / BRIEFING_FILE,
        "packet": memory_dir / PACKET_FILE,
        "issues": issues,
        "ready": not handoff_failed(issues, strict=strict),
    }


def iter_record_collections(state: dict[str, Any]):
    user_profile = state.get("user_profile", {})
    if isinstance(user_profile, dict):
        yield "user_profile.preferences", user_profile.get("preferences")
        yield "user_profile.working_style", user_profile.get("working_style")
        yield "user_profile.avoid", user_profile.get("avoid")

    project = state.get("project", {})
    if isinstance(project, dict):
        yield "project.facts", project.get("facts")
        yield "project.artifacts", project.get("artifacts")

    threads = state.get("threads", {})
    if isinstance(threads, dict):
        active = threads.get("active")
        if active is not None:
            yield "threads.active", [active]
        yield "threads.open", threads.get("open")
        yield "threads.parked", threads.get("parked")
        yield "threads.closed_recently", threads.get("closed_recently")

    yield "decisions", state.get("decisions")
    yield "episodes", state.get("episodes")


def record_text(record: Any) -> str:
    if record is None:
        return "None"
    if isinstance(record, str):
        return record
    if isinstance(record, dict):
        text = record.get("text", "")
        rid = record.get("id")
        status = record.get("status")
        suffix_parts = []
        if rid:
            suffix_parts.append(str(rid))
        if status and status != "active":
            suffix_parts.append(f"status: {status}")
        suffix = f" ({'; '.join(suffix_parts)})" if suffix_parts else ""
        return f"{text}{suffix}".strip()
    return str(record)


def bullet_list(items: Any) -> str:
    if not items:
        return "- None"
    if not isinstance(items, list):
        items = [items]
    return "\n".join(f"- {record_text(item) or 'None'}" for item in items)


def record_is_usable(record: Any, *, include_stale: bool = False, include_untrusted: bool = False) -> bool:
    if not isinstance(record, dict):
        return True
    status = record.get("status")
    if status == "candidate":
        return False
    if not include_stale and status in {"stale", "superseded"}:
        return False
    tags = record.get("tags", [])
    if not include_untrusted and isinstance(tags, list) and "untrusted" in tags:
        return False
    return True


def usable_records(
    items: Any,
    *,
    max_records: int,
    include_stale: bool = False,
    include_untrusted: bool = False,
) -> list[Any]:
    if not isinstance(items, list):
        items = [] if items is None else [items]
    records = [
        item
        for item in sort_records(items)
        if record_is_usable(item, include_stale=include_stale, include_untrusted=include_untrusted)
    ]
    return records[: max(1, max_records)]


def sort_records(items: Any) -> Any:
    if not isinstance(items, list):
        return items
    return sorted(
        items,
        key=lambda item: item.get("salience", 0) if isinstance(item, dict) else 0,
        reverse=True,
    )


def text_matches_query(query: str | None, text: str) -> bool:
    if not query:
        return True
    lowered_text = text.lower()
    lowered_query = query.lower().strip()
    if not lowered_query:
        return True
    if lowered_query in lowered_text:
        return True
    terms = [term for term in lowered_query.split() if term]
    return bool(terms) and all(term in lowered_text for term in terms)


def filter_contains(value: str | None, allowed: list[str] | None) -> bool:
    if not allowed:
        return True
    lowered = str(value or "").lower()
    return lowered in {item.lower() for item in allowed}


def collection_matches(path: str, collections: list[str] | None) -> bool:
    if not collections:
        return True
    lowered_path = path.lower()
    for collection in collections:
        lowered = collection.lower()
        if lowered_path.startswith(lowered) or lowered_path.endswith(f".{lowered}"):
            return True
        if f".{lowered}[" in lowered_path or f".{lowered}." in lowered_path:
            return True
        if lowered in lowered_path:
            return True
    return False


def record_search_text(path: str, record: dict[str, Any]) -> str:
    parts = [
        path,
        str(record.get("id", "")),
        str(record.get("text", "")),
        str(record.get("type", "")),
        str(record.get("status", "")),
        str(record.get("confidence", "")),
        str(record.get("evidence", "")),
        str(record.get("source", "")),
        str(record.get("scope", "")),
    ]
    tags = record.get("tags", [])
    if isinstance(tags, list):
        parts.extend(str(tag) for tag in tags)
    return " ".join(parts)


def selected_record_score(path: str, record: dict[str, Any], query: str | None) -> int:
    salience = record.get("salience", 0)
    score = salience if isinstance(salience, int) else 0
    if not query:
        return score
    lowered_query = query.lower().strip()
    if not lowered_query:
        return score
    if lowered_query in str(record.get("text", "")).lower():
        score += 4
    if lowered_query in str(record.get("id", "")).lower() or lowered_query in path.lower():
        score += 3
    if lowered_query in str(record.get("evidence", "")).lower():
        score += 2
    tags = record.get("tags", [])
    if isinstance(tags, list) and any(lowered_query in str(tag).lower() for tag in tags):
        score += 2
    return score


def select_memory_records(
    state: dict[str, Any],
    *,
    query: str | None = None,
    collections: list[str] | None = None,
    record_types: list[str] | None = None,
    tags: list[str] | None = None,
    statuses: list[str] | None = None,
    sources: list[str] | None = None,
    scopes: list[str] | None = None,
    min_salience: int = 1,
    limit: int = 10,
    include_stale: bool = False,
    include_candidates: bool = False,
    include_untrusted: bool = False,
) -> list[dict[str, Any]]:
    """Select high-signal memory records for targeted context loading."""

    results: list[dict[str, Any]] = []
    required_tags = [tag.lower() for tag in (tags or [])]
    status_filters = {status.lower() for status in (statuses or [])}
    allow_stale = include_stale or bool(status_filters)
    allow_candidates = include_candidates or "candidate" in status_filters
    allow_untrusted = include_untrusted or "untrusted" in required_tags
    for path, record in iter_records(state):
        if not collection_matches(path, collections):
            continue
        record_status = str(record.get("status", "")).lower()
        if not allow_candidates and record_status == "candidate":
            continue
        if not allow_stale and record_status in {"stale", "superseded"}:
            continue
        record_tags = record.get("tags", [])
        if not isinstance(record_tags, list):
            record_tags = []
        lowered_tags = {str(tag).lower() for tag in record_tags}
        if not allow_untrusted and "untrusted" in lowered_tags:
            continue
        if required_tags and not all(tag in lowered_tags for tag in required_tags):
            continue
        salience = record.get("salience", 0)
        if isinstance(salience, int) and salience < min_salience:
            continue
        if not filter_contains(record.get("type"), record_types):
            continue
        if not filter_contains(record.get("status"), statuses):
            continue
        if not filter_contains(record.get("source"), sources):
            continue
        if not filter_contains(record.get("scope"), scopes):
            continue
        search_text = record_search_text(path, record)
        if not text_matches_query(query, search_text):
            continue
        results.append(
            {
                "path": path,
                "score": selected_record_score(path, record, query),
                "record": clone_json(record),
            }
        )

    return sorted(
        results,
        key=lambda item: (
            item["score"],
            item["record"].get("salience", 0),
            item["record"].get("updated_at", ""),
            item["record"].get("id", ""),
        ),
        reverse=True,
    )[: max(1, limit)]


def render_selected_records(results: list[dict[str, Any]]) -> str:
    lines = ["# Selected Memory Records", "", f"Total: {len(results)}", ""]
    if not results:
        return "\n".join(lines + ["- None", ""])
    for item in results:
        record = item.get("record", {})
        tags = record.get("tags", [])
        tag_text = ", ".join(str(tag) for tag in tags) if isinstance(tags, list) and tags else "None"
        lines.extend(
            [
                f"## {record.get('id', 'unknown')}",
                "",
                (
                    f"- Path: {item.get('path', 'unknown')}"
                    f" | Score: {item.get('score', 0)}"
                    f" | Type: {record.get('type', 'unknown')}"
                    f" | Status: {record.get('status', 'unknown')}"
                    f" | Salience: {record.get('salience', 'unknown')}"
                    f" | Confidence: {record.get('confidence', 'unknown')}"
                    f" | Source: {record.get('source', 'unknown')}"
                    f" | Scope: {record.get('scope', 'unknown')}"
                ),
                f"- Tags: {tag_text}",
                "",
                str(record.get("text", "")),
                "",
                f"Evidence: {record.get('evidence', '')}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_briefing(
    state: dict[str, Any],
    *,
    max_records: int = 5,
    include_stale: bool = False,
    include_untrusted: bool = False,
) -> str:
    user_profile = state.get("user_profile", {})
    project = state.get("project", {})
    threads = state.get("threads", {})
    migration = state.get("migration", {})

    preferences = []
    if isinstance(user_profile, dict):
        preferences.extend(user_profile.get("preferences", []))
        preferences.extend(user_profile.get("working_style", []))
        preferences.extend(user_profile.get("avoid", []))

    facts = project.get("facts", []) if isinstance(project, dict) else []
    active = threads.get("active") if isinstance(threads, dict) else None
    parked_and_open = []
    if isinstance(threads, dict):
        parked_and_open.extend(threads.get("parked", []))
        parked_and_open.extend(threads.get("open", []))

    active_text = "None"
    if record_is_usable(active, include_stale=include_stale, include_untrusted=include_untrusted):
        active_text = record_text(active)

    next_actions = migration.get("next_actions", []) if isinstance(migration, dict) else []
    risks = migration.get("risks", []) if isinstance(migration, dict) else []
    handoff_notes = migration.get("handoff_notes", []) if isinstance(migration, dict) else []

    lines = [
        "# Agent Memory Briefing",
        "",
        "Use this as a short startup context for a new model or agent. Treat memory as guidance and trust the current environment.",
        "",
        f"Updated: {state.get('updated_at', 'unknown')}",
        "",
        "## Objective",
        "",
        project.get("objective", "None") if isinstance(project, dict) else "None",
        "",
        "## Summary",
        "",
        migration.get("summary", "None") if isinstance(migration, dict) else "None",
        "",
        "## Active Topic",
        "",
        f"- {active_text}",
        "",
        "## Next Actions",
        "",
        bullet_list(next_actions[: max(1, max_records)]),
        "",
        "## User Preferences",
        "",
        bullet_list(
            usable_records(
                preferences,
                max_records=max_records,
                include_stale=include_stale,
                include_untrusted=include_untrusted,
            )
        ),
        "",
        "## Key Decisions",
        "",
        bullet_list(
            usable_records(
                state.get("decisions", []),
                max_records=max_records,
                include_stale=include_stale,
                include_untrusted=include_untrusted,
            )
        ),
        "",
        "## Key Project Facts",
        "",
        bullet_list(
            usable_records(
                facts,
                max_records=max_records,
                include_stale=include_stale,
                include_untrusted=include_untrusted,
            )
        ),
        "",
        "## Parked Or Open Topics",
        "",
        bullet_list(
            usable_records(
                parked_and_open,
                max_records=max_records,
                include_stale=include_stale,
                include_untrusted=include_untrusted,
            )
        ),
        "",
        "## Recent Episodes",
        "",
        bullet_list(
            usable_records(
                state.get("episodes", []),
                max_records=max_records,
                include_stale=include_stale,
                include_untrusted=include_untrusted,
            )
        ),
        "",
        "## Risks And Handoff Notes",
        "",
        bullet_list((risks + handoff_notes)[: max(1, max_records)]),
        "",
        "For full detail, read migration-packet.md or state.json.",
        "",
    ]
    return "\n".join(lines)


def render_packet(state: dict[str, Any]) -> str:
    user_profile = state.get("user_profile", {})
    project = state.get("project", {})
    threads = state.get("threads", {})
    migration = state.get("migration", {})

    preferences = []
    if isinstance(user_profile, dict):
        preferences.extend(user_profile.get("preferences", []))
        preferences.extend(user_profile.get("working_style", []))
        preferences.extend(user_profile.get("avoid", []))

    facts = project.get("facts", []) if isinstance(project, dict) else []
    artifacts = project.get("artifacts", []) if isinstance(project, dict) else []

    packet = [
        "# Agent Memory Migration Packet",
        "",
        f"Updated: {state.get('updated_at', 'unknown')}",
        "",
        "## Objective",
        "",
        project.get("objective", "None") if isinstance(project, dict) else "None",
        "",
        "## Summary",
        "",
        migration.get("summary", "None") if isinstance(migration, dict) else "None",
        "",
        "## User Preferences",
        "",
        bullet_list(sort_records(preferences)),
        "",
        "## Project State",
        "",
        bullet_list(sort_records(facts)),
        "",
        "## Decisions",
        "",
        bullet_list(sort_records(state.get("decisions", []))),
        "",
        "## Topic Stack",
        "",
        f"- Active: {record_text(threads.get('active')) if isinstance(threads, dict) else 'None'}",
        "",
        "### Parked",
        "",
        bullet_list(sort_records(threads.get("parked", []) if isinstance(threads, dict) else [])),
        "",
        "### Open",
        "",
        bullet_list(sort_records(threads.get("open", []) if isinstance(threads, dict) else [])),
        "",
        "### Closed Recently",
        "",
        bullet_list(sort_records(threads.get("closed_recently", []) if isinstance(threads, dict) else [])),
        "",
        "## Episodes",
        "",
        bullet_list(sort_records(state.get("episodes", []))),
        "",
        "## Artifacts",
        "",
        bullet_list(sort_records(artifacts)),
        "",
        "## Next Actions",
        "",
        bullet_list(migration.get("next_actions", []) if isinstance(migration, dict) else []),
        "",
        "## Risks And Do-Not-Redo",
        "",
        bullet_list(migration.get("risks", []) if isinstance(migration, dict) else []),
        "",
        "## Handoff Notes",
        "",
        bullet_list(migration.get("handoff_notes", []) if isinstance(migration, dict) else []),
        "",
    ]
    return "\n".join(packet)


def update_meta(
    state: dict[str, Any],
    *,
    project_name: str | None = None,
    objective: str | None = None,
    summary: str | None = None,
    next_actions: list[str] | None = None,
    risks: list[str] | None = None,
    handoff_notes: list[str] | None = None,
) -> bool:
    changed = False
    if project_name is not None:
        state["project"]["name"] = project_name
        changed = True
    if objective is not None:
        state["project"]["objective"] = objective
        changed = True
    if summary is not None:
        state["migration"]["summary"] = summary
        changed = True
    for action in next_actions or []:
        state["migration"]["next_actions"].append(action)
        changed = True
    for risk in risks or []:
        state["migration"]["risks"].append(risk)
        changed = True
    for note in handoff_notes or []:
        state["migration"]["handoff_notes"].append(note)
        changed = True
    return changed


def add_record(
    state: dict[str, Any],
    *,
    collection: str,
    record_id: str,
    text: str,
    record_type: str | None = None,
    status: str = "active",
    confidence: str = "medium",
    salience: int = 3,
    evidence: str = "",
    tags: list[str] | None = None,
    source: str = "user",
    scope: str = "project",
    expires_at: str | None = None,
    supersedes: list[str] | None = None,
) -> dict[str, Any]:
    records, default_type = collection_list(state, collection)
    record = make_record(
        record_id=record_id,
        text=text,
        record_type=record_type or default_type,
        status=status,
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=tags,
        source=source,
        scope=scope,
        expires_at=expires_at,
        supersedes=supersedes,
    )
    records.append(record)
    return record


def set_active_thread(
    state: dict[str, Any],
    *,
    record_id: str,
    text: str,
    confidence: str = "medium",
    salience: int = 3,
    evidence: str = "",
    tags: list[str] | None = None,
    park_current: bool = False,
    source: str = "user",
    scope: str = "project",
    expires_at: str | None = None,
    supersedes: list[str] | None = None,
) -> dict[str, Any]:
    threads = state["threads"]
    timestamp = now_iso()
    if park_current and threads.get("active"):
        threads["parked"].append(copy_with_status(threads["active"], "parked", timestamp))
    thread = make_record(
        record_id=record_id,
        text=text,
        record_type="thread",
        status="active",
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=tags,
        source=source,
        scope=scope,
        expires_at=expires_at,
        supersedes=supersedes,
        timestamp=timestamp,
    )
    threads["active"] = thread
    return thread


def interrupt_thread(
    state: dict[str, Any],
    *,
    episode_id: str,
    episode_text: str,
    thread_id: str,
    thread_text: str,
    confidence: str = "medium",
    salience: int = 4,
    evidence: str = "",
    tags: list[str] | None = None,
    source: str = "user",
    scope: str = "project",
    expires_at: str | None = None,
    supersedes: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    threads = state["threads"]
    timestamp = now_iso()
    if threads.get("active"):
        threads["parked"].append(copy_with_status(threads["active"], "parked", timestamp))
    episode = make_record(
        record_id=episode_id,
        text=episode_text,
        record_type="episode",
        status="active",
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=tags,
        source=source,
        scope=scope,
        expires_at=expires_at,
        supersedes=supersedes,
        timestamp=timestamp,
    )
    thread = make_record(
        record_id=thread_id,
        text=thread_text,
        record_type="thread",
        status="active",
        confidence=confidence,
        salience=salience,
        evidence=evidence,
        tags=tags,
        source=source,
        scope=scope,
        expires_at=expires_at,
        supersedes=supersedes,
        timestamp=timestamp,
    )
    state["episodes"].append(episode)
    threads["active"] = thread
    return episode, thread


def detect_topic_cue(state: dict[str, Any], text: str) -> dict[str, str]:
    """Detect whether a user message likely closes an interruption and should resume a parked topic."""

    threads = state.get("threads", {})
    parked = threads.get("parked", []) if isinstance(threads, dict) else []
    active = threads.get("active") if isinstance(threads, dict) else None
    if not parked:
        return {
            "action": "stay",
            "confidence": "high",
            "reason": "no parked topic is available to resume",
            "active": record_text(active),
            "resume_candidate": "None",
        }

    stripped = text.strip()
    if not stripped:
        return {
            "action": "stay",
            "confidence": "high",
            "reason": "empty cue text",
            "active": record_text(active),
            "resume_candidate": record_text(parked[-1]),
        }

    explicit = contains_any(stripped, EXPLICIT_RETURN_CUES)
    if explicit:
        return {
            "action": "resume",
            "confidence": "high",
            "reason": f"explicit return cue: {explicit}",
            "active": record_text(active),
            "resume_candidate": record_text(parked[-1]),
        }

    closure = contains_any(stripped, CLOSURE_CUES)
    if closure:
        return {
            "action": "resume",
            "confidence": "medium",
            "reason": f"closure cue: {closure}",
            "active": record_text(active),
            "resume_candidate": record_text(parked[-1]),
        }

    ambiguous = contains_any(stripped, AMBIGUOUS_CONTINUE_CUES)
    if ambiguous:
        return {
            "action": "ask",
            "confidence": "low",
            "reason": f"ambiguous continuation cue: {ambiguous}",
            "active": record_text(active),
            "resume_candidate": record_text(parked[-1]),
        }

    return {
        "action": "stay",
        "confidence": "medium",
        "reason": "no closure or return cue detected",
        "active": record_text(active),
        "resume_candidate": record_text(parked[-1]),
    }


def resume_thread(state: dict[str, Any], *, current_destination: str = "closed") -> dict[str, Any]:
    threads = state["threads"]
    timestamp = now_iso()
    if not threads["parked"]:
        raise ValueError("no parked thread to resume")
    current = threads.get("active")
    if current and current_destination != "drop":
        destination_map = {
            "closed": ("closed_recently", "closed"),
            "open": ("open", "active"),
            "parked": ("parked", "parked"),
        }
        if current_destination not in destination_map:
            raise ValueError("current_destination must be closed, open, parked, or drop")
        destination, status = destination_map[current_destination]
        threads[destination].append(copy_with_status(current, status, timestamp))
    resumed = threads["parked"].pop()
    threads["active"] = copy_with_status(resumed, "active", timestamp)
    return threads["active"]
