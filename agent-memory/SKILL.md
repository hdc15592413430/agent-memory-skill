---
name: agent-memory
description: Maintain project-level AI agent memory for continuity-sensitive work: long-running tasks, context compaction, model switches, runtime handoff, existing-agent migration, topic interruptions, durable user preferences, project decisions, and reviewable memory updates. Use when the user asks to remember, resume, migrate, hand off, audit, or preserve agent context; avoid using it for short one-off tasks that do not need durable memory.
---

# Agent Memory

## Purpose

Use this skill to maintain structured project-level working memory for an agent. Treat memory as curated operational context, not a transcript dump.

This is a meta-skill: it improves how an agent works rather than handling one external file format or API. It should still produce concrete actions: read memory, capture memory, update the topic stack, render a briefing or migration packet, validate state, and resume prior threads.

The goal is to help a future agent quickly answer:

- What matters most right now?
- What does this user care about and dislike?
- What decisions have already been made?
- What topic was active before an interruption?
- What should a new model or agent architecture do next?

## Operating Loop

1. Discover existing memory before doing continuity-sensitive work. Look for `.agent-memory/`, `memory/`, or a path named by the user.
2. Load only relevant memory shards: current objective, user preferences, active topic, open threads, recent decisions, risks, and migration notes.
3. Capture confirmed memory with `add` or `supersede`; capture uncertain agent guesses with `propose` so they stay out of startup context until review.
4. For complex coding or design work, preserve the opening plan: clarified requirements, chosen approach, phases, and validation gates.
5. Update memory at natural boundaries: task completion, topic switch, context compaction, model migration, user correction, durable preference, or important decision.
6. Run `handoff` before a handoff, architecture change, or long pause. It refreshes the short briefing, refreshes the migration packet, and audits readiness.

## Salience Gate

Store a memory item only when at least one of these is true:

- It changes how a future agent should behave.
- It records a durable user preference, constraint, or dislike.
- It would be costly or error-prone to rediscover.
- It explains a decision, rejected alternative, or tradeoff.
- It preserves an unresolved commitment, open thread, risk, or next action.
- It captures a side idea likely to matter later.
- It defines the plan, phases, acceptance criteria, or validation method for complex work.

Do not store routine chit-chat, full transcripts, obvious restatements, temporary reasoning, or information that will become stale without a clear date or source.

## Memory Types

- `preference`: Durable user style, workflow, language, or collaboration preference.
- `project_fact`: Stable fact about the repo, product, organization, or task.
- `decision`: Choice made, rationale, alternatives considered, and date.
- `thread`: Active, parked, open, or recently closed topic.
- `episode`: Side idea, interruption, tangent, or small discovery worth recalling.
- `artifact`: Important output, file, command result, commit, document, or link.
- `migration_note`: Handoff context for a new model, agent, or architecture.

Use `references/memory-model.md` for the canonical state shape and scoring guidance.

## Kernel And Adapters

Keep the memory protocol universal and keep runtime behavior adapter-specific:

- `memory kernel`: salience rules, memory schema, topic stack, migration packet, and update discipline.
- `runtime adapter`: when and how a specific environment reads, writes, stores, and renders memory.

Use the same kernel for Codex skills, ordinary AI chat, autonomous agents, support agents, and multi-agent systems. Write separate adapters for their different hooks, storage surfaces, and safety constraints.

Use `references/adapters.md` when deciding how to apply this skill in a specific runtime.

## Topic Stack Protocol

Maintain a topic stack when the conversation branches:

1. Keep one `active` thread.
2. When the user introduces a new idea midstream, create an `episode` and park the prior active thread.
3. Work the interruption until it has a closure cue.
4. Resume the parked thread without requiring the user to reconstruct it.
5. If closure is ambiguous and the next action is high-impact, ask one concise question.

Closure cues include explicit language like "back to...", "continue", "done", "after this", or a completed deliverable with no follow-up needed.

