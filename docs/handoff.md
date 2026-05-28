# Handoff

`handoff` prepares a memory directory for a model switch, agent handoff, architecture change, context compaction, or long pause.

It is the one-command path for migration readiness:

```bash
python -m agent_memory handoff --path .agent-memory
```

The command does three things:

- writes `.agent-memory/memory-briefing.md`
- writes `.agent-memory/migration-packet.md`
- audits the memory state with the same quality checks as `doctor`

For complex coding tasks, make sure the state already contains the opening plan, phase boundaries, acceptance criteria, and validation commands before running `handoff`. Those early constraints are often more important than a long transcript when a new agent resumes:

```bash
python -m agent_memory plan --path .agent-memory --id plan-opening --title "Opening Implementation Plan" --input docs/plan.md
```

## Strict Mode

Use strict mode before publishing, committing an example, or handing a task to a fresh agent:

```bash
python -m agent_memory handoff --path .agent-memory --strict
```

Without strict mode, schema errors fail the command and warnings are printed. With strict mode, warnings also fail the command after the artifacts are written.

## JSON Output

Use JSON output for wrappers, CI, or adapters:

```bash
python -m agent_memory handoff --path .agent-memory --json
```

The JSON summary includes paths for `state.json`, `memory-briefing.md`, `migration-packet.md`, a readiness boolean, and any audit issues.

## Codex Workspace Adapter

For a Codex-style workspace, use the adapter form:

```bash
python -m agent_memory.adapters.codex handoff --workspace .
python -m agent_memory.adapters.codex checkpoint --workspace . --summary "Ready for handoff." --handoff
```

The adapter discovers `.agent-memory/` from the workspace, writes the same artifacts, and keeps prompt context focused on the short briefing.

## Other Adapters

Runtime adapters add their own handoff surfaces while reusing the same core readiness check:

```bash
python -m agent_memory.adapters.chat handoff --path .agent-memory
python -m agent_memory.adapters.agent handoff --path .agent-memory
python -m agent_memory.adapters.multi_agent handoff --path .agent-memory-multi
```

The chat adapter also refreshes `chat-memory-note.md`, the autonomous-agent adapter refreshes `agent-run-note.md`, and the multi-agent adapter prepares shared plus role-local briefing and packet files.

## When To Use It

Use `handoff` at natural boundaries:

- before changing models or agent architecture
- before context compaction
- before ending a long session
- after a major decision or topic-stack change
- after superseding an old preference, fact, or decision
- before asking another agent to continue the work

If the memory directory has grown noisy, run `compact` first to review low-signal cleanup, then run `handoff` to refresh artifacts:

```bash
python -m agent_memory compact --path .agent-memory
python -m agent_memory compact --path .agent-memory --apply
python -m agent_memory handoff --path .agent-memory
```

Use `brief` alone when only the short startup context is needed. Use `render` alone when only the full migration packet needs refreshing.
