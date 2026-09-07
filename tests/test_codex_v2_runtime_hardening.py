import json

from app.api.chat import ResponsesRequest
from app.services.codex_v2_runtime_hardening import _failure_events


def _body():
    return ResponsesRequest(
        model="chatgpt",
        stream=True,
        input=[{"role": "user", "content": "test"}],
        tools=[
            {
                "type": "function",
                "name": "exec_command",
                "description": "run command",
                "parameters": {"type": "object"},
            }
        ],
    )


def test_failure_boundary_emits_complete_responses_terminal_sequence():
    frames = _failure_events(
        _body(),
        code="codex_v2_attempt_stream_failed",
        exc=RuntimeError("private details must not be copied"),
    )

    assert len(frames) == 2
    assert frames[0].startswith("event: response.created\n")
    assert frames[1].startswith("event: response.failed\n")

    created = json.loads(frames[0].split("data: ", 1)[1].strip())
    failed = json.loads(frames[1].split("data: ", 1)[1].strip())

    assert created["response"]["id"] == failed["response"]["id"]
    assert failed["response"]["status"] == "failed"
    assert failed["response"]["error"]["code"] == "codex_v2_attempt_stream_failed"
    assert "private details must not be copied" not in frames[1]
