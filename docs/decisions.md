# Decisions

Why this repository is shaped the way it is. `AGENTS.md` states the resulting
rules without this reasoning; when the two touch the same subject, `AGENTS.md`
is what an agent follows and this file explains what it is for.

Each entry records the decision, the reasoning, and who took it. Supersede an
entry by adding a new one rather than editing history.

## D1 — The scaffold exists to hold scope, not to add process

**2026-09-12, Russell.** CCP-629 fixes the repo's shape: one stdlib-only
module of roughly 150 lines, no runtime dependencies, explicit non-goals. The
dominant delivery risk is therefore not a missing feature but a plausible
addition that turns that module into a framework. The scope guard in
`AGENTS.md` is the control for that risk, and the scaffold is kept to eight
files so it does not become the thing it guards against.

## D2 — Delivery loop and review rules adapted from existing practice

**2026-09-12, Russell.** The delivery loop comes from
`xchewtoyx/agent-cookbook`: a mandatory fresh-context review boundary, a
bounded retry count with structural escalation, and acceptance verification
kept separate from code review. The review rules adapt the
`xchewtoyx/review-guidance` baseline, which is candidate status there —
maturity-scoped scrutiny, one structural finding per root cause, an explicit
convergence definition.

That source also holds that a repository should add only two or three local
rules, and that mechanical checks belong in CI rather than review prose. The
three repository specifics encode this repo's actual failure modes.

## D3 — Checks stay offline because CI holds no key, not because of the network

**2026-09-12, Russell.** The original design comment recorded that
`api.fieldy.ai` was refused by its sandbox proxy, and the first draft of these
rules generalised that into "assume no network". That was wrong: a normal
developer host and the GitHub Actions runner both reach the host.

Tests and CI still run against recorded fixtures, for the real reason — CI
holds no API key and is not being given one. Egress is available for resolving
API facts and for hand-run smoke tests.

## D4 — The published spec outranks the issue on API facts

**2026-09-12, Russell.** CCP-629's design comment specifies `list_memories()`
and `get_memory(id)`. Public v2 has no `memories` resource; the records live
under `/conversations`.

This was raised as a decision for the owner and should not have been. The
design comment recorded its own lack of access to the API — it listed the
three facts as "resolve before coding" and noted the host was proxy-refused. A
source that documents it could not reach the docs is not evidence about what
the docs say, so there was nothing to weigh.

Hence the precedence split in `AGENTS.md`: CCP-629 owns scope, non-goals, and
acceptance criteria; the published spec owns API facts. Divergence between
them is recorded, not escalated. The client's shape is unaffected — the
conversation object carries the fields the design wanted from a "memory".

## D5 — Rationale lives here, not in the instructions

**2026-09-12, Russell.** Earlier revisions of `AGENTS.md` carried the
reasoning behind each rule inline, including the history of D3 and D4. Rules
and their justification compete for an agent's attention, and a rule that
arrives with its own argument invites re-litigation. `AGENTS.md` now states
rules; this file holds the decisions.

## D6 — Policy lives only in AGENTS.md; the mechanical checks enforce what they advertise

**2026-09-12, automated review of PR #1.** Two classes of finding, both
accepted.

Policy had leaked out of the canonical file: the harness adapters each carried
a standing implementation rule, and the evidence threshold for closing an API
question was set in `docs/open-questions.md`. Both made a non-canonical file a
secondary policy source that could drift. The adapters now carry invocation
detail only; the threshold is stated once in `AGENTS.md` and the ledger records
observations against it.

`scripts/check.py` claimed enforcement it did not deliver. Its key scan matched
three exact substrings, so the conventional `FIELDY_API_KEY = "…"` spelling
passed; it now matches assignments tolerant of whitespace and JSON/TOML
spellings, and flags the issued-key prefix wherever it appears with a body.
Import scanning also missed the installation surface, so a declared runtime
dependency in `pyproject.toml` would have passed the no-dependency rule; that
metadata is now checked too. Dynamically loaded dependencies remain outside
what a static check can see.

`.gitignore` was added by the first scaffold commit without appearing in either
layout table, leaving the scope contract inconsistent from the start. It is now
listed.

## D7 — The key scan tolerates prose about keys

**2026-09-12, CI failure on PR #1.** The hardened scan from D6 failed CI on
D6's own text: the prose quoting the vulnerable spelling was read as a live
assignment. Two gaps, both in the checker rather than the prose.

A Unicode ellipsis was not in the placeholder set, though its ASCII spelling
was. And any non-empty value counted, so a one-character value could trip the
scan. A literal shorter than twelve characters is now treated as prose or a
placeholder; the issued-key prefix rule still catches a real key whatever its
spelling or length, so detection is unchanged.

The D6 text stays as written. It is now a live regression case for the
false-positive path, sitting in the tree where any future change to the scan
must keep it passing.

## D8 — Supersedes D6 on dependency metadata

**2026-09-12, third review round.** D6 states that `pyproject.toml` dependency
metadata "is now checked". That is no longer true: the check was removed in
021517b.

It produced a finding in every round it existed — a pytest name match that
accepted `pytest-cov`, unchecked optional extras that become runtime
requirements on install, and a parse fallback that passed silently on Python
3.10 — always about a file that does not exist yet. `AGENTS.md` caps
remediation at three rounds and calls for a structural answer over further
site patching; the structural answer was that the check was speculative.

Dependency metadata is now unenforced by design. `AGENTS.md` says so, and
carries the requirement for whoever writes `pyproject.toml`.
