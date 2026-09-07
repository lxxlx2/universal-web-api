"""Runtime guardrails for the Codex Web Bridge V2 streaming path.

The browser bridge is intentionally layered on top of several optional local
facilities such as wire tracing, SQLite continuation snapshots and in-process
web-session affinity.  None of those helpers is allowed to tear down the HTTP
chunked response after ChatGPT Web has already produced a result.

This module installs narrow best-effort wrappers around those ancillary writes
and adds a final streaming exception envelope.  Browser/model failures are still
reported, but they are converted to a valid Responses ``response.failed`` event
instead of surfacing to Codex as ``error decoding response body``.

The guard is process-local and idempotent.  It stores no prompt, command, tool
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


def _failure_events(
    body: ResponsesRequest,
    *,
    code: str,
    exc: BaseException,
) -> List[str]:
    """Build a complete terminal Responses sequence without leaking exception text."""

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
    failed = _build_responses_object(
        body,
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

    # Import lazily so app.api.routes can finish importing the V2 router first.
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

    original_stream = v2._stream_codex_v2_attempt
    if not bool(getattr(original_stream, "_uwa_codex_v2_guarded", False)):

        async def _safe_stream(*args: Any, **kwargs: Any) -> AsyncIterator[str]:
            # Buffer protocol events until the attempt reaches a clean terminal
            # boundary. Transport comments are forwarded so the Codex HTTP
            # connection stays alive during long ChatGPT reasoning.
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
                logger.exception(
                    "[CODEX_V2_RUNTIME] browser turn preparation crashed; "
                    "converted to response.failed"
                )
                body = kwargs.get("body")
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

    _INSTALLED = True
    logger.info("[CODEX_V2_RUNTIME] streaming hardening installed")


__all__ = [
    "install_codex_v2_runtime_hardening",
]