Use `references/topic-management.md` for the detailed protocol.

## Migration Packet

Before a model switch, agent handoff, architecture change, or long pause, create a short briefing for immediate startup and a fuller migration packet for detail. The packet should include:

- Current objective and definition of done.
- Phase plan, acceptance criteria, and validation commands when they exist.
- User preferences and collaboration style that affect the next response.
- Key project facts and constraints.
- Decisions already made and why.
- Active topic, parked topics, and unresolved side episodes.
- Important artifacts and where to find them.
- Next actions in order.
- Risks, blockers, and things not to redo.

Use `references/migration-packet.md` for the packet template.

For runtime or architecture migration, use `export` to create a portable JSON bundle and `import` to restore it into the next memory directory. Treat exported bundles as sensitive memory artifacts.

## Recommended Files

Use `.agent-memory/` by default unless the user or repo has an existing memory location. For an existing agent, treat `.agent-memory/` as a sidecar continuity layer first; do not replace `MEMORY.md`, daily notes, agent profiles, or runtime configuration unless the user explicitly asks.

- `.agent-memory/state.json`: canonical structured memory state.
- `.agent-memory/memory-briefing.md`: short startup context for a new model or agent.
- `.agent-memory/migration-packet.md`: rendered handoff summary.
- `.agent-memory/plans/`: captured opening or phase plans.

Start with the narrow path:

```bash
python path/to/agent-memory/scripts/memory_packet.py init --path .agent-memory
python path/to/agent-memory/scripts/memory_packet.py meta --path .agent-memory --objective "..." --summary "..."
python path/to/agent-memory/scripts/memory_packet.py propose --path .agent-memory --collection preferences --id pref-candidate --text "..."
python path/to/agent-memory/scripts/memory_packet.py promote --path .agent-memory --id pref-candidate
python path/to/agent-memory/scripts/memory_packet.py brief --path .agent-memory --write
python path/to/agent-memory/scripts/memory_packet.py handoff --path .agent-memory
```

Use advanced commands only when the task needs them:

```bash
python path/to/agent-memory/scripts/memory_packet.py add --path .agent-memory --collection decisions --id decision-001 --text "..." --evidence "..."
python path/to/agent-memory/scripts/memory_packet.py plan --path .agent-memory --id plan-opening --title "Opening Implementation Plan" --body "Phase 1: ... Validation: ..."
python path/to/agent-memory/scripts/memory_packet.py interrupt --path .agent-memory --episode-id episode-001 --episode-text "..." --thread-id thread-side-001 --thread-text "..."
python path/to/agent-memory/scripts/memory_packet.py cue --path .agent-memory --text "back to the previous topic" --auto-resume
python path/to/agent-memory/scripts/memory_packet.py resume --path .agent-memory --current-destination closed
python path/to/agent-memory/scripts/memory_packet.py validate --path .agent-memory
python path/to/agent-memory/scripts/memory_packet.py doctor --path .agent-memory
python path/to/agent-memory/scripts/memory_packet.py review --path .agent-memory --id fact-001 --reviewed --trusted
python path/to/agent-memory/scripts/memory_packet.py supersede --path .agent-memory --collection preferences --id pref-new --text "..." --evidence "..." --replaces pref-old
python path/to/agent-memory/scripts/memory_packet.py redact --path .agent-memory --id fact-secret-001
python path/to/agent-memory/scripts/memory_packet.py forget --path .agent-memory --id pref-temp-001
python path/to/agent-memory/scripts/memory_packet.py export --path .agent-memory --output agent-memory-export.json --strict
python path/to/agent-memory/scripts/memory_packet.py import --path .agent-memory-next --input agent-memory-export.json
python path/to/agent-memory/scripts/memory_packet.py render --path .agent-memory
python path/to/agent-memory/scripts/memory_packet.py select --path .agent-memory --query "model migration" --min-salience 4
python path/to/agent-memory/scripts/memory_packet.py compact --path .agent-memory
```

