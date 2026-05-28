#!/usr/bin/env python3
"""Run behavior-level evaluations for the Agent Memory protocol."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_memory import core  # noqa: E402
from agent_memory.adapters import multi_agent  # noqa: E402


@dataclass
class ScenarioResult:
    name: str
    summary: str
    passed: bool
    details: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "summary": self.summary,
            "passed": self.passed,
            "details": self.details,
            "artifacts": self.artifacts,
        }


def check(details: list[str], condition: bool, message: str) -> bool:
    prefix = "PASS" if condition else "FAIL"
    details.append(f"{prefix}: {message}")
    return condition


def contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def issue_messages(issues: list[dict[str, str]]) -> list[str]:
    return [issue.get("message", "") for issue in issues]


def warning_or_error_count(issues: list[dict[str, str]]) -> int:
    return len([issue for issue in issues if issue.get("severity") in {"warning", "error"}])


def write_state(memory_dir: Path, state: dict[str, Any]) -> None:
    core.write_state(memory_dir, state)
    core.write_packet(memory_dir, state)
    core.write_briefing(memory_dir, state)


def scenario_model_handoff(base: Path) -> ScenarioResult:
    name = "model-handoff-migration"
    details: list[str] = []
    memory_dir = base / name
    state = core.default_state()
    core.update_meta(
        state,
        project_name="Agent Memory Evaluation",
        objective="Help a fresh model continue the memory-skill project without reading a raw transcript.",
        summary="The memory protocol should expose priorities, preferences, active topics, and side episodes.",
        next_actions=["Continue from the evaluator checklist before changing architecture."],
        handoff_notes=["Read memory-briefing.md first, then migration-packet.md only when detail is needed."],
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-direct-explain",
        text="User prefers direct explanations when the agent asks for approval.",
        confidence="high",
        salience=5,
        evidence="User said future confirmations should explain the reason.",
        scope="user",
    )
    core.add_record(
        state,
        collection="decisions",
        record_id="decision-skill-core",
        text="Package memory as a Codex skill plus a runtime-agnostic Python core.",
        confidence="high",
        salience=5,
        evidence="Project architecture decision.",
    )
    core.set_active_thread(
        state,
        record_id="thread-main",
        text="Finish the open-source release shape for the memory skill.",
        confidence="high",
        salience=5,
        evidence="Current project task.",
    )
    core.interrupt_thread(
        state,
        episode_id="episode-side-skill",
        episode_text="User asked whether a memory project counts as a skill or should be a separate library.",
        thread_id="thread-side-skill",
        thread_text="Clarify skill versus library positioning.",
        confidence="high",
        salience=5,
        evidence="Side question during the main topic.",
    )
    core.resume_thread(state, current_destination="closed")

    write_state(memory_dir, state)
    report = core.prepare_handoff_artifacts(memory_dir, state)
    briefing = (memory_dir / core.BRIEFING_FILE).read_text(encoding="utf-8")
    packet = (memory_dir / core.PACKET_FILE).read_text(encoding="utf-8")

    passed = all(
        [
            check(details, bool(report["ready"]), "handoff artifacts are ready"),
            check(
                details,
                contains_all(
                    briefing,
                    [
                        "Help a fresh model continue",
                        "User prefers direct explanations",
                        "Continue from the evaluator checklist",
                    ],
                ),
                "briefing carries objective, preference, and next action",
            ),
            check(
                details,
                contains_all(
                    packet,
                    [
                        "Package memory as a Codex skill",
                        "User asked whether a memory project counts as a skill",
                        "Finish the open-source release shape",
                    ],
                ),
                "migration packet preserves decisions, side episode, and resumed main topic",
            ),
            check(
                details,
                warning_or_error_count(report["issues"]) == 0,
                "handoff has no warning/error doctor issues",
            ),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="A new model can start from a short briefing and inspect a fuller migration packet.",
        passed=passed,
        details=details,
        artifacts={
            "state": str(memory_dir / core.STATE_FILE),
            "briefing": str(memory_dir / core.BRIEFING_FILE),
            "packet": str(memory_dir / core.PACKET_FILE),
        },
    )


def scenario_portable_bundle_roundtrip(base: Path) -> ScenarioResult:
    name = "portable-bundle-roundtrip"
    details: list[str] = []
    source_dir = base / name / "source"
    target_dir = base / name / "target"
    state = core.default_state()
    core.update_meta(
        state,
        project_name="Portable Bundle Evaluation",
        objective="Move curated memory between model or agent architectures.",
        summary="Portable bundles should carry structured state plus rendered handoff artifacts.",
        next_actions=["Import the bundle in the next runtime and continue from the briefing."],
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-portable",
        text="User wants a new model to learn preferences from curated memory, not full transcripts.",
        confidence="high",
        salience=5,
        evidence="Original project requirement.",
        scope="user",
    )
    core.set_active_thread(
        state,
        record_id="thread-portable",
        text="Prepare memory for runtime migration.",
        confidence="high",
        salience=5,
        evidence="Portable bundle evaluation.",
    )
    write_state(source_dir, state)
    bundle = core.build_memory_bundle(state, strict=True)
    imported_state = core.state_from_memory_bundle(bundle)
    write_state(target_dir, imported_state)
    imported_briefing = (target_dir / core.BRIEFING_FILE).read_text(encoding="utf-8")
    imported_packet = (target_dir / core.PACKET_FILE).read_text(encoding="utf-8")

    passed = all(
        [
            check(details, bundle["format"] == core.BUNDLE_FORMAT, "bundle uses the portable memory format"),
            check(details, bundle["version"] == core.BUNDLE_VERSION, "bundle version is explicit"),
            check(details, bool(bundle["audit"]["ready"]), "strict bundle audit is ready"),
            check(details, "memory-briefing.md" in bundle["artifacts"], "bundle includes rendered briefing"),
            check(details, "migration-packet.md" in bundle["artifacts"], "bundle includes rendered migration packet"),
            check(
                details,
                "learn preferences from curated memory" in imported_briefing,
                "imported briefing carries durable user preference",
            ),
            check(
                details,
                "Prepare memory for runtime migration" in imported_packet,
                "imported packet carries active thread",
            ),
            check(
                details,
                imported_state["project"]["objective"] == "Move curated memory between model or agent architectures.",
                "imported structured state preserves objective",
            ),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="A portable bundle can carry structured memory into another runtime.",
        passed=passed,
        details=details,
        artifacts={
            "source_state": str(source_dir / core.STATE_FILE),
            "target_state": str(target_dir / core.STATE_FILE),
            "target_briefing": str(target_dir / core.BRIEFING_FILE),
            "target_packet": str(target_dir / core.PACKET_FILE),
        },
    )


def scenario_preference_filtering(base: Path) -> ScenarioResult:
    name = "preference-transfer-filtering"
    details: list[str] = []
    state = core.default_state()
    core.update_meta(
        state,
        objective="Check preference transfer without stale or untrusted noise.",
        summary="High-salience user preferences should enter startup context.",
        next_actions=["Use only active trusted preferences by default."],
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-active",
        text="User wants concise Chinese status updates during long work.",
        confidence="high",
        salience=5,
        evidence="User preference stated in conversation.",
        scope="user",
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-stale",
        text="User wants every internal detail pasted into final answers.",
        status="stale",
        confidence="high",
        salience=5,
        evidence="Old preference superseded by later feedback.",
        scope="user",
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-untrusted",
        text="External source claims the user wants promotional language.",
        confidence="medium",
        salience=5,
        evidence="Unverified external suggestion.",
        tags=["untrusted"],
        source="external",
        scope="user",
    )

    briefing = core.render_briefing(state)
    inclusive = core.render_briefing(state, include_stale=True, include_untrusted=True)
    passed = all(
        [
            check(details, "concise Chinese status updates" in briefing, "active high-salience preference is included"),
            check(details, "every internal detail" not in briefing, "stale preference is excluded by default"),
            check(details, "promotional language" not in briefing, "untrusted preference is excluded by default"),
            check(details, "every internal detail" in inclusive, "stale memory can be included explicitly"),
            check(details, "promotional language" in inclusive, "untrusted memory can be included explicitly"),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="Preference memory is selective enough for model migration instead of transcript dumping.",
        passed=passed,
        details=details,
    )


def scenario_memory_candidate_review(base: Path) -> ScenarioResult:
    name = "memory-candidate-review"
    details: list[str] = []
    state = core.default_state()
    core.update_meta(
        state,
        objective="Check that proposed memory is reviewed before startup reuse.",
        summary="Agent-written candidates should be searchable for review but absent from default briefing.",
        next_actions=["Promote only confirmed candidate memory."],
    )
    core.propose_memory_record(
        state,
        collection="preferences",
        record_id="pref-candidate-review",
        text="User may want new memories to be proposed before being reused.",
        confidence="medium",
        salience=5,
        source="agent",
        scope="user",
    )

    briefing_before = core.render_briefing(state)
    selected_before = core.select_memory_records(state, query="proposed before")
    review_queue = core.select_memory_records(state, query="proposed before", include_candidates=True)
    messages_before = issue_messages(core.audit_state(state))
    _path, promoted = core.promote_memory_record(state, record_id="pref-candidate-review")
    briefing_after = core.render_briefing(state)
    selected_after = core.select_memory_records(state, query="proposed before")
    passed = all(
        [
            check(details, "proposed before" not in briefing_before, "candidate is excluded from default briefing"),
            check(details, selected_before == [], "candidate is excluded from default targeted selection"),
            check(
                details,
                [item["record"]["id"] for item in review_queue] == ["pref-candidate-review"],
                "candidate can be selected for review explicitly",
            ),
            check(details, "candidate memory awaiting review" in messages_before, "doctor reports review queue"),
            check(details, promoted["status"] == "active", "promotion makes candidate active"),
            check(details, "reviewed" in promoted.get("tags", []), "promotion marks reviewed"),
            check(details, "candidate" not in promoted.get("tags", []), "promotion clears candidate tag"),
            check(details, "proposed before" in briefing_after, "promoted memory enters briefing"),
            check(
                details,
                [item["record"]["id"] for item in selected_after] == ["pref-candidate-review"],
                "promoted memory enters targeted selection",
            ),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="Agent-proposed memory stays in a review queue until promotion.",
        passed=passed,
        details=details,
    )


def scenario_memory_update_supersession(base: Path) -> ScenarioResult:
    name = "memory-update-supersession"
    details: list[str] = []
    state = core.default_state()
    core.update_meta(
        state,
        objective="Check that updated preferences do not conflict during handoff.",
        summary="Supersession should keep old memory visible for audit but out of startup context.",
        next_actions=["Use the newest preference and ignore superseded guidance."],
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-old-style",
        text="User prefers exhaustive status reports with every internal detail.",
        confidence="high",
        salience=5,
        evidence="Older preference.",
        scope="user",
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-bad-style",
        text="User prefers concise direct status reports.",
        confidence="high",
        salience=5,
        evidence="Newer correction.",
        scope="user",
        supersedes=["pref-old-style"],
    )
    before_messages = issue_messages(core.audit_state(state))
    state["user_profile"]["preferences"].pop()
    replacement = core.supersede_record(
        state,
        collection="preferences",
        record_id="pref-new-style",
        text="User prefers concise direct status reports.",
        replaces=["pref-old-style"],
        confidence="high",
        salience=5,
        evidence="User corrected the old preference.",
        scope="user",
    )
    after_messages = issue_messages(core.audit_state(state))
    briefing = core.render_briefing(state)
    selected = core.select_memory_records(state, query="status reports", collections=["preferences"])
    packet = core.render_packet(state)

    passed = all(
        [
            check(
                details,
                "superseded record should be stale or superseded: pref-old-style" in before_messages,
                "doctor flags a replacement that leaves old memory active",
            ),
            check(details, replacement["supersedes"] == ["pref-old-style"], "replacement records superseded ids"),
            check(details, state["user_profile"]["preferences"][0]["status"] == "superseded", "old preference is marked superseded"),
            check(
                details,
                "superseded record should be stale or superseded: pref-old-style" not in after_messages,
                "supersede helper clears active-old-memory warning",
            ),
            check(details, "concise direct status reports" in briefing, "briefing includes the replacement preference"),
            check(details, "exhaustive status reports" not in briefing, "briefing excludes superseded preference"),
            check(details, [item["record"]["id"] for item in selected] == ["pref-new-style"], "selection returns the active replacement only"),
            check(details, "status: superseded" in packet, "full packet keeps audit visibility for superseded memory"),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="Updated preferences supersede old guidance so startup context does not contain conflicting memory.",
        passed=passed,
        details=details,
    )


def scenario_opening_plan_preservation(base: Path) -> ScenarioResult:
    name = "opening-plan-preservation"
    details: list[str] = []
    memory_dir = base / name
    state = core.default_state()
    core.update_meta(
        state,
        objective="Preserve a complex coding plan for a future agent.",
        summary="Opening plans should survive handoff as explicit artifacts.",
        next_actions=["Read the captured plan before implementation."],
    )
    captured = core.capture_plan_artifact(
        memory_dir,
        state,
        plan_id="plan-opening",
        title="Opening Agent Plan",
        body=(
            "## Phase 1\n\n"
            "Requirement: inspect the repository and confirm the goal.\n\n"
            "Validation: run behavior scenarios.\n\n"
            "## Phase 2\n\n"
            "Requirement: implement only after the plan is clear.\n\n"
            "Validation: run release validation."
        ),
        evidence="Complex coding-agent workflow requires saved phase plan and validation gates.",
        next_actions=["Run behavior scenarios after phase 1."],
    )
    write_state(memory_dir, state)
    report = core.prepare_handoff_artifacts(memory_dir, state)
    briefing = (memory_dir / core.BRIEFING_FILE).read_text(encoding="utf-8")
    packet = (memory_dir / core.PACKET_FILE).read_text(encoding="utf-8")
    plan_text = captured["path"].read_text(encoding="utf-8")

    passed = all(
        [
            check(details, captured["path"].exists(), "plan artifact file is persisted"),
            check(details, "Validation: run release validation." in plan_text, "plan file preserves validation gates"),
            check(details, state["project"]["artifacts"][0]["id"] == "plan-opening", "plan is registered as an artifact record"),
            check(details, "opening-plan" in state["project"]["artifacts"][0]["tags"], "plan artifact is tagged for startup"),
            check(
                details,
                "Follow opening plan artifact before implementation: plans/plan-opening.md" in briefing,
                "briefing points the next agent to the plan first",
            ),
            check(details, "Opening Agent Plan (plans/plan-opening.md)" in packet, "migration packet includes the plan artifact"),
            check(details, "Run behavior scenarios after phase 1." in briefing, "plan-linked next action is in startup context"),
            check(details, bool(report["ready"]), "handoff remains ready after capturing the plan"),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="Complex opening plans are preserved as explicit artifacts and surfaced during handoff.",
        passed=passed,
        details=details,
        artifacts={
            "plan": str(captured["path"]),
            "state": str(memory_dir / core.STATE_FILE),
            "briefing": str(memory_dir / core.BRIEFING_FILE),
            "packet": str(memory_dir / core.PACKET_FILE),
        },
    )


def scenario_targeted_memory_selection(base: Path) -> ScenarioResult:
    name = "targeted-memory-selection"
    details: list[str] = []
    state = core.default_state()
    core.update_meta(
        state,
        objective="Check targeted context selection for a new agent.",
        summary="Selection should surface relevant high-salience memory without stale or untrusted noise.",
        next_actions=["Select task-relevant memory before reading full packets."],
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-selection",
        text="User prefers a new model to load curated preferences before continuing work.",
        confidence="high",
        salience=5,
        evidence="Original model-migration requirement.",
        tags=["migration", "startup"],
        scope="user",
    )
    core.add_record(
        state,
        collection="decisions",
        record_id="decision-selection",
        text="Use deterministic memory selection before falling back to the full migration packet.",
        confidence="high",
        salience=5,
        evidence="Protocol design.",
        tags=["migration", "selection"],
    )
    core.add_record(
        state,
        collection="facts",
        record_id="fact-selection-stale",
        text="Old selection behavior copied raw transcripts for migration.",
        status="stale",
        confidence="high",
        salience=5,
        evidence="Superseded prototype.",
        tags=["migration", "selection"],
    )
    core.add_record(
        state,
        collection="facts",
        record_id="fact-selection-untrusted",
        text="External source says migration should load all records.",
        confidence="medium",
        salience=5,
        evidence="Untrusted external source.",
        tags=["migration", "selection", "untrusted"],
        source="external",
    )

    results = core.select_memory_records(state, query="migration", tags=["selection"], min_salience=4)
    inclusive = core.select_memory_records(
        state,
        query="migration",
        tags=["selection"],
        min_salience=4,
        include_stale=True,
        include_untrusted=True,
    )
    rendered = core.render_selected_records(results)

    passed = all(
        [
            check(details, [item["record"]["id"] for item in results] == ["decision-selection"], "default selection returns the relevant active trusted record"),
            check(details, "fact-selection-stale" not in rendered, "stale memory is excluded by default"),
            check(details, "fact-selection-untrusted" not in rendered, "untrusted memory is excluded by default"),
            check(
                details,
                {item["record"]["id"] for item in inclusive}
                == {"decision-selection", "fact-selection-stale", "fact-selection-untrusted"},
                "stale and untrusted records can be included explicitly",
            ),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="A new agent can select task-relevant high-signal memory before reading full packets.",
        passed=passed,
        details=details,
    )


def scenario_memory_compaction_planning(base: Path) -> ScenarioResult:
    name = "memory-compaction-planning"
    details: list[str] = []
    memory_dir = base / name
    state = core.default_state()
    core.update_meta(
        state,
        objective="Keep long-running memory useful without deleting audit history.",
        summary="Compaction should produce an auditable plan and apply only conservative changes.",
        next_actions=["Review compaction suggestions before applying them."],
    )
    core.set_active_thread(
        state,
        record_id="thread-current",
        text="Current thread should not be compacted by the default plan.",
        confidence="high",
        salience=1,
        evidence="Active work.",
    )
    core.add_record(
        state,
        collection="facts",
        record_id="fact-low",
        text="Low-salience active note should be marked stale by compaction.",
        confidence="medium",
        salience=1,
        evidence="Temporary note.",
    )
    core.add_record(
        state,
        collection="decisions",
        record_id="decision-keep",
        text="High-salience decision stays active during compaction.",
        confidence="high",
        salience=5,
        evidence="Important decision.",
    )
    core.add_record(
        state,
        collection="closed-threads",
        record_id="thread-closed-1",
        text="Older closed thread should be reviewed manually before forgetting.",
        status="closed",
        confidence="medium",
        salience=2,
        evidence="Closed thread fixture.",
    )
    core.add_record(
        state,
        collection="closed-threads",
        record_id="thread-closed-2",
        text="Another closed thread should remain available until reviewed.",
        status="closed",
        confidence="medium",
        salience=2,
        evidence="Closed thread fixture.",
    )

    plan = core.compact_state_plan(state, min_salience=3, max_closed_recently=1)
    rendered = core.render_compaction_plan(plan)
    result = core.apply_compaction_plan(state, plan)
    write_state(memory_dir, state)
    briefing = (memory_dir / core.BRIEFING_FILE).read_text(encoding="utf-8")

    passed = all(
        [
            check(details, plan["summary"]["auto_apply"] == 1, "plan has one auto-applicable stale suggestion"),
            check(details, plan["summary"]["review_only"] == 1, "plan keeps closed-thread cleanup as review-only"),
            check(details, "fact-low" in rendered, "rendered plan includes the low-salience record"),
            check(details, "thread-current" not in rendered, "default plan skips the active thread"),
            check(details, result["applied"][0]["id"] == "fact-low", "apply marks the low-salience record stale"),
            check(details, state["project"]["facts"][0]["status"] == "stale", "low-salience record is stale after apply"),
            check(details, "compacted" in state["project"]["facts"][0]["tags"], "applied record gets compaction tag"),
            check(details, state["decisions"][0]["status"] == "active", "high-salience decision remains active"),
            check(details, len(state["threads"]["closed_recently"]) == 2, "review-only closed threads are not deleted"),
            check(details, "Low-salience active note" not in briefing, "stale compacted memory is excluded from briefing"),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="Compaction produces a reviewable plan and only applies conservative stale-status changes.",
        passed=passed,
        details=details,
        artifacts={
            "state": str(memory_dir / core.STATE_FILE),
            "briefing": str(memory_dir / core.BRIEFING_FILE),
            "packet": str(memory_dir / core.PACKET_FILE),
        },
    )


def scenario_topic_interruption(base: Path) -> ScenarioResult:
    name = "topic-interruption-resume"
    details: list[str] = []
    state = core.default_state()
    core.update_meta(
        state,
        objective="Check interruption handling and return-to-main-topic behavior.",
        summary="A side idea should be remembered without losing the main thread.",
        next_actions=["Resume the main thread after a closure cue."],
    )
    core.set_active_thread(
        state,
        record_id="thread-main",
        text="Design the memory skill release plan.",
        confidence="high",
        salience=5,
        evidence="Main topic before interruption.",
    )
    episode, side_thread = core.interrupt_thread(
        state,
        episode_id="episode-side-idea",
        episode_text="User proposed adding online pain-point coverage to the roadmap.",
        thread_id="thread-side-idea",
        thread_text="Capture new pain points and map them to requirements.",
        confidence="high",
        salience=5,
        evidence="Side idea during release planning.",
    )
    cue = core.detect_topic_cue(state, "back to the previous topic")
    if cue["action"] == "resume":
        resumed = core.resume_thread(state, current_destination="closed")
    else:
        resumed = None

    threads = state["threads"]
    passed = all(
        [
            check(details, episode["id"] == "episode-side-idea", "side episode is recorded"),
            check(details, side_thread["id"] == "thread-side-idea", "side thread becomes active during interruption"),
            check(details, cue["action"] == "resume", "explicit return cue asks to resume the parked topic"),
            check(details, bool(resumed) and resumed["id"] == "thread-main", "main topic is restored as active"),
            check(
                details,
                any(thread.get("id") == "thread-side-idea" for thread in threads["closed_recently"]),
                "side thread is closed recently after resume",
            ),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="A side topic can be stored, closed, and followed by automatic return to the main thread.",
        passed=passed,
        details=details,
    )


def scenario_memory_safety_review(base: Path) -> ScenarioResult:
    name = "memory-safety-review"
    details: list[str] = []
    state = core.default_state()
    core.update_meta(
        state,
        objective="Check that questionable memory is reviewed before reuse.",
        summary="External high-impact memory should not silently enter startup context.",
        next_actions=["Review external memory before trusting it."],
    )
    core.add_record(
        state,
        collection="facts",
        record_id="fact-external",
        text="External source reports a compatibility note for memory adapters.",
        confidence="high",
        salience=5,
        evidence="Unverified external page.",
        tags=["untrusted"],
        source="external",
    )

    before = core.audit_state(state)
    before_messages = issue_messages(before)
    before_briefing = core.render_briefing(state)
    core.update_record(
        state,
        record_id="fact-external",
        add_tags=["reviewed"],
        remove_tags=["untrusted"],
        evidence="Reviewed against current project files.",
    )
    after = core.audit_state(state)
    after_messages = issue_messages(after)
    after_briefing = core.render_briefing(state)

    passed = all(
        [
            check(
                details,
                "high-impact memory from a non-user source should be reviewed before reuse" in before_messages,
                "doctor flags high-impact non-user memory before review",
            ),
            check(
                details,
                "untrusted memory should not remain active without review" in before_messages,
                "doctor flags active untrusted memory",
            ),
            check(
                details,
                "compatibility note for memory adapters" not in before_briefing,
                "untrusted memory is excluded from briefing before review",
            ),
            check(
                details,
                "high-impact memory from a non-user source should be reviewed before reuse" not in after_messages,
                "reviewed non-user memory clears high-impact warning",
            ),
            check(
                details,
                "untrusted memory should not remain active without review" not in after_messages,
                "trusted review clears untrusted warning",
            ),
            check(
                details,
                "compatibility note for memory adapters" in after_briefing,
                "reviewed memory can enter briefing",
            ),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="Memory doctor prevents untrusted external records from becoming durable guidance too early.",
        passed=passed,
        details=details,
    )


def scenario_sensitive_memory_redaction(base: Path) -> ScenarioResult:
    name = "sensitive-memory-redaction"
    details: list[str] = []
    memory_dir = base / name
    secret = "SECRET_TOKEN_12345"
    state = core.default_state()
    core.update_meta(
        state,
        objective="Check that sensitive memory can be removed from durable artifacts.",
        summary="A redaction flow should replace sensitive text and refresh generated handoff files.",
        next_actions=["Use redaction before sharing memory artifacts."],
    )
    core.add_record(
        state,
        collection="facts",
        record_id="fact-secret",
        text=f"Temporary credential {secret} was accidentally stored.",
        confidence="high",
        salience=5,
        evidence=f"Tool output included {secret}.",
        source="tool",
    )
    write_state(memory_dir, state)
    before_packet = (memory_dir / core.PACKET_FILE).read_text(encoding="utf-8")
    core.redact_record(state, record_id="fact-secret")
    write_state(memory_dir, state)
    after_state = (memory_dir / core.STATE_FILE).read_text(encoding="utf-8")
    after_briefing = (memory_dir / core.BRIEFING_FILE).read_text(encoding="utf-8")
    after_packet = (memory_dir / core.PACKET_FILE).read_text(encoding="utf-8")
    record = state["project"]["facts"][0]

    passed = all(
        [
            check(details, secret in before_packet, "scenario starts with sensitive text in an artifact"),
            check(details, secret not in after_state, "state.json no longer contains the sensitive text"),
            check(details, secret not in after_briefing, "memory briefing no longer contains the sensitive text"),
            check(details, secret not in after_packet, "migration packet no longer contains the sensitive text"),
            check(details, record["text"] == "[redacted sensitive memory]", "record text is replaced with a safe placeholder"),
            check(details, record["evidence"] == "Sensitive memory redacted.", "record evidence is replaced with safe evidence"),
            check(details, record["status"] == "stale", "redacted record is stale by default"),
            check(details, "redacted" in record["tags"] and "reviewed" in record["tags"], "record keeps redacted and reviewed tags"),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="Sensitive memory can be redacted from state and regenerated handoff artifacts.",
        passed=passed,
        details=details,
        artifacts={
            "state": str(memory_dir / core.STATE_FILE),
            "briefing": str(memory_dir / core.BRIEFING_FILE),
            "packet": str(memory_dir / core.PACKET_FILE),
        },
    )


def scenario_memory_forget_control(base: Path) -> ScenarioResult:
    name = "memory-forget-control"
    details: list[str] = []
    memory_dir = base / name
    forgotten_text = "Temporary preference that the user revoked."
    state = core.default_state()
    core.update_meta(
        state,
        objective="Check that a user can remove an unwanted memory record.",
        summary="Forgetting should remove a record and refresh generated handoff files.",
        next_actions=["Use forget when the user asks not to retain a memory."],
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-temp",
        text=forgotten_text,
        confidence="medium",
        salience=4,
        evidence="Temporary user preference.",
        scope="user",
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-current",
        text="Current durable preference remains available.",
        confidence="high",
        salience=5,
        evidence="User confirmed this preference.",
        scope="user",
        supersedes=["pref-temp"],
    )
    write_state(memory_dir, state)
    before_packet = (memory_dir / core.PACKET_FILE).read_text(encoding="utf-8")
    path, removed = core.delete_record(state, "pref-temp")
    write_state(memory_dir, state)
    after_state = (memory_dir / core.STATE_FILE).read_text(encoding="utf-8")
    after_briefing = (memory_dir / core.BRIEFING_FILE).read_text(encoding="utf-8")
    after_packet = (memory_dir / core.PACKET_FILE).read_text(encoding="utf-8")
    current = state["user_profile"]["preferences"][0]
    issues = [issue for issue in core.audit_state(state) if issue["severity"] in {"error", "warning"}]

    passed = all(
        [
            check(details, forgotten_text in before_packet, "scenario starts with the revoked memory in an artifact"),
            check(details, path == "user_profile.preferences[0]", "forget locates the revoked preference"),
            check(details, removed["id"] == "pref-temp", "forget removes the requested record id"),
            check(details, forgotten_text not in after_state, "state.json no longer contains the forgotten text"),
            check(details, forgotten_text not in after_briefing, "memory briefing no longer contains the forgotten text"),
            check(details, forgotten_text not in after_packet, "migration packet no longer contains the forgotten text"),
            check(details, current["id"] == "pref-current", "unrelated durable memory remains"),
            check(details, "supersedes" not in current, "supersedes references to forgotten memory are cleaned up"),
            check(details, not issues, "doctor has no warning/error issues after forgetting"),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="A user can remove revoked memory while preserving unrelated durable memory.",
        passed=passed,
        details=details,
        artifacts={
            "state": str(memory_dir / core.STATE_FILE),
            "briefing": str(memory_dir / core.BRIEFING_FILE),
            "packet": str(memory_dir / core.PACKET_FILE),
        },
    )


def scenario_multi_agent_separation(base: Path) -> ScenarioResult:
    name = "multi-agent-separation"
    details: list[str] = []
    memory_base = base / name
    multi_agent.ensure_multi_agent_dir(memory_base)
    multi_agent.ensure_role(memory_base, "planner")
    multi_agent.ensure_role(memory_base, "researcher")
    multi_agent.checkpoint_shared(
        memory_base,
        objective="Coordinate a multi-agent memory release task.",
        summary="Shared memory carries confirmed decisions; role memory carries local findings.",
        next_actions=["Read shared decisions before role-local notes."],
    )
    for role in ["planner", "researcher"]:
        role_dir = multi_agent.role_dir(memory_base, role)
        role_state = core.load_state(role_dir)
        core.update_meta(
            role_state,
            objective=f"Preserve {role} role-local memory.",
            summary=f"{role} keeps local context separate from shared decisions.",
            next_actions=[f"Use {role} memory only for {role} responsibilities."],
        )
        multi_agent.save_state(role_dir, role_state)

    multi_agent.record_shared_decision(
        memory_base,
        record_id="decision-shared",
        text="Only confirmed cross-role decisions belong in shared memory.",
        evidence="Multi-agent memory policy.",
        confidence="high",
        salience=5,
        role="planner",
    )
    multi_agent.record_role_memory(
        memory_base,
        role="researcher",
        kind="fact",
        record_id="fact-researcher",
        text="Researcher found that role-local notes reduce premature consensus.",
        evidence="Evaluation scenario.",
        confidence="high",
        salience=5,
    )
    multi_agent.record_role_memory(
        memory_base,
        role="planner",
        kind="artifact",
        record_id="artifact-planner",
        text="Planner owns the release checklist artifact.",
        evidence="Evaluation scenario.",
        confidence="high",
        salience=4,
    )

    report = multi_agent.prepare_handoff(memory_base)
    note = multi_agent.build_orchestration_note(memory_base)
    shared_state = core.load_state(memory_base / "shared")
    researcher_state = core.load_state(memory_base / "roles" / "researcher")
    planner_state = core.load_state(memory_base / "roles" / "planner")
    shared_text = json.dumps(shared_state, ensure_ascii=False)
    researcher_text = json.dumps(researcher_state, ensure_ascii=False)
    planner_text = json.dumps(planner_state, ensure_ascii=False)

    passed = all(
        [
            check(details, bool(report["ready"]), "multi-agent handoff reports ready"),
            check(details, warning_or_error_count(report["issues"]) == 0, "multi-agent handoff has no warning/error issues"),
            check(details, "Only confirmed cross-role decisions" in shared_text, "shared decision is in shared memory"),
            check(details, "Researcher found" not in shared_text, "researcher local fact is not copied into shared memory"),
            check(details, "Researcher found" in researcher_text, "researcher fact stays role-local"),
            check(details, "Only confirmed cross-role decisions" not in researcher_text, "shared decision is not duplicated into researcher memory"),
            check(details, "Planner owns the release checklist" in planner_text, "planner artifact stays role-local"),
            check(
                details,
                contains_all(note, ["Only confirmed cross-role decisions", "Researcher found", "Planner owns"]),
                "orchestration note presents shared and role-local memory without merging storage",
            ),
        ]
    )
    return ScenarioResult(
        name=name,
        summary="Shared decisions and role-local memories remain separate while still producing a handoff note.",
        passed=passed,
        details=details,
        artifacts={
            "note": str(memory_base / multi_agent.NOTE_FILE),
            "shared_state": str(memory_base / "shared" / core.STATE_FILE),
            "planner_state": str(memory_base / "roles" / "planner" / core.STATE_FILE),
            "researcher_state": str(memory_base / "roles" / "researcher" / core.STATE_FILE),
        },
    )


SCENARIOS: tuple[Callable[[Path], ScenarioResult], ...] = (
    scenario_model_handoff,
    scenario_portable_bundle_roundtrip,
    scenario_preference_filtering,
    scenario_memory_candidate_review,
    scenario_memory_update_supersession,
    scenario_opening_plan_preservation,
    scenario_targeted_memory_selection,
    scenario_memory_compaction_planning,
    scenario_topic_interruption,
    scenario_memory_safety_review,
    scenario_sensitive_memory_redaction,
    scenario_memory_forget_control,
    scenario_multi_agent_separation,
)


def run_evaluations(base: Path) -> list[ScenarioResult]:
    base.mkdir(parents=True, exist_ok=True)
    return [scenario(base) for scenario in SCENARIOS]


def prepare_output_dir(path: Path, *, force: bool) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.exists():
        if not force:
            raise FileExistsError(f"{resolved} already exists; pass --force to replace it")
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)
    return resolved


def print_human(results: list[ScenarioResult], base: Path) -> None:
    print("Agent memory scenario evaluation")
    print(f"Artifacts: {base}")
    print("")
    for result in results:
        status = "OK" if result.passed else "FAIL"
        print(f"{status} {result.name} - {result.summary}")
        if not result.passed:
            for detail in result.details:
                print(f"  {detail}")
    print("")
    if all(result.passed for result in results):
        print("All memory scenarios passed.")
    else:
        print("One or more memory scenarios failed.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Agent Memory behavior-level scenarios.")
    parser.add_argument(
        "--path",
        help="Optional directory for scenario artifacts. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace --path if it already exists.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable evaluation results.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.path:
        base = prepare_output_dir(Path(args.path), force=args.force)
        results = run_evaluations(base)
        if args.json:
            print(json.dumps({"base": str(base), "results": [result.as_dict() for result in results]}, indent=2))
        else:
            print_human(results, base)
    else:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / "agent-memory-eval"
            results = run_evaluations(base)
            if args.json:
                print(json.dumps({"base": str(base), "results": [result.as_dict() for result in results]}, indent=2))
            else:
                print_human(results, base)
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
