from app.api.chat import ResponsesRequest
from app.api import codex_responses_v2 as v2
from app.services.codex_required_tool_language_patch import (
    client_prefixed_required_tool_pattern,
    install_codex_required_tool_language_patch,
)


def _tool(name: str):
    return {
        "type": "function",
        "name": name,
        "description": f"test {name}",
        "parameters": {
            "type": "object",
            "properties": {"cmd": {"type": "string"}},
            "required": ["cmd"],
        },
    }


def _body(text: str):
    return ResponsesRequest(
        model="chatgpt",
        stream=True,
        input=[
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            }
        ],
        tools=[_tool("exec_command"), _tool("write_stdin")],
    )


def test_pattern_matches_stage_c_workspace_guard_wording():
    pattern = client_prefixed_required_tool_pattern()
    match = pattern.search(
        "第一步必须通过客户端 exec_command 在当前 Codex 工作区执行 pwd。"
    )
    assert match is not None
    assert match.group(1) == "exec_command"


def test_installed_detector_requires_real_exec_for_stage_c_workspace_guard():
    install_codex_required_tool_language_patch()
    body = _body(
        "第一步必须通过客户端 exec_command 在当前 Codex 工作区执行 "
        "pwd && test -f .uwa_codex_acceptance && test -d git_diff。"
    )
    assert v2.required_declared_tool(body) == "exec_command"


def test_plain_client_tool_reference_still_does_not_force_execution():
    install_codex_required_tool_language_patch()
    body = _body("解释客户端 exec_command 在这个协议中有什么作用。")
    assert v2.required_declared_tool(body) == ""
