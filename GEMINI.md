# fieldy-client — Gemini / Antigravity adapter

Follow the standing rules in [`AGENTS.md`](AGENTS.md). Do not duplicate or
override them here.

## Gemini-specific

- Run checks with `python scripts/check.py`.
- Dispatch the delivery loop's review round with `define_subagent` plus
  `invoke_subagent`, so the reviewer runs in a context that did not plan or
  implement the change. Pass it the integration base, changed paths, declared
  scope, `AGENTS.md`, and the check evidence only.
