# fieldy-client — Claude Code adapter

Follow the standing rules in [`AGENTS.md`](AGENTS.md). Do not duplicate or
override them here.

## Claude-specific

- Run checks with the Bash tool: `python scripts/check.py`.
- Dispatch the delivery loop's review round with the Agent tool, so the
  reviewer runs in a context that did not plan or implement the change. Pass
  it the integration base, changed paths, declared scope, `AGENTS.md`, and the
  check evidence — not this session's transcript.
