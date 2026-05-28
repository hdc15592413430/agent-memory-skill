# Adapter Contract

Adapters let the same memory protocol work in Codex, ordinary chat, autonomous agents, and multi-agent systems. This contract defines what a new adapter must preserve so runtimes can differ without fragmenting memory semantics.

## Required Behavior

Every adapter must be able to:

- initialize a memory location with a valid `state.json`
- load a short startup context from `memory-briefing.md` or equivalent rendered text
- select targeted high-signal records by query, type, tag, source, scope, status, and salience
- write durable records through the core schema instead of ad hoc files
- capture opening plans or phase plans as artifacts when complex work depends on them
- write uncertain agent-inferred memory as `candidate` records and require review before reuse
- capture user preferences, project facts, decisions, artifacts, topics, and episodes with the correct record types
- preserve `source`, `scope`, `status`, `confidence`, `salience`, `evidence`, `tags`, `expires_at`, and `supersedes`
- prepare a handoff that refreshes both a short briefing and a full migration packet
- run validation and doctor checks before treating memory as handoff-ready
- support supersession when newer memory replaces older preferences, facts, decisions, or artifacts
- expose compaction plans without silently deleting memory
- redact sensitive records and refresh generated artifacts
- forget revoked records and refresh generated artifacts
- export and import portable bundles for runtime migration when the adapter supports filesystem or equivalent artifact storage

Adapters may add runtime-specific notes, UI, storage, or prompts, but they should not redefine the core memory model.

## Read Path

Adapters should read memory in this order:

1. Validate `state.json`.
2. Load a compact briefing for startup.
3. Use targeted selection for task-specific records.
4. Load the full migration packet only when detail is needed.
5. Load raw structured records only for targeted operations such as review, redaction, topic resume, or conflict resolution.

Adapters must exclude stale, superseded, candidate, and untrusted records from startup context by default unless the user or runtime explicitly requests them.

## Write Path

Adapters should write memory at natural boundaries:

- durable user preference or correction
- important decision
- tool result that changes future work
- failed attempt that should not be repeated
- topic interruption or resume
- context compaction
- opening plan or phase plan creation for complex tasks
- model, architecture, or agent handoff
- runtime export or import
- explicit user request to remember, review, redact, or forget
- explicit user correction that requires supersession

Adapters should not write every message. A record should pass the salience gate before becoming durable memory; uncertain agent guesses should use `propose` and remain candidates until promoted.

## Privacy And Consent

Adapters must document:

- where memory is stored
- whether memory can leave the local machine
- when durable writes happen automatically
- when user consent is required
- how a user can inspect, edit, export, redact, or delete memory
- how user, project, agent, role, organization, and global scopes are isolated

Chat-style adapters should ask before storing identity-adjacent or sensitive preferences. Shared or networked adapters should default to narrow scopes and make remote storage explicit.

## Topic Stack

Adapters that handle conversation flow must preserve one active topic and separate parked, open, and recently closed topics. When a side topic appears, create an episode and park the previous active thread. When a closure cue appears, resume the parked thread or ask a concise question when the cue is ambiguous.

## Multi-Agent Memory

Multi-agent adapters must keep shared memory separate from role-local memory:

- shared memory: confirmed decisions, shared constraints, shared objectives, and cross-role artifacts
- role-local memory: partial findings, specialist assumptions, role-specific artifacts, and local failed attempts

Role-local findings should not be copied into shared memory until they are promoted as confirmed decisions with evidence.

## Handoff Readiness

A handoff-ready adapter should produce:

- valid `state.json`
- fresh `memory-briefing.md`
- fresh `migration-packet.md`
- no schema errors
- no warning-level doctor issues for published examples
- clear next actions and current objective

Strict handoff should fail when warnings indicate the memory may mislead a future agent.

## Test Requirements

New adapters should add tests or evaluator scenarios that prove:

- initialization creates valid memory
- opening plan capture writes an artifact and surfaces it in handoff context
- startup context excludes stale, candidate, and untrusted records by default
- targeted selection excludes stale, candidate, and untrusted records by default
- supersession marks old records inactive so startup context does not contain conflicting old and new guidance
- compaction plans skip the active thread by default and only auto-apply `mark-stale` changes
- checkpoint or remember operations preserve source and scope
- topic interruption can park and resume a main thread when the runtime supports conversation flow
- redaction removes sensitive text from state and generated artifacts
- forgetting removes a revoked record and cleans stale supersession references
- export/import roundtrips preserve structured state and regenerate handoff artifacts
- handoff refreshes artifacts and reports readiness

The release validator should import or execute at least one adapter handoff path before the adapter is considered part of the supported project surface.
