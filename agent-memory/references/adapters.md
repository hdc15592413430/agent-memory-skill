# Runtime Adapters

Use this reference when deciding whether memory behavior should be universal or runtime-specific.

## Recommendation

Do not split agent memory and AI chat memory into separate projects at the protocol level. Use one universal memory kernel with separate runtime adapters.

The kernel defines what memory means. Adapters define how memory is used in a particular environment.

## Universal Memory Kernel

The kernel should stay stable across runtimes:

- Memory types: preference, project fact, decision, thread, episode, artifact, migration note.
- Salience gate and confidence levels.
- Topic stack semantics.
- Migration packet format.
- Opening plan artifact capture for complex work.
- Stale, superseded, candidate, active, and tentative statuses.
- Retrieval order for resuming work.

This is the portable part across Codex, normal AI chat, API assistants, autonomous agents, and multi-agent systems.

## Adapter Responsibilities

Adapters decide:

- Where memory is stored.
- When memory is loaded.
- When memory is updated.
- Which tools can write memory.
- How user consent and privacy are handled.
- How much memory is injected into context.
- How conflicts are resolved when multiple agents write memory.

## Codex Skill Adapter

Codex is workspace-centered, artifact-heavy, and task-oriented.

Recommended behavior:

- Store memory in `.agent-memory/` inside the workspace unless the user chooses another path.
- Read memory before continuity-sensitive coding, planning, reviewing, or document tasks. Use the short briefing for prompt context and the full packet for detail.
- Update memory after significant file changes, decisions, task completion, topic switches, and context compaction.
- Use `propose` for inferred or agent-written memory that needs user or workflow review before reuse.
- Capture phase plans and validation gates as plan artifacts before long implementation runs.
- Run workspace handoff before model switches or long pauses so both `memory-briefing.md` and `migration-packet.md` are fresh.
- Keep file paths and command outputs as artifacts when they matter for future work.

The open-source prototype includes `agent_memory.adapters.codex`, which can initialize workspace memory, print briefing-based prompt context, write checkpoints, and prepare handoff artifacts.

## Ordinary AI Chat Adapter

General chat is conversation-centered and may not have a filesystem.

Recommended behavior:

- Store memory in the platform's memory store or a user-visible note artifact.
- Ask before storing sensitive or identity-adjacent information.
- Prefer short preference and episode records over project-heavy state.
- Use topic stack summaries to return to earlier conversation threads.
- Make memory updates visible when trust matters.

The open-source prototype includes `agent_memory.adapters.chat`, which can store preferences and episodes, manage side topics, render a user-visible `chat-memory-note.md`, and prepare chat handoff artifacts.

## Autonomous Agent Adapter

Autonomous agents are action-centered and may run for many steps without user supervision.

Recommended behavior:

- Write memory at explicit checkpoints.
- Separate observations from decisions.
- Store tool results as artifacts only when they affect future actions.
- Use stricter salience thresholds to avoid runaway memory growth.
- Include rollback notes and known failed attempts.

The open-source prototype includes `agent_memory.adapters.agent`, which can write checkpoints, record important tool results, record failed attempts, render `agent-run-note.md`, and prepare agent-run handoff artifacts.

## Multi-Agent Adapter

Multi-agent systems need shared memory plus role-local memory.

Recommended behavior:

- Keep a shared project memory for decisions, constraints, artifacts, and active objectives.
- Keep role-local memory for specialist assumptions and partial findings.
- Require evidence fields for shared memory writes.
- Resolve conflicts by status instead of deletion: active, tentative, candidate, superseded, stale.
- Render migration packets per role and one shared packet for orchestration.

The open-source prototype includes `agent_memory.adapters.multi_agent`, which separates `shared` memory from `roles/<role>` memory, renders `multi-agent-note.md`, and prepares shared plus role-local handoff artifacts.

## Product Shape

For open source, structure the project as:

- `agent_memory.core`: schema, salience rules, topic stack, migration packet renderer.
- `adapters/codex`: filesystem and skill workflow.
- `adapters/chat`: platform memory and user-visible memory notes.
- `adapters/agent`: checkpointing and tool-run memory.
- `adapters/multi-agent`: shared state and conflict handling.

This preserves one conceptual memory system while letting each runtime integrate naturally.
