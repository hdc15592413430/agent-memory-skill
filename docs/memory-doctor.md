# Memory Doctor

`doctor` audits memory quality beyond basic schema validation.

`validate` answers:

- Is the state structurally valid?
- Are required fields present?
- Are salience and confidence values legal?

`doctor` answers:

- Is the memory useful for handoff?
- Are high-salience records supported by evidence?
- Is the migration packet missing objective, summary, or next actions?
- Are records too transcript-like or too long?
- Are duplicate record IDs present?
- Are expired memories still active?
- Did high-impact memory come from a tool, external source, or derived note without review?
- Is there candidate memory waiting for review before promotion?
- Does a record look like prompt injection, secret-handling text, or memory poisoning?
- Does a record supersede an unknown memory ID?
- Does a replacement leave the superseded record active?

## Usage

```bash
python -m agent_memory doctor --path .agent-memory
```

Use strict mode in CI or before release:

```bash
python -m agent_memory doctor --path .agent-memory --strict
```

Strict mode exits non-zero on warnings. Without strict mode, only schema errors fail the command.

Use `handoff` when you also want fresh handoff artifacts:

```bash
python -m agent_memory handoff --path .agent-memory --strict
```

`handoff` writes `memory-briefing.md` and `migration-packet.md`, then applies the same quality checks.

Use `compact` after doctor when the issue is long-running memory bloat rather than a schema or trust problem:

```bash
python -m agent_memory compact --path .agent-memory
python -m agent_memory compact --path .agent-memory --apply
```

## Review Workflow

Use `review` after `doctor` flags a record:

```bash
python -m agent_memory review --path .agent-memory --id fact-001 --reviewed --trusted
python -m agent_memory review --path .agent-memory --id fact-002 --status stale --clear-expires-at --render
python -m agent_memory review --path .agent-memory --id decision-new --supersedes decision-old --render
python -m agent_memory promote --path .agent-memory --id pref-candidate
```

Use `supersede` when adding a replacement for older active memory:

```bash
python -m agent_memory supersede --path .agent-memory --collection preferences --id pref-new --text "User prefers concise direct updates." --evidence "User correction." --scope user --replaces pref-old
```

Use `redact` when the record contains sensitive text:

```bash
python -m agent_memory redact --path .agent-memory --id fact-secret-001
```

Redaction replaces the record text and evidence with safe placeholders, marks the record stale, adds `redacted` and `reviewed` tags, and refreshes both generated handoff artifacts.

Use `forget` when the user revokes a non-sensitive memory and wants it removed:

```bash
python -m agent_memory forget --path .agent-memory --id pref-temp-001
```

Forgetting removes the record, cleans up `supersedes` references to it, and refreshes both generated handoff artifacts.

Common actions:

- `--reviewed`: add the `reviewed` tag.
- `--trusted`: remove the `untrusted` tag.
- `--status stale`: keep a record for audit but stop applying it as active guidance.
- `--status superseded --supersedes old-id`: mark replacement relationships explicitly.
- `--evidence "..."`: replace weak evidence with a concrete source.
- `--clear-expires-at`: remove an expiry timestamp after review.
- `--render`: refresh `migration-packet.md`.

Candidate records are reported as info-level review items. Use `select --include-candidates` to inspect the queue and `promote` only after the memory is confirmed.

## Issue Severity

- `ERROR`: invalid or conflicting memory, such as duplicate record IDs or schema errors.
- `WARNING`: memory may mislead a future agent or weaken handoff.
- `INFO`: useful cleanup suggestion, usually not urgent.

## Why It Matters

Agent memory gets worse when it quietly turns into a transcript. The doctor command is a lightweight guardrail against memory bloat and weak handoffs.

It also catches early safety issues. Persistent memory can outlive the original conversation, so poisoned or stale records are more dangerous than ordinary bad context.
