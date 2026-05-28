# Memory Briefing

`brief` renders a short startup context for a new model, agent, architecture, or resumed thread.

Use it when the next agent needs the high-signal operating state without reading the full migration packet.

## Usage

Print the briefing:

```bash
python -m agent_memory brief --path .agent-memory
```

Write `.agent-memory/memory-briefing.md`:

```bash
python -m agent_memory brief --path .agent-memory --write
```

Write the briefing, write the full migration packet, and audit handoff readiness:

```bash
python -m agent_memory handoff --path .agent-memory
```

Limit each section:

```bash
python -m agent_memory brief --path .agent-memory --max-records 3
```

Select a targeted slice after reading the briefing:

```bash
python -m agent_memory select --path .agent-memory --query "current task" --min-salience 4
```

By default, the briefing excludes records with `status: stale`, `status: superseded`, `status: candidate`, or the `untrusted` tag.

## Briefing Vs. Migration Packet

Use `brief` for:

- starting a new model quickly
- giving an agent the current working rhythm
- reducing prompt cost
- avoiding transcript-like handoff context

Use `render` for:

- full model handoff
- context compaction
- audit-friendly migration
- debugging memory contents

The briefing is the first page. The migration packet is the fuller handoff.

`select` is the targeted lookup surface between those two: narrower than the packet, more specific than the briefing.

Use `handoff` when both should be refreshed together before a model switch or agent handoff.
