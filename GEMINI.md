# fieldy-client — Gemini / Antigravity adapter

Follow the standing rules in [`AGENTS.md`](AGENTS.md). Do not duplicate or
override them here.

## Gemini-specific

- Run checks with `python scripts/check.py`.
- For the review round of the delivery loop, use `define_subagent` plus
  `invoke_subagent` so the reviewer runs in a context that did not plan or
  implement the change. Hand it the integration base, changed paths, declared
  scope, `AGENTS.md`, and the check evidence only.
- Read `docs/open-questions.md` before writing any code that touches the
  Fieldy request or response shape.
