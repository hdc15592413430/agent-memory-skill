# Roadmap

Agent Memory is meant to become a small, portable memory protocol for AI agents, not a transcript store. The roadmap is organized around memory failures the project should prevent.

## V0.1: Local Protocol Prototype

Status: current prototype.

Goals:

- Provide a valid Codex skill folder.
- Provide a reusable Python core for `state.json`, validation, topic stack operations, briefing, and migration packet rendering.
- Support Codex, ordinary chat, autonomous-agent, and multi-agent adapter examples.
- Preserve durable user preferences, active topics, side episodes, decisions, artifacts, and next actions.
- Preserve complex opening plans as artifacts so fresh agents start from phase requirements and validation gates.
- Add memory quality checks for transcript bloat, weak evidence, stale memory, untrusted sources, poisoning-like text, and redaction.
- Provide portable export and import bundles for model, architecture, and runtime migration.
- Provide deterministic targeted selection for high-signal memory records.
- Provide candidate review flow so agent guesses do not enter startup context until promoted.
- Provide supersession flow for replacing old preferences, facts, and decisions without conflicting active memory.
- Provide reviewable compaction planning that can mark low-signal or expired records stale without deleting audit history.
- Provide release validation, behavior scenario evaluation, security guidance, and public contribution templates.

## V0.2: Adapter Hardening

Goals:

- Treat `docs/adapter-contract.md` as the acceptance checklist for new adapters.
- Add adapter fixtures that prove each runtime can initialize memory, load startup context, write a checkpoint, handle topic interruption, redact sensitive memory, and prepare handoff.
- Add explicit consent hooks for durable writes in chat and user-profile memory flows.
- Add conflict examples for concurrent multi-agent writes.
- Harden import/export helpers for moving memory between compatible runtimes, including adapter-specific consent and storage policies.

## V0.3: Retrieval And Compaction

Goals:

- Expand deterministic retrieval helpers beyond v0.1 selection into richer query plans and adapter-specific retrieval policies.
- Expand compaction policies for long-running memory directories, including richer summaries, archive conventions, and adapter-specific retention controls.
- Expand update flows for temporal facts, conflicting records, and cross-adapter merge conflicts without hiding audit history.
- Add evaluation cases for temporal updates, abstention, stale-record handling, and memory conflicts.

## V0.4: Runtime Integrations

Goals:

- Document integration recipes for popular agent frameworks without coupling the core to one framework.
- Add optional storage backends behind adapter boundaries.
- Keep local file storage as the reference backend.
- Require each networked or shared backend to document privacy, deletion, export, and trust boundaries.

## Contribution Lanes

Good first contributions:

- Add examples for realistic memory handoffs.
- Improve adapter docs for a specific runtime.
- Add behavior evaluator scenarios for memory failures not covered yet.
- Improve `doctor` checks for stale, poisoned, duplicated, or over-broad memory.

Larger contributions:

- Implement a new adapter that follows `docs/adapter-contract.md`.
- Add retrieval and compaction helpers with tests.
- Add benchmark-style evaluations while keeping deterministic local tests fast.
- Improve privacy and consent flows for user-scoped memory.

## Non-Goals For Now

- Store full transcripts as memory.
- Build a hidden remote memory service into the core package.
- Let an adapter silently upload local memory.
- Treat external documents or tool outputs as trusted user preferences.
- Replace project-specific judgment with automatic memory writes.
