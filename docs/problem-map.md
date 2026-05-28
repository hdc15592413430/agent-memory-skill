# Problem Map

This document maps the practical memory problems behind the project to concrete mechanisms in the skill.

## 1. Model Or Architecture Migration

Problem: copying the full transcript into a new model or architecture does not tell the new agent what matters.

Mechanisms:

- Salience gate: store only records that change future behavior, preserve decisions, reduce rediscovery cost, or keep open commitments.
- Memory briefing: render a short startup context for the next model or agent.
- Migration packet: render the current objective, preferences, decisions, topic stack, artifacts, next actions, and risks.
- `handoff` command: refresh the briefing and migration packet together, then audit whether the memory is ready for migration.
- Confidence and status fields: separate confirmed facts from tentative inferences, stale records, and superseded decisions.

Expected outcome:

- A new model can read a short briefing first, then a fuller handoff packet if needed, instead of reinterpreting the entire conversation. Strict handoff can fail early when the memory is too weak to trust.

## 2. Opening Plan Drift

Problem: for complex coding tasks, the first plan often determines whether the rest of the agent run stays on track. If the requirements, phase boundaries, and validation gates are not preserved, a later agent may implement the wrong thing very efficiently.

Mechanisms:

- Migration metadata: keep objective, summary, next actions, risks, and handoff notes explicit.
- Artifact records: keep important plan files, phase plans, and acceptance criteria discoverable.
- `plan` command: write `.agent-memory/plans/<id>.md`, register the plan as an artifact, and surface it in handoff notes.
- Decision records: preserve the chosen approach and rejected alternatives.
- `handoff` command: refresh the plan-aware startup briefing before model switches, context compaction, or long pauses.

Expected outcome:

- A new agent can start from the intended design and validation criteria instead of reconstructing the plan from scattered conversation context.

## 3. User Preference Transfer

Problem: a new agent does not automatically learn the user's collaboration style, preferences, constraints, and dislikes.

Mechanisms:

- `user_profile.preferences`: durable behavior preferences.
- `user_profile.working_style`: how the user likes work to proceed.
- `user_profile.avoid`: things future agents should not repeat.
- Evidence fields: prevent weak guesses from becoming permanent personality assumptions.
- `supersede` command: replace old preferences without leaving conflicting active guidance.

Expected outcome:

- A new agent can quickly adapt tone, autonomy, output shape, and decision style.

## 4. Topic Interruption And Return

Problem: during an active topic, the user introduces a side idea. The agent may forget the main thread, lose the side idea, or fail to resume properly.

Mechanisms:

- Topic stack: one active thread, plus parked, open, and recently closed threads.
- Episode records: capture side ideas without letting them overwrite the main objective.
- Closure cues: detect when the side thread has ended and resume the parked topic.
- `cue` command: classify the latest message as `resume`, `stay`, or `ask`, with optional safe auto-resume.

Expected outcome:

- The agent can say, in effect: "I captured that side idea. Returning to the prior thread, the next step is..."

## 5. Memory Bloat

Problem: if every message becomes memory, memory becomes another transcript and loses its usefulness.

Mechanisms:

- Salience scores from 1 to 5.
- Explicit "do not store" guidance.
- Compact migration packet as the primary handoff surface.
- Candidate records for uncertain agent-written memory, separate from confirmed startup context.
- `doctor` audit to flag transcript-like records, missing evidence, and low-salience active memory.
- `compact` planning to mark safe low-signal records stale while keeping deletion review-only.

Expected outcome:

- Memory remains small enough to read and useful enough to guide action.

## 6. Runtime Portability

Problem: Codex, normal chat assistants, autonomous agents, and multi-agent systems have different storage and trigger surfaces.

Mechanisms:

- Universal kernel: schema, salience, topic stack, migration packet.
- Runtime adapters: Codex workspace files, chat memory notes, autonomous checkpoints, and shared multi-agent memory.

Expected outcome:

- The project can start as a Codex skill without becoming locked to Codex.

## 7. Stale Or Superseded Memory

Problem: old memory may be false, outdated, or only true for one phase of the project.

Mechanisms:

- `status`: use `stale`, `superseded`, or `closed` instead of silently deleting memory.
- `expires_at`: optional review timestamp for time-sensitive records.
- `supersedes`: optional record IDs that this memory replaces.
- `doctor` audit: flag expired active memory and unknown superseded IDs.
- `doctor` audit: flag replacements that leave superseded records active.
- `compact` command: plan and apply conservative stale-status updates for expired or low-salience records.

Expected outcome:

- A future agent treats memory as guidance and can see which records should no longer drive behavior.

## 8. Memory Poisoning And Unsafe Sources

Problem: external documents, webpages, repositories, tool outputs, or other agents can inject instructions that persist as memory.

Mechanisms:

- `source`: distinguish `user`, `agent`, `tool`, `external`, `system`, and `derived` memory.
- `scope`: distinguish user, project, agent, role, organization, and global memory.
- `untrusted` and `reviewed` tags: keep suspect records visible without promoting them prematurely.
- `doctor` audit: flag instruction-like text, secret-handling text, untrusted active records, and high-impact non-user records that lack review.

Expected outcome:

- Memory from outside the user-agent trust boundary is inspectable and less likely to become persistent behavior control.

## 9. Experience Replay Quality

Problem: agents may copy a past execution pattern even when it was wrong, outdated, or only locally successful.

Mechanisms:

- Failed attempts are stored as artifacts and risks, not as successful recipes.
- High-salience records require evidence and confidence.
- Low-confidence critical memory triggers a doctor warning.

Expected outcome:

- Future agents can learn from mistakes without blindly replaying bad trajectories.

## 10. Evaluation Gap

Problem: memory systems often feel plausible in demos but fail on retrieval accuracy, temporal reasoning, updates, abstention, and multi-session continuity.

Mechanisms:

- Keep deterministic CLI demos for topic interruption, chat memory, autonomous agent runs, and multi-agent separation.
- Use `doctor` as a lightweight quality gate before larger benchmark work.
- Track LongMemEval-style abilities as future evaluation targets.

Expected outcome:

- The project has a path from useful local skill to measurable open-source memory protocol.

## V0.1 Definition

The v0.1 prototype should prove:

- The skill has a valid Codex skill format.
- A memory state can be initialized, validated, and rendered.
- The example demonstrates preference transfer, topic parking, side episodes, decisions, and migration context.
- The GitHub project explains the problem clearly enough for new contributors.
- The project documents public memory-system pain points beyond the author's initial examples.
- The project documents security, privacy, source/scope, and memory review boundaries before public use.
