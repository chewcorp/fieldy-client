#!/usr/bin/env python3
"""Hand-run live check against api.fieldy.ai. Never invoked by CI.

Usage: FIELDY_API_KEY=sk-fieldy-... python smoke.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone

from fieldy_client import FieldyClient, FieldyError


def main() -> int:
    if not os.environ.get("FIELDY_API_KEY"):
        print("smoke.py: set FIELDY_API_KEY and retry", file=sys.stderr)
        return 2
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    window = {
        "startTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        client = FieldyClient()
        result = {
            "user": client.call("user.get"),
            "summaries": client.summaries(pageSize=6, **window),
        }
    except FieldyError as exc:
        print(f"smoke.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
