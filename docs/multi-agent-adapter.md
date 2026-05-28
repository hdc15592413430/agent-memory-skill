# Multi-Agent Adapter

The multi-agent adapter separates shared memory from role-local memory.

It stores:

- `shared/state.json`: shared objectives, decisions, next actions, and risks
- `roles/<role>/state.json`: role-local findings, artifacts, and episodes
- `shared/memory-briefing.md` and `roles/<role>/memory-briefing.md`: startup context per memory scope
- `shared/migration-packet.md` and `roles/<role>/migration-packet.md`: detailed handoff context per memory scope
- `multi-agent-note.md`: orchestration note for handoff

This prevents premature consensus. A researcher can keep a tentative finding locally while the shared memory records only decisions that the team should treat as authoritative.

## Commands

Create multi-agent memory:

```bash
python -m agent_memory.adapters.multi_agent init \
  --path .agent-memory-multi \
  --role planner \
  --role researcher
```

Write a shared checkpoint:

```bash
python -m agent_memory.adapters.multi_agent checkpoint \
  --path .agent-memory-multi \
  --objective "Coordinate a memory skill design task." \
  --summary "Planner and researcher are working with separated memory." \
  --next-action "Promote only confirmed findings to shared memory." \
  --risk "Do not treat role-local guesses as shared decisions."
```

Record a shared decision:

```bash
python -m agent_memory.adapters.multi_agent shared-decision \
  --path .agent-memory-multi \
  --id decision-001 \
  --text "Use shared memory for decisions and role memory for partial findings." \
  --evidence "Architecture review." \
  --confidence high \
  --salience 5 \
  --role planner
```

Record role-local memory:

```bash
python -m agent_memory.adapters.multi_agent role-memory \
  --path .agent-memory-multi \
  --role researcher \
  --kind fact \
  --id fact-001 \
  --text "Role-local notes prevent premature consensus." \
  --evidence "Researcher finding." \
  --confidence high \
  --salience 5
```

Print the orchestration note:

```bash
python -m agent_memory.adapters.multi_agent note --path .agent-memory-multi
```

Prepare shared and role-local handoff artifacts:

```bash
python -m agent_memory.adapters.multi_agent handoff --path .agent-memory-multi
python -m agent_memory.adapters.multi_agent handoff --path .agent-memory-multi --strict
```

After installing the package, the same adapter is available as:

```bash
agent-memory-multi note --path .agent-memory-multi
```

## How Agents Should Use It

For multi-agent runs:

1. Put stable objectives, decisions, risks, and team-level next actions in `shared`.
2. Put partial findings, specialist assumptions, and intermediate artifacts in role-local memory.
3. Promote a role-local item to shared memory only when it becomes a decision or confirmed project fact.
4. Run `handoff` and use `multi-agent-note.md` for orchestration handoff.

## Boundary

This adapter does not implement a scheduler or message bus. It only defines memory separation and handoff surfaces for multi-agent systems.
