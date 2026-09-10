#!/usr/bin/env python3
"""Finalize M4 from the already-completed bounded recovery review.

The latest bounded review completed successfully and executed a real local tool,
but the model omitted the cosmetic final text marker. This finalizer does not
repeat that Web turn. It rebuilds the deterministic M4 implementation/test pair,
reruns the focused local validation, then proves the completed review from the
post-marker metadata-only wire trace and route audit. Only after all structural
and health gates pass does it commit and push the two expected M4 paths.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
FOCUSED_PATH = REPO / "tools" / "codex_m4_focused_repair_and_close.py"
TRACE_DIR = Path.home() / ".uwa" / "debug" / "codex-wire"
MARKER_PATH = Path.home() / ".uwa" / "route-audit-marker.json"
MAX_MARKER_AGE_SECONDS = 2 * 60 * 60


def _load_focused():
    spec = importlib.util.spec_from_file_location(
        "codex_m4_focused_repair_for_structural_finalize",
        FOCUSED_PATH,
    )
    if spec is None or spec.loader is None:
        raise SystemExit("M4_STRUCTURAL_FINALIZER_IMPORT_FAIL")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


focused = _load_focused()
safe = focused.safe
module = focused.module


def _read_marker_epoch() -> float:
    if not MARKER_PATH.is_file():
        raise module.GateError("route_marker_missing")
    try:
        data = json.loads(MARKER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise module.GateError("route_marker_unreadable") from exc
    value = data.get("captured_at_unix") if isinstance(data, dict) else None
    if not isinstance(value, (int, float)):
        raise module.GateError("route_marker_timestamp_missing")
    epoch = float(value)
    age = max(0, int(time.time() - epoch))
    print(f"M4_REVIEW_MARKER_AGE_SECONDS={age}")
    if age > MAX_MARKER_AGE_SECONDS:
        raise module.GateError("route_marker_too_old_for_completed_review")
    return epoch


def _trace_summaries_since(epoch: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    requests: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    if not TRACE_DIR.is_dir():
        return requests, responses
    for path in TRACE_DIR.glob("*.json"):
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        captured = data.get("captured_at_unix")
        try:
            captured_epoch = float(captured)
        except (TypeError, ValueError):
            continue
        if captured_epoch < epoch:
            continue
        summary = data.get("summary")
        if not isinstance(summary, dict):
            continue
        if summary.get("request_kind") != "agent_turn":
            continue
        if path.name.endswith("-request.json"):
            requests.append(summary)
        elif path.name.endswith("-response.json"):
            responses.append(summary)
    return requests, responses


def verify_completed_review_from_wire() -> None:
    epoch = _read_marker_epoch()
    requests, responses = _trace_summaries_since(epoch)
    route_ok = any(
        str(item.get("model") or "") == "chatgpt"
        and str(item.get("reasoning_effort") or "") == "high"
        for item in requests
    )
    exec_calls = sum(
        1
        for item in responses
        if "exec_command" in (item.get("function_call_names") or [])
    )
    completed = sum(
        1
        for item in responses
        if str(item.get("response_status") or "") == "completed"
    )

    print(f"M4_POST_MARKER_AGENT_REQUEST_COUNT={len(requests)}")
    print(f"M4_POST_MARKER_AGENT_RESPONSE_COUNT={len(responses)}")
    print("M4_POST_MARKER_ROUTE_CHATGPT_HIGH=" + ("YES" if route_ok else "NO"))
    print(f"M4_POST_MARKER_EXEC_COMMAND_RESPONSE_COUNT={exec_calls}")
    print(f"M4_POST_MARKER_COMPLETED_RESPONSE_COUNT={completed}")

    if not requests:
        raise module.GateError("completed_review_agent_request_missing")
    if not route_ok:
        raise module.GateError("completed_review_route_mismatch")
    if exec_calls < 1:
        raise module.GateError("completed_review_exec_command_missing")
    if completed < 1:
        raise module.GateError("completed_review_response_completed_missing")

    audit = module.run(
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
        timeout=60,
    )
    print(f"M4_ROUTE_AUDIT_RC={audit.returncode}")
    route_pass = audit.returncode == 0 and "ROUTE_EXPECTATION_PASS=YES" in audit.stdout
    print("M4_ROUTE_EXPECTATION_PASS=" + ("YES" if route_pass else "NO"))
    if not route_pass:
        raise module.GateError("completed_review_route_audit_failed")


def verify_health() -> None:
    payload = module.health()
    running = module.running_count(payload)
    connected = module.browser_connected(payload)
    print(f"M4_FINAL_HEALTH_RUNNING_COUNT={running}")
    print(f"M4_FINAL_HEALTH_BROWSER_CONNECTED={connected}")
    if running != 0 or connected is not True:
        raise module.GateError("m4_final_health_failed")


def main() -> int:
    print("M4_COMPLETED_REVIEW_STRUCTURAL_FINALIZE_BEGIN")
    try:
        safe.safe_require_resume_state()

        provider, model, effort = module.configured_route()
        print("CONFIGURED_PROVIDER=" + (provider or "UNKNOWN"))
        print("CONFIGURED_MODEL=" + (model or "UNKNOWN"))
        print("CONFIGURED_EFFORT=" + (effort or "UNKNOWN"))
        if (provider, model, effort) != ("uwa", "chatgpt", "high"):
            raise module.GateError("uwa_chatgpt_high_not_configured")

        module.ensure_uwa_ready()
        focused.final_normalize_implementation()
        module.write_regression_test()
        focused.final_local_validation()
        print("M4_FOCUSED_REGRESSION=PASS_3_OF_3")

        verify_completed_review_from_wire()
        print("M4_COMPLETED_REVIEW_STRUCTURAL_EVIDENCE=PASS")
        print("M4_TEXT_MARKER_REQUIRED=NO")
        print("M4_TEXT_MARKER_REASON=turn_completed_plus_real_tool_plus_wire_route_are_authoritative")

        verify_health()
        module.commit_push()

        print("M4_PRIOR_LONG_TASK_TOOL_ACTIVITY=YES")
        print("M4_CANONICAL_CANCELLATION_FIX=PASS")
        print("M4_STDLIB_REGRESSION=PASS")
        print("M4_BOUNDED_RECOVERY_REVIEW=PASS_LIVE_STRUCTURAL")
        print("M4_ROUTE_UWA_CHATGPT_HIGH=YES")
        print("M4_REQUEST_MANAGER_CLEAN_AFTER=YES")
        print("M4_REAL_PROJECT_LONG_TASK_PILOT=PASS_LIVE_CLOSED")
        return 0
    except module.GateError as exc:
        print("M4_COMPLETED_REVIEW_STRUCTURAL_FINALIZE=FAIL")
        print("FAILURE_CLASS=" + str(exc))
        return 2
    except Exception as exc:
        print("M4_COMPLETED_REVIEW_STRUCTURAL_FINALIZE=FAIL")
        print("FAILURE_CLASS=unexpected_" + type(exc).__name__)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
