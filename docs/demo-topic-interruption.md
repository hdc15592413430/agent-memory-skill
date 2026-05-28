# Topic Interruption Demo

This demo shows the core behavior this project is trying to make reliable:

1. An agent is working on a main topic.
2. The user introduces a side idea.
3. The agent stores the side idea as an episode and parks the main topic.
4. After the side idea closes, the agent resumes the main topic.
5. A migration packet lets a future agent see both the resumed main topic and the remembered side idea.

Run from the repository root:

```bash
python agent-memory/scripts/memory_packet.py init --path examples/topic-interruption-demo --force

python agent-memory/scripts/memory_packet.py meta \
  --path examples/topic-interruption-demo \
  --project-name "Agent Memory Skill" \
  --objective "Demonstrate topic interruption handling for an AI agent memory skill." \
  --summary "The demo parks a main topic, captures a side idea as an episode, then resumes the main topic for handoff." \
  --next-action "Continue designing the model migration packet." \
  --risk "Do not drop the side idea just because the main topic resumed." \
  --handoff-note "A future agent should read the episode before deciding whether the side idea matters again." \
  --render

python agent-memory/scripts/memory_packet.py set-active \
  --path examples/topic-interruption-demo \
  --id thread-main \
  --text "Design the model migration packet for an agent memory skill." \
  --evidence "Initial product objective." \
  --salience 5 \
  --confidence high \
  --render

python agent-memory/scripts/memory_packet.py interrupt \
  --path examples/topic-interruption-demo \
  --episode-id episode-side-idea \
  --episode-text "User raised a side idea: small interruptions should be remembered and recalled later when relevant." \
  --thread-id thread-side-idea \
  --thread-text "Explore how to capture and recall side ideas." \
  --evidence "The side idea appeared while discussing model migration." \
  --salience 5 \
  --confidence high \
  --tag topic-stack \
  --tag side-idea \
  --render

python agent-memory/scripts/memory_packet.py cue \
  --path examples/topic-interruption-demo \
  --text "back to the previous topic" \
  --auto-resume \
  --render
```

Expected result:

- `threads.active` returns to `thread-main`.
- `threads.closed_recently` contains `thread-side-idea`.
- `episodes` contains `episode-side-idea`.
- `migration-packet.md` shows the resumed main topic and the stored side idea.

You can still resume manually when the closure cue is obvious from context but not present in the latest text:

```bash
python agent-memory/scripts/memory_packet.py resume \
  --path examples/topic-interruption-demo \
  --current-destination closed \
  --render
```
