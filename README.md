# Agent Memory Skill

Agent Memory is an open-source skill prototype for structured AI agent memory. It helps agents preserve the useful parts of long conversations and project work without copying entire transcripts into future context.

The first target is Codex-style workspace agents, but the memory protocol is intentionally runtime-agnostic: one core memory model, with adapters for Codex, ordinary AI chat, autonomous agents, and multi-agent systems.

## Why This Exists

Current agent memory often fails in three places:

- Model or architecture migration: a new model receives lots of old context but cannot tell what matters.
- User preference transfer: a new agent does not quickly learn the user's style, priorities, and disliked behaviors.
- Topic interruption handling: a side idea appears during an active thread, then the agent forgets to return to the main thread or fails to store the side idea for later.

This project treats memory as curated operating state:

- important decisions
- durable user preferences
- active and parked topics
- side episodes
- relevant artifacts
- next actions and risks
- migration packets for handoff

## Repository Layout

```text
SECURITY.md
ROADMAP.md
agent_memory/
  core.py
  cli.py
  adapters/agent.py
  adapters/codex.py
  adapters/chat.py
  adapters/multi_agent.py
agent-memory/
  SKILL.md
  agents/openai.yaml
  references/
  scripts/memory_packet.py
examples/
  agent-run-demo/{state.json,memory-briefing.md,migration-packet.md,agent-run-note.md}
  chat-memory-demo/{state.json,memory-briefing.md,migration-packet.md,chat-memory-note.md}
  codex-memory/{state.json,memory-briefing.md,migration-packet.md}
  multi-agent-demo/{multi-agent-note.md,shared/,roles/}
  topic-interruption-demo/{state.json,migration-packet.md}
docs/
  agent-adapter.md
  adapter-contract.md
  architecture.md
  handoff.md
  memory-briefing.md
  chat-adapter.md
  demo-chat-memory.md
  demo-agent-run.md
  demo-multi-agent.md
  codex-adapter.md
  evaluation.md
  json-schema.md
  memory-candidates.md
  memory-compaction.md
  memory-doctor.md
  memory-selection.md
  memory-updates.md
  multi-agent-adapter.md
  opening-plans.md
  privacy-and-safety.md
  portable-bundles.md
  release.md
  demo-topic-interruption.md
  problem-map.md
  research-pain-points.md
tests/
  test_memory_packet.py
schemas/
  state.schema.json
scripts/
  demo_memory_flow.py
  evaluate_memory_scenarios.py
  install_skill.py
  validate_release.py
```

## Quick Start

Install locally for development:

```bash
python -m pip install -e .
```

Install the Codex skill into your local skills directory:

```bash
python scripts/install_skill.py --dry-run
python scripts/install_skill.py
```

By default this installs `agent-memory/` into `$CODEX_HOME/skills` when `CODEX_HOME` is set, otherwise into `~/.codex/skills`.

Run the end-to-end memory demo:

```bash
python scripts/demo_memory_flow.py
python scripts/demo_memory_flow.py --path .tmp-agent-memory-demo --force
```

This demonstrates preference transfer, topic interruption recovery, and handoff artifact generation.

Run behavior-level memory evaluations:

```bash
python scripts/evaluate_memory_scenarios.py
python scripts/evaluate_memory_scenarios.py --path .tmp-agent-memory-eval --force --json
```

This checks model handoff migration, portable bundle roundtrip, preference filtering, candidate review, memory update supersession, opening plan preservation, targeted memory selection, memory compaction planning, topic interruption resume, memory review, sensitive-memory redaction, user-controlled forgetting, and multi-agent separation.

Initialize memory in a workspace:

```bash
python agent-memory/scripts/memory_packet.py init --path .agent-memory
# or
python -m agent_memory init --path .agent-memory
# or, after install
agent-memory init --path .agent-memory
```

Set project handoff metadata:

```bash
python agent-memory/scripts/memory_packet.py meta --path .agent-memory --project-name "Agent Memory Skill" --objective "Create a memory skill that preserves preferences, topic state, and migration context." --summary "Prototype continuity skill for agent handoffs." --render
```

Validate the state:

```bash
python agent-memory/scripts/memory_packet.py validate --path .agent-memory
```

Render a migration packet:

```bash
python agent-memory/scripts/memory_packet.py render --path .agent-memory
```

Print or write a short startup briefing for a new model or agent:

```bash
python -m agent_memory brief --path .agent-memory
python -m agent_memory brief --path .agent-memory --write
```

Capture an opening or phase plan as a handoff artifact:

