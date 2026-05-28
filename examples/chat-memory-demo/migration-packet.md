# Agent Memory Migration Packet

Updated: 2026-05-27T16:26:42Z

## Objective

Demonstrate user preference transfer and side topic recovery in ordinary AI chat.

## Summary

The demo stores a durable user preference, tracks an active chat topic, captures a side question as an episode, then resumes the main topic.

## User Preferences

- User prefers concise Chinese progress updates while iterating on product ideas. (pref-chat-demo-001)

## Project State

- None

## Decisions

- None

## Topic Stack

- Active: Design memory behavior for ordinary AI chat. (thread-chat-main)

### Parked

- None

### Open

- None

### Closed Recently

- Clarify skill versus library positioning. (thread-skill-question; status: closed)

## Episodes

- User asked whether agent memory should be a skill, a library, or both. (episode-skill-question)

## Artifacts

- None

## Next Actions

- Continue the main topic without asking the user to reconstruct context.

## Risks And Do-Not-Redo

- Do not turn one side question into a permanent preference without evidence.

## Handoff Notes

- None
