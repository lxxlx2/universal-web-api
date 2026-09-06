"""Codex-specific Responses preflight.

For the logical ``chatgpt`` browser route, this layer prepares a fresh ChatGPT
composer, verifies the web reasoning mode, and applies ChatGPT-only network
budgets suitable for High reasoning before delegating to the existing Responses
implementation.
"""

from __future__ import annotations

import ipaddress
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.api.chat import ResponsesRequest, create_response as create_response_backing, verify_auth
from app.services.chatgpt_web_mode import (
    ChatGPTWebModeError,
    inspect_chatgpt_web_mode_diagnostics,
    web_mode_enabled,
)
from app.services.codex_network_tuning import install_codex_chatgpt_network_tuning
from app.services.codex_web_policy import (
    inspect_codex_web_mode_status,
    prepare_and_verify_codex_web_mode,
)


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


@router.get("/v1/codex/web-mode")
async def codex_web_mode_status(request: Request) -> Dict[str, object]:
    _require_loopback(request)
    try:
        return inspect_codex_web_mode_status()
    except ChatGPTWebModeError as exc:
        return {
            "enabled": web_mode_enabled(),
            "verified": False,
            "error": str(exc),
        }


@router.get("/v1/codex/web-mode/diagnostics")
async def codex_web_mode_diagnostics(request: Request) -> Dict[str, object]:
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
) -> Dict[str, object]:
    _require_loopback(request)
    try:
        return prepare_and_verify_codex_web_mode(payload.reasoning)
    except ChatGPTWebModeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/v1/responses")
async def codex_aware_responses(
    request: Request,
    body: ResponsesRequest,
    authenticated: bool = Depends(verify_auth),
):
    if str(body.model or "").strip().lower() == "chatgpt" and web_mode_enabled():
        # Install before the backing StreamingResponse starts iterating. The
        # wrapper changes only NetworkMonitor configs whose parser id is
        # ``chatgpt``; all other web providers keep their original budgets.
        install_codex_chatgpt_network_tuning()
        try:
            prepare_and_verify_codex_web_mode(body.reasoning)
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
