# Memory Updates

Memory changes over time. A user can correct a preference, a project decision can be replaced, and an old fact can become wrong. `supersede` records knowledge updates without letting old guidance stay active.

## Usage

Replace one old record:

```bash
python -m agent_memory supersede --path .agent-memory --collection preferences --id pref-new --text "User prefers concise direct updates." --evidence "User corrected the old preference." --scope user --confidence high --salience 5 --replaces pref-old
```

Replace multiple old records:

```bash
python -m agent_memory supersede --path .agent-memory --collection decisions --id decision-new --text "Use portable bundles for runtime migration." --evidence "Architecture review." --confidence high --salience 5 --replaces decision-old-a --replaces decision-old-b
```

By default, replaced records are marked `superseded`. Use `--old-status stale` when the old record was not wrong but should no longer guide startup context.

## Why This Exists

Without supersession, a new model can read both the old and new preference and fail to know which one should drive behavior. This is one of the core long-term memory failures: storage keeps growing, but the agent lacks an update policy.

`supersede` does three things in one safe update:

- adds a replacement record
- writes the replacement's `supersedes` links
- marks replaced records `superseded` and adds a `superseded` tag

It also refreshes `memory-briefing.md` and `migration-packet.md`.

## Doctor Checks

`doctor` flags a risky state when a record says it supersedes another record but the old record is still active, tentative, or parked:

```bash
python -m agent_memory doctor --path .agent-memory
```

Use `supersede` for new updates, or repair older states with:

```bash
python -m agent_memory review --path .agent-memory --id pref-old --status superseded --tag superseded --render
```

## Read Behavior

Default startup surfaces exclude superseded records:

- `brief` excludes `status: superseded`
- `select` excludes `status: superseded`
- `handoff` briefing excludes `status: superseded`

The full migration packet still shows superseded records with their status so a future agent can audit why the change happened.
