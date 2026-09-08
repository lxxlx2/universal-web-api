"""Request-local continuation guard for Codex required client tools.

A required-tool phrase in the latest user turn should force a real client tool
call when that turn has not yet produced one.  Codex then sends the resulting
function call and ``function_call_output`` back on the next Responses request.
Without request-local completion awareness, the V2 router re-detects the same
user phrase and forces the same tool again.

This compatibility layer suppresses only that duplicate re-enforcement.  A tool
is considered satisfied only when, after the latest user message, the current
Responses input contains both:

* a concrete ``function_call`` for the required tool with a non-empty call id;
* a matching ``function_call_output`` carrying the same call id.

Older tool calls before the latest user message, unmatched outputs, unmatched
calls, different tools, and plain-text claims never satisfy the contract.
Explicit request-level ``tool_choice`` remains authoritative and is never
suppressed by this patch.
"""

from __future__ import annotations

from typing import Any, Callable


_INSTALLED = False
_ORIGINAL_REQUIRED_DECLARED_TOOL: Callable[[Any], str] | None = None


def _latest_user_index(source: Any) -> int:
    if not isinstance(source, list):
        return -1

    for index in range(len(source) - 1, -1, -1):
        item = source[index]
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        item_type = str(item.get("type") or "").strip().lower()
        if role == "user" or (item_type == "message" and role == "user"):
            return index
    return -1


def _function_call_name(item: dict[str, Any]) -> str:
    direct = str(item.get("name") or "").strip()
    if direct:
        return direct
    function_data = item.get("function")
    if isinstance(function_data, dict):
        return str(function_data.get("name") or "").strip()
    return ""


def completed_tool_names_after_latest_user(source: Any) -> set[str]:
    """Return tools with a proven call/output cycle in the latest user turn."""

    if not isinstance(source, list):
        return set()

    latest_user = _latest_user_index(source)
    if latest_user < 0:
        return set()

    calls: dict[str, str] = {}
    outputs: set[str] = set()

    for item in source[latest_user + 1 :]:
        if not isinstance(item, dict):
            continue

        item_type = str(item.get("type") or "").strip().lower()

        if item_type == "function_call":
            call_id = str(item.get("call_id") or "").strip()
            name = _function_call_name(item)
            if call_id and name:
                calls[call_id] = name
            continue

        if item_type == "function_call_output":
            call_id = str(item.get("call_id") or "").strip()
            if call_id:
                outputs.add(call_id)

    return {
        calls[call_id]
        for call_id in outputs
        if call_id in calls and calls[call_id]
    }


def install_codex_required_tool_continuation_patch() -> None:
    """Patch V2 required-tool detection with request-local completion state."""

    global _INSTALLED, _ORIGINAL_REQUIRED_DECLARED_TOOL
    if _INSTALLED:
        return

    from app.api import codex_responses_v2 as v2

    original = v2.required_declared_tool
    _ORIGINAL_REQUIRED_DECLARED_TOOL = original

    def required_declared_tool_with_completion(body: Any) -> str:
        required = str(original(body) or "").strip()
        if not required:
            return ""

        declared = set(v2._declared_tool_names(body.tools))
        explicit_choice = v2._specific_tool_choice_name(body.tool_choice)
        if explicit_choice in declared:
            return required

        completed = completed_tool_names_after_latest_user(body.input)
        if required in completed:
            return ""
        return required

    v2.required_declared_tool = required_declared_tool_with_completion
    _INSTALLED = True


def original_required_declared_tool() -> Callable[[Any], str] | None:
    """Expose the wrapped detector for focused regression diagnostics."""

    return _ORIGINAL_REQUIRED_DECLARED_TOOL


__all__ = [
    "completed_tool_names_after_latest_user",
    "install_codex_required_tool_continuation_patch",
    "original_required_declared_tool",
]
