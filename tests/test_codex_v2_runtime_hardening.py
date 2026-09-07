import json

from app.api.chat import ResponsesRequest
from app.services.codex_v2_runtime_hardening import (
    _compact_failure_body,
    _degraded_reuse_state_body,
    _failure_events,
)


def _body(*, huge_tool_description: str = "run command"):
    return ResponsesRequest(
        model="chatgpt",
        stream=True,
        previous_response_id="resp_previous",
        instructions="large codex instructions",
        input=[{"role": "user", "content": "test"}],
        tools=[
            {
                "type": "function",
                "name": "exec_command",
                "description": huge_tool_description,
                "parameters": {"type": "object"},
            }
        ],
        tool_choice={"type": "function", "name": "exec_command"},
        metadata={"case": "runtime-hardening"},
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


def test_failure_boundary_does_not_echo_huge_tool_schema():
    body = _body(huge_tool_description="x" * 600_000)
    frames = _failure_events(
        body,
        code="codex_v2_turn_prepare_failed",
        exc=RuntimeError("boom"),
    )

    assert sum(len(frame) for frame in frames) < 20_000
    assert "x" * 1000 not in "".join(frames)


def test_compact_failure_body_removes_request_heavy_fields():
    body = _body()
    compact = _compact_failure_body(body)

    assert compact.model == body.model
    assert compact.stream is True
    assert compact.input == ""
    assert compact.instructions is None
    assert compact.previous_response_id is None
    assert compact.tools is None
    assert compact.tool_choice is None
    assert compact.metadata is None


def test_degraded_reuse_state_keeps_retry_delta_and_tools_but_clears_hydration_handle():
    body = _body()
    degraded = _degraded_reuse_state_body(body)

    assert degraded.previous_response_id is None
    assert degraded.instructions is None
    assert degraded.input == body.input
    assert degraded.tools == body.tools
    assert degraded.tool_choice == body.tool_choice
    assert body.previous_response_id == "resp_previous"
    assert body.instructions == "large codex instructions"
