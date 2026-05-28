# Evaluation Scenarios

`scripts/evaluate_memory_scenarios.py` is a lightweight behavior evaluator for the claims this project makes about agent memory. It is not a model benchmark. It checks whether the protocol still preserves the right operating state when the implementation changes.

Run it with temporary artifacts:

```bash
python scripts/evaluate_memory_scenarios.py
```

Keep the generated artifacts for inspection:

```bash
python scripts/evaluate_memory_scenarios.py --path .tmp-agent-memory-eval --force
python scripts/evaluate_memory_scenarios.py --path .tmp-agent-memory-eval --force --json
```

## Scenario Coverage

The evaluator currently checks these behaviors:

- `model-handoff-migration`: a fresh model can read a short briefing, then inspect a fuller migration packet with objective, preferences, decisions, active topic, and side episode.
- `portable-bundle-roundtrip`: structured memory can be exported and imported into another runtime while preserving briefing and packet behavior.
- `preference-transfer-filtering`: active trusted preferences enter startup context, while stale and untrusted preferences are excluded unless explicitly requested.
- `memory-candidate-review`: agent-proposed memory stays out of briefing and selection until promoted after review.
- `memory-update-supersession`: corrected preferences supersede old guidance so startup context does not contain both versions.
- `opening-plan-preservation`: complex task plans are saved as artifacts and surfaced in startup handoff context.
- `targeted-memory-selection`: a new agent can retrieve relevant high-salience records without stale or untrusted noise.
- `memory-compaction-planning`: low-signal active memory can be marked stale through a reviewable plan, while current active threads and review-only cleanup remain protected.
- `topic-interruption-resume`: a side topic parks the main topic, stores the side episode, detects a return cue, and restores the main topic.
- `memory-safety-review`: untrusted high-impact external memory is flagged by doctor, excluded from briefing, and only becomes reusable after review.
- `sensitive-memory-redaction`: sensitive text can be replaced in state and regenerated handoff artifacts.
- `memory-forget-control`: a revoked memory can be removed while preserving unrelated memory and cleaning supersession references.
- `multi-agent-separation`: shared decisions and role-local findings remain in separate state files while still producing an orchestration handoff note.

## How To Read Results

Each scenario returns pass/fail checks and optional artifact paths. A passing run means the core memory protocol still satisfies the current v0.1 behavioral contract. A failing run should be treated as either:

- a regression in memory behavior
- an intentional protocol change that needs the evaluator, docs, and examples updated together

The release validator imports this evaluator, runs all scenarios in a temporary directory, and fails if any scenario fails.
