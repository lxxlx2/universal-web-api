#!/usr/bin/env python3
"""Run M4 pilot while excluding transient bytecode/cache files from change-scope checks."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools" / "codex_m4_real_project_pilot.py"
SPEC = importlib.util.spec_from_file_location("codex_m4_real_project_pilot", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise SystemExit("M4_WRAPPER_IMPORT_FAIL")
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)

_original_ignored_untracked = module.ignored_untracked


def _is_transient_cache(path: str) -> bool:
    normalized = str(path or "").replace("\\", "/")
    return (
        "/__pycache__/" in f"/{normalized}"
        or normalized.endswith(".pyc")
        or normalized.startswith(".pytest_cache/")
        or "/.pytest_cache/" in f"/{normalized}"
    )


def filtered_ignored_untracked() -> set[str]:
    return {path for path in _original_ignored_untracked() if not _is_transient_cache(path)}


module.ignored_untracked = filtered_ignored_untracked

if __name__ == "__main__":
    raise SystemExit(module.main())
