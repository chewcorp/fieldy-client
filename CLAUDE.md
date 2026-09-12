# fieldy-client — Claude Code adapter

Follow the standing rules in [`AGENTS.md`](AGENTS.md). Do not duplicate or
override them here.

## Claude-specific

- Run checks with the Bash tool: `python scripts/check.py`. There is no
  project skill or slash command to invoke; the delivery loop in `AGENTS.md`
  is the procedure.
- Dispatch the review round of that loop with the Agent tool so the reviewer
  gets a fresh context. Pass it the integration base, changed paths, declared
  scope, `AGENTS.md`, and the check evidence — not this session's transcript.
  A reviewer that inherits the implementation context does not satisfy the
  fresh-review boundary, whatever model it runs.
- Read `docs/open-questions.md` before writing any code that touches the
  Fieldy request or response shape.
