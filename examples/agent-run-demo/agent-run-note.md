# Agent Run Note

Use this before continuing an autonomous agent run.

## Objective

Demonstrate autonomous agent checkpoint memory.

## Active Thread

- None

## Next Actions

- Continue from the useful tool result and avoid the failed approach.

## Important Tool Results

- inspect-files: Found the canonical state shape in agent_memory/core.py. (tool-schema-001)

## Failed Attempts

- Tried using the whole transcript as memory and made the handoff noisy. (failed-transcript-001; status: closed)

## Risks And Do-Not-Redo

- Do not save every raw tool call as durable memory.
- Do not copy full transcripts into durable memory; use salience scoring.

## Handoff Notes

- None
