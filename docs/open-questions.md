# Open questions

Facts about the Fieldy public API. Each row is a blank in the design, not a
design decision — see the implementation-design comment on
[CCP-629](https://linear.app/chewcorp/issue/CCP-629).

Do not close a row from inference or from a plausible convention. `AGENTS.md`
sets the evidence threshold; this file records what was actually observed.
Until a row is closed, code that depends on it says so at the call site and in
the handoff.

| # | Question | Status |
| --- | --- | --- |
| 1 | Auth header name and format | **resolved** — `Authorization: Bearer sk-fieldy-<key>` |
| 2 | Does `api/public/v2` serve an OpenAPI document? | **resolved** — yes, OpenAPI 3.1.1, API version 2.0.0 |
| 3 | Summary on the object, or its own endpoint? | **resolved** — on the object; `summary` is a field of each `GET /conversations` item |
| 4 | The design names a `memories` resource that v2 does not have | **resolved** — the spec wins; the resource is `conversations` |

## Evidence for rows 1–3

Resolved on 2026-09-12 from the published spec, unauthenticated, no API key
used. The spec is not served at a plain URL — `/openapi.json` and
`/api/public/v2/openapi.json` both 404. It is embedded in the API reference
page, so extract it rather than hunting for a spec endpoint:

```bash
curl -s https://api.fieldy.ai/docs -o docs.html
python -c "import json,re,html;raw=open('docs.html').read();cfg=json.loads(html.unescape(re.search(r'const scalarConfig = (\{.*?\});?\s*\n',raw,re.S).group(1)));print(json.dumps(json.loads(cfg['content']),indent=2))" > openapi.json
```

- **Row 1.** `components.securitySchemes.bearerAuth` is HTTP bearer, described
  as "API key issued from the Fieldy Developer Settings screen. Prefix:
  `sk-fieldy-`."
- **Row 2.** The spec exists and covers 13 paths, so `OPS` can be generated
  rather than hand-written. It is embedded in an HTML page, so a generator
  carries the extraction step above, not a plain fetch.
- **Row 3.** `summary` is a nullable string field on each item of
  `GET /conversations`, alongside `title`, `content`, `keywords`, `speakers`,
  and `quotes`. So `summaries()` is a projection over one response, not a
  second call.

## Row 4 — resource naming

Public v2 has no `memories` resource. Its resources are `conversations`,
`transcriptions`, `tasks`, `speaker-profiles`, `memory-templates`,
`sharables`, and `user`; `memory-templates` is templates, not records. The
conversation object carries the fields CCP-629's design comment expected from
a "memory".

Closed 2026-09-12: the resource is `conversations`, and the catalog uses the
API's own vocabulary. See `docs/decisions.md` D4.

Two constraints the design comment does not mention, which the spec states:

- `startTime` and `endTime` are **required** query parameters on
  `GET /conversations`. A listing method cannot default to "everything"; the
  caller must supply a window.
- Items carry a `locked` boolean — content redacted by the free-plan history
  window. A null `summary` on a locked item means redacted, not absent.

## Environment

A normal developer host and the GitHub Actions runner both reach
`api.fieldy.ai`; some agent sandboxes refuse it (403 on CONNECT). See
`docs/decisions.md` D3 for why tests and CI stay offline regardless.
