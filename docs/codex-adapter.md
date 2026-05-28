# Codex Adapter

The Codex adapter is a small workspace adapter for Codex-style agents. It does not depend on private Codex internals. It uses normal files in a workspace:

- `.agent-memory/state.json`
- `.agent-memory/memory-briefing.md`
- `.agent-memory/migration-packet.md`

## Commands

Create or discover workspace memory:

```bash
python -m agent_memory.adapters.codex init --workspace .
```

Print memory context that can be injected into a prompt or read before work:

```bash
python -m agent_memory.adapters.codex context --workspace .
```

`context` renders the short briefing view by default, filters stale or untrusted records, and points to the full migration packet for detail.

The `--workspace` value can point either to a workspace containing `.agent-memory/state.json` or directly to a memory directory containing `state.json`.

Write a checkpoint before compaction, handoff, or model migration:

```bash
python -m agent_memory.adapters.codex checkpoint \
  --workspace . \
  --summary "Finished the first implementation pass." \
  --next-action "Run tests and inspect the migration packet." \
  --risk "Do not overwrite user edits without checking the worktree." \
  --handoff-note "Read .agent-memory/migration-packet.md before continuing." \
  --handoff
```

Prepare handoff artifacts without changing checkpoint metadata:

```bash
python -m agent_memory.adapters.codex handoff --workspace .
python -m agent_memory.adapters.codex handoff --workspace . --strict
```

After installing the package, the same adapter is available as:

```bash
agent-memory-codex context --workspace .
```

## How Agents Should Use It

At the start of continuity-sensitive work:

1. Run `context`.
2. Read the active topic, high-salience preferences, decisions, and next actions.
3. Continue the task without asking the user to reconstruct state.

When a side topic appears:

1. Use the core `interrupt` command or API to park the current thread.
2. Capture the side idea as an episode.
3. Resume the parked thread when the side topic closes.

Before compaction or model migration:

1. Run `checkpoint`.
2. Use `--handoff` or run `handoff`.
3. Hand `memory-briefing.md` to the next model first, with `migration-packet.md` available for detail.

## Boundary

The adapter only handles workspace discovery, prompt-context preparation, and handoff artifact orchestration. The portable memory semantics remain in `agent_memory.core`.
