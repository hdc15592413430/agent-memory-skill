# Adaptive Memory Integration

Agent Memory should behave like an adaptive charger: use full power when an agent has no memory, use a lighter sidecar when an agent already has memory, and use audit-only mode when trust is unclear.

## Goal

The goal of memory is to adapt to the user. The protocol should help an agent:

- remember durable user preferences without asking repeatedly
- preserve current work across session resets, model switches, and handoffs
- avoid transcript bloat
- complement existing memory instead of replacing it blindly
- support review, rollback, and privacy boundaries

## Modes

| Mode | Use When | Behavior |
| --- | --- | --- |
| `bootstrap` | No durable memory exists | Create `.agent-memory/` as the primary project memory layer |
| `augment` | Existing memory exists | Use `.agent-memory/` as a sidecar and fill gaps |
| `audit` | Trust, freshness, scope, or consent is unclear | Inspect only; do not write durable memory by default |

Check the recommended mode:

```bash
python -m agent_memory integration-mode
python -m agent_memory integration-mode --existing-memory-exists
python -m agent_memory integration-mode --existing-memory-exists --trust-unclear
```

## Bootstrap Workflow

Use bootstrap for a new agent or new workspace:

```bash
python -m agent_memory init --path .agent-memory
python -m agent_memory meta --path .agent-memory --objective "..." --summary "..."
python -m agent_memory handoff --path .agent-memory
```

Then capture durable records with `add`, `plan`, `interrupt`, `propose`, and `supersede` as needed.

## Augment Workflow

Use augment for agents that already have `MEMORY.md`, daily notes, profiles, maintenance protocols, or platform memory.

```bash
python -m agent_memory init --path .agent-memory
python -m agent_memory propose --path .agent-memory --collection preferences --id pref-imported-001 --text "..." --source agent --scope user --tag imported --tag legacy-memory
python -m agent_memory select --path .agent-memory --status candidate --include-candidates
python -m agent_memory handoff --path .agent-memory
```

Leave the existing system untouched unless the user asks for migration.

## Audit Workflow

Use audit when imported memory might be stale, private, poisoned, duplicated, or owned by another runtime.

```bash
python -m agent_memory integration-mode --existing-memory-exists --trust-unclear
python -m agent_memory doctor --path .agent-memory
python -m agent_memory select --path .agent-memory --status candidate --include-candidates
```

The output should say what would be imported, skipped, redacted, promoted, or left in place.

## Session Health

Long sessions can make agents slower and less reliable. The fix is not to remember more; it is to preserve the important state and safely forget the transcript.

Check session pressure:

```bash
python -m agent_memory session-health --messages 365 --session-bytes 1048576
```

When status is `handoff-recommended` or `critical`:

1. Run `python -m agent_memory handoff --path .agent-memory`.
2. Start a fresh session.
3. Load `memory-briefing.md`.
4. Use `select` for task-specific high-signal records.
5. Avoid loading the full old transcript.

## Yanheng Case

Yanheng, a local AI agent assistant, became slow after a main session grew to hundreds of messages and about 1 MB of session data. The useful fix was not a new personality prompt. It was:

- preserve key conclusions into memory
- refresh handoff artifacts
- start a fresh daily session
- shorten automatic continuation prompts
- show what long task was running

This case maps directly to Agent Memory:

- `session-health` detects when the conversation backpack is too heavy
- `handoff` writes a compact startup packet
- `brief` gives the next session a small context surface
- `select` avoids loading irrelevant history
- `integration-mode` prevents the memory skill from overwriting an existing assistant's own memory

## Release Boundary

This feature is a good `v0.2.0` theme because it adds a clear new capability over `v0.1.0`: adaptive integration and session health, while preserving the original memory schema, candidate review, topic stack, and handoff behavior.
