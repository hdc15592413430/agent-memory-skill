# Security Policy

Agent Memory stores operational context that may include user preferences, project facts, tool results, and handoff notes. Treat memory files as potentially sensitive even when they look like ordinary Markdown or JSON.

## Supported Versions

This project is currently a `v0.1` prototype. Security fixes should target the current main branch unless a release branch exists.

## Reporting A Vulnerability

Do not paste secrets, private memory files, exploit prompts, or sensitive user data into public issues.

If GitHub private vulnerability reporting is enabled for the repository, use it. If it is not enabled yet, open a public issue with only a non-sensitive summary and ask the maintainers for a private disclosure channel.

Useful reports include:

- memory poisoning that causes unsafe persistent behavior
- accidental promotion of untrusted external content into trusted memory
- CLI behavior that writes memory outside the requested directory
- adapter behavior that leaks user-scoped or role-local memory into shared context
- examples or docs that encourage storing secrets, credentials, or raw private transcripts

## Handling Sensitive Memory

- Prefer minimal, curated memory records over raw transcripts.
- Do not store API keys, passwords, tokens, private keys, or recovery codes.
- Mark external, tool, derived, or agent-generated records with the correct `source`.
- Tag unreviewed external candidates with `untrusted`.
- Use `doctor`, `review`, and `handoff --strict` before sharing or publishing memory examples.
- Use `redact` when a memory record already contains sensitive text; it replaces the record and refreshes handoff artifacts.
- Use `forget` when the user revokes a non-sensitive memory and wants it removed from structured memory.
- Redact example `state.json`, `memory-briefing.md`, and `migration-packet.md` files before opening issues or pull requests.

## Security Scope

The core package stores local files and does not send memory to a remote service by itself. Runtime adapters may introduce additional storage, sync, retrieval, or prompt-injection risks. Adapter maintainers are responsible for documenting those boundaries before enabling networked or shared memory backends.
