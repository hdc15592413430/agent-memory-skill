# Chat Adapter

The chat adapter is for ordinary AI conversation systems that may not have a workspace, tool sandbox, or private memory API.

It stores the same core memory state, but its main output is a user-visible note:

- `state.json`
- `memory-briefing.md`
- `migration-packet.md`
- `chat-memory-note.md`

The note is intentionally readable. A chat assistant can load it at the start of a new conversation, after context compaction, or before switching models.

## Commands

Create chat memory:

```bash
python -m agent_memory.adapters.chat init --path .agent-memory
```

Remember a user preference:

```bash
python -m agent_memory.adapters.chat remember \
  --path .agent-memory \
  --kind preference \
  --id pref-001 \
  --text "User prefers concise Chinese progress updates." \
  --evidence "User asked for collaborative iteration in Chinese." \
  --confidence high \
  --salience 5 \
  --note
```

Set the current chat topic:

```bash
python -m agent_memory.adapters.chat set-topic \
  --path .agent-memory \
  --id thread-main \
  --text "Design the open-source agent memory skill." \
  --evidence "Current conversation objective." \
  --confidence high \
  --salience 5 \
  --note
```

Capture a side topic:

```bash
python -m agent_memory.adapters.chat side-topic \
  --path .agent-memory \
  --episode-id episode-skill-format \
  --episode-text "User asked whether this counts as a skill or should be a library." \
  --thread-id thread-skill-format \
  --thread-text "Clarify skill versus library positioning." \
  --evidence "Side question appeared during product design." \
  --confidence high \
  --salience 5 \
  --note
```

Resume the previous topic:

```bash
python -m agent_memory.adapters.chat resume \
  --path .agent-memory \
  --current-destination closed \
  --note
```

Print the note:

```bash
python -m agent_memory.adapters.chat note --path .agent-memory
```

Prepare a chat handoff:

```bash
python -m agent_memory.adapters.chat handoff --path .agent-memory
python -m agent_memory.adapters.chat handoff --path .agent-memory --strict
```

After installing the package, the same adapter is available as:

```bash
agent-memory-chat note --path .agent-memory
```

## How Agents Should Use It

At the start of a new chat:

1. Read `chat-memory-note.md` or run `note`.
2. Apply only high-salience preferences and active topic state.
3. Treat weak or tentative records as hints, not permanent truth.

When the user introduces a side idea:

1. Capture it as an episode.
2. Park the previous topic.
3. Resume the previous topic once the side topic closes.

Before switching models:

1. Update next actions and risks in the core memory.
2. Run `handoff`.
3. Include `memory-briefing.md` first, with `chat-memory-note.md` and `migration-packet.md` available for detail.

## Boundary

The chat adapter does not assume hidden platform memory. If a product has its own memory API, this adapter can still produce the visible note and the product-specific adapter can decide what to store.
