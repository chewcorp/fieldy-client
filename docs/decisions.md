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