```bash
python -m agent_memory plan --path .agent-memory --id plan-opening --title "Opening Implementation Plan" --body "Phase 1: inspect context. Validation: run tests." --next-action "Run phase 1 validation."
```

Select targeted high-signal memory records:

```bash
python -m agent_memory select --path .agent-memory --query "model migration" --min-salience 4
python -m agent_memory select --path .agent-memory --tag migration --json
```

Propose a memory candidate and promote it only after review:

```bash
python -m agent_memory propose --path .agent-memory --collection preferences --id pref-candidate --text "User may prefer short progress updates." --scope user
python -m agent_memory select --path .agent-memory --include-candidates --status candidate
python -m agent_memory promote --path .agent-memory --id pref-candidate
```

Plan or apply conservative memory compaction:

```bash
python -m agent_memory compact --path .agent-memory
python -m agent_memory compact --path .agent-memory --apply
```

Prepare a model or agent handoff in one step:

```bash
python -m agent_memory handoff --path .agent-memory
python -m agent_memory handoff --path .agent-memory --strict
```

Export or import a portable memory bundle for runtime migration:

```bash
python -m agent_memory export --path .agent-memory --output agent-memory-export.json --strict
python -m agent_memory import --path .agent-memory-next --input agent-memory-export.json
```

Audit memory quality:

```bash
python -m agent_memory doctor --path .agent-memory
```

Review or repair a flagged memory record:

```bash
python -m agent_memory review --path .agent-memory --id fact-001 --reviewed --trusted --render
python -m agent_memory review --path .agent-memory --id fact-002 --status stale --clear-expires-at
```

Replace outdated memory with a newer record:

```bash
python -m agent_memory supersede --path .agent-memory --collection preferences --id pref-new --text "User prefers concise direct updates." --evidence "User corrected the old preference." --scope user --confidence high --salience 5 --replaces pref-old
```

Redact sensitive memory and refresh handoff artifacts:

```bash
python -m agent_memory redact --path .agent-memory --id fact-secret-001
```

Forget a revoked memory record and refresh handoff artifacts:

```bash
python -m agent_memory forget --path .agent-memory --id pref-temp-001
```

Print the JSON Schema:

```bash
python -m agent_memory schema
```

Capture an interruption and resume the previous thread:

```bash
python agent-memory/scripts/memory_packet.py interrupt --path .agent-memory --episode-id episode-001 --episode-text "User raised a side idea worth remembering." --thread-id thread-side-001 --thread-text "Explore the side idea." --evidence "User introduced this during an active topic." --salience 5 --confidence high --render
python agent-memory/scripts/memory_packet.py cue --path .agent-memory --text "back to the previous topic" --auto-resume --render
python agent-memory/scripts/memory_packet.py resume --path .agent-memory --current-destination closed --render
```

Try the example memory state:

```bash
python agent-memory/scripts/memory_packet.py validate --path examples/codex-memory
python agent-memory/scripts/memory_packet.py render --path examples/codex-memory
python agent-memory/scripts/memory_packet.py validate --path examples/topic-interruption-demo
```

See `docs/demo-topic-interruption.md` for a runnable end-to-end demo.

See `docs/demo-chat-memory.md` for a chat-specific demo.

Use the Codex-style workspace adapter:

```bash
python -m agent_memory.adapters.codex init --workspace .
python -m agent_memory.adapters.codex context --workspace .
python -m agent_memory.adapters.codex checkpoint --workspace . --summary "Ready for handoff." --handoff
python -m agent_memory.adapters.codex handoff --workspace .
```

Use the ordinary chat adapter:

```bash
python -m agent_memory.adapters.chat init --path .agent-memory
python -m agent_memory.adapters.chat remember --path .agent-memory --kind preference --id pref-001 --text "User prefers concise Chinese progress updates." --evidence "User stated this preference." --confidence high --salience 5 --note
python -m agent_memory.adapters.chat note --path .agent-memory
python -m agent_memory.adapters.chat handoff --path .agent-memory
```

Use the autonomous agent adapter:

```bash
python -m agent_memory.adapters.agent checkpoint --path .agent-memory --summary "Finished a useful step." --next-action "Continue from the validated result." --note --handoff
python -m agent_memory.adapters.agent tool-result --path .agent-memory --id tool-001 --tool tests --result "Tests passed." --evidence "Local run." --confidence high --salience 4 --note
python -m agent_memory.adapters.agent note --path .agent-memory
python -m agent_memory.adapters.agent handoff --path .agent-memory
```

Use the multi-agent adapter:

