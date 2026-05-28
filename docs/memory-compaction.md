# Memory Compaction

`compact` keeps long-running memory directories useful without treating cleanup as silent deletion.

Use it when memory has accumulated low-signal notes, expired records, many old closed topics, or old artifacts that a future agent should not load by default.

## Usage

Print a reviewable plan:

```bash
python -m agent_memory compact --path .agent-memory
```

Print JSON for tooling:

```bash
python -m agent_memory compact --path .agent-memory --json
```

Apply only conservative auto-applicable changes:

```bash
python -m agent_memory compact --path .agent-memory --apply
```

Tune the salience threshold:

```bash
python -m agent_memory compact --path .agent-memory --min-salience 4
```

By default, the active thread is skipped. Include it only when you are sure the current topic is safe to review:

```bash
python -m agent_memory compact --path .agent-memory --include-active-thread
```

## What The Plan Can Suggest

- `mark-stale`: auto-applicable for active or tentative records below `--min-salience`, or active records past `expires_at`.
- `review-for-forget`: review-only for old closed threads, episodes, or artifacts over the configured collection limits.

`--apply` only applies `mark-stale` suggestions. It adds the `compacted` tag, refreshes `state.json`, `memory-briefing.md`, and `migration-packet.md`, and leaves review-only suggestions untouched.

## Why It Does Not Delete By Default

Compaction should reduce startup noise without hiding audit history. Marking a record `stale` removes it from default briefing and selection paths, but keeps the record available for review. Use `forget` only when the user revokes a memory or a maintainer intentionally removes review-only old records.

## Recommended Flow

```bash
python -m agent_memory doctor --path .agent-memory
python -m agent_memory compact --path .agent-memory
python -m agent_memory compact --path .agent-memory --apply
python -m agent_memory handoff --path .agent-memory
```

Read `doctor` findings first for schema, safety, poisoning, evidence, and trust issues. Use `compact` for low-signal cleanup after quality issues are understood.
