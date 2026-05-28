# Agent Memory Migration Packet

Updated: 2026-05-27T16:29:59Z

## Objective

Demonstrate autonomous agent checkpoint memory.

## Summary

The agent is testing which execution details should survive handoff.

## User Preferences

- None

## Project State

- None

## Decisions

- None

## Topic Stack

- Active: None

### Parked

- None

### Open

- None

### Closed Recently

- None

## Episodes

- None

## Artifacts

- inspect-files: Found the canonical state shape in agent_memory/core.py. (tool-schema-001)
- Tried using the whole transcript as memory and made the handoff noisy. (failed-transcript-001; status: closed)

## Next Actions

- Continue from the useful tool result and avoid the failed approach.

## Risks And Do-Not-Redo

- Do not save every raw tool call as durable memory.
- Do not copy full transcripts into durable memory; use salience scoring.

## Handoff Notes

- None
