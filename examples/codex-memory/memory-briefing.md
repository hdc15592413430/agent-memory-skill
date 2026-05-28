# Agent Memory Briefing

Use this as a short startup context for a new model or agent. Treat memory as guidance and trust the current environment.

Updated: 2026-05-28T00:00:00Z

## Objective

Create an open-source AI agent memory skill that preserves user preferences, project decisions, topic state, side ideas, and migration context across model or architecture changes.

## Summary

Agent Memory Skill is a prototype continuity skill for AI agents. It should help future agents identify important context, preserve user preferences, manage topic interruptions, and create handoff packets for model or architecture migration.

## Active Topic

- Prepare the agent-memory skill as a GitHub-ready open-source prototype. (thread-001)

## Next Actions

- Expand tests for edge cases such as stale records, superseded decisions, and conflicting topic states.
- Decide the GitHub license.
- Create a short demo showing a side topic being captured and the main thread resumed.
- Consider extracting the script into a core package after the skill protocol stabilizes.

## User Preferences

- Do not treat full transcripts as memory; prioritize curated operating state. (avoid-001)
- The user wants warm, concise Chinese collaboration with concrete progress rather than abstract theory. (pref-001)

## Key Decisions

- Use one universal memory kernel with runtime-specific adapters instead of separate agent and chat memory projects. (decision-001)

## Key Project Facts

- The first version is implemented as a Codex-compatible skill while keeping the memory protocol runtime-agnostic. (fact-001)

## Parked Or Open Topics

- Clarify whether memory should be a skill, a library, or both. (thread-002; status: parked)

## Recent Episodes

- The user raised a concern that most skills do practical external tasks, while this memory skill changes agent behavior. This should be framed as a meta-skill or continuity skill. (episode-001)

## Risks And Handoff Notes

- If memory records become too verbose, the system will recreate transcript dumping in another form.
- If adapters are mixed into the core protocol too early, the project may become Codex-specific.
- Keep the skill itself lean. Put GitHub-facing documentation outside the skill folder.
- Treat inferred user preferences as tentative unless explicitly confirmed.

For full detail, read migration-packet.md or state.json.
