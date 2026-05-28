#!/usr/bin/env python3
"""Run open-source release checks without local Codex-only dependencies."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "agent-memory"
FORBIDDEN_SKILL_FILES = {
    "README.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
}
REQUIRED_ROOT_FILES = (
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "ROADMAP.md",
    "pyproject.toml",
    "MANIFEST.in",
    "docs/adapter-contract.md",
    "docs/existing-agent-integration.md",
    "docs/privacy-and-safety.md",
    "docs/opening-plans.md",
    "docs/memory-candidates.md",
    "docs/memory-selection.md",
    "docs/memory-updates.md",
    "docs/memory-compaction.md",
    "docs/portable-bundles.md",
    "scripts/demo_memory_flow.py",
    "scripts/evaluate_memory_scenarios.py",
    "scripts/install_skill.py",
    ".github/workflows/ci.yml",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/pull_request_template.md",
)
REQUIRED_PYPROJECT_STRINGS = (
    'name = "agent-memory-skill"',
    'requires-python = ">=3.10"',
    'agent-memory = "agent_memory.cli:main"',
    'agent-memory-chat = "agent_memory.adapters.chat:main"',
    'agent-memory-agent = "agent_memory.adapters.agent:main"',
    'agent-memory-codex = "agent_memory.adapters.codex:main"',
    'agent-memory-multi = "agent_memory.adapters.multi_agent:main"',
)
REQUIRED_MANIFEST_STRINGS = (
    "recursive-include agent-memory *",
    "recursive-include docs *.md",
    "recursive-include examples *",
    "recursive-include schemas *.json",
    "recursive-include scripts *.py",
    "recursive-include tests *.py",
)
REQUIRED_README_STRINGS = (
    "python scripts/demo_memory_flow.py",
    "python scripts/evaluate_memory_scenarios.py",
    "python scripts/install_skill.py",
    "python scripts/validate_release.py",
    "SECURITY.md",
    "ROADMAP.md",
    "docs/adapter-contract.md",
    "docs/existing-agent-integration.md",
    "docs/privacy-and-safety.md",
    "docs/opening-plans.md",
    "docs/memory-candidates.md",
    "docs/memory-updates.md",
    "python -m agent_memory handoff",
    "python -m agent_memory plan",
    "python -m agent_memory propose",
    "python -m agent_memory promote",
    "python -m agent_memory select",
    "python -m agent_memory supersede",
    "python -m agent_memory compact",
    "python -m agent_memory export",
    "python -m agent_memory import",
    "python -m agent_memory redact",
    "python -m agent_memory forget",
    "python -m agent_memory.adapters.codex handoff",
    "python -m agent_memory.adapters.chat handoff",
    "python -m agent_memory.adapters.agent handoff",
    "python -m agent_memory.adapters.multi_agent handoff",
)
REQUIRED_SECURITY_STRINGS = (
    "Do not paste secrets",
    "memory poisoning",
    "Use `redact`",
    "Use `forget`",
    "The core package stores local files",
)
REQUIRED_PRIVACY_STRINGS = (
    "Do not store",
    "python -m agent_memory redact",
    "python -m agent_memory forget",
    "python -m agent_memory export",
    "agent-memory-export.json",
    "Source And Scope",
    "Adapter Responsibilities",
    "Publishing Examples",
)
REQUIRED_ROADMAP_STRINGS = (
    "V0.1: Local Protocol Prototype",
    "V0.2: Adapter Hardening",
    "Non-Goals For Now",
)
REQUIRED_ADAPTER_CONTRACT_STRINGS = (
    "Required Behavior",
    "Read Path",
    "Write Path",
    "Privacy And Consent",
    "Existing Agent Integration",
    "Test Requirements",
    "forgetting removes",
    "export/import roundtrips",
    "opening plan",
    "targeted selection excludes",
    "supersession",
)
REQUIRED_EXISTING_AGENT_STRINGS = (
    "sidecar",
    "Do not overwrite",
    "candidate",
    "Rollback",
    "python -m agent_memory handoff",
)
REQUIRED_BUNDLE_STRINGS = (
    "agent-memory-bundle",
    "python -m agent_memory export",
    "python -m agent_memory import",
    "Import validates",
    "Migration Workflow",
)
REQUIRED_SELECTION_STRINGS = (
    "python -m agent_memory select",
    "Default Filters",
    "Selection Fields",
    "How To Use With Handoff",
)
REQUIRED_CANDIDATE_STRINGS = (
    "python -m agent_memory propose",
    "python -m agent_memory promote",
    "candidate",
    "review",
    "briefing",
)
REQUIRED_OPENING_PLAN_STRINGS = (
    "python -m agent_memory plan",
    "plans/",
    "acceptance criteria",
    "validation",
    "handoff",
)
REQUIRED_UPDATE_STRINGS = (
    "python -m agent_memory supersede",
    "--replaces",
    "superseded",
    "knowledge updates",
    "doctor",
)
REQUIRED_COMPACTION_STRINGS = (
    "python -m agent_memory compact",
    "--apply",
    "review-only",
    "mark-stale",
    "active thread",
)


def add_import_path() -> None:
    root_text = str(ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"OK: {message}")


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0] != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = lines[1:].index("---") + 1
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter must end with ---") from exc
    data: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def check_skill_folder(failures: list[str]) -> None:
    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.exists():
        fail("agent-memory/SKILL.md is missing", failures)
        return

    try:
        metadata = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except ValueError as exc:
        fail(str(exc), failures)
        return

    if metadata.get("name") != "agent-memory":
        fail("SKILL.md frontmatter name must be agent-memory", failures)
    if not metadata.get("description"):
        fail("SKILL.md frontmatter description is required", failures)

    openai_yaml = SKILL_DIR / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        fail("agent-memory/agents/openai.yaml is missing", failures)

    for filename in FORBIDDEN_SKILL_FILES:
        if (SKILL_DIR / filename).exists():
            fail(f"skill folder should not contain {filename}", failures)

    ok("skill folder structure")


def check_project_files(failures: list[str]) -> None:
    for filename in REQUIRED_ROOT_FILES:
        if not (ROOT / filename).exists():
            fail(f"{filename} is missing", failures)

    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for expected in REQUIRED_PYPROJECT_STRINGS:
        if expected not in pyproject_text:
            fail(f"pyproject.toml missing: {expected}", failures)

    manifest_text = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    for expected in REQUIRED_MANIFEST_STRINGS:
        if expected not in manifest_text:
            fail(f"MANIFEST.in missing: {expected}", failures)

    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    for expected in REQUIRED_README_STRINGS:
        if expected not in readme_text:
            fail(f"README.md missing: {expected}", failures)

    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    if "python scripts/validate_release.py" not in ci_text:
        fail("CI must run scripts/validate_release.py", failures)
    ok("project entry files")


def check_security_docs(failures: list[str]) -> None:
    security_text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    for expected in REQUIRED_SECURITY_STRINGS:
        if expected not in security_text:
            fail(f"SECURITY.md missing: {expected}", failures)

    privacy_text = (ROOT / "docs" / "privacy-and-safety.md").read_text(encoding="utf-8")
    for expected in REQUIRED_PRIVACY_STRINGS:
        if expected not in privacy_text:
            fail(f"docs/privacy-and-safety.md missing: {expected}", failures)

    bug_template = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md").read_text(encoding="utf-8")
    if "SECURITY.md" not in bug_template:
        fail("bug report template must point sensitive reports to SECURITY.md", failures)

    pr_template = (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
    if "whether memory can leave the local machine" not in pr_template:
        fail("pull request template must ask about memory storage and sharing", failures)

    ok("security and privacy docs")


def check_project_direction_docs(failures: list[str]) -> None:
    roadmap_text = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    for expected in REQUIRED_ROADMAP_STRINGS:
        if expected not in roadmap_text:
            fail(f"ROADMAP.md missing: {expected}", failures)

    contract_text = (ROOT / "docs" / "adapter-contract.md").read_text(encoding="utf-8")
    for expected in REQUIRED_ADAPTER_CONTRACT_STRINGS:
        if expected not in contract_text:
            fail(f"docs/adapter-contract.md missing: {expected}", failures)

    existing_agent_text = (ROOT / "docs" / "existing-agent-integration.md").read_text(encoding="utf-8")
    for expected in REQUIRED_EXISTING_AGENT_STRINGS:
        if expected not in existing_agent_text:
            fail(f"docs/existing-agent-integration.md missing: {expected}", failures)

    feature_template = (ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.md").read_text(encoding="utf-8")
    if "docs/adapter-contract.md" not in feature_template:
        fail("feature request template must mention adapter contract for runtime adapter requests", failures)

    pr_template = (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
    if "docs/adapter-contract.md" not in pr_template:
        fail("pull request template must mention adapter contract", failures)

    ok("roadmap and adapter contract docs")


def check_portable_bundle_docs(failures: list[str]) -> None:
    bundle_text = (ROOT / "docs" / "portable-bundles.md").read_text(encoding="utf-8")
    for expected in REQUIRED_BUNDLE_STRINGS:
        if expected not in bundle_text:
            fail(f"docs/portable-bundles.md missing: {expected}", failures)

    gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    if "agent-memory-export.json" not in gitignore_text:
        fail(".gitignore should exclude agent-memory-export.json", failures)

    ok("portable bundle docs")


def check_selection_docs(failures: list[str]) -> None:
    selection_text = (ROOT / "docs" / "memory-selection.md").read_text(encoding="utf-8")
    for expected in REQUIRED_SELECTION_STRINGS:
        if expected not in selection_text:
            fail(f"docs/memory-selection.md missing: {expected}", failures)
    ok("memory selection docs")


def check_candidate_docs(failures: list[str]) -> None:
    candidate_text = (ROOT / "docs" / "memory-candidates.md").read_text(encoding="utf-8")
    for expected in REQUIRED_CANDIDATE_STRINGS:
        if expected not in candidate_text:
            fail(f"docs/memory-candidates.md missing: {expected}", failures)
    ok("memory candidate docs")


def check_opening_plan_docs(failures: list[str]) -> None:
    plan_text = (ROOT / "docs" / "opening-plans.md").read_text(encoding="utf-8")
    for expected in REQUIRED_OPENING_PLAN_STRINGS:
        if expected not in plan_text:
            fail(f"docs/opening-plans.md missing: {expected}", failures)
    ok("opening plan docs")


def check_update_docs(failures: list[str]) -> None:
    update_text = (ROOT / "docs" / "memory-updates.md").read_text(encoding="utf-8")
    for expected in REQUIRED_UPDATE_STRINGS:
        if expected not in update_text:
            fail(f"docs/memory-updates.md missing: {expected}", failures)
    ok("memory update docs")


def check_compaction_docs(failures: list[str]) -> None:
    compaction_text = (ROOT / "docs" / "memory-compaction.md").read_text(encoding="utf-8")
    for expected in REQUIRED_COMPACTION_STRINGS:
        if expected not in compaction_text:
            fail(f"docs/memory-compaction.md missing: {expected}", failures)
    ok("memory compaction docs")


def check_schema_sync(failures: list[str]) -> None:
    from agent_memory.schema import state_schema

    schema_path = ROOT / "schemas" / "state.schema.json"
    if not schema_path.exists():
        fail("schemas/state.schema.json is missing", failures)
        return
    file_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if file_schema != state_schema():
        fail("schemas/state.schema.json does not match agent_memory.schema.state_schema()", failures)
        return
    ok("schema file matches Python export")


def check_skill_installer(failures: list[str]) -> None:
    script_path = ROOT / "scripts" / "install_skill.py"
    spec = importlib.util.spec_from_file_location("install_skill", script_path)
    if spec is None or spec.loader is None:
        fail("cannot import scripts/install_skill.py", failures)
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory() as temp:
        target_dir = Path(temp) / "skills"
        destination = module.install_skill(target_dir=target_dir)
        if not (destination / "SKILL.md").exists():
            fail("install_skill.py did not copy SKILL.md", failures)
            return
        if not (destination / "agents" / "openai.yaml").exists():
            fail("install_skill.py did not copy agents/openai.yaml", failures)
            return
    ok("skill installer")


def check_demo_runner(failures: list[str]) -> None:
    script_path = ROOT / "scripts" / "demo_memory_flow.py"
    spec = importlib.util.spec_from_file_location("demo_memory_flow", script_path)
    if spec is None or spec.loader is None:
        fail("cannot import scripts/demo_memory_flow.py", failures)
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory() as temp:
        memory_dir = Path(temp) / "demo-memory"
        report = module.run_demo(memory_dir, force=True)
        if not report.get("ready"):
            fail("demo_memory_flow.py did not produce a ready handoff", failures)
            return
        if not (memory_dir / "memory-briefing.md").exists():
            fail("demo_memory_flow.py did not write memory-briefing.md", failures)
            return
        if not (memory_dir / "migration-packet.md").exists():
            fail("demo_memory_flow.py did not write migration-packet.md", failures)
            return
    ok("end-to-end demo runner")


def check_portable_bundle_runner(failures: list[str]) -> None:
    from agent_memory import core

    state = core.default_state()
    core.update_meta(
        state,
        objective="Validate portable bundle release behavior.",
        summary="Portable bundle release check.",
        next_actions=["Import this memory elsewhere."],
    )
    core.add_record(
        state,
        collection="decisions",
        record_id="decision-bundle-release",
        text="Portable bundles carry curated memory between runtimes.",
        confidence="high",
        salience=5,
        evidence="Release validation.",
    )
    bundle = core.build_memory_bundle(state, strict=True)
    restored = core.state_from_memory_bundle(bundle)
    with tempfile.TemporaryDirectory() as temp:
        target = Path(temp) / "imported"
        core.write_state(target, restored)
        core.write_briefing(target, restored)
        core.write_packet(target, restored)
        if not (target / core.BRIEFING_FILE).exists():
            fail("portable bundle import did not write briefing", failures)
            return
        if not (target / core.PACKET_FILE).exists():
            fail("portable bundle import did not write migration packet", failures)
            return
    ok("portable bundle roundtrip")


def check_selection_runner(failures: list[str]) -> None:
    from agent_memory import core

    state = core.default_state()
    core.update_meta(
        state,
        objective="Validate targeted selection release behavior.",
        summary="Selection release check.",
        next_actions=["Select relevant memory."],
    )
    core.add_record(
        state,
        collection="decisions",
        record_id="decision-selection-release",
        text="Targeted selection helps a new agent load only relevant memory.",
        confidence="high",
        salience=5,
        evidence="Release validation.",
        tags=["selection"],
    )
    core.add_record(
        state,
        collection="facts",
        record_id="fact-selection-release-stale",
        text="Old targeted selection behavior loaded transcript noise.",
        status="stale",
        confidence="high",
        salience=5,
        evidence="Old behavior.",
        tags=["selection"],
    )
    selected = core.select_memory_records(state, query="targeted selection", tags=["selection"], min_salience=4)
    if [item["record"]["id"] for item in selected] != ["decision-selection-release"]:
        fail("targeted selection did not exclude stale release fixture", failures)
        return
    ok("targeted memory selection")


def check_candidate_runner(failures: list[str]) -> None:
    from agent_memory import core

    state = core.default_state()
    core.update_meta(
        state,
        objective="Validate candidate memory release behavior.",
        summary="Candidate review release check.",
        next_actions=["Promote confirmed memory only."],
    )
    candidate = core.propose_memory_record(
        state,
        collection="preferences",
        record_id="pref-candidate-release",
        text="User wants proposed memories reviewed before reuse.",
        confidence="medium",
        salience=5,
        source="agent",
        scope="user",
    )
    if candidate.get("status") != "candidate":
        fail("propose_memory_record did not create a candidate", failures)
        return
    if "proposed memories" in core.render_briefing(state):
        fail("candidate memory leaked into default briefing", failures)
        return
    selected = core.select_memory_records(state, query="proposed memories", include_candidates=True)
    if [item["record"]["id"] for item in selected] != ["pref-candidate-release"]:
        fail("candidate memory was not selectable for review", failures)
        return
    _path, promoted = core.promote_memory_record(state, record_id="pref-candidate-release")
    if promoted.get("status") != "active" or "candidate" in promoted.get("tags", []):
        fail("promote_memory_record did not activate and clear candidate metadata", failures)
        return
    if "proposed memories" not in core.render_briefing(state):
        fail("promoted candidate did not enter default briefing", failures)
        return
    ok("candidate memory review")


def check_update_runner(failures: list[str]) -> None:
    from agent_memory import core

    state = core.default_state()
    core.update_meta(
        state,
        objective="Validate memory update release behavior.",
        summary="Supersession release check.",
        next_actions=["Use the newest memory."],
    )
    core.add_record(
        state,
        collection="preferences",
        record_id="pref-update-old",
        text="User prefers long release updates.",
        confidence="high",
        salience=5,
        evidence="Old release fixture.",
        scope="user",
    )
    replacement = core.supersede_record(
        state,
        collection="preferences",
        record_id="pref-update-new",
        text="User prefers concise release updates.",
        replaces=["pref-update-old"],
        confidence="high",
        salience=5,
        evidence="Release validation.",
        scope="user",
    )
    briefing = core.render_briefing(state)
    if replacement.get("supersedes") != ["pref-update-old"]:
        fail("supersede_record did not link replacement to old record", failures)
        return
    if state["user_profile"]["preferences"][0].get("status") != "superseded":
        fail("supersede_record did not mark old record superseded", failures)
        return
    if "long release updates" in briefing or "concise release updates" not in briefing:
        fail("superseded preference leaked into default briefing", failures)
        return
    ok("memory update supersession")


def check_opening_plan_runner(failures: list[str]) -> None:
    from agent_memory import core

    state = core.default_state()
    core.update_meta(
        state,
        objective="Validate opening plan release behavior.",
        summary="Opening plan release check.",
        next_actions=["Read the plan before implementation."],
    )
    with tempfile.TemporaryDirectory() as temp:
        memory_dir = Path(temp) / "memory"
        captured = core.capture_plan_artifact(
            memory_dir,
            state,
            plan_id="plan-release",
            title="Release Opening Plan",
            body="Phase 1: inspect.\nValidation: run tests.",
            evidence="Release validation.",
        )
        core.write_state(memory_dir, state)
        core.write_briefing(memory_dir, state)
        core.write_packet(memory_dir, state)
        briefing = (memory_dir / core.BRIEFING_FILE).read_text(encoding="utf-8")
        packet = (memory_dir / core.PACKET_FILE).read_text(encoding="utf-8")
        if not captured["path"].exists():
            fail("opening plan artifact was not written", failures)
            return
        if "plans/plan-release.md" not in briefing:
            fail("opening plan handoff note missing from briefing", failures)
            return
        if "Release Opening Plan (plans/plan-release.md)" not in packet:
            fail("opening plan artifact missing from migration packet", failures)
            return
    ok("opening plan artifact capture")


def check_compaction_runner(failures: list[str]) -> None:
    from agent_memory import core

    state = core.default_state()
    core.update_meta(
        state,
        objective="Validate compaction release behavior.",
        summary="Compaction release check.",
        next_actions=["Review compaction suggestions."],
    )
    core.set_active_thread(
        state,
        record_id="thread-active-release",
        text="Active low-salience thread should be skipped by default.",
        confidence="medium",
        salience=1,
        evidence="Release validation.",
    )
    core.add_record(
        state,
        collection="facts",
        record_id="fact-compact-release",
        text="Low-salience release fixture should be compacted.",
        confidence="medium",
        salience=1,
        evidence="Release validation.",
    )
    plan = core.compact_state_plan(state, min_salience=3)
    if [item["id"] for item in plan["suggestions"]] != ["fact-compact-release"]:
        fail("compaction plan did not target only the low-salience non-active fixture", failures)
        return
    result = core.apply_compaction_plan(state, plan)
    if result["applied"] != [{"id": "fact-compact-release", "path": "project.facts[0]", "action": "mark-stale"}]:
        fail("compaction apply did not mark the expected record stale", failures)
        return
    if state["project"]["facts"][0]["status"] != "stale":
        fail("compaction apply did not update record status", failures)
        return
    ok("memory compaction planning")


def check_evaluation_runner(failures: list[str]) -> None:
    script_path = ROOT / "scripts" / "evaluate_memory_scenarios.py"
    spec = importlib.util.spec_from_file_location("evaluate_memory_scenarios", script_path)
    if spec is None or spec.loader is None:
        fail("cannot import scripts/evaluate_memory_scenarios.py", failures)
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    expected = {
        "model-handoff-migration",
        "portable-bundle-roundtrip",
        "preference-transfer-filtering",
        "memory-candidate-review",
        "memory-update-supersession",
        "opening-plan-preservation",
        "targeted-memory-selection",
        "memory-compaction-planning",
        "topic-interruption-resume",
        "memory-safety-review",
        "sensitive-memory-redaction",
        "memory-forget-control",
        "multi-agent-separation",
    }
    with tempfile.TemporaryDirectory() as temp:
        results = module.run_evaluations(Path(temp) / "eval")
        names = {result.name for result in results}
        if names != expected:
            fail("evaluate_memory_scenarios.py did not run the expected scenario set", failures)
            return
        failures_found = [result.name for result in results if not result.passed]
        if failures_found:
            fail(f"memory scenario evaluations failed: {', '.join(failures_found)}", failures)
            return
    ok("behavior scenario evaluator")


def run_unittests(failures: list[str]) -> None:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        fail("unit tests failed", failures)
        return
    ok("unit tests")


def issue_count(report: dict[str, Any]) -> int:
    return len([issue for issue in report.get("issues", []) if issue.get("severity") in {"error", "warning"}])


def check_examples(failures: list[str]) -> None:
    from agent_memory import core

    state_paths = sorted((ROOT / "examples").glob("**/state.json"))
    if not state_paths:
        fail("no example state.json files found", failures)
        return
    for state_path in state_paths:
        memory_dir = state_path.parent
        state = core.load_state(memory_dir)
        errors = core.validate_state(state)
        if errors:
            fail(f"{state_path.relative_to(ROOT)} validation failed: {'; '.join(errors)}", failures)
            continue
        issues = [issue for issue in core.audit_state(state) if issue["severity"] in {"error", "warning"}]
        if issues:
            fail(f"{state_path.relative_to(ROOT)} has doctor warnings or errors", failures)
            continue
    ok(f"validated {len(state_paths)} example state files")


def check_handoffs(failures: list[str]) -> None:
    from agent_memory.adapters import agent, chat, codex, multi_agent

    checks = {
        "chat": chat.prepare_handoff(ROOT / "examples" / "chat-memory-demo"),
        "agent": agent.prepare_handoff(ROOT / "examples" / "agent-run-demo"),
        "codex": codex.prepare_handoff(ROOT / "examples" / "codex-memory"),
        "multi-agent": multi_agent.prepare_handoff(ROOT / "examples" / "multi-agent-demo"),
    }
    for name, report in checks.items():
        if not report.get("ready"):
            fail(f"{name} handoff is not ready", failures)
        if issue_count(report):
            fail(f"{name} handoff has warning or error issues", failures)
    ok("adapter handoff examples")


def main() -> int:
    add_import_path()
    failures: list[str] = []
    check_skill_folder(failures)
    check_project_files(failures)
    check_security_docs(failures)
    check_project_direction_docs(failures)
    check_portable_bundle_docs(failures)
    check_selection_docs(failures)
    check_candidate_docs(failures)
    check_opening_plan_docs(failures)
    check_update_docs(failures)
    check_compaction_docs(failures)
    check_schema_sync(failures)
    check_skill_installer(failures)
    check_demo_runner(failures)
    check_portable_bundle_runner(failures)
    check_selection_runner(failures)
    check_candidate_runner(failures)
    check_opening_plan_runner(failures)
    check_update_runner(failures)
    check_compaction_runner(failures)
    check_evaluation_runner(failures)
    run_unittests(failures)
    check_examples(failures)
    check_handoffs(failures)
    if failures:
        print("")
        print("Release validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("")
    print("Release validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
