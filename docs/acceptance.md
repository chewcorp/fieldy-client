# Acceptance evidence — CCP-629

Acceptance criteria are owned by
[CCP-629](https://linear.app/chewcorp/issue/CCP-629); this file is the
evidence ledger for them, not a second copy of the requirement.

Verify each criterion independently as **pass**, **fail**, or **unproven**,
each with specific evidence. Do not replace the per-criterion result with a
holistic judgement, and do not raise the evidence bar after the work is done.
Rank evidence by how close it sits to the claim: a working artifact or direct
observation beats an automated check, which beats an assertion.

A recorded waiver from the human owner supersedes a criterion — record the
waiver in the row rather than re-failing wording the owner has removed.
Verification is a recommendation; it does not close the work item.

| # | Criterion (abbreviated) | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Thin client, documented auth via API key / env var, no MCP dependency | unproven | — |
| 2 | Agent self-discovery: OpenAPI-driven op list or static method catalog | unproven | — |
| 3 | At least one summary-generating call path agents can invoke | unproven | — |
| 4 | README covers auth → discover → call in one screen or less | unproven | — |
| 5 | Non-goals respected: no governance framework, no multi-service platform, no MCP rewrite | unproven | — |

## Evidence that CI cannot supply

Criteria 1 and 3 describe behaviour against a live service. `scripts/check.py`
runs offline against recorded fixtures, so a green run evidences the client's
internal behaviour and nothing about the real API. Only a hand-run `smoke.py`
against `api.fieldy.ai` with a real key does that — from a host with direct
egress, since the agent sandbox proxy refuses the host.

Record such a run as: who ran it, when, against which base URL, and what came
back. Absent that, the honest status for those criteria is **unproven**, not
pass.
