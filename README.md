# fieldy-client

Thin stdlib wrapper around Fieldy public API v2. No MCP.

## Auth

Create a key in the Fieldy app: Settings → Developer Settings. Prefix `sk-fieldy-`.

```bash
export FIELDY_API_KEY="YOUR_FIELDY_API_KEY"
```

The client sends `Authorization: Bearer $FIELDY_API_KEY`. Pass `api_key=` to the constructor in tests.

## Discover

```bash
python -m fieldy_client ops
```

Or `from fieldy_client import ops; print(ops())`. Catalog is static (generated from the published OpenAPI spec by `tools/refresh_ops.py`).

## Call

`GET /conversations` requires `startTime` and `endTime`. Summaries are a field on each conversation — `summaries()` projects `{id, title, summary, started_at, locked}`. A null summary with `locked: true` is redacted, not missing.

```python
from fieldy_client import FieldyClient
c = FieldyClient()
print(c.summaries(startTime="2026-09-01T00:00:00Z", endTime="2026-09-12T23:59:59Z"))
print(c.call("conversations.get", id="CONV_ID"))
```

```bash
python -m fieldy_client summaries --startTime 2026-09-01T00:00:00Z --endTime 2026-09-12T23:59:59Z
python -m fieldy_client call conversations.get --id CONV_ID
```

Checks: `python scripts/check.py`. Live (needs a real key): `python smoke.py`.