```bash
python -m agent_memory.adapters.multi_agent init --path .agent-memory-multi --role planner --role researcher
python -m agent_memory.adapters.multi_agent shared-decision --path .agent-memory-multi --id decision-001 --text "Use shared memory only for confirmed decisions." --evidence "Team agreement." --confidence high --salience 5 --role planner
python -m agent_memory.adapters.multi_agent note --path .agent-memory-multi
python -m agent_memory.adapters.multi_agent handoff --path .agent-memory-multi
```

## Problem Coverage

See `docs/problem-map.md` for the mapping between current agent-memory pain points and the mechanisms in this project.

See `docs/research-pain-points.md` for the broader public pain-point scan that informs the roadmap.

See `ROADMAP.md` for planned adapter hardening, expanded retrieval, compaction policy work, and runtime integration work.

See `docs/architecture.md` for the skill/core/adapter split.

See `docs/adapter-contract.md` for the required behavior of new runtime adapters.

See `docs/codex-adapter.md` for the first runtime adapter.

See `docs/chat-adapter.md` for ordinary AI conversation memory.

See `docs/agent-adapter.md` for autonomous agent run memory.

See `docs/multi-agent-adapter.md` for shared and role-local memory.

See `docs/memory-doctor.md` for memory quality audits.

See `docs/privacy-and-safety.md` for privacy, source/scope, review, retention, and adapter safety guidance.

See `docs/memory-briefing.md` for the short startup context used before a fuller migration packet.

See `docs/opening-plans.md` for preserving complex task plans, phases, acceptance criteria, and validation commands.

See `docs/memory-selection.md` for selecting targeted high-signal records without loading the full packet.

See `docs/memory-candidates.md` for candidate memories that stay out of startup context until review.

See `docs/memory-updates.md` for replacing outdated preferences, facts, or decisions without keeping conflicting active memory.

See `docs/memory-compaction.md` for reviewable cleanup plans that mark low-signal memory stale without deleting audit history.

See `docs/portable-bundles.md` for exporting and importing memory between runtimes.

See `docs/evaluation.md` for behavior scenarios that validate the project's core memory claims.

See `docs/handoff.md` for the one-command handoff workflow.

See `docs/json-schema.md` for `state.json` schema usage.

See `docs/release.md` for the GitHub release checklist.

## Security And Privacy

Memory files can contain sensitive project context or personal preferences. Keep them local unless an adapter explicitly documents remote storage, avoid storing secrets or raw transcripts, tag unreviewed external records with `untrusted`, and run `doctor` before sharing examples.

See `SECURITY.md` for vulnerability reporting and `docs/privacy-and-safety.md` for memory-specific safety guidance.

## Skill Or Library?

The first version is a skill because the most important behavior is procedural:

- when to read memory
- what deserves to be remembered
- how to handle topic switches
- how to prepare a model handoff
- how to avoid transcript dumping

The long-term shape can be:

- `skill`: the agent-facing operating guide
- `agent_memory.core`: schema, scoring, validation, topic stack operations, and packet rendering
- `adapters`: Codex, chat, autonomous agent, and multi-agent integrations

## Publishing Checklist

Before publishing on GitHub:

- Run `python scripts/validate_release.py`.
- Run `python scripts/evaluate_memory_scenarios.py` if you want to inspect behavior checks directly.
- Review `SECURITY.md` and `docs/privacy-and-safety.md`.
- Follow `docs/release.md`.
- Optionally record a short screencast or GIF of the topic interruption demo.
- Decide whether examples should be English-only, Chinese-only, or bilingual.
- Add a version tag such as `v0.1.0`.

## Development

Run tests:

```bash
python -m unittest discover -s tests
```

Run the full release validation used by CI:

```bash
python scripts/validate_release.py
```

Run the behavior evaluator directly:

```bash
python scripts/evaluate_memory_scenarios.py
```

Validate examples:

```bash
python -m agent_memory validate --path examples/chat-memory-demo
python -m agent_memory validate --path examples/agent-run-demo
python -m agent_memory validate --path examples/codex-memory
python -m agent_memory validate --path examples/topic-interruption-demo
python -m agent_memory validate --path examples/multi-agent-demo/shared
python -m agent_memory validate --path examples/multi-agent-demo/roles/planner
python -m agent_memory validate --path examples/multi-agent-demo/roles/researcher
python -m agent_memory doctor --path examples/chat-memory-demo
python -m agent_memory handoff --path examples/codex-memory
python -m agent_memory schema
```

## License

MIT License. See `LICENSE`.

## Status

Prototype v0.1. The current version is suitable for early local testing and design iteration.
