# Topic Management

Use this reference when a conversation branches, pauses, or returns to an earlier thread.

## Topic Stack

Represent topics as a stack:

- `active`: the current thread being worked.
- `parked`: earlier active threads paused by an interruption.
- `open`: topics that still need work but are not next in line.
- `closed_recently`: completed threads retained briefly for continuity.

## Interruption Protocol

When the user introduces a side point during an active task:

1. Snapshot the active thread: objective, latest state, next action.
2. Create an episode for the side point.
3. Mark the side point as active if the user wants to pursue it now.
4. After the side point closes, resume the parked thread and state the next action briefly.

Example memory update:

```json
{
  "id": "episode-20260528-idea-001",
  "text": "User raised a side idea: memory should preserve small interruptions and recall them later if mentioned.",
  "status": "active",
  "confidence": "high",
  "salience": 5,
  "evidence": "User described this as a core problem for the open-source memory skill.",
  "tags": ["topic-stack", "side-idea", "memory-design"]
}
```

## Closure Cues

Treat the side thread as closed or parkable when:

- The user explicitly says it is done, solved, or should be left for later.
- The requested deliverable has been produced.
- The user says "back to", "continue", "resume", or similar.
- The next user message clearly returns to the previous objective.

If the closure cue is weak but the consequence is low, resume and mention it lightly. If the consequence is high, ask one concise question.

Use `cue` to turn this into a repeatable check:

```bash
python -m agent_memory cue --path .agent-memory --text "back to the previous topic"
python -m agent_memory cue --path .agent-memory --text "回到之前的话题继续" --auto-resume --render
```

`cue` returns one of:

- `resume`: explicit return or closure cue with a parked topic available.
- `stay`: no parked topic or no closure cue.
- `ask`: ambiguous continuation cue such as "continue" or "继续".

## Resuming The Main Thread

When resuming, do not force the user to restate context. Use a short transition:

```text
Got it. I captured that as a side idea. Returning to the previous thread: we were deciding how the migration packet should prioritize user preferences and current project state.
```

Then continue with the next concrete action.

## Memory Rules For Episodes

Store an episode when:

- It introduces a new product idea, constraint, concern, or feature.
- It changes future priorities.
- The user asks to remember it.
- It explains why the conversation changed direction.

Skip or discard an episode when it is only a temporary aside, joke, or logistical note with no future use.
