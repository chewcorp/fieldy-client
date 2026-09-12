"""Thin Fieldy public API v2 client. Stdlib only. No MCP.

Auth: FIELDY_API_KEY as ``Authorization: Bearer …``.
Discover: ``ops()`` / ``python -m fieldy_client ops``.
Summaries: ``FieldyClient.summaries(startTime, endTime)``.
"""

from __future__ import annotations

import email.utils
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

DEFAULT_BASE = "https://api.fieldy.ai/api/public/v2"
TIMEOUT = 30

# BEGIN OPS (tools/refresh_ops.py)
OPS = {
    'conversations.create': ('POST', '/conversations', 'startTime,calendarEventId,templateId', 'Create a conversation'),
    'conversations.delete': ('DELETE', '/conversations/{id}', 'id', 'Delete a conversation'),
    'conversations.get': ('GET', '/conversations/{id}', 'id', 'Get a conversation'),
    'conversations.list': ('GET', '/conversations', 'startTime,endTime,mode,cursor,pageSize,recordingSource', 'List conversations in a time range (summary on each item)'),
    'conversations.update': ('PATCH', '/conversations/{id}', 'id,title,summary,content,templateId,endTime,location,type,calendarEventId', 'Update a conversation'),
    'memoryTemplates.create': ('POST', '/memory-templates', 'title,prompt,description,emoji,sections', 'Create a memory template'),
    'memoryTemplates.delete': ('DELETE', '/memory-templates/{id}', 'id', 'Delete a memory template'),
    'memoryTemplates.get': ('GET', '/memory-templates/{id}', 'id', 'Get a memory template'),
    'memoryTemplates.list': ('GET', '/memory-templates', '', 'List memory templates'),
    'memoryTemplates.update': ('PATCH', '/memory-templates/{id}', 'id,title,prompt,description,emoji,sections', 'Update a memory template'),
    'sharables.create': ('POST', '/sharables', 'authorName,sharedFields,targetDocId', 'Create a share link'),
    'sharables.delete': ('DELETE', '/sharables/{id}', 'id', 'Delete a share link'),
    'sharables.list': ('GET', '/sharables', 'conversationId', 'List share links'),
    'sharables.resolve': ('GET', '/sharables/resolve', 'idOrUrl', 'Resolve a share link'),
    'sharables.update': ('PATCH', '/sharables/{id}', 'id,authorName,sharedFields,enabled', 'Update a share link'),
    'speakerProfiles.create': ('POST', '/speaker-profiles', 'name,color', 'Create a speaker profile'),
    'speakerProfiles.delete': ('DELETE', '/speaker-profiles/{id}', 'id', 'Delete a speaker profile'),
    'speakerProfiles.get': ('GET', '/speaker-profiles/{id}', 'id', 'Get a speaker profile'),
    'speakerProfiles.list': ('GET', '/speaker-profiles', '', 'List speaker profiles'),
    'speakerProfiles.update': ('PATCH', '/speaker-profiles/{id}', 'id,name,color', 'Update a speaker profile'),
    'tasks.create': ('POST', '/tasks', 'title,date', 'Create a task'),
    'tasks.delete': ('DELETE', '/tasks/{id}', 'id', 'Delete a task'),
    'tasks.list': ('GET', '/tasks', 'status', 'List tasks by status'),
    'tasks.update': ('PATCH', '/tasks/{id}', 'id,title,date,status,completionDate,cancellationDate', 'Update a task'),
    'transcriptions.list': ('GET', '/transcriptions', 'startTime,endTime,conversationId,recordingSource,limit,cursor,pageSize,order,inclusive', 'List transcript segments in a time range'),
    'user.get': ('GET', '/user/me', '', 'Get the authenticated user'),
}
# END OPS

urlopen = urllib.request.urlopen


class FieldyError(Exception):
    def __init__(self, message, status=None, body=None):
        super().__init__(message)
        self.status = status
        self.body = body


def ops():
    """Static catalog: ``{name, method, path, params, doc}`` per op."""
    return [
        {
            "name": name,
            "method": method,
            "path": path,
            "params": [p for p in params.split(",") if p],
            "doc": doc,
        }
        for name, (method, path, params, doc) in OPS.items()
    ]


def _auth_headers(api_key):
    return {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}


