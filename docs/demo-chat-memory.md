# Chat Memory Demo

This demo shows ordinary AI chat memory without assuming a hidden platform memory API.

It demonstrates:

- storing a durable user preference
- tracking the active chat topic
- capturing a side question as an episode
- resuming the main topic
- rendering a user-visible `chat-memory-note.md`

Run from the repository root:

```bash
python -m agent_memory init --path examples/chat-memory-demo --force

python -m agent_memory meta \
  --path examples/chat-memory-demo \
  --project-name "Chat Memory Demo" \
  --objective "Demonstrate user preference transfer and side topic recovery in ordinary AI chat." \
  --summary "The demo stores a durable user preference, tracks an active chat topic, captures a side question as an episode, then resumes the main topic." \
  --next-action "Continue the main topic without asking the user to reconstruct context." \
  --risk "Do not turn one side question into a permanent preference without evidence." \
  --render

python -m agent_memory.adapters.chat remember \
  --path examples/chat-memory-demo \
  --kind preference \
  --id pref-chat-demo-001 \
  --text "User prefers concise Chinese progress updates while iterating on product ideas." \
  --evidence "User collaborates in Chinese and asks for concrete progress." \
  --confidence high \
  --salience 5 \
  --render \
  --note

python -m agent_memory.adapters.chat set-topic \
  --path examples/chat-memory-demo \
  --id thread-chat-main \
  --text "Design memory behavior for ordinary AI chat." \
  --evidence "Main chat objective." \
  --confidence high \
  --salience 5 \
  --render \
  --note

python -m agent_memory.adapters.chat side-topic \
  --path examples/chat-memory-demo \
  --episode-id episode-skill-question \
  --episode-text "User asked whether agent memory should be a skill, a library, or both." \
  --thread-id thread-skill-question \
  --thread-text "Clarify skill versus library positioning." \
  --evidence "Side question appeared during memory product design." \
  --confidence high \
  --salience 5 \
  --tag positioning \
  --tag side-topic \
  --render \
  --note

python -m agent_memory.adapters.chat resume \
  --path examples/chat-memory-demo \
  --current-destination closed \
  --render \
  --note
```

Expected result:

- `chat-memory-note.md` contains the user preference.
- The active topic returns to `thread-chat-main`.
- The side question remains stored as `episode-skill-question`.
- The side topic is moved to `closed_recently`.
