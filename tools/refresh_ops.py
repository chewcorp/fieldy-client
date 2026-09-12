#!/usr/bin/env python3
"""Regenerate OPS in fieldy_client.py from the published Fieldy spec.

The spec is OpenAPI 3.1.1 embedded in https://api.fieldy.ai/docs — it is not
served at openapi.json. This script fetches that page, extracts the document,
and rewrites the marked OPS block. Runtime discovery still reads the static
dict; this is a maintainer refresh, not a runtime dependency.

Usage: python tools/refresh_ops.py
"""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIENT = ROOT / "fieldy_client.py"
DOCS_URL = "https://api.fieldy.ai/docs"
BEGIN = "# BEGIN OPS (tools/refresh_ops.py)\n"
END = "# END OPS\n"


def load_spec(text: str) -> dict:
    match = re.search(r"const scalarConfig = (\{.*?\});?\s*\n", text, re.S)
    if not match:
        raise SystemExit("error: could not find scalarConfig in the docs page")
    cfg = json.loads(html.unescape(match.group(1)))
    return json.loads(cfg["content"])


def verb(method: str, path: str) -> str:
    resource = path.strip("/").split("/")[0].replace("-", " ") or "resource"
    singular = resource[:-1] if resource.endswith("s") else resource
    if path.endswith("/me"):
        return "Get the authenticated user"
    if path.endswith("/resolve"):
        return "Resolve a share link"
    if resource == "sharables":
        action = {"GET": "List", "POST": "Create", "PATCH": "Update", "DELETE": "Delete"}[method]
        return f"{action} share links" if action == "List" else f"{action} a share link"
    if resource == "conversations" and method == "GET" and "{id}" not in path:
        return "List conversations in a time range (summary on each item)"
    if resource == "transcriptions" and method == "GET":
        return "List transcript segments in a time range"
    if resource == "tasks" and method == "GET":
        return "List tasks by status"
    if method == "GET" and "{id}" in path:
        return f"Get a {singular}"
    if method == "GET":
        return f"List {resource}"
    action = {"POST": "Create", "PATCH": "Update", "DELETE": "Delete"}[method]
    article = "an" if singular[:1].lower() in "aeiou" else "a"
    return f"{action} {article} {singular}"


def build_ops(spec: dict) -> dict[str, tuple]:
    ops: dict[str, tuple] = {}
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            if method.startswith("x-") or not isinstance(op, dict):
                continue
            name = op.get("operationId")
            if not name:
                continue
            params = [p["name"] for p in op.get("parameters") or [] if p.get("name")]
            body = (
                ((op.get("requestBody") or {}).get("content") or {})
                .get("application/json", {})
                .get("schema", {})
                .get("properties")
                or {}
            )
            for key in body:
                if key not in params:
                    params.append(key)
            ops[name] = (
                method.upper(),
                path,
                ",".join(params),
                verb(method.upper(), path),
            )
    return dict(sorted(ops.items()))


def render(ops: dict[str, tuple]) -> str:
    lines = ["OPS = {"]
    for name, triple in ops.items():
        lines.append(f"    {name!r}: {triple!r},")
    lines.append("}")
    return "\n".join(lines) + "\n"


def replace_block(source: str, ops_src: str) -> str:
    start = source.find(BEGIN)
    end = source.find(END)
    if start < 0 or end < 0 or end < start:
        raise SystemExit("error: OPS markers missing from fieldy_client.py")
    return source[:start] + BEGIN + ops_src + END + source[end + len(END) :]


def main() -> int:
    try:
        raw = urllib.request.urlopen(DOCS_URL, timeout=30).read().decode("utf-8", "replace")
    except OSError as exc:
        print(f"error: fetching {DOCS_URL}: {exc}", file=sys.stderr)
        return 1
    spec = load_spec(raw)
    ops_src = render(build_ops(spec))
    CLIENT.write_text(replace_block(CLIENT.read_text(encoding="utf-8"), ops_src), encoding="utf-8")
    print(f"wrote {len(build_ops(spec))} ops to {CLIENT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
