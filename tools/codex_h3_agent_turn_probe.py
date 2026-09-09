#!/usr/bin/env python3
"""One-shot local probe for the H3 UWA agent-turn / exec_command path.

The probe intentionally prints metadata only. It never prints prompts, command bodies,
tool outputs, thread ids, browser ids, cookies, credentials, or raw wire traces.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


REPO = Path(__file__).resolve().parents[1]
TRACE_DIR = Path(
    os.path.expanduser(
        os.getenv("UWA_CODEX_WIRE_TRACE_DIR", "~/.uwa/debug/codex-wire")
    )
).resolve()
PROBE_PROMPT = (
    "You must use the local exec_command tool. Run exactly pwd. "
    "Then reply exactly UWA_CLI_AGENT_OK. Do not edit files."
)
TIMEOUT_SECONDS = int(os.getenv("UWA_H3_AGENT_PROBE_TIMEOUT", "330"))


def _run(cmd: List[str], *, timeout: int = 30) -> Tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return 124, stdout, stderr


def _json_lines_event_types(text: str) -> List[str]:
    types: List[str] = []
    for line in text.splitlines():
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        event_type = str(payload.get("type") or "").strip()
        if event_type and event_type not in types:
            types.append(event_type)
    return types


def _health() -> Dict[str, Any]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8199/health", timeout=5) as response:
            raw = response.read().decode("utf-8", "replace")
            payload = json.loads(raw)
            return payload if isinstance(payload, dict) else {"http_status": response.status}
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "error": "http_error"}
    except Exception as exc:
        return {"error": type(exc).__name__}


def _find_key(value: Any, wanted: str) -> Any:
    if isinstance(value, dict):
        if wanted in value:
            return value[wanted]
        for item in value.values():
            found = _find_key(item, wanted)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_key(item, wanted)
            if found is not None:
                return found
    return None


def _trace_files_after(started_at: float) -> List[Path]:
    if not TRACE_DIR.exists():
        return []
    files = []
    for path in TRACE_DIR.glob("*.json"):
        try:
            if path.is_file() and path.stat().st_mtime >= started_at - 1.0:
                files.append(path)
        except OSError:
            continue
    return sorted(files, key=lambda p: (p.stat().st_mtime, p.name))


def _safe_trace_summary(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {"file_kind": "unreadable"}
    if not isinstance(payload, dict):
        return {"file_kind": "invalid"}
    if str(payload.get("mode") or "") != "metadata":
        return {"file_kind": "skipped_non_metadata", "mode": str(payload.get("mode") or "")}

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    if path.name.endswith("-request.json"):
        return {
            "file_kind": "request",
            "attempt": payload.get("attempt"),
            "model": summary.get("model"),
            "reasoning_effort": summary.get("reasoning_effort"),
            "tool_names": summary.get("tool_names") if isinstance(summary.get("tool_names"), list) else [],
            "required_tool": summary.get("required_tool"),
            "previous_response_id_present": summary.get("previous_response_id_present"),
            "input": summary.get("input") if isinstance(summary.get("input"), dict) else {},
        }
    if path.name.endswith("-response.json"):
        event_order = summary.get("event_order") if isinstance(summary.get("event_order"), list) else []
        return {
            "file_kind": "response",
            "attempt": payload.get("attempt"),
            "response_status": summary.get("response_status"),
            "function_call_names": summary.get("function_call_names") if isinstance(summary.get("function_call_names"), list) else [],
            "output_text_chars": summary.get("output_text_chars"),
            "event_order_tail": event_order[-8:],
        }
    return {"file_kind": "other"}


def _print_health(label: str, payload: Dict[str, Any]) -> None:
    print(f"{label}_ERROR={payload.get('error', '')}")
    for key in ("running_count", "healthy", "connected"):
        value = _find_key(payload, key)
        if value is not None:
            print(f"{label}_{key.upper()}={value}")


def main() -> int:
    print("H3_AGENT_TURN_PROBE_BEGIN")

    rc, branch, _ = _run(["git", "branch", "--show-current"])
    branch = branch.strip()
    print(f"BRANCH={branch}")
    if rc != 0 or branch != "codex-web-bridge-v2":
        print("PRECONDITION_FAIL=wrong_branch")
        return 2

    rc, status, _ = _run(["git", "status", "--short"])
    dirty_lines = [line for line in status.splitlines() if line.strip()]
    print(f"WORKTREE_DIRTY_COUNT={len(dirty_lines)}")

    route_rc, route_out, _ = _run([sys.executable, "tools/codex_route_audit.py", "status"], timeout=20)
    print(f"ROUTE_AUDIT_RC={route_rc}")
    for line in route_out.splitlines():
        if any(
            token in line
            for token in (
                "CONFIGURED_PROVIDER=",
                "CONFIGURED_MODEL=",
                "CONFIGURED_REASONING_EFFORT=",
                "ROUTE_EXPECTATION_PASS=",
            )
        ):
            print(line.strip())

    health_before = _health()
    _print_health("HEALTH_BEFORE", health_before)

    started_at = time.time()
    print(f"CODEX_EXEC_TIMEOUT_SECONDS={TIMEOUT_SECONDS}")
    exec_rc, exec_out, exec_err = _run(
        [
            "codex",
            "exec",
            "--json",
            "--skip-git-repo-check",
            PROBE_PROMPT,
        ],
        timeout=TIMEOUT_SECONDS,
    )
    print(f"CODEX_EXEC_RC={exec_rc}")
    print("CODEX_EXEC_EVENT_TYPES=" + ",".join(_json_lines_event_types(exec_out)))
    stderr_kinds: List[str] = []
    lowered = exec_err.lower()
    if "stream disconnected before completion" in lowered:
        stderr_kinds.append("stream_disconnected")
    if "response.completed" in lowered:
        stderr_kinds.append("mentions_response_completed")
    if "timeout" in lowered or exec_rc == 124:
        stderr_kinds.append("timeout")
    print("CODEX_EXEC_STDERR_KINDS=" + ",".join(stderr_kinds))

    time.sleep(1.0)
    summaries = [_safe_trace_summary(path) for path in _trace_files_after(started_at)]
    requests = [item for item in summaries if item.get("file_kind") == "request"]
    responses = [item for item in summaries if item.get("file_kind") == "response"]
    skipped = [item for item in summaries if item.get("file_kind") == "skipped_non_metadata"]

    print(f"NEW_TRACE_REQUESTS={len(requests)}")
    print(f"NEW_TRACE_RESPONSES={len(responses)}")
    print(f"SKIPPED_NON_METADATA_TRACES={len(skipped)}")

    for index, item in enumerate(requests, 1):
        print(
            "TRACE_REQUEST_{}={}".format(
                index,
                json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            )
        )
    for index, item in enumerate(responses, 1):
        print(
            "TRACE_RESPONSE_{}={}".format(
                index,
                json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            )
        )

    required_exec = any(str(item.get("required_tool") or "") == "exec_command" for item in requests)
    emitted_exec = any("exec_command" in (item.get("function_call_names") or []) for item in responses)
    completed = any(str(item.get("response_status") or "") == "completed" for item in responses)

    print(f"REQUIRED_EXEC_COMMAND_DETECTED={'YES' if required_exec else 'NO'}")
    print(f"EXEC_COMMAND_FUNCTION_CALL_EMITTED={'YES' if emitted_exec else 'NO'}")
    print(f"COMPLETED_RESPONSE_OBSERVED={'YES' if completed else 'NO'}")

    health_after = _health()
    _print_health("HEALTH_AFTER", health_after)

    running_after = _find_key(health_after, "running_count")
    clean_after = running_after in (0, "0", None)
    print(f"REQUEST_MANAGER_CLEAN_AFTER={'YES' if clean_after else 'NO'}")

    if exec_rc == 0 and required_exec and emitted_exec and completed and clean_after:
        print("H3_AGENT_TURN_PROBE=PASS")
        return 0

    print("H3_AGENT_TURN_PROBE=FAIL")
    if not required_exec:
        print("FAILURE_CLASS=required_tool_not_detected_or_agent_turn_not_observed")
    elif not emitted_exec:
        print("FAILURE_CLASS=required_tool_detected_but_function_call_missing")
    elif not completed:
        print("FAILURE_CLASS=function_call_seen_but_terminal_completion_missing")
    elif not clean_after:
        print("FAILURE_CLASS=orphan_request_after_client_turn")
    else:
        print("FAILURE_CLASS=codex_client_nonzero_exit")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
