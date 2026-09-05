#!/usr/bin/env python3
"""Hardened launcher for the local Universal Web API fork.

The upstream launcher is preserved verbatim as start_upstream.py. This module
keeps its helper API available for existing tests and integrations while adding
a security gate before the upstream main() function is executed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import start_upstream as _upstream
from security_guard import (
    effective_startup_environment,
    ensure_safe_defaults,
    validate_runtime_security,
)

PROJECT_DIR = Path(__file__).resolve().parent


def __getattr__(name: str):
    """Delegate upstream launcher helpers, including private compatibility APIs."""
    return getattr(_upstream, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_upstream)))


def main() -> int:
    os.chdir(PROJECT_DIR)
    ensure_safe_defaults()

    try:
        validate_runtime_security(effective_startup_environment(PROJECT_DIR / ".env"))
    except RuntimeError as exc:
        print(f"[SECURITY] {exc}", file=sys.stderr)
        print(
            "[SECURITY] Keep APP_HOST=127.0.0.1 for local Codex use, or follow "
            "SECURITY-HARDENING.md for controlled remote access.",
            file=sys.stderr,
        )
        return 78

    return int(_upstream.main())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        _upstream._log()
        _upstream._log("[INFO] 已取消启动")
        raise SystemExit(130)
    except Exception as exc:
        _upstream._log()
        _upstream._log(f"[ERROR] {exc}")
        raise SystemExit(1)
