#!/usr/bin/env python3
"""Run a small end-to-end Agent Memory flow."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_memory import core


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def prepare_output_dir(memory_dir: Path, *, force: bool = False) -> None:
    if memory_dir.exists():
        if not force:
            raise FileExistsError(f"memory directory already exists: {memory_dir}; use --force to replace it")
        if not memory_dir.is_dir():
            raise ValueError(f"refusing to replace non-directory path: {memory_dir}")
        shutil.rmtree(memory_dir)
    memory_dir.mkdir(parents=True, exist_ok=True)


def build_demo_state() -> dict[str, Any]:
    state = core.default_state()
    core.update_meta(
        state,
        project_name="Agent Memory End-to-End Demo",
        objective="Show preference transfer, topic interruption recovery, and model handoff.",
        summary=(
            "The demo stores a durable user preference, parks the main topic for a side idea, "
            "resumes the main topic, and prepares handoff artifacts."
        ),
        next_actions=["Read memory-briefing.md first, then migration-packet.md for detail."],
        risks=["Do not copy the transcript; use curated high-salience memory records."],
        handoff_notes=["The side idea is preserved as an episode even after the main topic resumes."],
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-demo-concise-zh",
        text="User prefers concise Chinese progress updates with concrete next steps.",
        confidence="high",
        salience=5,
        evidence="Demo setup based on the project objective.",
        scope="user",
    )
    core.set_active_thread(
        state,
        record_id="thread-main",
        text="Design the model migration memory protocol.",
        confidence="high",
        salience=5,
        evidence="Main demo objective.",
    )
    core.interrupt_thread(
        state,
        episode_id="episode-side-idea",
        episode_text="User raised a side idea: small interruptions should be remembered for later recall.",
        thread_id="thread-side",
        thread_text="Explore how to remember side ideas without losing the main topic.",
        confidence="high",
        salience=5,
        evidence="Side idea introduced during the main topic.",
        tags=["side-idea", "topic-stack"],
    )
    return state


def run_demo(memory_dir: Path, *, force: bool = False) -> dict[str, Any]:
    prepare_output_dir(memory_dir, force=force)
    state = build_demo_state()

    cue = core.detect_topic_cue(state, "back to the previous topic")
    require(cue["action"] == "resume", f"expected resume cue, got {cue['action']}")
    resumed = core.resume_thread(state, current_destination="closed")
    require(resumed["id"] == "thread-main", "main topic did not resume")

    core.write_state(memory_dir, state)
    report = core.prepare_handoff_artifacts(memory_dir, state)
    require(report["ready"], "handoff report is not ready")
    require(not report["issues"], "demo memory should not have handoff issues")

    final_state = core.load_state(memory_dir)
    require(final_state["threads"]["active"]["id"] == "thread-main", "active topic should be thread-main")
    require(final_state["threads"]["closed_recently"][0]["id"] == "thread-side", "side topic should be closed")
    require(final_state["episodes"][0]["id"] == "episode-side-idea", "side episode was not stored")

    briefing = (memory_dir / core.BRIEFING_FILE).read_text(encoding="utf-8")
    packet = (memory_dir / core.PACKET_FILE).read_text(encoding="utf-8")
    require("User prefers concise Chinese progress updates" in briefing, "briefing missing user preference")
    require("small interruptions should be remembered" in packet, "packet missing side episode")
    return report


def print_report(report: dict[str, Any]) -> None:
    print("Agent Memory demo completed.")
    print(f"- State: {report['state']}")
    print(f"- Briefing: {report['briefing']}")
    print(f"- Packet: {report['packet']}")
    print("- Demonstrated: preference transfer, topic interruption recovery, handoff readiness")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an end-to-end Agent Memory demo.")
    parser.add_argument("--path", help="memory directory to write; defaults to a temporary directory")
    parser.add_argument("--force", action="store_true", help="replace an existing demo memory directory")
    parser.add_argument("--keep", action="store_true", help="keep the temporary directory when --path is omitted")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.path:
        try:
            report = run_demo(Path(args.path).expanduser().resolve(), force=args.force)
        except (FileExistsError, RuntimeError, ValueError) as exc:
            print(f"ERROR: {exc}")
            return 1
        print_report(report)
        return 0

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        memory_dir = Path(temp) / "agent-memory-demo"
        try:
            report = run_demo(memory_dir, force=True)
        except (FileExistsError, RuntimeError, ValueError) as exc:
            print(f"ERROR: {exc}")
            return 1
        print_report(report)
        if args.keep:
            kept = Path.cwd() / ".tmp-agent-memory-demo"
            if kept.exists():
                shutil.rmtree(kept)
            shutil.copytree(memory_dir, kept)
            print(f"- Kept copy: {kept}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
