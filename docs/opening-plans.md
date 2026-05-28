# Opening Plans

Complex agent work is most likely to drift when the first plan is vague or lost. `plan` captures the opening plan, phase plan, acceptance criteria, and validation commands as a durable memory artifact.

## Usage

Capture an inline plan:

```bash
python -m agent_memory plan --path .agent-memory --id plan-opening --title "Opening Implementation Plan" --body "Phase 1: inspect context. Validation: run tests." --next-action "Run phase 1 validation."
```

Capture an existing Markdown file:

```bash
python -m agent_memory plan --path .agent-memory --id plan-release --title "Release Plan" --input docs/release-plan.md --next-action "Start with phase 1."
```

The command writes:

- `.agent-memory/plans/<id>.md`
- a high-salience `project.artifacts` record tagged `plan` and `opening-plan`
- a handoff note that tells the next agent to read the plan before implementation
- any repeatable `--next-action` values

It also refreshes `state.json`, `memory-briefing.md`, and `migration-packet.md`.

## What To Put In The Plan

Use a short Markdown plan with:

- clarified requirements
- chosen approach
- rejected alternatives when they matter
- phases
- acceptance criteria
- validation commands
- manual review points

The plan should be specific enough that a cheaper or fresh model can continue without guessing the intended direction.

## Handoff Behavior

`brief`, `handoff`, and the migration packet surface the plan differently:

- `memory-briefing.md` includes the handoff note and plan-linked next actions.
- `migration-packet.md` includes the plan artifact record.
- `.agent-memory/plans/<id>.md` keeps the full phase details out of the default context until needed.

This keeps startup context small while preserving the critical opening constraints.
