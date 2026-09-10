#!/usr/bin/env python3
"""Close H3-H5 Hybrid Routing Safety in one live synthetic run.

Runs the final H3 official-to-UWA handoff acceptance, records the resulting
private metadata-only H4 transition ledger, and performs an aggregate H5
synthetic hybrid acceptance. The official source action is never rerun.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WORKSPACE = Path(os.getenv("UWA_H3_WORKSPACE", str(Path.home() / "uwa-hybrid-acceptance"))).expanduser()
EXPECTED_FINAL = ["BASELINE", "OFFICIAL_EFFECT_ONCE", "UWA_CONTINUATION_ONCE"]


class FinalizeError(RuntimeError):
    pass


def run(cmd: list[str], *, cwd: Path, timeout: int = 420) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def print_safe_lines(text: str) -> None:
    allowed_prefixes = (
        "H3_",
        "PROJECT_",
        "CONFIGURED_",
        "HEALTH_",
        "SOURCE_",
        "OFFICIAL_CHECKER_",
        "ROUTE_MARK_",
        "CODEX_EXEC_",
        "FINAL_",
        "HANDOFF_CHECKER_",
        "NEW_TRACE_",
        "AGENT_",
        "METADATA_HELPER_",
        "ROUTE_AUDIT_",
        "LATEST_SESSION_",
        "UWA_WIRE_",
        "FAILURE_CLASS=",
    )
    for line in text.splitlines():
        if line.startswith(allowed_prefixes):
            print(line)


def parse_key(text: str, key: str) -> str:
    prefix = key + "="
    for line in reversed(text.splitlines()):
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def route_check() -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    result = run(
        [
            sys.executable,
            "tools/codex_route_audit.py",
            "check",
            "--expect-provider",
            "uwa",
            "--expect-model",
            "chatgpt",
            "--expect-effort",
            "high",
        ],
        cwd=REPO,
        timeout=60,
    )
    wanted = {
        "LATEST_SESSION_PROVIDER",
        "LATEST_SESSION_MODEL",
        "LATEST_SESSION_EFFORT",
        "LATEST_SESSION_IDENTITY_HASH",
        "UWA_WIRE_REQUEST_COUNT",
        "UWA_WIRE_RESPONSE_COUNT",
        "UWA_WIRE_LATEST_MODEL",
        "UWA_WIRE_LATEST_EFFORT",
        "UWA_WIRE_LATEST_STATUS",
        "ROUTE_EXPECTATION_PASS",
        "ROUTE_EXPECTATION_FAILURES",
    }
    parsed: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in wanted:
            parsed[key] = value.strip()
    return result, parsed


def write_h4_ledger(session_hash: str) -> None:
    base = [
        sys.executable,
        "tools/codex_hybrid_ledger.py",
        "record",
        "--workspace",
        str(WORKSPACE),
        "--source-provider",
        "openai",
        "--source-model",
        "gpt-6-astra",
        "--source-effort",
        "low",
        "--target-provider",
        "uwa",
        "--target-model",
        "chatgpt",
        "--target-effort",
        "high",
    ]
    handoff = run(base + ["--event", "handoff"], cwd=REPO, timeout=30)
    print(f"H4_HANDOFF_RECORD_RC={handoff.returncode}")
    if handoff.returncode != 0:
        raise FinalizeError("h4_handoff_record_failed")

    complete_cmd = base + ["--event", "complete"]
    if session_hash and session_hash != "UNKNOWN":
        complete_cmd += ["--session-identity-hash", session_hash]
    complete = run(complete_cmd, cwd=REPO, timeout=30)
    print(f"H4_COMPLETE_RECORD_RC={complete.returncode}")
    if complete.returncode != 0:
        raise FinalizeError("h4_complete_record_failed")

    status = run([sys.executable, "tools/codex_hybrid_ledger.py", "status"], cwd=REPO, timeout=30)
    print(f"H4_LEDGER_STATUS_RC={status.returncode}")
    safe_keys = {
        "HYBRID_LEDGER_PRESENT",
        "HYBRID_LEDGER_PRIVATE_MODE",
        "LAST_EVENT",
        "LAST_SOURCE_PROVIDER",
        "LAST_SOURCE_MODEL",
        "LAST_SOURCE_EFFORT",
        "LAST_TARGET_PROVIDER",
        "LAST_TARGET_MODEL",
        "LAST_TARGET_EFFORT",
        "LAST_WORKSPACE_HASH",
        "LAST_SESSION_IDENTITY_HASH",
    }
    values: dict[str, str] = {}
    for line in status.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in safe_keys:
            values[key] = value.strip()
            print(f"{key}={values[key]}")
    expected = {
        "HYBRID_LEDGER_PRESENT": "YES",
        "HYBRID_LEDGER_PRIVATE_MODE": "YES",
        "LAST_EVENT": "complete",
        "LAST_SOURCE_PROVIDER": "openai",
        "LAST_SOURCE_MODEL": "gpt-6-astra",
        "LAST_SOURCE_EFFORT": "low",
        "LAST_TARGET_PROVIDER": "uwa",
        "LAST_TARGET_MODEL": "chatgpt",
        "LAST_TARGET_EFFORT": "high",
    }
    if status.returncode != 0 or any(values.get(key) != value for key, value in expected.items()):
        raise FinalizeError("h4_ledger_verification_failed")
    print("H4_TRANSITION_LEDGER=PASS")


def h5_acceptance(route: dict[str, str]) -> None:
    effects_path = WORKSPACE / "effects.log"
    if not effects_path.is_file():
        raise FinalizeError("h5_effects_missing")
    effects = effects_path.read_text(encoding="utf-8").splitlines()
    print(f"H5_OFFICIAL_EFFECT_COUNT={effects.count('OFFICIAL_EFFECT_ONCE')}")
    print(f"H5_UWA_EFFECT_COUNT={effects.count('UWA_CONTINUATION_ONCE')}")
    if effects != EXPECTED_FINAL:
        raise FinalizeError("h5_effect_counts_wrong")

    checker = run([sys.executable, "check_handoff.py"], cwd=WORKSPACE, timeout=30)
    print(f"H5_HANDOFF_CHECKER_RC={checker.returncode}")
    if checker.returncode != 0:
        raise FinalizeError("h5_handoff_checker_failed")

    route_ok = (
        route.get("LATEST_SESSION_PROVIDER") == "uwa"
        and route.get("LATEST_SESSION_MODEL") == "chatgpt"
        and route.get("LATEST_SESSION_EFFORT") == "high"
        and route.get("UWA_WIRE_LATEST_MODEL") == "chatgpt"
        and route.get("UWA_WIRE_LATEST_EFFORT") == "high"
        and route.get("UWA_WIRE_LATEST_STATUS") == "completed"
        and route.get("ROUTE_EXPECTATION_PASS") == "YES"
    )
    print("H5_ROUTE_UWA_CHATGPT_HIGH=" + ("YES" if route_ok else "NO"))
    if not route_ok:
        raise FinalizeError("h5_route_verification_failed")

    print("H5_NO_DUPLICATE_EFFECT=YES")
    print("H5_SYNTHETIC_HYBRID_ACCEPTANCE=PASS")


def main() -> int:
    print("M3A_HYBRID_FINALIZE_BEGIN")
    try:
        h3 = run([sys.executable, "tools/codex_h3_final_handoff_live.py"], cwd=REPO, timeout=420)
        print_safe_lines(h3.stdout)
        print(f"H3_FINALIZER_RC={h3.returncode}")
        if h3.returncode != 0 or parse_key(h3.stdout, "H3_FINAL_HANDOFF") != "PASS_LIVE":
            raise FinalizeError("h3_final_handoff_failed")

        route_result, route = route_check()
        print(f"H4_ROUTE_CHECK_RC={route_result.returncode}")
        if route_result.returncode != 0 or route.get("ROUTE_EXPECTATION_PASS") != "YES":
            raise FinalizeError("h4_route_check_failed")

        session_hash = route.get("LATEST_SESSION_IDENTITY_HASH", "")
        write_h4_ledger(session_hash)
        h5_acceptance(route)

        print("H3_STATEFUL_HANDOFF=PASS_LIVE_CLOSED")
        print("H4_PRIVATE_TRANSITION_LEDGER=PASS_CLOSED")
        print("H5_SYNTHETIC_HYBRID_ACCEPTANCE=PASS_CLOSED")
        print("M3A_HYBRID_ROUTING_SAFETY=PASS_LIVE_CLOSED")
        return 0
    except subprocess.TimeoutExpired:
        print("M3A_HYBRID_ROUTING_SAFETY=FAIL")
        print("FAILURE_CLASS=local_subprocess_timeout")
        return 1
    except FinalizeError as exc:
        print("M3A_HYBRID_ROUTING_SAFETY=FAIL")
        print(f"FAILURE_CLASS={exc}")
        return 1
    except Exception as exc:
        print("M3A_HYBRID_ROUTING_SAFETY=FAIL")
        print("FAILURE_CLASS=unexpected_" + type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
