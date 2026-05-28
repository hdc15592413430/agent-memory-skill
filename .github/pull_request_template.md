## Summary

What changed, and which memory problem does it address?

## Layer

- [ ] Skill instructions
- [ ] Core memory model
- [ ] Codex adapter
- [ ] Chat adapter
- [ ] Autonomous-agent adapter
- [ ] Multi-agent adapter
- [ ] Documentation
- [ ] Tests or release validation

## Adapter Contract

If this changes or adds a runtime adapter, does it still satisfy `docs/adapter-contract.md`?

## Validation

Commands run:

```bash
python scripts/validate_release.py
```

## Memory Safety

Does this change affect stale memory, memory poisoning, user preference inference, topic-stack behavior, or handoff readiness?

Does this change where memory is stored, whether memory can leave the local machine, or how user/role/shared scopes are isolated?
