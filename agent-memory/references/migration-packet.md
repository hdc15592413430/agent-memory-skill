# Migration Packet

Use this reference when preparing a handoff between models, agents, architectures, long sessions, or context windows.

## One-Step Handoff

Use `handoff` when the next model or agent needs both startup context and audit readiness:

```bash
python -m agent_memory handoff --path .agent-memory
python -m agent_memory handoff --path .agent-memory --strict
```

It writes `.agent-memory/memory-briefing.md`, writes `.agent-memory/migration-packet.md`, then runs the same quality checks as `doctor`. Strict mode exits non-zero on warnings.

## Briefing First

Use `brief` when the next model or agent needs a compact startup context:

```bash
python -m agent_memory brief --path .agent-memory
python -m agent_memory brief --path .agent-memory --write
```

The briefing should include only the highest-signal objective, summary, active topic, next actions, user preferences, decisions, key facts, open topics, episodes, and risks. It excludes stale, superseded, and `untrusted` records by default.

Use the full migration packet when the next agent needs audit detail or a more complete handoff.

## Template

```markdown
# Agent Memory Migration Packet

## Objective

What the agent is trying to achieve now, including definition of done.

## User Preferences

Durable preferences and collaboration patterns that should affect the next response.

## Project State

Stable project facts, constraints, and relevant files.

## Decisions

Important decisions already made, with rationale and rejected alternatives when useful.

## Topic Stack

- Active:
- Parked:
- Open:
- Closed recently:

## Episodes

Side ideas or tangents worth recalling later.

## Artifacts

Important outputs, files, links, commands, or commits.
Include opening or phase plans that define requirements and validation gates.

## Next Actions

Ordered steps for the next agent.

## Risks And Do-Not-Redo

Known blockers, risks, stale assumptions, and work that should not be repeated.
```

## Good Packet Qualities

A good migration packet is:

- Short enough to read quickly.
- Specific enough to act on.
- Explicit about dates when facts may change.
- Clear about user preferences versus agent inferences.
- Honest about uncertainty.
- Focused on decisions, state, and next actions rather than narrative.

## Bad Packet Patterns

Avoid:

- Copying the transcript.
- Hiding uncertainty.
- Omitting why a decision was made.
- Saying "continue from above" without a concrete next action.
- Recording every idea with equal weight.
- Treating a temporary preference as permanent.

## Model Switch Checklist

Before switching models or agent architecture:

1. Render the packet from the latest state.
2. Verify that the active topic and next action are clear.
3. Include user preferences that affect tone, autonomy, and output shape.
4. Include constraints and artifacts the new agent cannot infer.
5. Mark unresolved questions and risks.
6. Remove stale implementation details that would mislead the new agent.
7. Supersede corrected preferences, facts, or decisions so startup context carries the current version only.
