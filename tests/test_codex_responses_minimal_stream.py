import json

from app.api.codex_responses import (
    _codex_event,
    _codex_wire_item,
    _sanitize_codex_tool_payload,
)


def _tool_payload(content="I cannot access exec_command"):
    return {
        "model": "chatgpt",
        "choices": [
            {
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": [
                        {
                            "id": "call_test",
                            "type": "function",
                            "function": {
                                "name": "exec_command",
                                "arguments": '{"cmd":"cat calc.py"}',
                            },
                        }
                    ],
                },
            }
        ],
        "usage": {},
    }


def test_tool_payload_drops_contradictory_visible_text():
    clean = _sanitize_codex_tool_payload(_tool_payload())
    message = clean["choices"][0]["message"]
    assert message["content"] is None
    assert message["tool_calls"][0]["function"]["name"] == "exec_command"


def test_plain_final_text_is_preserved():
    payload = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": "done"},
            }
        ]
    }
    clean = _sanitize_codex_tool_payload(payload)
    assert clean["choices"][0]["message"]["content"] == "done"


def test_function_call_wire_item_matches_codex_minimal_shape():
    wire = _codex_wire_item(
        {
            "id": "fc_test",
            "type": "function_call",
            "status": "completed",
            "call_id": "call_test",
            "name": "exec_command",
            "arguments": '{"cmd":"cat calc.py"}',
        }
    )
    assert wire == {
        "type": "function_call",
        "call_id": "call_test",
        "name": "exec_command",
        "arguments": '{"cmd":"cat calc.py"}',
    }


def test_codex_output_item_done_event_contains_parseable_function_call():
    event = _codex_event(
        "response.output_item.done",
        sequence_number=2,
        output_index=0,
        item={
            "type": "function_call",
            "call_id": "call_test",
            "name": "exec_command",
            "arguments": '{"cmd":"cat calc.py"}',
        },
    )
    assert event.startswith("event: response.output_item.done\n")
    data_line = next(line for line in event.splitlines() if line.startswith("data: "))
    payload = json.loads(data_line[len("data: ") :])
    assert payload["type"] == "response.output_item.done"
    assert payload["item"]["type"] == "function_call"
    assert payload["item"]["name"] == "exec_command"
    assert payload["item"]["call_id"] == "call_test"