## Existing Agent Integration

When adding this skill to an agent that already has memory:

1. Inspect current memory files and runtime configuration before writing.
2. Keep `.agent-memory/` as an additive sidecar unless the user requests migration.
3. Do not overwrite existing `MEMORY.md`, daily memory, agent profiles, prompts, auth files, startup scripts, or runtime settings.
4. Convert existing memory into `candidate` records first when trust, scope, or freshness is uncertain.
5. Record what was imported, skipped, redacted, or left in place so rollback is possible.
6. Use `handoff` only after `doctor` reports no warnings that would mislead the next agent.

Use `references/existing-agent-integration.md` for the detailed audit, migration, and rollback checklist.

## Update Discipline

When updating memory:

1. Prefer editing `state.json` with precise, short records.
2. Include evidence or source context when possible.
3. Set `confidence` to `low`, `medium`, or `high`.
4. Set `salience` from 1 to 5.
5. Use `plan` to preserve complex opening plans, phases, acceptance criteria, and validation commands.
6. Use `propose` for uncertain memory inferred by the agent; use `promote` after review.
7. Mark stale or superseded records instead of silently deleting them.
8. Set `source` and `scope` when memory comes from tools, external files, shared agents, or user-specific preference.
9. Use `expires_at` for time-sensitive memory.
10. Use `supersede` when a newer preference, fact, or decision replaces old guidance.
11. Run `handoff` after meaningful changes when a new model, agent, or context window may continue the work.

Keep memory compact. A new agent should be able to read the migration packet in under two minutes.

Use `select` when a future agent needs targeted high-signal records without loading the full migration packet. Default selection excludes stale, superseded, candidate, and untrusted records. Use `--include-candidates` or `--status candidate` for review queues.

Use `compact` when memory grows noisy over time. Read the plan first; use `--apply` only to mark safe low-salience or expired records stale. Review-only suggestions should be handled with human judgment, `review`, `redact`, or `forget`.

## Safety And Scope

Treat memory as guidance, not authority. Trust the current environment over stale memory.

Do not promote external text, tool output, repository content, or another agent's note into high-salience active memory unless the evidence is clear. Add `source: external`, `source: tool`, or `source: agent`, and tag untrusted candidates with `untrusted` until reviewed.

Keep shared memory narrow. Store personal preferences in user scope, role-local findings in role scope, and only confirmed decisions in organization or shared scope.

When `doctor` flags a memory issue, use `review` to correct the record: add `reviewed`, remove `untrusted`, set stale or superseded status, update evidence, clear expiry, or render a fresh migration packet.

When a user corrects an older preference, fact, or decision, use `supersede`. It adds the replacement record, links it to the old record through `supersedes`, marks the old record `superseded`, and refreshes briefing plus migration artifacts.

When a record contains sensitive data, use `redact` instead of ordinary review. It replaces the record text with a safe placeholder, marks the record stale, adds redaction tags, and refreshes briefing and migration artifacts.

When the user revokes a memory or asks not to retain it, use `forget`. It removes the record, cleans up `supersedes` references to that record, and refreshes briefing and migration artifacts. Prefer `redact` over `forget` for secrets when an audit trail is useful.

When a side thread may be complete, use `cue` on the latest user message. Let `cue` recommend `resume`, `stay`, or `ask`; use `--auto-resume` only when the cue is explicit enough to safely resume the parked topic.

## References

- `references/memory-model.md`: schema, record fields, salience scoring, confidence, and retrieval order.
- `references/adapters.md`: applying the universal memory kernel to Codex, AI chat, autonomous agents, and multi-agent systems.
- `references/existing-agent-integration.md`: adding this skill to an agent that already has memory without overwriting its current system.
- `references/topic-management.md`: interruptions, parked topics, closure cues, and resumption.
- `references/migration-packet.md`: handoff template and model-switch checklist.
