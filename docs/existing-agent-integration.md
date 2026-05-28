# Existing Agent Integration

Use Agent Memory as an additive sidecar before treating it as a replacement for an agent's current memory system.

If you are unsure how strongly to attach it, run:

```bash
python -m agent_memory integration-mode --existing-memory-exists
python -m agent_memory integration-mode --existing-memory-exists --trust-unclear
```

## When To Use This

Use this flow when an agent or workspace already has:

- `MEMORY.md`, daily notes, summaries, or handoff files
- custom prompts, profiles, model settings, or startup scripts
- user preferences or project facts stored outside `.agent-memory/`
- multiple agents sharing one project

For a brand-new workspace, the normal `init -> brief -> handoff` path is enough.

## Recommended Flow

1. Audit the current memory surface.
2. Create `.agent-memory/` in the project workspace.
3. Keep existing memory files untouched.
4. Convert uncertain legacy memory into candidate records.
5. Promote only reviewed records.
6. Run `doctor` and `handoff --strict`.
7. Record what was imported, skipped, redacted, or left in place.

Check whether the current session is too heavy before migration or reset:

```bash
python -m agent_memory session-health --messages 365 --session-bytes 1048576
```

## Commands

```bash
python -m agent_memory init --path .agent-memory
python -m agent_memory propose --path .agent-memory --collection preferences --id pref-imported-001 --text "..." --source agent --scope user --tag imported --tag legacy-memory
python -m agent_memory select --path .agent-memory --status candidate --include-candidates
python -m agent_memory promote --path .agent-memory --id pref-imported-001 --trusted
python -m agent_memory doctor --path .agent-memory
python -m agent_memory handoff --path .agent-memory --strict
```

## Do Not Overwrite By Default

Do not overwrite existing:

- memory files
- agent profiles or prompt files
- model configuration
- auth files or credentials
- startup scripts, services, scheduled jobs, or registry entries
- shared or global memory stores

If a migration needs to modify an existing file, describe the exact change first and keep a rollback path.

## Rollback

A sidecar integration should be reversible. Rollback means deleting the new `.agent-memory/` directory or reverting the explicitly listed changes. It should not delete or rewrite the original memory files.

When rollback is important, record:

- files created
- files modified
- records imported as candidates
- records promoted
- records redacted or forgotten
- commands used during migration

## Readiness

The integration is ready only when:

- startup context excludes stale, superseded, candidate, and untrusted records by default
- imported records have clear `source`, `scope`, `evidence`, and review status
- sensitive memory has been redacted
- `doctor` has no warnings that would mislead the next agent
- `handoff --strict` passes

If any of these are not true, keep the integration in audit or candidate mode.
