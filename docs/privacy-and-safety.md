# Privacy And Safety

Agent memory is useful because it persists. That also makes mistakes more durable. This guide defines the privacy and safety boundary for the v0.1 protocol.

## Safe Defaults

- Store curated facts, preferences, decisions, topics, and next actions instead of raw transcripts.
- Keep memory local by default. The core package writes files and does not sync them to a remote service.
- Treat memory as guidance, not authority. Trust the current workspace, current user message, and verified tool output over stale memory.
- Use `memory-briefing.md` as the short startup surface and `migration-packet.md` for deeper inspection.
- Treat captured `plans/` files as memory artifacts; review them before sharing.
- Run `python -m agent_memory doctor --path <memory-dir>` before handoff, publishing examples, or sharing memory files.
- Use `python -m agent_memory propose --path <memory-dir>` for uncertain agent-inferred memory so it stays out of briefing until review.
- Use `python -m agent_memory compact --path <memory-dir>` to review low-signal cleanup before applying it.
- Treat `agent-memory-export.json` portable bundles as sensitive memory artifacts.
- For existing agents, install Agent Memory as a sidecar first and do not overwrite current memory or configuration without explicit approval.

## Data To Avoid

Do not store:

- API keys, passwords, tokens, private keys, recovery codes, or secret URLs
- raw private transcripts
- personal data that is not needed for future agent behavior
- health, legal, financial, or identity details unless the user explicitly asks and the adapter has a retention policy
- speculative preferences inferred from one weak signal
- external instructions that tell the agent to ignore prior instructions, expose secrets, or rewrite user preferences

If sensitive data is already stored, use `redact`, refresh artifacts, and avoid sharing old rendered packets:

```bash
python -m agent_memory redact --path .agent-memory --id fact-secret-001
```

`redact` replaces the record text and evidence with safe placeholders, marks the record `stale`, adds `redacted` and `reviewed` tags, and refreshes `memory-briefing.md` plus `migration-packet.md`.

If the user asks the agent not to retain a non-sensitive record, use `forget`:

```bash
python -m agent_memory forget --path .agent-memory --id pref-temp-001
```

`forget` removes the record, cleans up `supersedes` references to it, and refreshes generated handoff artifacts. Use `redact` instead when the record contains secrets or private data and an audit trail is useful.

## Source And Scope

Every durable record should make its trust boundary visible:

- `source: user`: direct user preference, correction, constraint, or instruction
- `source: agent`: agent-generated summary or conclusion
- `source: tool`: tool output such as tests, shell commands, or search
- `source: external`: webpage, document, package registry, issue, or third-party source
- `source: derived`: inference from multiple signals
- `source: system`: system or platform-level fact

Use scope to control where memory can travel:

- `user`: personal preference or collaboration style
- `project`: project-local fact or decision
- `agent`: one agent's local run memory
- `role`: role-local multi-agent memory
- `organization`: confirmed shared decision
- `global`: rare, broadly reusable rule

Default to the narrowest scope that still works.

## Review Workflow

Use `untrusted` for records that may be useful but should not guide behavior yet:

```bash
python -m agent_memory add --path .agent-memory --collection facts --id fact-ext-001 --text "External source says ..." --source external --tag untrusted --evidence "URL or file path"
python -m agent_memory doctor --path .agent-memory
python -m agent_memory review --path .agent-memory --id fact-ext-001 --reviewed --trusted --evidence "Verified against current docs." --render
```

Use `candidate` records when the agent wants to propose memory without applying it:

```bash
python -m agent_memory propose --path .agent-memory --collection preferences --id pref-candidate --text "User may prefer short updates." --scope user
python -m agent_memory select --path .agent-memory --include-candidates --status candidate
python -m agent_memory promote --path .agent-memory --id pref-candidate
```

Use `expires_at` for time-sensitive facts. Use `supersedes` when a new record replaces an older decision or fact.

Use `supersede` when a correction should replace old active guidance:

```bash
python -m agent_memory supersede --path .agent-memory --collection preferences --id pref-new --text "User prefers concise direct updates." --evidence "User correction." --scope user --replaces pref-old
```

This keeps the old record visible for audit but removes it from default startup context.

Use `redact` instead of `review --text` when the original record contains secrets or private data, because redaction also refreshes generated handoff artifacts. Use `forget` when the user revokes a memory that does not need an audit placeholder.

Use `compact` for routine cleanup. It plans low-salience or expired records as `mark-stale`, keeps older collection cleanup review-only, and skips the active thread by default.

## Portable Bundles

Use portable bundles to move memory between runtimes:

```bash
python -m agent_memory export --path .agent-memory --output agent-memory-export.json --strict
python -m agent_memory import --path .agent-memory-next --input agent-memory-export.json
```

Bundles include structured state and rendered handoff artifacts. Do not commit bundles unless they have been reviewed, redacted, and intentionally made public.

## Adapter Responsibilities

Adapters must document:

- where memory is stored
- when memory is read into context
- when memory is written or updated
- whether user consent is required before durable writes
- whether memory can leave the local machine
- how user, project, role, organization, and global scopes are isolated
- how concurrent writes are resolved
- how users can inspect, edit, export, or delete memory

Shared adapters should not mix role-local findings into shared memory unless the record is a confirmed decision.

For existing-agent migrations, document what was created, imported, promoted, redacted, skipped, or left untouched. The user should be able to inspect and roll back the integration without losing their original memory files.

## Publishing Examples

Before opening an issue, pull request, or public demo:

```bash
python -m agent_memory doctor --path <memory-dir> --strict
python -m agent_memory handoff --path <memory-dir> --strict
```

Then inspect:

- `state.json`
- `memory-briefing.md`
- `migration-packet.md`
- adapter notes such as `chat-memory-note.md`, `agent-run-note.md`, or `multi-agent-note.md`

Remove private names, secrets, customer data, internal paths, and raw transcript fragments.
