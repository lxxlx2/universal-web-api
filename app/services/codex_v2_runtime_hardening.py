"""Runtime guardrails for the Codex Web Bridge V2 streaming path.

The browser bridge is intentionally layered on top of several optional local
facilities such as wire tracing, SQLite continuation snapshots and in-process
web-session affinity. None of those helpers is allowed to tear down the HTTP
chunked response after ChatGPT Web has already produced a result.

This module also protects the strict required-tool retry path. When a mapped
ChatGPT conversation is healthy but local Responses hydration fails, the retry
may still continue as an incremental browser delta on that already-bound web
conversation. This preserves the live Codex tool loop instead of failing before
the repair prompt reaches ChatGPT Web.

The guard is process-local and idempotent. It stores no prompt, command, tool
result, cookie or browser credential.
"""

from __future__ import annotations

import time
from typing import Any, AsyncIterator, Callable, Dict, List

from fastapi.responses import StreamingResponse

from app.api.chat import ResponsesRequest, _build_responses_object, _new_response_id
from app.api.codex_responses import _codex_event
from app.core.config import get_logger


logger = get_logger("CODEX_V2_RUNTIME")
_INSTALLED = False


def _model_copy(body: ResponsesRequest) -> ResponsesRequest:
    if hasattr(body, "model_copy"):
        return body.model_copy(deep=True)
    return body.copy(deep=True)


def _compact_failure_body(body: ResponsesRequest) -> ResponsesRequest:
    """Keep failure envelopes small even when Codex advertises huge tool schemas."""

    compact = _model_copy(body)
    compact.input = ""
    compact.instructions = None
    compact.previous_response_id = None
    compact.tools = None
    compact.tool_choice = None
    compact.metadata = None
    compact.prompt = None
    compact.user = None
    return compact


def _degraded_reuse_state_body(body: ResponsesRequest) -> ResponsesRequest:
    """Build state for a same-web-conversation retry when hydration is unavailable.

    The browser conversation already owns the earlier dialogue. The retry only
    needs the current delta and declared tools. Clearing previous_response_id
    prevents a second hydration attempt while preserving the repair input.
    """

    cloned = _model_copy(body)
    cloned.previous_response_id = None
    cloned.instructions = None
    return cloned


def _failure_events(
    body: ResponsesRequest,
    *,
    code: str,
    exc: BaseException,
) -> List[str]:
    """Build a compact terminal Responses sequence without leaking exception text."""

    compact = _compact_failure_body(body)
    response_id = _new_response_id()
    created_at = int(time.time())
    in_progress = _build_responses_object(
        compact,
        {"choices": [], "usage": {}},
        response_id=response_id,
        created_at=created_at,
        status="in_progress",
        error=None,
    )
    failed = _build_responses_object(
        compact,
        {"choices": [], "usage": {}},
        response_id=response_id,
        created_at=created_at,
        status="failed",
        error={
            "message": (
                "Codex Web Bridge V2 terminated the browser attempt safely after an "
                f"internal {type(exc).__name__}. Check the private local UWA log."
            ),
            "type": "execution_error",
            "code": code,
        },
    )
    return [
        _codex_event(
            "response.created",
            sequence_number=1,
            response=in_progress,
        ),
        _codex_event(
            "response.failed",
            sequence_number=2,
            response=failed,
        ),
    ]


async def _iter_failure_events(
    body: ResponsesRequest,
    *,
    code: str,
    exc: BaseException,
) -> AsyncIterator[str]:
    for event in _failure_events(body, code=code, exc=exc):
        yield event


def _best_effort_wrapper(
    label: str,
    fn: Callable[..., Any],
    *,
    default: Any = None,
) -> Callable[..., Any]:
    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            logger.warning(
                f"[CODEX_V2_RUNTIME] ancillary {label} failed and was isolated: "
                f"{type(exc).__name__}"
            )
            return default

    setattr(_wrapped, "_uwa_codex_v2_guarded", True)
    return _wrapped


