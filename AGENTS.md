# Agent instructions — fieldy-client

A thin Python wrapper around the Fieldy public API v2
(`https://api.fieldy.ai/api/public/v2`) for agents that need Fieldy data and
summaries without an MCP dependency.

The authoritative specification is Linear **CCP-629** (mirrored as
chewcorp/chewcorp-tracker#151), including its implementation-design comment.
Where this file and CCP-629 disagree, CCP-629 wins and this file is wrong —
say so rather than working around it.

This file is the canonical standing rules for **every** agent harness (Codex,
Claude Code, Cursor, Gemini/Antigravity, and others). Harness files add only
invocation details; they never restate or override a rule from here.

## Scope guard

This repository is deliberately small — roughly one 150-line module. The
dominant delivery risk is not a missing feature; it is a plausible addition
that turns that module into a framework.

Out of scope by decision, not by omission:

- governance framework, multi-service platform, MCP rewrite (stated
  non-goals);
- async variant, pagination iterators, response model classes, caching layer,
  plugin interface, or any retry policy beyond one 429 retry honouring
  `Retry-After`;
- third-party runtime dependencies, a `src/` layout, a package directory, or a
  client/transport/model split.

Dicts in, dicts out. If a change needs one of the above to work, stop and put
the trade-off to the human owner; do not add it and mention it in the pull
request body.

## Layout (fixed)

Deliverable, per CCP-629:

| Path | Holds |
| --- | --- |
| `fieldy_client.py` | Client, `OPS` catalog, `__main__` CLI. One module. |
| `tests/test_client.py` | pytest over recorded fixtures with a stubbed opener. |
| `tests/fixtures/*.json` | Recorded responses. No live API in tests. |
| `pyproject.toml` | Packaging and pytest config. Written by the implementer. |
| `smoke.py` | Hand-run check against the real API. Never runs in CI. |
| `README.md` | Auth → Discover → Call, one screen or less. |
| `tools/refresh_ops.py` | Only if open question 2 resolves to "v2 serves OpenAPI". |

Scaffold:

| Path | Holds |
| --- | --- |
| `AGENTS.md` | These rules. Canonical for every harness. |
| `CLAUDE.md`, `GEMINI.md` | Harness adapters. Invocation details only. |
| `scripts/check.py` | The one check entry point. |
| `.github/workflows/checks.yml` | CI. Runs `scripts/check.py` and nothing else. |
| `docs/acceptance.md` | Per-criterion evidence ledger. |
| `docs/open-questions.md` | Facts not yet resolved from Fieldy's docs. |

Adding a file outside these tables is a scope decision, not a detail. Say
which table it belongs in and why before you add it.

## Working rules

- Python, standard library only at runtime (`urllib.request` + `json`).
  `pytest` is the only development dependency.
- Keep every script runnable as `python scripts/<name>.py` on any OS. No
  shell-only steps, no hard-coded POSIX paths.
- Auth reads `FIELDY_API_KEY` from the environment, overridable by a
  constructor argument for tests. Header construction stays in one
  `_auth_headers()` method so the format is a one-line change.
- Never commit an API key, nor a fixture you have not read. Recorded responses
  carry real conversation content: scrub them before they are committed.
- Tests and CI stay offline and deterministic: they run against recorded
  fixtures, never the live API, because CI holds no API key. That is a design
  choice, not an environment limit — this host and the GitHub Actions runner
  both reach `api.fieldy.ai`. Use that egress to resolve facts and to run
  `smoke.py`; do not wire a live call into `scripts/check.py`.
- Some agent sandboxes do refuse `api.fieldy.ai` (403 on CONNECT), and the
  Fieldy MCP server has returned 429. If you cannot reach the host, that is
  your environment, not the repository's assumption — say so and escalate
  rather than guessing at a response shape.
- Do not push to `main`. Branch from the work item's `gitBranchName` and open
  a pull request.

## Unresolved facts

Three facts are not yet settled — see `docs/open-questions.md`: the auth
header name and format, whether v2 serves an OpenAPI document, and whether the
summary arrives on the memory object or from its own endpoint.

Do not silently guess one. Either resolve it from Fieldy's published docs plus
one authenticated request and record that evidence, or implement behind the
agreed seam, mark it open, and say plainly in the handoff that it is
unverified. An unverified assumption presented as settled is the failure this
section exists to prevent.

## Delivery loop

1. Plan against the current acceptance criteria. Report blockers and defective
   criteria before implementing; never rewrite a criterion silently.
2. Implement on a branch. Run `python scripts/check.py` and hand off a compact
   evidence summary — branch, commit, checks run, files touched — not a
   transcript.
3. Review in a **fresh context** that did not plan or implement the change.
   Give the reviewer the integration base, changed paths, declared scope,
   these rules, and the check evidence; not the debugging history or the
   author's rationale for a shortcut.
4. Cap review and remediation at **three rounds**. If a finding class recurs,
   stop patching sites: escalate a structural fix or a human decision.
5. Verify each acceptance criterion in `docs/acceptance.md` as pass, fail, or
   unproven, with specific evidence. A green check is not evidence that a call
   against the real API works.
6. Merge, closure, and acceptance are the human owner's decisions. Agent
   approval is not acceptance.

For a trivial reversible change, do not stage every role. The fresh review
context stays the default whenever self-review would be material.

## Checks

`python scripts/check.py` is the single entry point, and CI runs exactly that.
It must stay offline, deterministic, and runnable from a clean clone with
`pytest` installed. Encode a new mechanical rule there rather than in the
review rules below.

## Code Review Rules

Baseline adapted from `xchewtoyx/review-guidance` (candidate status).

### Review calibration

- Scope review to the maturity and risk of the changed surface. Apply full
  behavioural scrutiny to shipping code, fixtures, scripts, and workflows. For
  proposed or unwired material, check stage-appropriate completeness, internal
  consistency, claims about current behaviour, and runnable commands; do not
  require implementation explicitly deferred to a later decision.
- Trace a changed invariant through affected consumers before commenting. One
  shared root cause gets one structural finding listing the affected sites and
  the canonical enforcement point. Keep unrelated causes separate.
- Make each finding independently checkable: state one defect, its exact
  evidence or verification path, its consequence, and the smallest safe
  remedy. On later rounds, retain prior dispositions, label causal follow-ons,
  and escalate repeated classes structurally instead of rediscovering sites.
  Declare convergence only when no prior blocking finding remains unresolved
  and a complete changed-surface pass finds no actionable finding, whether new
  or recurring.

### Repository specifics

- Treat the scope guard as a review criterion. A change that adds a runtime
  dependency, a layer, a module, or an extensibility seam is a blocking
  finding unless the pull request cites the decision that admitted it —
  however good the addition is on its own terms.
- Check claims about the Fieldy API against `docs/open-questions.md`. When a
  change depends on an unresolved fact, the finding is that the dependency is
  undeclared, not that the guess is wrong.
- Tests must be able to fail. For a new or changed test over fixtures, state
  how you established that it fails under a targeted contrary change, or
  record that you could not.

Mechanical formatting and policy checks belong in `scripts/check.py`, not
here.

## Harness adapters

| Harness | Rules entry | Adds |
| --- | --- | --- |
| Codex / OpenAI | this file | read natively |
| Cursor | this file | read natively |
| Claude Code | `CLAUDE.md` | invocation details only |
| Gemini / Antigravity | `GEMINI.md` | invocation details only |

An adapter holding a rule that is not in this file is a defect: move the rule
here.
