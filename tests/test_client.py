"""Tests for fieldy_client — recorded fixtures, stubbed opener, no live API.

Each new behaviour below was confirmed to fail before the matching code
existed (collection error: no ``fieldy_client`` module). After the client
landed, ``test_summaries_projects_server_summary_field`` was re-checked by
replacing the expected summary string with a value that is not in the
fixture: it failed on that assertion, then the original string was restored.
"""

from __future__ import annotations

import json
from email.message import Message
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request

import pytest

import fieldy_client

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeOpener:
    """Return queued HTTP responses; record the Request objects sent."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests: list[Request] = []

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        status, body, headers = self.responses.pop(0)
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        hdrs = Message()
        for key, value in (headers or {}).items():
            hdrs[key] = str(value)
        if status >= 400:
            raise HTTPError(req.full_url, status, "error", hdrs, BytesIO(raw))

        class _Resp:
            def read(self_inner):
                return raw

            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *exc):
                return False

        return _Resp()


def _client(responses, **kwargs):
    opener = FakeOpener(responses)
    sleeps = []
    client = fieldy_client.FieldyClient(
        api_key="test-key",
        urlopen=opener,
        sleep=sleeps.append,
        **kwargs,
    )
    return client, opener, sleeps


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("FIELDY_API_KEY", raising=False)
    with pytest.raises(fieldy_client.FieldyError) as exc:
        fieldy_client.FieldyClient()
    assert "FIELDY_API_KEY" in str(exc.value)
    assert exc.value.status is None


def test_env_key_is_used(monkeypatch):
    monkeypatch.setenv("FIELDY_API_KEY", "from-env")
    client, opener, _ = _client([(200, {"email": "a@b.test"}, None)])
    # constructor in _client passed api_key=; this test is the env path:
    client = fieldy_client.FieldyClient(urlopen=opener)
    client.call("user.get")
    assert opener.requests[0].headers["Authorization"] == "Bearer from-env"


def test_ops_lists_catalog_without_a_key(monkeypatch):
    monkeypatch.delenv("FIELDY_API_KEY", raising=False)
    names = {row["name"] for row in fieldy_client.ops()}
    assert "conversations.list" in names
    assert "conversations.get" in names
    assert "user.get" in names
    listing = next(row for row in fieldy_client.ops() if row["name"] == "conversations.list")
    assert listing["method"] == "GET"
    assert listing["path"] == "/conversations"
    assert "startTime" in listing["params"]
    assert "endTime" in listing["params"]


def test_call_sends_bearer_and_query():
    payload = _load("conversations_list.json")
    client, opener, _ = _client([(200, payload, None)])
    got = client.call(
        "conversations.list",
        startTime="2026-09-01T00:00:00Z",
        endTime="2026-09-12T23:59:59Z",
        pageSize=6,
    )
    assert got == payload
    req = opener.requests[0]
    assert req.get_method() == "GET"
    assert req.headers["Authorization"] == "Bearer test-key"
    assert "startTime=2026-09-01T00%3A00%3A00Z" in req.full_url
    assert "pageSize=6" in req.full_url
    assert req.full_url.startswith("https://api.fieldy.ai/api/public/v2/conversations?")


def test_call_interpolates_path_params():
    client, opener, _ = _client([(200, {"id": "conv_open"}, None)])
    client.call("conversations.get", id="conv_open")
    req = opener.requests[0]
    assert req.full_url.endswith("/conversations/conv_open")
    assert "{" not in req.full_url


def test_call_sends_json_body_on_post():
    client, opener, _ = _client([(200, {"id": "task_1"}, None)])
    client.call("tasks.create", title="Follow up", date="2026-09-15")
    req = opener.requests[0]
    assert req.get_method() == "POST"
    assert json.loads(req.data.decode()) == {"title": "Follow up", "date": "2026-09-15"}
    assert req.headers["Content-type"] == "application/json"


def test_http_error_becomes_fieldy_error():
    body = _load("unauthorized.json")
    client, _, _ = _client([(401, body, None)])
    with pytest.raises(fieldy_client.FieldyError) as exc:
        client.call("user.get")
    assert exc.value.status == 401
    assert exc.value.body == body
    assert "UNAUTHORIZED" in str(exc.value)


def test_429_retries_once_honouring_retry_after():
    payload = {"email": "a@b.test"}
    client, opener, sleeps = _client(
        [
            (429, {"code": "RATE"}, {"Retry-After": "2"}),
            (200, payload, None),
        ]
    )
    assert client.call("user.get") == payload
    assert sleeps == [2]
    assert len(opener.requests) == 2


def test_retry_wait_parses_http_date():
    from datetime import datetime, timezone

    now = datetime(2026, 9, 12, 11, 0, 0, tzinfo=timezone.utc)
    header = "Sat, 12 Sep 2026 11:00:07 GMT"
    assert fieldy_client._retry_wait(header, now=now) == 7
    assert fieldy_client._retry_wait("Sat, 12 Sep 2026 10:59:00 GMT", now=now) == 0
    assert fieldy_client._retry_wait("2") == 2
    assert fieldy_client._retry_wait(None) == 0
    frac = datetime(2026, 9, 12, 11, 0, 0, 500000, tzinfo=timezone.utc)
    assert fieldy_client._retry_wait(header, now=frac) == 6.5


def test_timeout_becomes_fieldy_error():
    def boom(req, timeout=None):
        raise TimeoutError("timed out")

    client = fieldy_client.FieldyClient(api_key="test-key", urlopen=boom)
    with pytest.raises(fieldy_client.FieldyError) as exc:
        client.call("user.get")
    assert exc.value.status is None
    assert "timed out" in str(exc.value)


def test_summaries_projects_server_summary_field():
    payload = _load("conversations_list.json")
    client, opener, _ = _client([(200, payload, None)])
    rows = client.summaries(
        startTime="2026-09-01T00:00:00Z",
        endTime="2026-09-12T23:59:59Z",
    )
    assert rows == [
        {
            "id": "conv_open",
            "title": "Standup",
                "summary": "Agreed to ship a thin Fieldy API wrapper.",
            "started_at": "2026-09-11T09:00:00Z",
            "locked": False,
        },
        {
            "id": "conv_locked",
            "title": "Older chat",
            "summary": None,
            "started_at": "2026-08-01T10:00:00Z",
            "locked": True,
        },
    ]
    assert "startTime=" in opener.requests[0].full_url


def test_unknown_op_raises():
    client, opener, _ = _client([])
    with pytest.raises(fieldy_client.FieldyError) as exc:
        client.call("does.not.exist")
    assert opener.requests == []
    assert "does.not.exist" in str(exc.value)


def test_cli_ops_does_not_need_a_key(monkeypatch, capsys):
    monkeypatch.delenv("FIELDY_API_KEY", raising=False)
    code = fieldy_client.main(["ops"])
    assert code == 0
    out = capsys.readouterr().out
    assert "conversations.list" in out
    assert "GET" in out
    assert "/conversations" in out


def test_cli_summaries_requires_time_window(monkeypatch, capsys):
    monkeypatch.setenv("FIELDY_API_KEY", "cli-key")
    code = fieldy_client.main(["summaries"])
    assert code == 1
    err = capsys.readouterr().err
    assert "error:" in err
    assert "startTime" in err


def test_cli_summaries_prints_projection(monkeypatch, capsys):
    payload = _load("conversations_list.json")
    opener = FakeOpener([(200, payload, None)])
    monkeypatch.setattr(fieldy_client, "urlopen", opener)
    monkeypatch.setenv("FIELDY_API_KEY", "cli-key")
    code = fieldy_client.main(
        [
            "summaries",
            "--startTime",
            "2026-09-01T00:00:00Z",
            "--endTime",
            "2026-09-12T23:59:59Z",
        ]
    )
    assert code == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed[0]["summary"].startswith("Agreed to ship")
    assert opener.requests[0].headers["Authorization"] == "Bearer cli-key"
