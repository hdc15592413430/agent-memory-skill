# Existing Agent Integration

Use this reference when adding Agent Memory to an agent or workspace that already has memory, profiles, prompts, or runtime configuration.

## Goal

Install Agent Memory as a sidecar continuity layer first. Do not replace the agent's current memory system until the user explicitly asks for a migration and the current memory has been reviewed.

## Preflight

Before writing:

- Identify the workspace root and intended `.agent-memory/` path.
- List existing memory files such as `MEMORY.md`, daily notes, summaries, handoff files, or previous `.agent-memory/` directories.
- Identify agent configuration files, startup scripts, auth profiles, scheduled jobs, and global settings.
- Check whether any existing memory contains personal data, secrets, stale instructions, or untrusted imported text.
- Decide whether the task is sidecar install, audit-only, candidate import, full migration, or rollback.

## Safe Modes

- `audit`: inspect existing memory and report what would be imported, skipped, or redacted.
- `sidecar`: create `.agent-memory/` and keep old memory untouched.
- `candidate-import`: convert existing records into `candidate` entries for review before startup reuse.
- `migration`: promote reviewed records and render a briefing plus migration packet.
- `rollback`: remove Agent Memory artifacts created during the integration and leave existing memory in place.

## Boundaries

Never overwrite these without explicit user approval:

- existing memory files
- agent profile or prompt files
- model configuration
- auth files or credentials
- startup scripts, services, scheduled tasks, or registry entries
- shared or global memory locations

Prefer adding a new `.agent-memory/` directory inside the project workspace. If another memory location is requested, name it clearly in the handoff notes.

## Candidate Import

Use `propose` for memory imported from existing files when freshness, source, scope, or consent is uncertain. Add useful tags such as `imported`, `needs-review`, `legacy-memory`, or the source filename.

Promote only after review:

```bash
python -m agent_memory propose --path .agent-memory --collection preferences --id pref-imported-001 --text "..." --source agent --scope user --tag imported --tag legacy-memory
python -m agent_memory select --path .agent-memory --status candidate --include-candidates
python -m agent_memory promote --path .agent-memory --id pref-imported-001 --trusted
```

## Rollback Notes

Record:

- files created by Agent Memory
- files modified by Agent Memory
- records imported as candidates
- records promoted into startup context
- records redacted or forgotten
- commands used for migration

Rollback should be possible by deleting the created `.agent-memory/` directory or reverting the explicitly listed file changes. Do not delete the user's original memory files as part of rollback.

## Handoff Check

Before treating the integration as ready:

```bash
python -m agent_memory doctor --path .agent-memory
python -m agent_memory handoff --path .agent-memory --strict
```

If warnings remain, keep the integration in candidate or audit mode and explain what needs review.
