# Architecture

Agent Memory has three layers:

## 1. Skill Layer

Path: `agent-memory/`

This is the agent-facing operating guide. It tells an AI agent:

- when to read memory
- what deserves to be remembered
- how to manage topic interruptions
- how to prepare a migration packet
- how to avoid transcript dumping

The skill layer should stay concise. It should point to references and scripts instead of carrying every implementation detail in `SKILL.md`.

## 2. Core Layer

Path: `agent_memory/`

This is the reusable Python package. It owns:

- the canonical state shape
- validation
- record creation
- salience ordering
- source, scope, expiry, and supersession metadata
- supersession updates for corrected preferences, facts, and decisions
- candidate memory proposal and promotion
- opening plan artifact capture
- topic stack operations
- closure cue detection for topic resumption
- startup briefing rendering
- migration packet rendering
- targeted selection and conservative compaction planning
- handoff readiness CLI workflow
- atomic local file writes and `state.json` revision checks for the reference filesystem backend
- the CLI used by demos and adapters

The core should not know about Codex, chat products, or a specific agent runtime.

## 3. Adapter Layer

Future paths:

- `agent_memory/adapters/codex.py`
- `agent_memory/adapters/chat.py`
- `agent_memory/adapters/agent.py`
- `agent_memory/adapters/multi_agent.py`

Adapters decide runtime-specific behavior:

- where memory is stored
- when memory is loaded
- when memory is updated
- how much memory is injected into context
- how user consent and privacy are handled
- how trust boundaries are represented with `source` and `scope`
- how conflicting writes are resolved

## Data Flow

```text
agent runtime
  -> adapter decides when to read/write
  -> agent_memory.core updates state.json
  -> memory-briefing.md is rendered for startup
  -> migration-packet.md is rendered for handoff
  -> doctor or handoff checks readiness
  -> skill guidance tells the next agent how to use it
```

## Design Boundary

Keep in core:

- portable memory semantics
- schema and validation
- topic stack operations
- source/scope validation
- expiry, supersession, and memory-safety audits
- selection, candidate review, and compaction policies that remain runtime-agnostic
- adaptive integration recommendations and session health assessment
- rendering

Keep out of core:

- product-specific memory APIs
- UI behavior
- hidden platform storage
- model-specific prompt hacks
- runtime-specific privacy policy

This boundary lets the project start as a Codex-compatible skill while remaining useful for ordinary AI chat, autonomous agents, and multi-agent systems.
