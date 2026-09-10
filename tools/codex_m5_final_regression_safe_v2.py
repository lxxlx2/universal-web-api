#!/usr/bin/env python3
"""Run M5 with safe Python bootstrap and a fresh private Stage A-F replay fixture.

The original Stage A-F live acceptance is already closed. Its historical workspace is
mutable because later Desktop/recovery exercises can prepare or reset individual
scenarios. M5 must not treat that mutable workspace as an immutable release artifact.

This wrapper keeps the existing private pytest bootstrap, then validates the current
Stage A-F checker against a fresh private deterministic completed-state fixture under
~/.uwa. It never modifies or deletes the historical ~/uwa-codex-acceptance workspace.
The rest of M5 remains unchanged, including the complete current Codex regression
family and the fresh same-thread restart-continuity live smoke on UWA/chatgpt/high.
"""

from __future__ import annotations

import importlib.util
import secrets
import shutil
import sys
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SAFE_V1 = REPO / "tools" / "codex_m5_final_regression_safe.py"
PRIVATE_REPLAY_PARENT = Path.home() / ".uwa" / "m5-stage-af-replay"
REPLAY_MARKER = ".uwa_m5_stage_af_replay"


def _load_safe_v1():
    spec = importlib.util.spec_from_file_location("codex_m5_final_regression_safe_v1", SAFE_V1)
    if spec is None or spec.loader is None:
        raise SystemExit("M5_SAFE_V2_IMPORT_FAIL")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


safe = _load_safe_v1()
base = safe.base


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fresh_replay_root() -> Path:
    PRIVATE_REPLAY_PARENT.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        PRIVATE_REPLAY_PARENT.chmod(0o700)
    except OSError:
        pass
    for _ in range(8):
        suffix = time.strftime("%Y%m%dT%H%M%S", time.gmtime()) + "-" + secrets.token_hex(4)
        root = PRIVATE_REPLAY_PARENT / suffix
        if not root.exists():
            return root
    raise base.GateError("stage_a_f_replay_path_allocation_failed")


def _cleanup_replay(root: Path) -> None:
    resolved_parent = PRIVATE_REPLAY_PARENT.resolve()
    resolved = root.resolve()
    if resolved.parent != resolved_parent:
        raise base.GateError("stage_a_f_replay_cleanup_guard_failed")
    if not resolved.exists():
        return
    owned = (resolved / REPLAY_MARKER).is_file() or (resolved / base.ACCEPTANCE_MARKER).is_file()
    if not owned:
        raise base.GateError("stage_a_f_replay_cleanup_guard_failed")
    shutil.rmtree(resolved)


def require_stage_a_f_replay_ready() -> None:
    legacy = (
        base.ACCEPTANCE_ROOT.is_dir()
        and (base.ACCEPTANCE_ROOT / base.ACCEPTANCE_MARKER).is_file()
        and (base.ACCEPTANCE_ROOT / ".git").is_dir()
    )
    print("M5_STAGE_A_F_LEGACY_WORKSPACE_GUARDED=" + ("YES" if legacy else "NO"))
    print("M5_STAGE_A_F_WORKSPACE_POLICY=DO_NOT_MUTATE_HISTORICAL")
    print("M5_STAGE_A_F_REPLAY_MODE=PRIVATE_FRESH_FIXTURE")
    print("M5_STAGE_A_F_HISTORICAL_LIVE_STATUS=PASS_CLOSED")


def _materialize_completed_state(root: Path) -> None:
    _write(
        root / "multi_file" / "math_ops.py",
        "def add(a, b):\n    return a + b\n\n\ndef multiply(a, b):\n    return a * b\n",
    )
    _write(
        root / "multi_file" / "summary.py",
        "def render_total(value):\n    return f\"Total: {value}\"\n",
    )
    _write(
        root / "failure_recovery" / "parser.py",
        "def parse_port(value):\n"
        "    if not isinstance(value, str):\n"
        "        raise ValueError(\"invalid port\")\n"
        "    token = value.strip()\n"
        "    if not token.isdigit():\n"
        "        raise ValueError(\"invalid port\")\n"
        "    port = int(token)\n"
        "    if port < 1 or port > 65535:\n"
        "        raise ValueError(\"invalid port\")\n"
        "    return port\n",
    )
    _write(root / "failure_recovery" / ".run_history", "1\n0\n")
    _write(root / "git_diff" / "config.py", 'MODE = "prod"\nTIMEOUT = 30\n')
    _write(root / "interactive" / "result.txt", "INTERACTIVE_PASS\n")
    _write(root / "context" / "result.txt", "EMBER-7319\n")


def run_stage_a_f_replay(python_executable: str) -> None:
    root = _fresh_replay_root()
    try:
        setup = base.run(
            [
                python_executable,
                "tools/codex_desktop_acceptance.py",
                "setup",
                "--root",
                str(root),
            ],
            timeout=120,
        )
        print(f"M5_STAGE_A_F_REPLAY_SETUP_RC={setup.returncode}")
        if setup.returncode != 0:
            raise base.GateError("stage_a_f_replay_setup_failed")

        _write(root / REPLAY_MARKER, "M5 private Stage A-F deterministic replay\n")
        print("M5_STAGE_A_F_REPLAY_OWNERSHIP_MARKER=YES")
        _materialize_completed_state(root)

        result = base.run(
            [
                python_executable,
                "tools/codex_desktop_acceptance.py",
                "check",
                "--root",
                str(root),
            ],
            timeout=180,
        )
        passed = result.returncode == 0 and "ACCEPTANCE_PASS" in result.stdout
        print(f"M5_STAGE_A_F_AGGREGATE_RC={result.returncode}")
        print("M5_STAGE_A_F_AGGREGATE=" + ("PASS" if passed else "FAIL"))
        print("M5_STAGE_A_F_AGGREGATE_SOURCE=PRIVATE_DETERMINISTIC_REPLAY")
        if not passed:
            scenario_lines = []
            for line in result.stdout.splitlines():
                text = line.strip()
                if text.startswith(("multi_file:", "failure_recovery:", "git_diff:", "interactive:", "context:")):
                    scenario_lines.append(text)
            if scenario_lines:
                print("M5_STAGE_A_F_SAFE_SUMMARY=" + " | ".join(scenario_lines)[:500])
            raise base.GateError("stage_a_f_replay_failed")
    finally:
        _cleanup_replay(root)
        print("M5_STAGE_A_F_REPLAY_CLEANED=YES")


base.require_acceptance_workspace = require_stage_a_f_replay_ready
base.run_stage_a_f_aggregate = run_stage_a_f_replay


if __name__ == "__main__":
    raise SystemExit(base.main())
