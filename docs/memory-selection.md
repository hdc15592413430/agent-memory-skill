# Memory Selection

`select` retrieves targeted high-signal memory records without loading the full migration packet.

Use it when a new model or agent needs a narrow slice of memory:

- user preferences for a specific workflow
- decisions related to one feature
- role-local or project-local facts
- high-salience records tagged for migration, startup, safety, or evaluation

## Usage

Select by keyword:

```bash
python -m agent_memory select --path .agent-memory --query "model migration"
```

Select high-salience preferences:

```bash
python -m agent_memory select --path .agent-memory --collection preferences --min-salience 4
```

Select tagged records as JSON:

```bash
python -m agent_memory select --path .agent-memory --tag migration --min-salience 4 --json
```

Include stale or untrusted records explicitly:

```bash
python -m agent_memory select --path .agent-memory --query "old adapter" --include-stale
python -m agent_memory select --path .agent-memory --query "external source" --include-untrusted
python -m agent_memory select --path .agent-memory --status candidate --include-candidates
```

## Default Filters

By default, `select` excludes:

- `status: stale`
- `status: superseded`
- `status: candidate`
- records tagged `untrusted`

This matches the briefing behavior. Use explicit flags when reviewing old, candidate, or untrusted records.

Use `python -m agent_memory supersede --path .agent-memory ... --replaces <old-id>` when selection returns conflicting old and new guidance that should be represented as a knowledge update.

When default selection returns too much low-signal memory, run `python -m agent_memory compact --path .agent-memory` to review cleanup suggestions before applying them.

## Selection Fields

Filters include:

- `--query`: keyword or phrase matched across id, text, type, status, evidence, source, scope, tags, and path
- `--collection`: collection or path fragment such as `preferences`, `decisions`, or `threads`
- `--type`: record type such as `preference`, `decision`, `project_fact`, `thread`, `episode`, or `artifact`
- `--tag`: required tag, repeatable
- `--status`: status filter, repeatable
- `--source`: source filter, repeatable
- `--scope`: scope filter, repeatable
- `--min-salience`: minimum salience from 1 to 5
- `--limit`: maximum records to return

Results are sorted by selection score, salience, update time, and id. The score is deterministic and favors direct query matches in record text, id/path, evidence, and tags.

## How To Use With Handoff

Recommended startup flow:

```bash
python -m agent_memory brief --path .agent-memory
python -m agent_memory select --path .agent-memory --query "current task" --min-salience 4
python -m agent_memory render --path .agent-memory
```

Read the briefing first, use `select` for targeted context, and read the full migration packet only when the selected records are not enough.
