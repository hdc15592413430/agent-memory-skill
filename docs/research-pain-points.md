# Research Pain Points

This scan turns public agent-memory problems into project requirements. Last updated: 2026-05-28.

## 1. Context Is Not Memory

Public systems increasingly separate short-term conversation state from long-term memory. OpenAI Agents SDK distinguishes run/session history from memory distilled into workspace files, and LangChain describes short-term memory as thread-scoped state while long-term memory is namespace-scoped across sessions.

Project response:

- Keep transcript history outside curated memory.
- Render a short migration packet as the handoff surface.
- Keep source records compact and evidence-backed.

## 2. Memory Needs Types

Agent memory work repeatedly separates semantic memory, episodic memory, and procedural memory. "Memory Matters" calls out separation of memory types and lifetime management as open problems; LangChain uses the same semantic/episodic/procedural framing.

Project response:

- Use `preferences`, `facts`, `decisions`, `threads`, `episodes`, and `artifacts` instead of one blob.
- Keep procedural instructions in the skill, not mixed into user memories.
- Use tags only as secondary labels; the collection still carries the primary memory type.

## 3. Retrieval Must Be Selective

MemGPT frames context as a limited working set managed across memory tiers. OpenAI Agents SDK uses progressive disclosure: a small memory summary first, then deeper rollout summaries only if relevant.
Recent coding-agent work also argues that long-context work can be externalized into explicit filesystem and tool operations, which supports keeping memory as inspectable files rather than hidden prompt-only state.

Project response:

- Read the migration packet first.
- Load detailed `state.json` records only when needed.
- Keep salience scoring so future adapters can index or retrieve high-signal records first.
- Keep plans, handoff packets, and briefings as files a coding agent can inspect with normal tools.

## 4. Stale Memory Can Mislead

LangChain notes that long histories can distract models with stale or off-topic content. OpenAI Agents SDK instructs agents to treat memory as guidance and trust the current environment. MemoryBank explicitly explores selective forgetting and reinforcement over time.

Project response:

- Support `status: stale` and `status: superseded`.
- Add optional `expires_at` metadata.
- `doctor` warns when expired records remain active.

## 5. Bad Experiences Get Replayed

Recent empirical work on experience-following behavior found that agents may imitate retrieved past executions, causing error propagation or misleading replay when memory quality is poor.

Project response:

- Store failed attempts as explicit artifacts and risks, not as successful examples.
- Require evidence for salient records.
- `doctor` flags low-confidence critical memory and transcript-like records.

## 6. Memory Evaluation Is Still Thin

LongMemEval evaluates information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention, and reports significant accuracy drops across sustained interactions.

Project response:

- Treat those five abilities as the future evaluation matrix.
- Keep demos for topic interruption, migration packet generation, chat memory, agent runs, and multi-agent separation.
- Add supersession tests so knowledge updates do not leave old guidance active.
- Add benchmark-style tests only after the core protocol stabilizes.

## 7. Memory Ownership And Scope Matter

LangChain Deep Agents highlights user-scoped memory, organization-level memory, read-only shared policies, human validation for sensitive writes, and concurrent write conflicts. OpenAI Agents SDK recommends separate layouts to isolate memory for different agents.

Project response:

- Add optional `scope` metadata: `user`, `project`, `agent`, `role`, `organization`, or `global`.
- Keep multi-agent memory split into shared and role-local directories.
- Prefer user or role scope unless a record is a confirmed shared decision.
- Use `supersede` when a shared or user-scoped memory changes, so newer records do not conflict with old active records.

## 8. Persistent Memory Is A Security Boundary

MemoryGraft shows that malicious "successful" experiences can persist and later shape agent behavior. Sleeper memory poisoning shows that external context can cause an assistant to store fabricated user memories that re-emerge later.

Project response:

- Add optional `source` metadata: `user`, `agent`, `tool`, `external`, `system`, or `derived`.
- `doctor` warns on high-impact non-user memories without `reviewed`.
- `doctor` flags instruction-like or secret-handling text that may indicate memory poisoning.
- Tag untrusted external candidates as `untrusted` until reviewed.
- Use `review` to add `reviewed`, remove `untrusted`, mark records stale, or supersede unsafe memories after inspection.

## Sources

- OpenAI Agents SDK: [Agent memory](https://openai.github.io/openai-agents-python/sandbox/memory/)
- LangChain: [Memory overview](https://docs.langchain.com/oss/python/concepts/memory)
- LangChain Deep Agents: [Long-term memory](https://docs.langchain.com/oss/python/deepagents/memory)
- LlamaIndex: [Agent memory](https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/)
- Hatalis et al.: [Memory Matters](https://ojs.aaai.org/index.php/AAAI-SS/article/view/27688)
- Packer et al.: [MemGPT](https://arxiv.org/abs/2310.08560)
- Cao et al.: [Coding Agents are Effective Long-Context Processors](https://arxiv.org/abs/2603.20432)
- Zhong et al.: [MemoryBank](https://arxiv.org/abs/2305.10250)
- Wu et al.: [LongMemEval](https://arxiv.org/abs/2410.10813)
- Xiong et al.: [How Memory Management Impacts LLM Agents](https://arxiv.org/abs/2505.16067)
- Srivastava and He: [MemoryGraft](https://arxiv.org/abs/2512.16962)
- Pulipaka et al.: [Hidden in Memory](https://arxiv.org/abs/2605.15338)
