# Release Checklist

Use this before publishing the project on GitHub or tagging a release.

## Required

- Run `python scripts/validate_release.py`.
- Confirm `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, and CI are present.
- Confirm `MANIFEST.in` includes the bundled skill, docs, examples, schemas, scripts, and tests for source releases.
- Review `docs/privacy-and-safety.md` before publishing examples or demos.
- Review `ROADMAP.md` and `docs/adapter-contract.md` so new contributors know the project direction and adapter requirements.
- Confirm the Codex skill installer works:
  - `python scripts/install_skill.py --dry-run`
- Confirm the end-to-end demo works:
  - `python scripts/demo_memory_flow.py`
- Confirm behavior scenarios pass:
  - `python scripts/evaluate_memory_scenarios.py`
- Confirm opening plan capture help is available:
  - `python -m agent_memory plan --help`
- Confirm candidate review help is available:
  - `python -m agent_memory propose --help`
  - `python -m agent_memory promote --help`
- Confirm portable bundle export/import works:
  - `python -m agent_memory export --path examples/codex-memory --output agent-memory-export.json --strict`
  - `python -m agent_memory import --path .tmp-agent-memory-import --input agent-memory-export.json --force`
- Confirm supersession help is available:
  - `python -m agent_memory supersede --help`
- Confirm compaction planning works:
  - `python -m agent_memory compact --path examples/codex-memory`
- Confirm example handoffs are ready:
  - `python -m agent_memory.adapters.codex handoff --workspace examples/codex-memory --json`
  - `python -m agent_memory.adapters.chat handoff --path examples/chat-memory-demo --json`
  - `python -m agent_memory.adapters.agent handoff --path examples/agent-run-demo --json`
  - `python -m agent_memory.adapters.multi_agent handoff --path examples/multi-agent-demo --json`
- Replace any future placeholder repository URLs in package metadata before publishing to a package index.
- Tag the release, for example `v0.1.0`.

## Optional

- Add a short demo GIF or screencast for the topic-interruption flow.
- Decide whether the examples should remain English-only, Chinese-only, or bilingual.
- Add issue labels for memory safety, adapter work, docs, and evaluation.

## Release Definition

A release is ready when a fresh clone can:

- install the package locally
- install the bundled Codex skill locally
- inspect a source release that contains the bundled skill and validation assets
- run the end-to-end memory demo
- run behavior-level memory evaluations
- capture an opening plan artifact for complex work
- keep proposed candidate memory out of startup context until promoted
- inspect security and privacy guidance
- inspect roadmap and adapter-contract guidance
- export and import a portable memory bundle
- supersede outdated memory without conflicting active records
- produce a reviewable compaction plan
- initialize memory
- capture a topic interruption
- render a short briefing and full migration packet
- run adapter handoffs for Codex, chat, autonomous-agent, and multi-agent examples
- pass `scripts/validate_release.py`
