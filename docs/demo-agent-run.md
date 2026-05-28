# Autonomous Agent Run Demo

This demo shows how a long-running agent can preserve execution memory without storing every tool call.

It demonstrates:

- writing a checkpoint
- recording an important tool result
- recording a failed attempt
- adding a do-not-repeat risk
- rendering `agent-run-note.md`

Run from the repository root:

```bash
python -m agent_memory init --path examples/agent-run-demo --force

python -m agent_memory.adapters.agent checkpoint \
  --path examples/agent-run-demo \
  --objective "Demonstrate autonomous agent checkpoint memory." \
  --summary "The agent is testing which execution details should survive handoff." \
  --next-action "Continue from the useful tool result and avoid the failed approach." \
  --risk "Do not save every raw tool call as durable memory." \
  --note \
  --render

python -m agent_memory.adapters.agent tool-result \
  --path examples/agent-run-demo \
  --id tool-schema-001 \
  --tool inspect-files \
  --result "Found the canonical state shape in agent_memory/core.py." \
  --evidence "Source inspection during the run." \
  --confidence high \
  --salience 5 \
  --note \
  --render

python -m agent_memory.adapters.agent failed-attempt \
  --path examples/agent-run-demo \
  --id failed-transcript-001 \
  --text "Tried using the whole transcript as memory and made the handoff noisy." \
  --do-not-repeat "Do not copy full transcripts into durable memory; use salience scoring." \
  --evidence "Observed failure mode from agent memory design." \
  --confidence high \
  --salience 5 \
  --note \
  --render
```

Expected result:

- `agent-run-note.md` contains the checkpoint, tool result, failed attempt, and do-not-repeat risk.
- `migration-packet.md` contains the same durable handoff context.
- `state.json` remains compact and structured.
