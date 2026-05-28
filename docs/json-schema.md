# JSON Schema

Agent Memory publishes a JSON Schema for `state.json`.

Canonical locations:

- Python export: `agent_memory.schema.state_schema()`
- CLI export: `python -m agent_memory schema`
- Repository file: `schemas/state.schema.json`

## Usage

Print the schema:

```bash
python -m agent_memory schema
```

Write the schema to a file:

```bash
python -m agent_memory schema --output schemas/state.schema.json
```

Use the schema from another runtime to validate generated memory before handoff.

## Scope

The JSON Schema validates structure:

- required top-level sections
- required record fields
- legal confidence values
- salience range
- legal record statuses
- optional `source`, `scope`, `expires_at`, and `supersedes` metadata

Use `python -m agent_memory doctor` for quality checks that JSON Schema cannot express well, such as transcript-like records, missing evidence, expired active memory, unsafe external memory, and weak handoff summaries.
