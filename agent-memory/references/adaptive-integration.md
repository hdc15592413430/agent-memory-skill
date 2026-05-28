# Adaptive Integration

Use this reference when deciding how strongly Agent Memory should attach to an agent.

## Principle

Memory exists to adapt to the user, not to preserve the transcript. Adjust the strength of this skill to the agent's current memory maturity.

## Modes

### Bootstrap

Use when no durable memory system exists.

- Create `.agent-memory/`.
- Capture durable user preferences, project objective, active topic, decisions, and next actions.
- Treat Agent Memory as the primary project memory layer.
- Run `handoff` before context compaction, model switches, or long pauses.

Command:

```bash
python -m agent_memory integration-mode
```

### Augment

Use when the agent already has memory files, daily notes, profiles, or maintenance protocols.

- Keep existing memory untouched.
- Use `.agent-memory/` as a sidecar.
- Import uncertain legacy memory as `candidate`.
- Fill gaps such as handoff packets, session health checks, export/import, review, and redaction.

Command:

```bash
python -m agent_memory integration-mode --existing-memory-exists
```

### Audit

Use when trust, freshness, privacy, or ownership is unclear.

- Do not write durable memory by default.
- Inspect memory surfaces and report import, skip, redact, or rollback suggestions.
- Move to augment or bootstrap only after review.

Command:

```bash
python -m agent_memory integration-mode --existing-memory-exists --trust-unclear
```

## Session Health

Use session health when an agent becomes slow because it carries too much conversation history.

```bash
python -m agent_memory session-health --messages 365 --session-bytes 1048576
```

If the report recommends handoff:

1. Refresh `memory-briefing.md` and `migration-packet.md`.
2. Start a fresh session.
3. Inject only the briefing and high-signal selected records.
4. Keep long audits, repository scans, and test runs out of the main chat path when possible.

This is the reusable pattern from the Yanheng local assistant case: a long main session became slow, useful state was preserved into memory, and a fresh session continued with a smaller context.
