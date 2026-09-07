"""Codex Web Bridge V2 guardrail and observability layer.

This router intentionally sits before the existing Codex Responses router. It
keeps the proven browser/tool bridge underneath, while adding two V2 behaviors:

1. private request/response metadata tracing for protocol diagnosis;
2. a strict contract when the client/user explicitly requires a declared tool.

A plain-text imitation of a tool result is never accepted for a strict tool turn.
The bridge retries once with the requested function forced through ``tool_choice``
and then fails closed if a real Responses ``function_call`` still does not appear.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, AsyncIterator, Dict, Iterable, List, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.chat import ResponsesRequest, _build_responses_object, _new_response_id, verify_auth
from app.api.codex_responses import (
    _require_loopback,
    codex_aware_responses,
)
from app.services.chatgpt_web_mode import web_mode_enabled
from app.services.codex_wire_observability import (
    new_trace_id,
    summarize_responses_request,
    summarize_responses_sse,
    trace_status,
    write_trace_attempt,
)


router = APIRouter()

_WORKSPACE_TOOL_NAMES = {
    "exec_command",
    "shell_command",
    "local_shell",
    "apply_patch",
    "write_stdin",
}

_REQUIRED_TOOL_PATTERNS = (
    re.compile(
        r"(?:必须|务必|一定要|必须通过|请务必|只能)\s*(?:通过|使用|调用)?\s*`?"
        r"(exec_command|shell_command|local_shell|apply_patch|write_stdin)`?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:must|required\s+to|have\s+to)\s+(?:use|call|invoke)\s+`?"
        r"(exec_command|shell_command|local_shell|apply_patch|write_stdin)`?\b",
        re.IGNORECASE,
    ),
)


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = str(os.getenv(name, str(default)) or str(default)).strip()
    try:
        value = int(raw)
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


def _strict_retry_max() -> int:
    return _env_int("UWA_CODEX_REQUIRED_TOOL_RETRY_MAX", 1, 0, 3)


def _model_copy(body: ResponsesRequest) -> ResponsesRequest:
    if hasattr(body, "model_copy"):
        return body.model_copy(deep=True)
    return body.copy(deep=True)


def _declared_tool_names(tools: Any) -> List[str]:
    names: List[str] = []
    for item in tools if isinstance(tools, list) else []:
        if not isinstance(item, dict):
            continue
        function_data = item.get("function") if isinstance(item.get("function"), dict) else {}
        name = str(function_data.get("name") or item.get("name") or "").strip()
        if name and name not in names:
            names.append(name)
    return names


def _specific_tool_choice_name(tool_choice: Any) -> str:
    if not isinstance(tool_choice, dict):
        return ""
    if str(tool_choice.get("type") or "").strip().lower() != "function":
        return ""
    function_data = tool_choice.get("function") if isinstance(tool_choice.get("function"), dict) else {}
    return str(function_data.get("name") or tool_choice.get("name") or "").strip()


def _content_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        preferred = value.get("text")
        if isinstance(preferred, str):
            return preferred
        return "\n".join(_content_text(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return "\n".join(_content_text(item) for item in value)
    return ""


def _latest_user_text(source: Any) -> str:
    if isinstance(source, str):
        return source
    if not isinstance(source, list):
        return ""
    for item in reversed(source):
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        item_type = str(item.get("type") or "").strip().lower()
        if role == "user" or (item_type == "message" and role == "user"):
            return _content_text(item.get("content"))
    return ""


def required_declared_tool(body: ResponsesRequest) -> str:
    declared = set(_declared_tool_names(body.tools))
    if not declared:
        return ""

    choice_name = _specific_tool_choice_name(body.tool_choice)
    if choice_name in declared:
        return choice_name

    user_text = _latest_user_text(body.input)
    for pattern in _REQUIRED_TOOL_PATTERNS:
        match = pattern.search(user_text)
        if not match:
            continue
        name = str(match.group(1) or "").strip()
        if name in declared:
            return name
    return ""


def _clone_for_required_tool_retry(
    body: ResponsesRequest,
    required_tool: str,
    attempt: int,
) -> ResponsesRequest:
    cloned = _model_copy(body)
    existing = str(cloned.instructions or "").rstrip()
    repair = (
        "[Codex V2 Required Tool Contract]\n"
        f"This turn explicitly requires a real client function call to `{required_tool}`. "
        "A plain-text answer, simulated command output, or statement that the tool is unavailable is invalid. "
        f"Emit an actual call to `{required_tool}` using the declared schema and wait for the client tool result. "
        "Do not invent tool output. For exec-like tools, omit `workdir` unless the user explicitly requested a "
        "different working directory; the Codex turn cwd is authoritative. "
        f"Repair attempt: {attempt}."
    )
    cloned.instructions = f"{existing}\n\n{repair}" if existing else repair
    cloned.tool_choice = {"type": "function", "name": required_tool}
    return cloned


def _chunk_text(chunk: Any) -> str:
    if isinstance(chunk, bytes):
        return chunk.decode("utf-8", "replace")
    return str(chunk or "")


def _is_transport_comment(text: str) -> bool:
    stripped = str(text or "").lstrip()
    return stripped.startswith(":") and "event:" not in stripped and "data:" not in stripped


def _stream_headers() -> Dict[str, str]:
    return {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


def _pack_event(event: str, payload: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _required_tool_failed_events(body: ResponsesRequest, required_tool: str) -> List[str]:
    response_id = _new_response_id()
    created_at = int(time.time())
    in_progress = _build_responses_object(
        body,
        {"choices": [], "usage": {}},
        response_id=response_id,
        created_at=created_at,
        status="in_progress",
        error=None,
    )
    error = {
        "type": "invalid_tool_output",
        "code": "required_client_tool_not_called",
        "message": (
            f"The web model did not emit the explicitly required client tool `{required_tool}` "
            "after bounded repair attempts. Plain-text simulated tool output was rejected."
        ),
    }
    failed = _build_responses_object(
        body,
        {"choices": [], "usage": {}},
        response_id=response_id,
        created_at=created_at,
        status="failed",
        error=error,
    )
    return [
        _pack_event(
            "response.created",
            {"type": "response.created", "sequence_number": 1, "response": in_progress},
        ),
        _pack_event(
            "response.failed",
            {"type": "response.failed", "sequence_number": 2, "response": failed},
        ),
    ]


async def _trace_passthrough(
    *,
    response: StreamingResponse,
    body: ResponsesRequest,
    trace_id: str,
) -> AsyncIterator[str]:
    chunks: List[str] = []
    async for chunk in response.body_iterator:
        text = _chunk_text(chunk)
        chunks.append(text)
        yield text
    summary = summarize_responses_sse(chunks)
    write_trace_attempt(
        trace_id=trace_id,
        attempt=1,
        request_summary=summarize_responses_request(body),
        response_summary=summary,
        full_request=body,
        raw_sse="".join(chunks),
    )


async def _strict_required_tool_stream(
    *,
    request: Request,
    body: ResponsesRequest,
    authenticated: bool,
    required_tool: str,
    trace_id: str,
) -> AsyncIterator[str]:
    attempts = _strict_retry_max() + 1
    current_body = body

    for attempt in range(1, attempts + 1):
        response = await codex_aware_responses(
            request=request,
            body=current_body,
            authenticated=authenticated,
        )
        if not isinstance(response, StreamingResponse):
            yield from _required_tool_failed_events(body, required_tool)
            return

        buffered: List[str] = []
        async for chunk in response.body_iterator:
            text = _chunk_text(chunk)
            if _is_transport_comment(text):
                yield text
            else:
                buffered.append(text)

        response_summary = summarize_responses_sse(buffered)
        names = response_summary.get("function_call_names") or []
        satisfied = required_tool in names
        response_summary["required_tool"] = required_tool
        response_summary["required_tool_satisfied"] = satisfied
        response_summary["strict_attempt"] = attempt

        write_trace_attempt(
            trace_id=trace_id,
            attempt=attempt,
            request_summary=summarize_responses_request(current_body, required_tool),
            response_summary=response_summary,
            full_request=current_body,
            raw_sse="".join(buffered),
        )

        if satisfied:
            for text in buffered:
                yield text
            return

        if attempt < attempts:
            current_body = _clone_for_required_tool_retry(
                body,
                required_tool,
                attempt=attempt + 1,
            )
            yield f": codex-v2-required-tool-retry attempt={attempt + 1}\n\n"
            continue

        for text in _required_tool_failed_events(body, required_tool):
            yield text
        return


@router.get("/v1/codex/wire-trace")
async def codex_wire_trace_status(request: Request) -> Dict[str, Any]:
    _require_loopback(request)
    return trace_status()


@router.post("/v1/responses")
async def codex_responses_v2(
    request: Request,
    body: ResponsesRequest,
    authenticated: bool = Depends(verify_auth),
):
    is_codex_web = (
        str(body.model or "").strip().lower() == "chatgpt"
        and web_mode_enabled()
        and bool(body.stream)
        and isinstance(body.tools, list)
        and bool(body.tools)
    )
    if not is_codex_web:
        return await codex_aware_responses(
            request=request,
            body=body,
            authenticated=authenticated,
        )

    trace_id = new_trace_id()
    required_tool = required_declared_tool(body)

    if required_tool:
        return StreamingResponse(
            _strict_required_tool_stream(
                request=request,
                body=body,
                authenticated=authenticated,
                required_tool=required_tool,
                trace_id=trace_id,
            ),
            media_type="text/event-stream",
            headers=_stream_headers(),
        )

    response = await codex_aware_responses(
        request=request,
        body=body,
        authenticated=authenticated,
    )
    if not isinstance(response, StreamingResponse):
        return response

    return StreamingResponse(
        _trace_passthrough(response=response, body=body, trace_id=trace_id),
        media_type="text/event-stream",
        headers=_stream_headers(),
    )


__all__ = [
    "codex_responses_v2",
    "required_declared_tool",
    "router",
]
