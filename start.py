#!/usr/bin/env python3
"""Hardened launcher.

The upstream launcher is preserved verbatim as start_upstream.py. This wrapper
sets safe defaults, validates .env, then executes the upstream launcher.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

from security_guard import (
    effective_startup_environment,
    ensure_safe_defaults,
    validate_runtime_security,
)

PROJECT_DIR = Path(__file__).resolve().parent
UPSTREAM_START = PROJECT_DIR / "start_upstream.py"


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

    if not UPSTREAM_START.exists():
        print("[SECURITY] Missing start_upstream.py; hardened startup aborted.", file=sys.stderr)
        return 66

    sys.argv[0] = str(UPSTREAM_START)
    runpy.run_path(str(UPSTREAM_START), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
