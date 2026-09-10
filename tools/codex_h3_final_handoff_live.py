#!/usr/bin/env python3
"""Run the final synthetic H3 official-to-UWA handoff acceptance in one shot.

The official source half must already exist exactly once in the preserved local
workspace. This helper never re-runs the official source action. It starts one
fresh UWA Codex CLI agent turn in the same workspace, requires a real
exec_command call, verifies the continuation effect exactly once, checks
metadata-only route evidence, and leaves public project files untouched.

No prompt body, command body, tool output, thread id, browser id, PID, cookie or
credential is printed by this helper.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
BRANCH = "codex-web-bridge-v2"
WORKSPACE = Path(os.getenv("UWA_H3_WORKSPACE", str(Path.home() / "uwa-hybrid-acceptance"))).expanduser()
TRACE_DIR = Path.home() / ".uwa" / "debug" / "codex-wire"
CONFIG = Path.home() / ".codex" / "config.toml"
HEALTH_URL = "http://127.0.0.1:8199/health"
EXPECTED_SOURCE = ["BASELINE", "OFFICIAL_EFFECT_ONCE"]
EXPECTED_FINAL = ["BASELINE", "OFFICIAL_EFFECT_ONCE", "UWA_CONTINUATION_ONCE"]
TIMEOUT_SECONDS = int(os.getenv("UWA_H3_FINAL_TIMEOUT", "330"))


class GateError(RuntimeError):
    pass


def run(cmd: list[str], *, cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def git_clean_branch() -> None:
    branch = run(["git", "branch", "--show-current"], cwd=REPO, timeout=20)
    print("PROJECT_BRANCH=" + branch.stdout.strip())
    if branch.returncode != 0 or branch.stdout.strip() != BRANCH:
        raise GateError("project_wrong_branch")
    status = run(["git", "status", "--porcelain"], cwd=REPO, timeout=20)
    dirty = [line for line in status.stdout.splitlines() if line.strip()]
    print(f"PROJECT_WORKTREE_DIRTY_COUNT={len(dirty)}")
    if status.returncode != 0 or dirty:
        raise GateError("project_worktree_dirty")


def configured_route() -> tuple[str, str, str]:
    if not CONFIG.exists():
        return "", "", ""
    data = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    provider = str(data.get("model_provider") or "").strip()
    model = str(data.get("model") or "").strip()
    effort = str(data.get("model_reasoning_effort") or "").strip()
    return provider, model, effort


def health() -> dict[str, Any]:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2.0) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return {}
    return payload if isinstance(payload, dict) else {}


def running_count(payload: dict[str, Any]) -> int:
    manager = payload.get("request_manager")
    if isinstance(manager, dict):
        value = manager.get("running_count")
        if isinstance(value, int):
            return value
    stats = payload.get("stats")
    if isinstance(stats, dict):
        value = stats.get("running_requests")
        if isinstance(value, int):
            return value
    return -1


def browser_connected(payload: dict[str, Any]) -> bool | None:
    browser = payload.get("browser")
    if isinstance(browser, dict) and isinstance(browser.get("connected"), bool):
        return browser["connected"]
    value = payload.get("browser_connected")
    return value if isinstance(value, bool) else None


def read_effects() -> list[str]:
    path = WORKSPACE / "effects.log"
    if not path.is_file():
        raise GateError("effects_log_missing")
    return [line.rstrip("\r\n") for line in path.read_text(encoding="utf-8").splitlines()]


def verify_workspace_source() -> None:
    if not WORKSPACE.is_dir():
        raise GateError("handoff_workspace_missing")
    effects = read_effects()
    print(f"SOURCE_LINE_COUNT={len(effects)}")
    print(f"SOURCE_OFFICIAL_EFFECT_COUNT={effects.count('OFFICIAL_EFFECT_ONCE')}")
    print(f"SOURCE_UWA_EFFECT_COUNT={effects.count('UWA_CONTINUATION_ONCE')}")
    if effects != EXPECTED_SOURCE:
        raise GateError("source_state_not_exact")
    checker = WORKSPACE / "check_official.py"
    if not checker.is_file():
        raise GateError("official_checker_missing")
    result = run([sys.executable, checker.name], cwd=WORKSPACE, timeout=30)
    print(f"OFFICIAL_CHECKER_RC={result.returncode}")
    print("OFFICIAL_CHECKER_PASS=" + ("YES" if result.returncode == 0 else "NO"))
    if result.returncode != 0:
        raise GateError("official_source_checker_failed")


def trace_snapshot() -> set[str]:
    if not TRACE_DIR.is_dir():
        return set()
    return {path.name for path in TRACE_DIR.glob("*.json") if path.is_file()}


def safe_event_summary(stdout: str) -> tuple[list[str], int]:
    event_types: list[str] = []
    tool_item_count = 0
    for line in stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        event_type = str(item.get("type") or "").strip()
        if event_type and event_type not in event_types:
            event_types.append(event_type)
        if event_type in {"item.started", "item.completed"}:
            event_item = item.get("item")
            if isinstance(event_item, dict):
                item_type = str(event_item.get("type") or "").strip().lower()
                if "command" in item_type or "tool" in item_type or "function" in item_type:
                    tool_item_count += 1
    return event_types, tool_item_count


def handoff_prompt() -> str:
    return (
        "You are completing the UWA continuation half of a synthetic hybrid-routing acceptance. "
        "You must use the local exec_command tool. First inspect the existing effects.log and "
        "check_handoff.py in the current workspace using real local tools. Preserve every existing "
        "line and do not re-run, remove, or rewrite the official source effect. If and only if the "
        "exact line UWA_CONTINUATION_ONCE is absent, append that exact line once to effects.log. "
        "Do not edit any other file. Then use exec_command to run python3 check_handoff.py. "
        "Only after the checker succeeds, finish with H3_UWA_AGENT_DONE. Do not simulate tool output."
    )


def run_fresh_uwa_agent() -> tuple[int, list[str], int]:
    cmd = [
        "codex",
        "exec",
        "--json",
        "--skip-git-repo-check",
        handoff_prompt(),
    ]
    started = time.time()
    try:
        result = run(cmd, cwd=WORKSPACE, timeout=TIMEOUT_SECONDS)
        rc = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        rc = 124
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    elapsed = int(time.time() - started)
    event_types, tool_items = safe_event_summary(stdout)
    stderr_kinds: list[str] = []
    low = stderr.lower()
    for name, needle in (
        ("timeout", "timed out"),
        ("stream_disconnect", "stream disconnected"),
        ("quota", "usage limit"),
        ("error", "error"),
    ):
        if needle in low and name not in stderr_kinds:
            stderr_kinds.append(name)
    print(f"CODEX_EXEC_RC={rc}")
    print(f"CODEX_EXEC_ELAPSED_SECONDS={elapsed}")
    print("CODEX_EXEC_EVENT_TYPES=" + (",".join(event_types) or "NONE"))
    print(f"CODEX_EXEC_TOOL_ITEM_COUNT={tool_items}")
    print("CODEX_EXEC_STDERR_KINDS=" + (",".join(stderr_kinds) or "NONE"))
    return rc, event_types, tool_items


def verify_final_effect() -> None:
    effects = read_effects()
    print(f"FINAL_LINE_COUNT={len(effects)}")
    print(f"FINAL_OFFICIAL_EFFECT_COUNT={effects.count('OFFICIAL_EFFECT_ONCE')}")
    print(f"FINAL_UWA_EFFECT_COUNT={effects.count('UWA_CONTINUATION_ONCE')}")
    if effects != EXPECTED_FINAL:
        raise GateError("final_effect_state_not_exact")
    checker = WORKSPACE / "check_handoff.py"
    if not checker.is_file():
        raise GateError("handoff_checker_missing")
    result = run([sys.executable, checker.name], cwd=WORKSPACE, timeout=30)
    print(f"HANDOFF_CHECKER_RC={result.returncode}")
    print("HANDOFF_CHECKER_PASS=" + ("YES" if result.returncode == 0 else "NO"))
    if result.returncode != 0:
        raise GateError("handoff_checker_failed")


def load_new_trace_summaries(before: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    requests: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    if not TRACE_DIR.is_dir():
        return requests, responses
    for path in sorted(TRACE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime):
        if path.name in before:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        summary = data.get("summary")
        if not isinstance(summary, dict):
            continue
        if path.name.endswith("-request.json"):
            requests.append(summary)
        elif path.name.endswith("-response.json"):
            responses.append(summary)
    return requests, responses


def verify_trace(before: set[str]) -> None:
    requests, responses = load_new_trace_summaries(before)
    req_kinds = [str(item.get("request_kind") or "") for item in requests]
    resp_kinds = [str(item.get("request_kind") or "") for item in responses]
    agent_requests = [item for item in requests if item.get("request_kind") == "agent_turn"]
    helper_requests = [item for item in requests if item.get("request_kind") == "metadata_helper"]
    agent_responses = [item for item in responses if item.get("request_kind") == "agent_turn"]
    exec_calls = sum(
        1
        for item in agent_responses
        if "exec_command" in (item.get("function_call_names") or [])
    )
    completed_agent = sum(
        1 for item in agent_responses if str(item.get("response_status") or "") == "completed"
    )
    correct_req_route = any(
        str(item.get("model") or "") == "chatgpt"
        and str(item.get("reasoning_effort") or "") == "high"
        for item in agent_requests
    )
    print(f"NEW_TRACE_REQUEST_COUNT={len(requests)}")
    print(f"NEW_TRACE_RESPONSE_COUNT={len(responses)}")
    print("NEW_TRACE_REQUEST_KINDS=" + (",".join(req_kinds) or "NONE"))
    print("NEW_TRACE_RESPONSE_KINDS=" + (",".join(resp_kinds) or "NONE"))
    print(f"AGENT_TRACE_REQUEST_COUNT={len(agent_requests)}")
    print(f"METADATA_HELPER_TRACE_REQUEST_COUNT={len(helper_requests)}")
    print(f"AGENT_EXEC_COMMAND_RESPONSE_COUNT={exec_calls}")
    print(f"AGENT_COMPLETED_RESPONSE_COUNT={completed_agent}")
    print("AGENT_REQUEST_ROUTE_CHATGPT_HIGH=" + ("YES" if correct_req_route else "NO"))
    if not agent_requests:
        raise GateError("no_agent_trace_request")
    if exec_calls < 1:
        raise GateError("no_real_exec_command_trace")
    if completed_agent < 1:
        raise GateError("no_completed_agent_response")
    if not correct_req_route:
        raise GateError("agent_request_route_not_chatgpt_high")


def verify_route_audit() -> None:
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
        timeout=45,
    )
    safe: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {
            "LATEST_SESSION_PROVIDER",
            "LATEST_SESSION_MODEL",
            "LATEST_SESSION_EFFORT",
            "UWA_WIRE_REQUEST_COUNT",
            "UWA_WIRE_RESPONSE_COUNT",
            "UWA_WIRE_LATEST_MODEL",
            "UWA_WIRE_LATEST_EFFORT",
            "UWA_WIRE_LATEST_STATUS",
            "ROUTE_EXPECTATION_PASS",
            "ROUTE_EXPECTATION_FAILURES",
        }:
            safe[key] = value
    print(f"ROUTE_AUDIT_RC={result.returncode}")
    for key in sorted(safe):
        print(f"{key}={safe[key]}")
    if result.returncode != 0 or safe.get("ROUTE_EXPECTATION_PASS") != "YES":
        raise GateError("route_audit_failed")


def main() -> int:
    print("H3_FINAL_HANDOFF_BEGIN")
    try:
        git_clean_branch()
        provider, model, effort = configured_route()
        print("CONFIGURED_PROVIDER=" + (provider or "UNKNOWN"))
        print("CONFIGURED_MODEL=" + (model or "UNKNOWN"))
        print("CONFIGURED_EFFORT=" + (effort or "UNKNOWN"))
        if (provider, model, effort) != ("uwa", "chatgpt", "high"):
            raise GateError("uwa_route_not_configured")

        before_health = health()
        print("HEALTH_BEFORE_SERVICE=" + str(before_health.get("service") or before_health.get("status") or "UNKNOWN"))
        print(f"HEALTH_BEFORE_RUNNING_COUNT={running_count(before_health)}")
        print("HEALTH_BEFORE_BROWSER_CONNECTED=" + str(browser_connected(before_health)))
        if not before_health or running_count(before_health) != 0 or browser_connected(before_health) is not True:
            raise GateError("uwa_health_precondition_failed")

        verify_workspace_source()
        route_mark = run([sys.executable, "tools/codex_route_audit.py", "mark"], cwd=REPO, timeout=45)
        print(f"ROUTE_MARK_RC={route_mark.returncode}")
        if route_mark.returncode != 0:
            raise GateError("route_marker_failed")

        before_traces = trace_snapshot()
        rc, events, _ = run_fresh_uwa_agent()
        if rc != 0:
            raise GateError("codex_exec_failed")
        if "turn.completed" not in events:
            raise GateError("codex_turn_not_completed")

        verify_final_effect()
        verify_trace(before_traces)
        verify_route_audit()

        after_health = health()
        print(f"HEALTH_AFTER_RUNNING_COUNT={running_count(after_health)}")
        print("HEALTH_AFTER_BROWSER_CONNECTED=" + str(browser_connected(after_health)))
        if running_count(after_health) != 0 or browser_connected(after_health) is not True:
            raise GateError("uwa_health_not_clean_after")

        print("H3_OFFICIAL_EFFECT_EXACTLY_ONCE=YES")
        print("H3_UWA_CONTINUATION_EXACTLY_ONCE=YES")
        print("H3_REAL_CLIENT_TOOL_CALL=YES")
        print("H3_METADATA_HELPER_EXCLUDED_FROM_AGENT_ACCOUNTING=YES")
        print("H3_AGENT_ROUTE_UWA_CHATGPT_HIGH=YES")
        print("H3_FINAL_HANDOFF=PASS_LIVE")
        return 0
    except GateError as exc:
        print("H3_FINAL_HANDOFF=FAIL")
        print(f"FAILURE_CLASS={exc}")
        return 1
    except subprocess.TimeoutExpired:
        print("H3_FINAL_HANDOFF=FAIL")
        print("FAILURE_CLASS=local_subprocess_timeout")
        return 1
    except Exception as exc:
        print("H3_FINAL_HANDOFF=FAIL")
        print("FAILURE_CLASS=unexpected_" + type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
