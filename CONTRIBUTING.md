# Contributing

Thanks for helping improve Agent Memory.

This project is both a Codex skill and a reusable Python package. Keep those layers separate:

- Put agent-facing operating instructions in `agent-memory/SKILL.md`.
- Put reusable memory behavior in `agent_memory/`.
- Put runtime-specific behavior in `agent_memory/adapters/`.
- Put user-facing project documentation in root docs, not inside the skill folder.
- Follow `docs/adapter-contract.md` when adding or changing a runtime adapter.
- Use `ROADMAP.md` to align larger work with the current project direction.

## Local Setup

```bash
python -m pip install -e .
```

Install the local Codex skill during manual testing:

```bash
python scripts/install_skill.py --dry-run
python scripts/install_skill.py --target-dir /path/to/codex/skills
```

Run the end-to-end demo when changing topic-stack, preference, or handoff behavior:

```bash
python scripts/demo_memory_flow.py
```

## Validation

Run the full release validation before opening a pull request:

```bash
python scripts/validate_release.py
```

This checks:

- skill folder structure
- JSON Schema sync
- unit tests
- behavior scenario evaluation
- example memory states
- adapter handoff readiness
- security, privacy, and adapter-contract documentation

## Memory Design Rules

When changing memory behavior, preserve these invariants:

- Memory is curated operating state, not a transcript.
- High-salience records need evidence.
- Stale or superseded memory should be marked, not silently deleted.
- External, tool, or agent-derived memory should keep `source` and `scope`.
- Startup context should prefer `memory-briefing.md`; deeper handoff should use `migration-packet.md`.
- Complex work should preserve opening plans, phases, acceptance criteria, and validation commands as plan artifacts.
- Targeted context should use `select` before loading the full migration packet.
- Long-running memory cleanup should use `compact` plans before any manual deletion.
- Sensitive memory should be handled with `redact` so generated artifacts are refreshed.
- Revoked memory should be handled with `forget` so state and generated artifacts stop carrying it.
- Runtime migration should use portable `export` and `import` bundles instead of raw transcript copying.
- Chat, Codex, autonomous-agent, and multi-agent adapters should share the same core semantics.

## Pull Request Notes

In PR descriptions, include:

- the memory problem being addressed
- commands run
- whether examples or docs were updated
- any new risks around stale memory, memory poisoning, or topic-stack behavior