def _parse_body(raw):
    if not raw:
        return {}
    text = raw.decode("utf-8", "replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _retry_wait(raw, now=None):
    """Seconds to sleep for Retry-After: delta-seconds or HTTP-date."""
    if raw is None or raw == "":
        return 0
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        pass
    try:
        when = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError, OverflowError):
        return 0
    if when is None:
        return 0
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return max(0, int((when - current).total_seconds()))


def _fill_path(path, params):
    leftover = dict(params)
    filled = path
    for name in re.findall(r"\{([^}]+)\}", path):
        if name not in leftover:
            raise FieldyError(f"missing path parameter {name!r}")
        filled = filled.replace("{" + name + "}", urllib.parse.quote(str(leftover.pop(name)), safe=""))
    return filled, leftover


class FieldyClient:
    def __init__(self, api_key=None, base_url=DEFAULT_BASE, urlopen=None, sleep=None):
        key = os.environ.get("FIELDY_API_KEY") if api_key is None else api_key
        if not key:
            raise FieldyError("FIELDY_API_KEY is not set")
        self.api_key = key
        self.base_url = base_url.rstrip("/")
        self._urlopen = urlopen if urlopen is not None else globals()["urlopen"]
        self._sleep = sleep if sleep is not None else time.sleep

    def ops(self):
        return ops()

    def list_conversations(self, startTime, endTime, **kwargs):
        return self.call("conversations.list", startTime=startTime, endTime=endTime, **kwargs)

    def get_conversation(self, id):
        return self.call("conversations.get", id=id)

    def summaries(self, startTime, endTime, **kwargs):
        """Projection of server-side summaries on ``GET /conversations``."""
        items = self.list_conversations(startTime, endTime, **kwargs).get("items") or []
        return [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "summary": item.get("summary"),
                "started_at": item.get("startTime"),
                "locked": item.get("locked"),
            }
            for item in items
        ]

    def call(self, op_name, **params):
        if op_name not in OPS:
            raise FieldyError(f"unknown op {op_name!r}")
        method, path, _params, _doc = OPS[op_name]
        path, leftover = _fill_path(path, params)
        url, headers, data = self.base_url + path, _auth_headers(self.api_key), None
        if method in ("GET", "HEAD"):
            if leftover:
                url += "?" + urllib.parse.urlencode(leftover, doseq=True)
        elif leftover:
            data = json.dumps(leftover).encode("utf-8")
            headers["Content-Type"] = "application/json"
        return self._request(method, url, headers, data)

    def _request(self, method, url, headers, data):
        retried = False
        while True:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with self._urlopen(req, timeout=TIMEOUT) as resp:
                    return _parse_body(resp.read())
            except urllib.error.HTTPError as exc:
                body = _parse_body(exc.read())
                if exc.code == 429 and not retried:
                    retried = True
                    raw = exc.headers.get("Retry-After") if exc.headers else None
                    self._sleep(_retry_wait(raw))
                    continue
                raise FieldyError(f"{exc.code} {body}", status=exc.code, body=body) from exc
            except urllib.error.URLError as exc:
                raise FieldyError(str(exc.reason)) from exc


def _flags(argv):
    out, i = {}, 0
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith("--"):
            raise FieldyError(f"unexpected argument {tok!r}")
        key = tok[2:]
        if "=" in key:
            name, value = key.split("=", 1)
            out[name] = value
        else:
            i += 1
            if i >= len(argv):
                raise FieldyError(f"missing value for --{key}")
            out[key] = argv[i]
        i += 1
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: python -m fieldy_client ops | summaries | call OP  [--name value ...]")
        return 0
    cmd = argv[0]
    try:
        if cmd == "ops":
            rows = ops()
            nw, mw = max(len(r["name"]) for r in rows), max(len(r["method"]) for r in rows)
            for row in rows:
                print(f"{row['name']:<{nw}}  {row['method']:<{mw}}  {row['path']}  {','.join(row['params'])}")
            return 0
        if cmd == "summaries":
            flags = _flags(argv[1:])
            missing = [name for name in ("startTime", "endTime") if name not in flags]
            if missing:
                raise FieldyError("summaries requires --startTime and --endTime")
            result = FieldyClient().summaries(**flags)
        elif cmd == "call":
            if len(argv) < 2 or argv[1].startswith("--"):
                raise FieldyError("call requires an op name")
            result = FieldyClient().call(argv[1], **_flags(argv[2:]))
        else:
            raise FieldyError(f"unknown command {cmd!r}")
        print(json.dumps(result, indent=2))
        return 0
    except FieldyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
