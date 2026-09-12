# Open questions

Facts about the Fieldy public API. Each row is a blank in the design, not a
design decision — see the implementation-design comment on
[CCP-629](https://linear.app/chewcorp/issue/CCP-629).

Do not close a row from inference or from a plausible convention. Close it
with evidence: Fieldy's published documentation, or one authenticated request
and its response. Until a row is closed, code that depends on it says so at
the call site and in the handoff.

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

The design comment specifies `list_memories()`, `get_memory(id)`, and "the
server-side summary Fieldy already produces per memory". Public v2 has no
`memories` resource. Its resources are `conversations`, `transcriptions`,
`tasks`, `speaker-profiles`, `memory-templates`, `sharables`, and `user`.
`memory-templates` is a different concept — templates, not records.

**Resolved 2026-09-12 by the owner: the published spec wins.** The resource is
`conversations`, and the catalog uses the API's own vocabulary. This was never
a real question. The design comment was written by an agent that recorded its
own lack of access to the API — it listed these three facts as "resolve before
coding" and noted the host was proxy-refused. A source that documents it could
not reach the docs is not evidence about what the docs say.

The conversation object carries the fields the design wanted from a "memory",
so nothing about the client's shape changes. Do not re-open this to preserve
the design's wording.

Two constraints the design does not mention, which the spec does:

- `startTime` and `endTime` are **required** query parameters on
  `GET /conversations`. A listing method cannot default to "everything"; the
  caller must supply a window.
- Items carry a `locked` boolean — content redacted by the free-plan history
  window. An agent reading `summary` must handle a locked item rather than
  treating a null summary as "no summary".

## Environment

This host and the GitHub Actions runner both reach `api.fieldy.ai`. Some agent
sandboxes refuse it (403 on CONNECT), which is what the original design note
recorded. Tests and CI stay offline because CI holds no API key, not because
the host is unreachable.