def install_codex_v2_runtime_hardening() -> None:
    """Install the V2 guard exactly once for the running UWA process."""

    global _INSTALLED
    if _INSTALLED:
        return

    from app.api import codex_responses_v2 as v2

    for name, default in (
        ("write_trace_attempt", None),
        ("_store_responses_state", None),
        ("_persist_codex_history", None),
        ("bind_response_to_conversation", False),
    ):
        current = getattr(v2, name, None)
        if current is None or bool(getattr(current, "_uwa_codex_v2_guarded", False)):
            continue
        setattr(v2, name, _best_effort_wrapper(name, current, default=default))

    original_required_tool_failed_events = v2._required_tool_failed_events
    if not bool(getattr(original_required_tool_failed_events, "_uwa_codex_v2_guarded", False)):

        def _compact_required_tool_failed_events(
            body: ResponsesRequest,
            required_tool: str,
        ) -> List[str]:
            return original_required_tool_failed_events(
                _compact_failure_body(body),
                required_tool,
            )

        setattr(_compact_required_tool_failed_events, "_uwa_codex_v2_guarded", True)
        v2._required_tool_failed_events = _compact_required_tool_failed_events

    original_stream = v2._stream_codex_v2_attempt
    if not bool(getattr(original_stream, "_uwa_codex_v2_guarded", False)):

        async def _safe_stream(*args: Any, **kwargs: Any) -> AsyncIterator[str]:
            buffered: List[str] = []
            try:
                async for chunk in original_stream(*args, **kwargs):
                    text = v2._chunk_text(chunk)
                    if v2._is_transport_comment(text):
                        yield text
                    else:
                        buffered.append(text)
            except Exception as exc:
                logger.exception(
                    "[CODEX_V2_RUNTIME] browser attempt stream crashed; "
                    "converted to response.failed"
                )
                state_body = kwargs.get("state_body")
                if isinstance(state_body, ResponsesRequest):
                    for event in _failure_events(
                        state_body,
                        code="codex_v2_attempt_stream_failed",
                        exc=exc,
                    ):
                        yield event
                return

            for text in buffered:
                yield text

        setattr(_safe_stream, "_uwa_codex_v2_guarded", True)
        v2._stream_codex_v2_attempt = _safe_stream

    original_attempt_response = v2._codex_web_attempt_response
    if not bool(getattr(original_attempt_response, "_uwa_codex_v2_guarded", False)):

        async def _safe_attempt_response(*args: Any, **kwargs: Any) -> StreamingResponse:
            try:
                return await original_attempt_response(*args, **kwargs)
            except Exception as exc:
                body = kwargs.get("body")
                request = kwargs.get("request")
                authenticated = kwargs.get("authenticated")
                if isinstance(body, ResponsesRequest) and str(body.previous_response_id or "").strip():
                    try:
                        reasoning = v2.normalize_codex_reasoning(body.reasoning)
                        binding = v2.resolve_conversation_binding(
                            body.previous_response_id,
                            model=v2.target_web_model(),
                            reasoning=reasoning,
                        )
                        if binding is not None and v2.ensure_chatgpt_conversation(binding.pathname):
                            state = v2.inspect_codex_web_mode_status(reasoning)
                            if bool(state.get("verified")):
                                logger.warning(
                                    "[CODEX_V2_RUNTIME] local continuation hydration failed; "
                                    "continuing the strict repair as a delta on the already-bound "
                                    f"ChatGPT conversation: {type(exc).__name__}"
                                )
                                fallback_state = _degraded_reuse_state_body(body)
                                v2.install_codex_chatgpt_network_tuning()
                                return StreamingResponse(
                                    v2._stream_codex_v2_attempt(
                                        request=request,
                                        state_body=fallback_state,
                                        browser_source_body=_model_copy(body),
                                        reuse_web_conversation=True,
                                        reused_path=binding.pathname,
                                        reasoning=reasoning,
                                        authenticated=authenticated,
                                    ),
                                    media_type="text/event-stream",
                                    headers=v2._stream_headers(),
                                )
                    except Exception as fallback_exc:
                        logger.warning(
                            "[CODEX_V2_RUNTIME] same-conversation degraded retry was unavailable: "
                            f"{type(fallback_exc).__name__}"
                        )

                logger.exception(
                    "[CODEX_V2_RUNTIME] browser turn preparation crashed; "
                    "converted to response.failed"
                )
                if not isinstance(body, ResponsesRequest):
                    raise
                return StreamingResponse(
                    _iter_failure_events(
                        body,
                        code="codex_v2_turn_prepare_failed",
                        exc=exc,
                    ),
                    media_type="text/event-stream",
                    headers=v2._stream_headers(),
                )

        setattr(_safe_attempt_response, "_uwa_codex_v2_guarded", True)
        v2._codex_web_attempt_response = _safe_attempt_response

    original_strict_stream = v2._strict_required_tool_stream
    if not bool(getattr(original_strict_stream, "_uwa_codex_v2_guarded", False)):

        async def _safe_strict_required_tool_stream(
            *,
            request: Any,
            body: ResponsesRequest,
            authenticated: bool,
            required_tool: str,
            trace_id: str,
        ) -> AsyncIterator[str]:
            attempts = v2._strict_retry_max() + 1
            current_body = body

            for attempt in range(1, attempts + 1):
                response = await v2._codex_web_attempt_response(
                    request=request,
                    body=current_body,
                    authenticated=authenticated,
                )

                buffered: List[str] = []
                async for chunk in response.body_iterator:
                    text = v2._chunk_text(chunk)
                    if v2._is_transport_comment(text):
                        yield text
                    else:
                        buffered.append(text)

                response_summary = v2.summarize_responses_sse(buffered)
                names = response_summary.get("function_call_names") or []
                satisfied = required_tool in names
                response_summary["required_tool"] = required_tool
                response_summary["required_tool_satisfied"] = satisfied
                response_summary["strict_attempt"] = attempt

                request_summary = v2.summarize_responses_request(current_body, required_tool)
                request_summary["previous_response_id_present"] = bool(
                    str(current_body.previous_response_id or "").strip()
                )
                v2.write_trace_attempt(
                    trace_id=trace_id,
                    attempt=attempt,
                    request_summary=request_summary,
                    response_summary=response_summary,
                    full_request=current_body,
                    raw_sse="".join(buffered),
                )

                if satisfied:
                    for text in buffered:
                        yield text
                    return

                if str(response_summary.get("response_status") or "").strip().lower() == "failed":
                    logger.warning(
                        "[CODEX_V2_RUNTIME] strict repair attempt returned response.failed; "
                        "preserving the real terminal failure instead of rewriting it as a "
                        "missing-tool error"
                    )
                    for text in buffered:
                        yield text
                    return

                attempt_response_id = v2._response_id_from_sse(buffered)
                if attempt < attempts and attempt_response_id:
                    current_body = v2._clone_for_required_tool_retry(
                        body,
                        required_tool,
                        attempt=attempt + 1,
                        previous_response_id=attempt_response_id,
                    )
                    yield f": codex-v2-required-tool-retry attempt={attempt + 1}\n\n"
                    continue

                for text in v2._required_tool_failed_events(body, required_tool):
                    yield text
                return

        setattr(_safe_strict_required_tool_stream, "_uwa_codex_v2_guarded", True)
        v2._strict_required_tool_stream = _safe_strict_required_tool_stream

    _INSTALLED = True
    logger.info("[CODEX_V2_RUNTIME] streaming hardening installed")


__all__ = [
    "_compact_failure_body",
    "_degraded_reuse_state_body",
    "_failure_events",
    "install_codex_v2_runtime_hardening",
]
