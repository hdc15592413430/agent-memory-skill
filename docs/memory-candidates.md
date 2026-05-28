# Memory Candidates

Candidate memory is for notes the agent thinks may matter, but should not shape future startup context until reviewed.

Use it when the signal is plausible but not confirmed: inferred preferences, tentative facts, side observations, or tool-derived notes that may be wrong. Candidate records use `status: candidate` and tags such as `candidate` and `needs-review`.

## Commands

```bash
python -m agent_memory propose --path .agent-memory --collection preferences --id pref-style-candidate --text "User may prefer short progress updates." --scope user
python -m agent_memory select --path .agent-memory --include-candidates --status candidate
python -m agent_memory promote --path .agent-memory --id pref-style-candidate
```

## Behavior

- `python -m agent_memory propose` writes a candidate record.
- Candidate records are excluded from `memory-briefing.md` by default.
- Candidate records are excluded from targeted selection unless `--include-candidates` or `--status candidate` is used.
- `doctor` reports candidate records as a review queue.
- `python -m agent_memory promote` marks the record active or tentative, removes candidate review tags, adds `reviewed` by default, and refreshes briefing and packet artifacts.

## Suggested Rule

Store user-confirmed preferences and project decisions with `add` or `supersede`. Store agent guesses with `propose`, then promote only when the user, adapter, or review workflow confirms them.
