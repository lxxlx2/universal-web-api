from app.api.codex_compact import (
    CodexCompactRequest,
    compact_output_items,
    compact_request_to_responses,
    router,
)


def _history():
    return [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Keep constraint ALPHA."}],
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Working on it."}],
        },
    ]


def test_compact_route_is_registered():
    assert "/v1/responses/compact" in {route.path for route in router.routes}


def test_compact_request_disables_tools_and_does_not_pin_a_new_model():
    body = CodexCompactRequest(
        model="incoming-codex-model",
        input=_history(),
        instructions="Important project rule.",
        tools=[{"type": "function", "name": "exec_command", "parameters": {}}],
        parallel_tool_calls=True,
        reasoning={"effort": "high"},
    )

    adapted = compact_request_to_responses(body)

    assert adapted.model == "incoming-codex-model"
    assert adapted.input == body.input
    assert adapted.stream is False
    assert adapted.store is False
    assert adapted.tools is None
    assert adapted.tool_choice == "none"
    assert adapted.parallel_tool_calls is False
    assert adapted.reasoning == {"effort": "high"}
    assert "Important project rule." in (adapted.instructions or "")
    assert "Do not call tools" in (adapted.instructions or "")


def test_compact_output_returns_only_assistant_message_items():
    adapted = compact_request_to_responses(
        CodexCompactRequest(model="chatgpt", input=_history())
    )
    payload = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Goal: continue ALPHA. Tests were green.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {},
    }

    output = compact_output_items(adapted, payload)

    assert len(output) == 1
    assert output[0]["type"] == "message"
    assert output[0]["role"] == "assistant"
    content = output[0].get("content") or []
    assert any("ALPHA" in str(part.get("text") or "") for part in content if isinstance(part, dict))


def test_compact_output_rejects_function_call_only_payload():
    adapted = compact_request_to_responses(
        CodexCompactRequest(model="chatgpt", input=_history())
    )
    payload = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "exec_command", "arguments": "{}"},
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {},
    }

    assert compact_output_items(adapted, payload) == []
