"""Codex-specific Responses preflight.

This route is registered before the generic Responses route. For the logical
``chatgpt`` browser route it prepares a fresh ChatGPT composer, applies the
configured web model/reasoning/Temporary Chat preference, verifies them, then
delegates to the existing Responses implementation.
"""

from __future__ import annotations

import ipaddress
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.api.chat import ResponsesRequest, create_response as create_response_backing, verify_auth
from app.services.chatgpt_web_mode import (
    ChatGPTWebModeError,
    ensure_codex_chatgpt_web_mode,
    inspect_chatgpt_web_mode,
    inspect_chatgpt_web_mode_diagnostics,
    normalize_reasoning_effort,
    temporary_chat_enabled,
    web_mode_enabled,
)
from app.services.chatgpt_web_prepare import prepare_chatgpt_fresh_composer


router = APIRouter()


def _is_loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(str(host or "").split("%", 1)[0]).is_loopback
    except ValueError:
        return str(host or "").casefold() == "localhost"


def _require_loopback(request: Request) -> None:
    host = request.client.host if request.client else ""
    if not _is_loopback(host):
        raise HTTPException(status_code=403, detail="Codex Web mode control is local-only")


class CodexWebModeApplyRequest(BaseModel):
    reasoning: str = "high"


def _prepare_and_verify_web_mode(reasoning: Any) -> Dict[str, Any]:
    preparation = prepare_chatgpt_fresh_composer()
    state = ensure_codex_chatgpt_web_mode(reasoning)
    state["composer_preparation"] = preparation
    return state


@router.get("/v1/codex/web-mode")
async def codex_web_mode_status(request: Request) -> Dict[str, Any]:
    _require_loopback(request)
    if not web_mode_enabled():
        return {"enabled": False, "verified": False}
    try:
        state = inspect_chatgpt_web_mode()
        effort = normalize_reasoning_effort(state.get("target_reasoning_default"))
        temp_ok = state.get("temporary_chat") is True if temporary_chat_enabled() else True
        state["verified"] = (
            str(state.get("model") or "").casefold() == str(state.get("target_model") or "").casefold()
            and state.get("reasoning") == effort
            and temp_ok
        )
        return state
    except ChatGPTWebModeError as exc:
        return {
            "enabled": True,
            "verified": False,
            "error": str(exc),
        }


@router.get("/v1/codex/web-mode/diagnostics")
async def codex_web_mode_diagnostics(request: Request) -> Dict[str, Any]:
    """Return sanitized model/mode UI metadata for the local controlled tab only."""
    _require_loopback(request)
    try:
        return inspect_chatgpt_web_mode_diagnostics()
    except ChatGPTWebModeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/v1/codex/web-mode/apply")
async def codex_web_mode_apply(
    request: Request,
    payload: CodexWebModeApplyRequest,
) -> Dict[str, Any]:
    _require_loopback(request)
    try:
        return _prepare_and_verify_web_mode(payload.reasoning)
    except ChatGPTWebModeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/v1/responses")
async def codex_aware_responses(
    request: Request,
    body: ResponsesRequest,
    authenticated: bool = Depends(verify_auth),
):
    if str(body.model or "").strip().lower() == "chatgpt" and web_mode_enabled():
        try:
            _prepare_and_verify_web_mode(body.reasoning)
        except ChatGPTWebModeError as exc:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "chatgpt_web_mode_verification_failed",
                    "message": str(exc),
                },
            ) from exc

    return await create_response_backing(
        request=request,
        body=body,
        authenticated=authenticated,
    )
