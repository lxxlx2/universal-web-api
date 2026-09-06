"""Client-side coding tool policy for web-model tool calling.

Web chat models often assume that they cannot access a user's local machine. In a
Codex-style client this assumption is incomplete: the web page itself has no local
filesystem access, but declared function tools such as ``exec_command`` execute in
the client under the client's own sandbox and approval policy.

This module only repairs a narrow failure mode: an obvious local-workspace access
refusal before any client tool result has been observed. It never executes commands
itself and it never bypasses client permission checks.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional


_WORKSPACE_TOOL_PRIORITY = (
    "exec_command",
    "shell_command",
    "local_shell",
    "apply_patch",
    "write_stdin",
)

_WORKSPACE_REQUEST_PATTERNS = (
    re.compile(r"\bworkspace\b", re.IGNORECASE),
    re.compile(r"\brepo(?:sitory)?\b", re.IGNORECASE),
    re.compile(r"\blocal\s+(?:file|directory|project|workspace)\b", re.IGNORECASE),
    re.compile(r"\b(?:read|inspect|open|edit|modify|fix|patch|test|run)\b.{0,80}\b(?:file|code|test|project|repo)\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"(?:^|[\s/])[^\s/]+\.(?:py|js|jsx|ts|tsx|java|kt|kts|cs|cpp|cc|c|h|hpp|go|rs|rb|php|swift|sh|zsh|bash|toml|yaml|yml|json|md)(?:\b|$)", re.IGNORECASE),
    re.compile(r"(?:/Users/|/home/|[A-Za-z]:\\)", re.IGNORECASE),
    re.compile(r"(?:本机|本地|工作区|仓库|项目|文件|目录|代码|测试|修复|修改|检查)"),
)

_REFUSAL_PATTERNS = (
    re.compile(r"\b(?:i\s+)?(?:can(?:not|'t)|do\s+not|don't)\s+(?:directly\s+)?(?:access|see|read|modify|edit)\b.{0,100}\b(?:local|machine|computer|filesystem|file|workspace|directory)\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bno\s+access\s+to\b.{0,100}\b(?:local|machine|filesystem|file|workspace)\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b(?:please|you\s+need\s+to)\s+upload\b.{0,80}\b(?:file|project|repo)\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b(?:run|execute)\s+(?:these|the\s+following)\s+commands?\s+(?:yourself|locally|on\s+your\s+machine)\b", re.IGNORECASE),
    re.compile(r"(?:无法|不能|没法|访问不到).{0,30}(?:本机|本地|工作区|目录|文件)"),
    re.compile(r"(?:当前这个会话环境|当前会话环境).{0,40}(?:访问不到|无法访问|不能访问)"),
    re.compile(r"(?:没有发现|未发现).{0,30}(?:已上传|上传的).{0,20}(?:文件|代码)"),
    re.compile(r"(?:请|需要你).{0,20}上传.{0,20}(?:文件|项目|代码)"),
    re.compile(r"你可以直接在.{0,30}(?:本地|工作区).{0,20}执行"),
)


def _flag_enabled(name: str, default: bool = True) -> bool:
    raw = str(os.getenv(name, "1" if default else "0") or "").strip().lower()
    if not raw:
        return default
    return raw not in {"0", "false", "no", "off"}


def _tool_name(item: Any) -> str:
    if not isinstance(item, dict):
        return ""
    function_data = item.get("function") if isinstance(item.get("function"), dict) else {}
    return str(function_data.get("name") or item.get("name") or "").strip()


def _workspace_tool_defs(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_name = {_tool_name(item): item for item in tools or [] if _tool_name(item)}
    result: List[Dict[str, Any]] = []
    for name in _WORKSPACE_TOOL_PRIORITY:
        item = by_name.get(name)
        if isinstance(item, dict):
            result.append(item)
    return result


def has_client_workspace_tools(tools: List[Dict[str, Any]]) -> bool:
    return bool(_workspace_tool_defs(tools))


def _has_tool_history(messages: List[Dict[str, Any]]) -> bool:
    for message in messages or []:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "").strip().lower()
        if role in {"tool", "function"}:
            return True
        if message.get("tool_calls") or message.get("function_call"):
            return True
    return False


def _latest_user_text(messages: List[Dict[str, Any]]) -> str:
    for message in reversed(messages or []):
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "user").strip().lower()
        if role != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
        try:
            return json.dumps(content, ensure_ascii=False)
        except Exception:
            return str(content or "")
    return ""


def looks_like_local_workspace_request(messages: List[Dict[str, Any]]) -> bool:
    text = _latest_user_text(messages).strip()
    if not text:
        return False
    return any(pattern.search(text) for pattern in _WORKSPACE_REQUEST_PATTERNS)


def looks_like_client_access_refusal(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    return any(pattern.search(value) for pattern in _REFUSAL_PATTERNS)


def should_repair_client_workspace_refusal(
    *,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    tool_choice: Any,
    assistant_text: str,
    parsed: Dict[str, Any],
) -> bool:
    """Return True only for the narrow pre-tool local-access refusal case."""

    if not _flag_enabled("TOOL_CALLING_CLIENT_WORKSPACE_REPAIR", True):
        return False
    if isinstance(tool_choice, str) and tool_choice.strip().lower() == "none":
        return False
    if str(parsed.get("mode") or "").strip().lower() != "final":
        return False
    if parsed.get("tool_calls"):
        return False
    if not has_client_workspace_tools(tools):
        return False
    # After a real tool call/result, a missing file or permission failure may be
    # genuine. Do not transform such a final answer into an endless tool loop.
    if _has_tool_history(messages):
        return False
    if not looks_like_local_workspace_request(messages):
        return False
    return looks_like_client_access_refusal(assistant_text)


def build_client_workspace_repair_messages(
    *,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    assistant_text: str,
    attempt: int,
    total_attempts: int,
) -> List[Dict[str, str]]:
    """Build a small corrective prompt without exposing additional local data."""

    workspace_tools = _workspace_tool_defs(tools)
    preferred_name = _tool_name(workspace_tools[0]) if workspace_tools else "exec_command"
    tool_defs = json.dumps(workspace_tools, ensure_ascii=False, indent=2)
    user_request = _latest_user_text(messages).strip()
    if len(user_request) > 2200:
        user_request = user_request[:2197] + "..."
    rejected = str(assistant_text or "").strip()
    if len(rejected) > 1400:
        rejected = rejected[:1397] + "..."

    system = (
        "You are connected to a local coding client through declared function tools. "
        "The web page itself has no filesystem access, but the client tools DO execute on the user's machine "
        "under the client's sandbox and approval policy. Never claim that local files are unavailable merely "
        "because this web page cannot see them. For a local workspace task, inspect the real workspace by calling "
        f"a declared client tool, preferably {preferred_name}. Do not ask the user to upload a file and do not give "
        "commands for the user to run manually when the declared client tool can perform the action. "
        "Return exactly one complete <adapter_calls> root when calling tools. Put the tool name in the call name "
        "attribute and put one JSON object inside <arguments encoding=\"json\"><![CDATA[...]]></arguments>. "
        "Do not use markdown fences. Do not invent tool results.\n\n"
        "AVAILABLE CLIENT WORKSPACE TOOLS:\n"
        f"{tool_defs}"
    )

    user = (
        "[Client Workspace Repair]\n"
        f"Attempt: {attempt}/{total_attempts}\n"
        "The previous reply incorrectly treated the browser's lack of direct filesystem access as if the client "
        "had no tools. Correct that behavior now.\n\n"
        "Original user request:\n"
        f"{user_request}\n\n"
        "Rejected reply:\n"
        f"{rejected}\n\n"
        "Use the client tool now. Return only the corrected tool-call output."
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


__all__ = [
    "build_client_workspace_repair_messages",
    "has_client_workspace_tools",
    "looks_like_client_access_refusal",
    "looks_like_local_workspace_request",
    "should_repair_client_workspace_refusal",
]
