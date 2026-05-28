# Autonomous Agent Adapter

The autonomous agent adapter is for long-running agents that call tools, make incremental progress, and may switch models or architectures mid-run.

It stores the same core memory state and renders:

- `state.json`
- `memory-briefing.md`
- `migration-packet.md`
- `agent-run-note.md`

The adapter focuses on:

- checkpoints
- important tool results
- failed attempts
- risks and do-not-repeat notes

## Commands

Create agent memory:

```bash
python -m agent_memory.adapters.agent init --path .agent-memory
```

Write a checkpoint:

```bash
python -m agent_memory.adapters.agent checkpoint \
  --path .agent-memory \
  --objective "Run an autonomous research task." \
  --summary "Collected the first round of evidence." \
  --next-action "Inspect source files and validate assumptions." \
  --risk "Do not assume every tool result is durable memory." \
  --note \
  --handoff
```

Record an important tool result:

```bash
python -m agent_memory.adapters.agent tool-result \
  --path .agent-memory \
  --id tool-001 \
  --tool search \
  --result "Found the canonical schema in agent_memory/core.py." \
  --evidence "Tool output from the current run." \
  --confidence high \
  --salience 5 \
  --note \
  --render
```

Record a failed attempt:

```bash
python -m agent_memory.adapters.agent failed-attempt \
  --path .agent-memory \
  --id fail-001 \
  --text "Tried storing the full transcript and produced noisy memory." \
  --do-not-repeat "Do not store full transcripts as memory records." \
  --evidence "Agent run trace." \
  --confidence high \
  --salience 5 \
  --note \
  --render
```

Print the run note:

```bash
python -m agent_memory.adapters.agent note --path .agent-memory
```

Prepare an agent-run handoff:

```bash
python -m agent_memory.adapters.agent handoff --path .agent-memory
python -m agent_memory.adapters.agent handoff --path .agent-memory --strict
```

After installing the package, the same adapter is available as:

```bash
agent-memory-agent note --path .agent-memory
```

## How Agents Should Use It

During a long run:

1. Write a checkpoint after meaningful progress.
2. Record only tool results that affect future action.
3. Record failed attempts when repeating them would waste time or cause regression.
4. Run `handoff` before compaction, handoff, or model migration.

## Boundary

The adapter does not try to store every tool call. It keeps only durable execution memory that changes what a future agent should do.
