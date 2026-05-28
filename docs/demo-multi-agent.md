# Multi-Agent Memory Demo

This demo shows shared versus role-local memory.

It demonstrates:

- shared objective and next action
- shared decision
- role-local researcher finding
- orchestration note for handoff

Run from the repository root:

```bash
python -m agent_memory.adapters.multi_agent init \
  --path examples/multi-agent-demo \
  --role planner \
  --role researcher

python -m agent_memory.adapters.multi_agent checkpoint \
  --path examples/multi-agent-demo \
  --objective "Demonstrate shared and role-local memory for a multi-agent system." \
  --summary "Shared memory contains team decisions; role memory contains partial specialist findings." \
  --next-action "Promote only confirmed role findings into shared memory." \
  --risk "Do not confuse role-local assumptions with team decisions."

python -m agent_memory.adapters.multi_agent shared-decision \
  --path examples/multi-agent-demo \
  --id decision-shared-001 \
  --text "Use shared memory for decisions and role memory for partial findings." \
  --evidence "Multi-agent architecture decision." \
  --confidence high \
  --salience 5 \
  --role planner

python -m agent_memory.adapters.multi_agent role-memory \
  --path examples/multi-agent-demo \
  --role researcher \
  --kind fact \
  --id fact-research-001 \
  --text "Researcher found that role-local notes prevent premature consensus." \
  --evidence "Researcher local finding." \
  --confidence high \
  --salience 5

python -m agent_memory.adapters.multi_agent note \
  --path examples/multi-agent-demo \
  --write
```

Expected result:

- `shared/state.json` contains the shared decision.
- `roles/researcher/state.json` contains the researcher-local fact.
- `multi-agent-note.md` shows both without flattening them into one undifferentiated memory.
