#!/usr/bin/env python3
"""Run the M4 real-project long-task pilot through UWA and push only after validation."""

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
CODE_REL = "app/api/codex_responses_v2.py"
TEST_REL = "tests/test_codex_v2_stream_cancellation.py"
CODE = REPO / CODE_REL
TEST = REPO / TEST_REL
TRACE_DIR = Path.home() / ".uwa" / "debug" / "codex-wire"
CONFIG = Path.home() / ".codex" / "config.toml"
HEALTH_URL = "http://127.0.0.1:8199/health"
TIMEOUT_SECONDS = int(os.getenv("UWA_M4_TIMEOUT", "720"))
EXPECTED_PATHS = {CODE_REL, TEST_REL}


class GateError(RuntimeError):
    pass


def run(cmd: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def git_lines(*args: str) -> list[str]:
    result = run(["git", *args], timeout=45)
    if result.returncode != 0:
        raise GateError("git_query_failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def current_head() -> str:
    result = run(["git", "rev-parse", "HEAD"], timeout=30)
    if result.returncode != 0:
        raise GateError("head_unavailable")
    return result.stdout.strip()


def ignored_untracked() -> set[str]:
    return set(git_lines("ls-files", "--others", "--ignored", "--exclude-standard"))


def standard_untracked() -> set[str]:
    return set(git_lines("ls-files", "--others", "--exclude-standard"))


def require_preconditions() -> tuple[str, set[str]]:
    branch = run(["git", "branch", "--show-current"], timeout=30)
    print("PROJECT_BRANCH=" + branch.stdout.strip())
    if branch.returncode != 0 or branch.stdout.strip() != BRANCH:
        raise GateError("wrong_branch")

    status = git_lines("status", "--porcelain", "--untracked-files=all")
    print(f"PROJECT_WORKTREE_DIRTY_COUNT={len(status)}")
    if status:
        raise GateError("project_worktree_dirty")

    if TEST.exists():
        tracked = run(["git", "ls-files", "--error-unmatch", TEST_REL], timeout=20)
        if tracked.returncode != 0:
            raise GateError("stale_untracked_m4_test_file")

    head = current_head()
    ignored = ignored_untracked()
    print("BASE_HEAD_PRESENT=YES")
    return head, ignored


def configured_route() -> tuple[str, str, str]:
    if not CONFIG.exists():
        return "", "", ""
    data = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    return (
        str(data.get("model_provider") or "").strip(),
        str(data.get("model") or "").strip(),
        str(data.get("model_reasoning_effort") or "").strip(),
    )


def health() -> dict[str, Any]:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=2.0) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return {}
    return payload if isinstance(payload, dict) else {}


def running_count(payload: dict[str, Any]) -> int:
    manager = payload.get("request_manager")
    if isinstance(manager, dict) and isinstance(manager.get("running_count"), int):
        return manager["running_count"]
    stats = payload.get("stats")
    if isinstance(stats, dict) and isinstance(stats.get("running_requests"), int):
        return stats["running_requests"]
    return -1


def browser_connected(payload: dict[str, Any]) -> bool | None:
    browser = payload.get("browser")
    if isinstance(browser, dict) and isinstance(browser.get("connected"), bool):
        return browser["connected"]
    value = payload.get("browser_connected")
    return value if isinstance(value, bool) else None


def trace_snapshot() -> set[str]:
    if not TRACE_DIR.is_dir():
        return set()
    return {path.name for path in TRACE_DIR.glob("*.json") if path.is_file()}


def task_prompt() -> str:
    return (
        "M4 real-project pilot. You must use the local exec_command tool first. "
        "Work in the current universal-web-api repository and inspect git status plus "
        "app/api/codex_responses_v2.py, especially _stream_codex_v2_attempt and its backing "
        "asyncio task around _run_chat_completion_final. Implement the narrow runtime hardening "
        "needed so premature cancellation or closure of the outer async/ASGI stream cannot leave "
        "that backing task alive. If the backing task is pending during cleanup, cancel it and "
        "await its termination. Preserve caller cancellation semantics: do not swallow an incoming "
        "asyncio.CancelledError. Do not change normal completion event ordering, web affinity, "
        "required-tool behavior, metadata-helper behavior, or unrelated code. "
        "Create exactly tests/test_codex_v2_stream_cancellation.py using Python stdlib unittest. "
        "The regression coverage must exercise cancellation of an in-flight consumer and premature "
        "generator close after the backing task has started, and must also protect normal completion "
        "from spurious cancellation. Make the test file directly executable with python3. "
        "Run the new test file, py_compile for both changed files, and git diff --check. "
        "Only modify app/api/codex_responses_v2.py and tests/test_codex_v2_stream_cancellation.py. "
        "Do not stage, commit, push, reset, checkout, restore, or modify any other file. "
        "Finish only after the focused checks pass."
    )


def safe_event_summary(stdout: str) -> tuple[list[str], int]:
    event_types: list[str] = []
    tool_items = 0
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
            inner = item.get("item")
            if isinstance(inner, dict):
                kind = str(inner.get("type") or "").lower()
                if "command" in kind or "tool" in kind or "function" in kind or "file" in kind:
                    tool_items += 1
    return event_types, tool_items


def run_codex() -> tuple[int, list[str], int]:
    started = time.time()
    cmd = ["codex", "exec", "--json", "--skip-git-repo-check", task_prompt()]
    try:
        result = run(cmd, timeout=TIMEOUT_SECONDS)
        rc = result.returncode
        stdout = result.stdout or ""
        stderr = result.stderr or ""
    except subprocess.TimeoutExpired as exc:
        rc = 124
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    event_types, tool_items = safe_event_summary(stdout)
    stderr_kinds: list[str] = []
    low = stderr.lower()
    for name, needle in (
        ("stream_disconnect", "stream disconnected"),
        ("timeout", "timed out"),
        ("quota", "usage limit"),
        ("error", "error"),
    ):
        if needle in low and name not in stderr_kinds:
            stderr_kinds.append(name)
    print(f"CODEX_EXEC_RC={rc}")
    print(f"CODEX_EXEC_ELAPSED_SECONDS={int(time.time() - started)}")
    print("CODEX_EXEC_EVENT_TYPES=" + (",".join(event_types) or "NONE"))
    print(f"CODEX_EXEC_TOOL_ITEM_COUNT={tool_items}")
    print("CODEX_EXEC_STDERR_KINDS=" + (",".join(stderr_kinds) or "NONE"))
    return rc, event_types, tool_items


def verify_codex_changes(base_head: str, ignored_before: set[str]) -> None:
    if current_head() != base_head:
        raise GateError("codex_changed_git_head")

    staged = set(git_lines("diff", "--cached", "--name-only"))
    print(f"CODEX_STAGED_PATH_COUNT={len(staged)}")
    if staged:
        raise GateError("codex_staged_changes")

    tracked_changed = set(git_lines("diff", "--name-only"))
    untracked = standard_untracked()
    ignored_after = ignored_untracked()
    ignored_delta = ignored_after - ignored_before

    print("TRACKED_CHANGED_PATHS=" + (",".join(sorted(tracked_changed)) or "NONE"))
    print("NEW_UNTRACKED_PATHS=" + (",".join(sorted(untracked)) or "NONE"))
    print("NEW_IGNORED_PATHS=" + (",".join(sorted(ignored_delta)) or "NONE"))

    if tracked_changed != {CODE_REL}:
        raise GateError("unexpected_tracked_change_set")
    if untracked - {TEST_REL}:
        raise GateError("unexpected_untracked_files")
    if ignored_delta - {TEST_REL}:
        raise GateError("unexpected_ignored_files")
    if not TEST.is_file():
        raise GateError("m4_regression_test_missing")

    actual = set(tracked_changed)
    if TEST_REL in untracked or TEST_REL in ignored_after:
        actual.add(TEST_REL)
    if actual != EXPECTED_PATHS:
        raise GateError("m4_expected_change_set_incomplete")

    code_diff = run(["git", "diff", "--", CODE_REL], timeout=45)
    if code_diff.returncode != 0:
        raise GateError("code_diff_unavailable")
    low = code_diff.stdout.lower()
    if ".cancel()" not in low or "await" not in low or "finally" not in low:
        raise GateError("cancellation_cleanup_shape_not_detected")

    test_text = TEST.read_text(encoding="utf-8", errors="replace")
    required_test_markers = ("unittest", "CancelledError", "aclose", "__main__")
    if not all(marker in test_text for marker in required_test_markers):
        raise GateError("regression_test_shape_incomplete")
    print("M4_IMPLEMENTATION_SHAPE=PASS")
    print("M4_REGRESSION_TEST_SHAPE=PASS")


def local_validation() -> None:
    compile_result = run([sys.executable, "-m", "py_compile", CODE_REL, TEST_REL], timeout=60)
    print(f"PY_COMPILE_RC={compile_result.returncode}")
    if compile_result.returncode != 0:
        raise GateError("py_compile_failed")

    test_result = run([sys.executable, TEST_REL], timeout=120)
    print(f"FOCUSED_UNITTEST_RC={test_result.returncode}")
    if test_result.returncode != 0:
        raise GateError("focused_unittest_failed")

    diff_check = run(["git", "diff", "--check", "--", CODE_REL], timeout=45)
    print(f"TRACKED_GIT_DIFF_CHECK_RC={diff_check.returncode}")
    if diff_check.returncode != 0:
        raise GateError("tracked_diff_check_failed")


def load_new_trace_summaries(before: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    requests: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    if not TRACE_DIR.is_dir():
        return requests, responses
    for path in sorted(TRACE_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime):
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


def verify_live_route(before: set[str]) -> None:
    requests, responses = load_new_trace_summaries(before)
    agent_requests = [item for item in requests if item.get("request_kind") == "agent_turn"]
    helper_requests = [item for item in requests if item.get("request_kind") == "metadata_helper"]
    agent_responses = [item for item in responses if item.get("request_kind") == "agent_turn"]
    exec_calls = sum(
        1 for item in agent_responses if "exec_command" in (item.get("function_call_names") or [])
    )
    completed = sum(
        1 for item in agent_responses if str(item.get("response_status") or "") == "completed"
    )
    correct_route = any(
        str(item.get("model") or "") == "chatgpt"
        and str(item.get("reasoning_effort") or "") == "high"
        for item in agent_requests
    )
    print(f"AGENT_TRACE_REQUEST_COUNT={len(agent_requests)}")
    print(f"METADATA_HELPER_TRACE_REQUEST_COUNT={len(helper_requests)}")
    print(f"AGENT_EXEC_COMMAND_RESPONSE_COUNT={exec_calls}")
    print(f"AGENT_COMPLETED_RESPONSE_COUNT={completed}")
    print("AGENT_REQUEST_ROUTE_CHATGPT_HIGH=" + ("YES" if correct_route else "NO"))
    if not agent_requests or exec_calls < 1 or completed < 1 or not correct_route:
        raise GateError("live_agent_route_or_tool_evidence_failed")

    audit = run(
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
    safe: dict[str, str] = {}
    for line in audit.stdout.splitlines():
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
    print(f"ROUTE_AUDIT_RC={audit.returncode}")
    for key in sorted(safe):
        print(f"{key}={safe[key]}")
    if audit.returncode != 0 or safe.get("ROUTE_EXPECTATION_PASS") != "YES":
        raise GateError("route_audit_failed")


def stage_commit_push() -> str:
    add_code = run(["git", "add", CODE_REL], timeout=45)
    add_test = run(["git", "add", "-f", TEST_REL], timeout=45)
    print(f"GIT_ADD_CODE_RC={add_code.returncode}")
    print(f"GIT_ADD_TEST_RC={add_test.returncode}")
    if add_code.returncode != 0 or add_test.returncode != 0:
        raise GateError("git_add_failed")

    staged = set(git_lines("diff", "--cached", "--name-only"))
    print("STAGED_PATHS=" + (",".join(sorted(staged)) or "NONE"))
    if staged != EXPECTED_PATHS:
        raise GateError("unexpected_staged_paths")

    check = run(["git", "diff", "--cached", "--check"], timeout=45)
    print(f"STAGED_DIFF_CHECK_RC={check.returncode}")
    if check.returncode != 0:
        raise GateError("staged_diff_check_failed")

    commit = run(["git", "commit", "-m", "Harden Codex V2 stream cancellation cleanup"], timeout=90)
    print(f"GIT_COMMIT_RC={commit.returncode}")
    if commit.returncode != 0:
        raise GateError("git_commit_failed")

    push = run(["git", "push", "origin", BRANCH], timeout=120)
    print(f"GIT_PUSH_RC={push.returncode}")
    if push.returncode != 0:
        raise GateError("git_push_failed")

    head = current_head()
    status = git_lines("status", "--porcelain", "--untracked-files=all")
    print(f"POST_PUSH_WORKTREE_DIRTY_COUNT={len(status)}")
    if status:
        raise GateError("post_push_worktree_dirty")
    print("PUSHED_HEAD=" + head)
    return head


def main() -> int:
    print("M4_REAL_PROJECT_LONG_TASK_PILOT_BEGIN")
    try:
        base_head, ignored_before = require_preconditions()

        provider, model, effort = configured_route()
        print("CONFIGURED_PROVIDER=" + (provider or "UNKNOWN"))
        print("CONFIGURED_MODEL=" + (model or "UNKNOWN"))
        print("CONFIGURED_EFFORT=" + (effort or "UNKNOWN"))
        if (provider, model, effort) != ("uwa", "chatgpt", "high"):
            raise GateError("uwa_chatgpt_high_not_configured")

        before_health = health()
        print(f"HEALTH_BEFORE_RUNNING_COUNT={running_count(before_health)}")
        print("HEALTH_BEFORE_BROWSER_CONNECTED=" + str(browser_connected(before_health)))
        if not before_health or running_count(before_health) != 0 or browser_connected(before_health) is not True:
            raise GateError("uwa_health_precondition_failed")

        mark = run([sys.executable, "tools/codex_route_audit.py", "mark"], timeout=60)
        print(f"ROUTE_MARK_RC={mark.returncode}")
        if mark.returncode != 0:
            raise GateError("route_marker_failed")

        traces_before = trace_snapshot()
        rc, event_types, tool_items = run_codex()
        if rc != 0:
            raise GateError("codex_exec_failed")
        if "turn.completed" not in event_types:
            raise GateError("codex_turn_not_completed")
        if tool_items < 2:
            raise GateError("insufficient_real_tool_activity")

        verify_codex_changes(base_head, ignored_before)
        local_validation()
        verify_live_route(traces_before)

        after_health = health()
        print(f"HEALTH_AFTER_RUNNING_COUNT={running_count(after_health)}")
        print("HEALTH_AFTER_BROWSER_CONNECTED=" + str(browser_connected(after_health)))
        if running_count(after_health) != 0 or browser_connected(after_health) is not True:
            raise GateError("uwa_health_postcondition_failed")

        stage_commit_push()

        print("M4_REAL_LOCAL_TOOL_ACTIVITY=YES")
        print("M4_NONTRIVIAL_CODE_CHANGE=YES")
        print("M4_REGRESSION_COVERAGE=PASS")
        print("M4_ROUTE_UWA_CHATGPT_HIGH=YES")
        print("M4_REQUEST_MANAGER_CLEAN_AFTER=YES")
        print("M4_REAL_PROJECT_LONG_TASK_PILOT=PASS_LIVE_CLOSED")
        return 0
    except GateError as exc:
        print("M4_REAL_PROJECT_LONG_TASK_PILOT=FAIL")
        print("FAILURE_CLASS=" + str(exc))
        return 2
    except subprocess.TimeoutExpired:
        print("M4_REAL_PROJECT_LONG_TASK_PILOT=FAIL")
        print("FAILURE_CLASS=local_validation_timeout")
        return 3
    except Exception as exc:
        print("M4_REAL_PROJECT_LONG_TASK_PILOT=FAIL")
        print("FAILURE_CLASS=unexpected_" + type(exc).__name__)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
