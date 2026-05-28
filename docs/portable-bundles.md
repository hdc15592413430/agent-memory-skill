# Portable Bundles

Portable bundles move curated memory between models, agent architectures, or runtimes without copying an entire transcript or workspace.

## Export

```bash
python -m agent_memory export --path .agent-memory --output agent-memory-export.json
python -m agent_memory export --path .agent-memory --output agent-memory-export.json --strict
```

`--strict` fails when doctor reports warning-level issues. Use it before sharing a bundle or moving memory into a higher-trust runtime.

## Import

```bash
python -m agent_memory import --path .agent-memory-restored --input agent-memory-export.json
python -m agent_memory import --path .agent-memory-restored --input agent-memory-export.json --force
```

Import validates the bundled `state`, writes it to the target memory directory, and regenerates `memory-briefing.md` plus `migration-packet.md` from the structured state.

## Bundle Shape

A bundle is JSON with:

- `format`: `agent-memory-bundle`
- `version`: bundle format version
- `exported_at`: export timestamp
- `state`: canonical structured memory state
- `artifacts`: rendered `memory-briefing.md` and `migration-packet.md`
- `audit`: doctor issues and handoff readiness at export time

Import trusts the structured state only after validation. Rendered artifacts are useful for inspection, but import regenerates artifacts from state so stale exported Markdown does not become authoritative.

## Safety

Bundles can contain user preferences, project facts, private artifacts, and handoff notes. Treat them like memory files:

- do not commit exported bundles by accident
- run `doctor --strict` or `export --strict` before sharing
- run `redact` or `forget` before export when memory contains sensitive or revoked records
- prefer project-local or role-local scopes unless the target runtime really needs broader memory

## Migration Workflow

Recommended runtime migration flow:

```bash
python -m agent_memory doctor --path .agent-memory --strict
python -m agent_memory export --path .agent-memory --output agent-memory-export.json --strict
python -m agent_memory import --path .agent-memory-next --input agent-memory-export.json
python -m agent_memory handoff --path .agent-memory-next --strict
```

The new runtime should read `memory-briefing.md` first, then inspect `migration-packet.md` only when it needs detail.
