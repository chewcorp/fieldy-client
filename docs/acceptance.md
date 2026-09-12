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
| 1 | Thin client, documented auth via API key / env var, no MCP dependency | unproven | Offline: `FIELDY_API_KEY` / `api_key=`, `_auth_headers()` sends `Authorization: Bearer`, `scripts/check.py` stdlib-only scan, no MCP import. Live `smoke.py` not run in this environment (no key). |
| 2 | Agent self-discovery: OpenAPI-driven op list or static method catalog | pass | `python -m fieldy_client ops` prints the static `OPS` catalog (26 ops from the published spec). `ops()` needs no key. `tools/refresh_ops.py` regenerates the dict from `https://api.fieldy.ai/docs`. |
| 3 | At least one summary-generating call path agents can invoke | unproven | Offline: `FieldyClient.summaries(startTime, endTime)` projects `{id, title, summary, started_at, locked}` from `GET /conversations` (fixture `tests/fixtures/conversations_list.json`). Live `smoke.py` not run (no key). |
| 4 | README covers auth → discover → call in one screen or less | pass | `README.md` is three headings (Auth, Discover, Call) plus one Python and one CLI block. |
| 5 | Non-goals respected: no governance framework, no multi-service platform, no MCP rewrite | pass | One module `fieldy_client.py`, stdlib `urllib`, no plugin/async/models/cache. `scripts/check.py` rejects third-party runtime imports and non-empty `project.dependencies`. |

## Evidence that CI cannot supply

Criteria 1 and 3 describe behaviour against a live service. `scripts/check.py`
runs offline against recorded fixtures, so a green run evidences the client's
internal behaviour and nothing about the real API.

Only a hand-run `smoke.py` against `api.fieldy.ai` with a real key does that.
Egress is available from a normal developer host and from the GitHub Actions
runner, so the blocker is the key, not the network: CI holds no API key and is
not being given one.

Record such a run as: who ran it, when, against which base URL, and what came
back. Absent that, the honest status for those criteria is **unproven**, not
pass.

Unauthenticated observation, 2026-09-12, this implementation session:
`GET https://api.fieldy.ai/api/public/v2/user/me` with no key (and with a
non-issued placeholder) returns `401 {"code":"UNAUTHORIZED","message":"No
recognised credentials"}`. That confirms the host and auth scheme, not a
successful summary call.
