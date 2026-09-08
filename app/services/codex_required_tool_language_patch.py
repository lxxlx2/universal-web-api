"""Compatibility detector extensions for explicit Codex client-tool requests.

Live macOS acceptance exposed wording gaps in the V2 required-tool contract.
The acceptance harness may say forms such as ``必须通过客户端 exec_command`` or
``必须单独调用一次客户端 exec_command`` while the original detector covered
direct forms such as ``必须使用 exec_command``. A web model could therefore
answer a plain-text failure sentinel without a real workspace probe and escape
strict repair.

This module extends only the request-language detector. It does not execute
commands or change Codex sandbox/approval behavior.
"""

from __future__ import annotations

import re
from typing import Any


_CLIENT_PREFIXED_REQUIRED_TOOL_PATTERN = re.compile(
    r"(?:必须|务必|一定要|请务必|只能)\s*"
    r"(?:先|再)?\s*"
    r"(?:单独\s*)?"
    r"(?:通过|使用|调用|执行)?\s*"
    r"(?:一次|一遍|一个)?\s*"
    r"(?:客户端\s*)?`?"
    r"(exec_command|shell_command|local_shell|apply_patch|write_stdin)`?",
    re.IGNORECASE,
)

_INSTALLED = False


def install_codex_required_tool_language_patch() -> None:
    """Extend V2 detection for explicit client-prefixed Chinese tool wording."""

    global _INSTALLED
    if _INSTALLED:
        return

    from app.api import codex_responses_v2 as v2

    existing = tuple(getattr(v2, "_REQUIRED_TOOL_PATTERNS", ()) or ())
    pattern_text = _CLIENT_PREFIXED_REQUIRED_TOOL_PATTERN.pattern
    if not any(str(getattr(item, "pattern", "")) == pattern_text for item in existing):
        v2._REQUIRED_TOOL_PATTERNS = (
            _CLIENT_PREFIXED_REQUIRED_TOOL_PATTERN,
            *existing,
        )

    _INSTALLED = True


def client_prefixed_required_tool_pattern() -> Any:
    """Expose the compiled pattern for focused regression tests."""

    return _CLIENT_PREFIXED_REQUIRED_TOOL_PATTERN


__all__ = [
    "client_prefixed_required_tool_pattern",
    "install_codex_required_tool_language_patch",
]
