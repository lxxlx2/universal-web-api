import pytest

from app.services.client_tool_policy import (
    build_client_workspace_repair_messages,
    should_repair_client_workspace_refusal,
)
from app.services.tool_calling import complete_tool_calling_roundtrip


EXEC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "exec_command",
            "description": "Run a shell command in the local client workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string"},
                    "workdir": {"type": "string"},
                },
                "required": ["cmd"],
                "additionalProperties": False,
            },
        },
    }
]


def test_detects_false_local_workspace_refusal_before_any_tool_result(monkeypatch):
    monkeypatch.setenv("TOOL_CALLING_CLIENT_WORKSPACE_REPAIR", "true")
    messages = [
        {
            "role": "user",
            "content": "Inspect calc.py, fix add(2, 3), and run a real test in the local workspace.",
        }
    ]
    parsed = {
        "mode": "final",
        "content": "I cannot access your local files. Please upload calc.py.",
        "tool_calls": [],
    }

    assert should_repair_client_workspace_refusal(
        messages=messages,
        tools=EXEC_TOOLS,
        tool_choice="auto",
        assistant_text=parsed["content"],
        parsed=parsed,
    ) is True


def test_does_not_override_a_genuine_failure_after_tool_history(monkeypatch):
    monkeypatch.setenv("TOOL_CALLING_CLIENT_WORKSPACE_REPAIR", "true")
    messages = [
        {"role": "user", "content": "Inspect calc.py and run its tests."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "exec_command",
                        "arguments": '{"cmd":"cat calc.py"}',
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "name": "exec_command",
            "content": "cat: calc.py: No such file or directory",
        },
    ]
    parsed = {
        "mode": "final",
        "content": "I cannot read calc.py because the tool confirmed that the file does not exist.",
        "tool_calls": [],
    }

    assert should_repair_client_workspace_refusal(
        messages=messages,
        tools=EXEC_TOOLS,
        tool_choice="auto",
        assistant_text=parsed["content"],
        parsed=parsed,
    ) is False


def test_repair_prompt_explains_client_side_execution_without_bypassing_permissions():
    messages = [{"role": "user", "content": "Fix calc.py and test it."}]
    repair = build_client_workspace_repair_messages(
        messages=messages,
        tools=EXEC_TOOLS,
        assistant_text="I cannot access your local files.",
        attempt=1,
        total_attempts=3,
    )

    assert len(repair) == 2
    system = repair[0]["content"]
    assert "exec_command" in system
    assert "client tools DO execute on the user's machine" in system
    assert "sandbox and approval policy" in system
    assert "Do not invent tool results" in system


def test_roundtrip_repairs_refusal_into_exec_command(monkeypatch):
    monkeypatch.setenv("TOOL_CALLING_CLIENT_WORKSPACE_REPAIR", "true")
    monkeypatch.setenv("TOOL_CALLING_INTERNAL_RETRY_MAX", "2")
    replies = iter(
        [
            "I cannot access your local files. Please upload calc.py.",
            (
                '<adapter_calls><call name="exec_command">'
                '<arguments encoding="json"><![CDATA['
                '{"cmd":"cat calc.py","workdir":"."}'
                ']]></arguments></call></adapter_calls>'
            ),
        ]
    )
    seen_messages = []

    def executor(browser_messages):
        seen_messages.append(browser_messages)
        return next(replies)

    result = complete_tool_calling_roundtrip(
        messages=[
            {
                "role": "user",
                "content": "Inspect calc.py, fix the add function, and run a real test.",
            }
        ],
        tools=EXEC_TOOLS,
        tool_choice="auto",
        parallel_tool_calls=False,
        round_executor=executor,
    )

    assert result["mode"] == "tool_calls"
    assert result["tool_calls"][0]["function"]["name"] == "exec_command"
    assert len(seen_messages) == 2
    assert "Client Workspace Repair" in seen_messages[1][1]["content"]


def test_roundtrip_fails_closed_after_repeated_false_refusals(monkeypatch):
    monkeypatch.setenv("TOOL_CALLING_CLIENT_WORKSPACE_REPAIR", "true")
    monkeypatch.setenv("TOOL_CALLING_INTERNAL_RETRY_MAX", "1")

    def executor(_browser_messages):
        return "I cannot access your local workspace. Please upload the file."

    with pytest.raises(RuntimeError, match="client_workspace_tool_refusal"):
        complete_tool_calling_roundtrip(
            messages=[{"role": "user", "content": "Fix calc.py and run the test."}],
            tools=EXEC_TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,
            round_executor=executor,
        )
