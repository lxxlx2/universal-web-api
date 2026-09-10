#!/usr/bin/env python3
"""Run M4 pilot with transient-cache filtering and safe UWA preflight recovery."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools" / "codex_m4_real_project_pilot.py"
LIFECYCLE_PATH = REPO / "tools" / "codex_uwa_lifecycle.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"M4_WRAPPER_IMPORT_FAIL={name}")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


module = _load_module("codex_m4_real_project_pilot", MODULE_PATH)
lifecycle = _load_module("codex_uwa_lifecycle_for_m4", LIFECYCLE_PATH)
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


def _health_ready() -> tuple[bool, int, bool | None]:
    payload = module.health()
    running = module.running_count(payload)
    connected = module.browser_connected(payload)
    return bool(payload) and running == 0 and connected is True, running, connected


def _ensure_uwa_preflight() -> None:
    ready, running, connected = _health_ready()
    print(f"UWA_PREFLIGHT_INITIAL_RUNNING_COUNT={running}")
    print(f"UWA_PREFLIGHT_INITIAL_BROWSER_CONNECTED={connected}")
    if ready:
        print("UWA_PREFLIGHT_RECOVERY=NOT_NEEDED")
        return

    if connected is True and running > 0:
        print("UWA_PREFLIGHT_RECOVERY=BLOCKED_ACTIVE_WORK")
        return

    print("UWA_PREFLIGHT_RECOVERY=NEEDED")
    listeners = lifecycle.listener_pids()
    if listeners:
        lifecycle.require_owned_listeners(listeners, repo_root=REPO)
        print("UWA_PREFLIGHT_RECOVERY_ACTION=restart")
        lifecycle.restart_uwa(repo_root=REPO)
    else:
        print("UWA_PREFLIGHT_RECOVERY_ACTION=start")
        lifecycle.start_uwa(repo_root=REPO)

    deadline = time.monotonic() + 30.0
    final_running = -1
    final_connected = None
    while time.monotonic() < deadline:
        ready, final_running, final_connected = _health_ready()
        if ready:
            break
        time.sleep(1.0)

    print(f"UWA_PREFLIGHT_FINAL_RUNNING_COUNT={final_running}")
    print(f"UWA_PREFLIGHT_FINAL_BROWSER_CONNECTED={final_connected}")
    if not ready:
        raise SystemExit("M4_WRAPPER_UWA_RECOVERY_FAILED")
    print("UWA_PREFLIGHT_RECOVERY=PASS")


module.ignored_untracked = filtered_ignored_untracked

if __name__ == "__main__":
    _ensure_uwa_preflight()
    raise SystemExit(module.main())
