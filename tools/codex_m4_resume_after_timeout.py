#!/usr/bin/env python3
"""Recover the M4 real-project pilot after the first long Codex turn timed out.

The first M4 turn already performed substantial real client-tool work and left only
app/api/codex_responses_v2.py modified. This runner preserves the live evidence,
normalizes the intended cancellation cleanup from the tracked base, writes a
stdlib regression test that does not depend on pytest, validates locally, runs one
bounded read-only Codex review turn through UWA, verifies route/cleanup metadata,
and commits/pushes only the two expected implementation/test paths.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import threading
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
REVIEW_TIMEOUT = int(os.getenv("UWA_M4_RECOVERY_TIMEOUT", "300"))
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


def standard_untracked() -> set[str]:
    return set(git_lines("ls-files", "--others", "--exclude-standard"))


def ignored_untracked() -> set[str]:
    return set(git_lines("ls-files", "--others", "--ignored", "--exclude-standard"))


def transient(path: str) -> bool:
    normalized = str(path or "").replace("\\", "/")
    return (
        "/__pycache__/" in f"/{normalized}"
        or normalized.endswith(".pyc")
        or normalized.startswith(".pytest_cache/")
        or "/.pytest_cache/" in f"/{normalized}"
    )


def require_resume_state() -> None:
    branch = run(["git", "branch", "--show-current"], timeout=30)
    print("PROJECT_BRANCH=" + branch.stdout.strip())
    if branch.returncode != 0 or branch.stdout.strip() != BRANCH:
        raise GateError("wrong_branch")

    staged = set(git_lines("diff", "--cached", "--name-only"))
    print(f"STAGED_PATH_COUNT_BEFORE={len(staged)}")
    if staged:
        raise GateError("unexpected_staged_state")

    tracked = set(git_lines("diff", "--name-only"))
    untracked = {p for p in standard_untracked() if not transient(p)}
    ignored = {p for p in ignored_untracked() if not transient(p)}
    print("TRACKED_CHANGED_BEFORE=" + (",".join(sorted(tracked)) or "NONE"))
    print("UNTRACKED_BEFORE=" + (",".join(sorted(untracked)) or "NONE"))

    if tracked - {CODE_REL}:
        raise GateError("unexpected_tracked_resume_paths")
    if untracked - {TEST_REL}:
        raise GateError("unexpected_untracked_resume_paths")
    if ignored - {TEST_REL}:
        raise GateError("unexpected_ignored_resume_paths")


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


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise GateError("helper_import_failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def ensure_uwa_ready() -> None:
    payload = health()
    running = running_count(payload)
    connected = browser_connected(payload)
    print(f"UWA_INITIAL_RUNNING_COUNT={running}")
    print(f"UWA_INITIAL_BROWSER_CONNECTED={connected}")
    if payload and running == 0 and connected is True:
        print("UWA_RECOVERY=NOT_NEEDED")
        return

    if connected is True and running > 0:
        raise GateError("uwa_has_active_work")

    lifecycle = load_module(
        "codex_uwa_lifecycle_for_m4_recovery",
        REPO / "tools" / "codex_uwa_lifecycle.py",
    )
    listeners = lifecycle.listener_pids()
    if listeners:
        lifecycle.require_owned_listeners(listeners, repo_root=REPO)
        print("UWA_RECOVERY_ACTION=restart")
        lifecycle.restart_uwa(repo_root=REPO)
    else:
        print("UWA_RECOVERY_ACTION=start")
        lifecycle.start_uwa(repo_root=REPO)

    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        payload = health()
        if payload and running_count(payload) == 0 and browser_connected(payload) is True:
            print("UWA_RECOVERY=PASS")
            return
        time.sleep(1.0)
    raise GateError("uwa_recovery_failed")


def tracked_base_text() -> str:
    result = run(["git", "show", f"HEAD:{CODE_REL}"], timeout=45)
    if result.returncode != 0:
        raise GateError("tracked_base_unavailable")
    return result.stdout


def normalize_implementation() -> None:
    base = tracked_base_text()
    old = (
        "    finally:\n"
        "        set_codex_workflow_reuse_hint(False)\n"
    )
    new = (
        "    finally:\n"
        "        if not task.done():\n"
        "            task.cancel()\n"
        "            try:\n"
        "                await task\n"
        "            except asyncio.CancelledError:\n"
        "                pass\n"
        "        set_codex_workflow_reuse_hint(False)\n"
    )
    count = base.count(old)
    print(f"CANONICAL_PATCH_TARGET_COUNT={count}")
    if count != 1:
        raise GateError("canonical_patch_target_not_unique")
    CODE.write_text(base.replace(old, new, 1), encoding="utf-8")
    print("CANONICAL_IMPLEMENTATION_WRITTEN=YES")


def regression_test_text() -> str:
    return r'''#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api import codex_responses_v2 as mod


class FakeRequest:
    async def is_disconnected(self) -> bool:
        return False


class StreamCancellationTests(unittest.IsolatedAsyncioTestCase):
    def stream_patches(self, worker, reuse_calls):
        stack = ExitStack()
        stack.enter_context(patch.object(mod, "_run_chat_completion_final", worker))
        stack.enter_context(
            patch.object(
                mod,
                "_responses_request_to_chat_request",
                lambda body, stream=False: SimpleNamespace(messages=[]),
            )
        )
        stack.enter_context(
            patch.object(
                mod,
                "_build_responses_object",
                lambda *args, **kwargs: {
                    "output": [],
                    "status": kwargs.get("status"),
                },
            )
        )
        stack.enter_context(
            patch.object(
                mod,
                "_codex_event",
                lambda event, **kwargs: f"event:{event}\n",
            )
        )
        stack.enter_context(
            patch.object(
                mod,
                "set_codex_workflow_reuse_hint",
                lambda value: reuse_calls.append(value),
            )
        )
        stack.enter_context(patch.object(mod, "_sanitize_codex_tool_payload", lambda payload: payload))
        stack.enter_context(
            patch.object(
                mod,
                "_sanitize_codex_root_workdirs",
                lambda payload, messages: payload,
            )
        )
        stack.enter_context(
            patch.object(
                mod,
                "_responses_completion_status_from_chat_payload",
                lambda payload: ("completed", None, "response.completed"),
            )
        )
        stack.enter_context(patch.object(mod, "_codex_wire_item", lambda item: item))
        stack.enter_context(patch.object(mod, "_store_responses_state", lambda *args, **kwargs: None))
        stack.enter_context(patch.object(mod, "_persist_codex_history", lambda *args, **kwargs: None))
        stack.enter_context(patch.object(mod, "current_chatgpt_conversation_path", lambda: ""))
        stack.enter_context(patch.object(mod, "bind_response_to_conversation", lambda *args, **kwargs: None))
        stack.enter_context(patch.object(mod, "target_web_model", lambda: "chatgpt"))
        stack.enter_context(patch.object(mod, "_CODEX_SSE_KEEPALIVE_SEC", 0.01))
        return stack

    def make_stream(self):
        body = SimpleNamespace(store=True)
        return dict(
            request=FakeRequest(),
            state_body=body,
            browser_source_body=body,
            reuse_web_conversation=False,
            reused_path="",
            reasoning="high",
            authenticated=True,
        )

    async def test_consumer_cancellation_cleans_backing_task(self):
        started = asyncio.Event()
        cancelled = asyncio.Event()
        reuse_calls = []

        async def worker(**kwargs):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        with self.stream_patches(worker, reuse_calls):
            stream = mod._stream_codex_v2_attempt(**self.make_stream())
            await stream.__anext__()
            pending = asyncio.create_task(stream.__anext__())
            await asyncio.wait_for(started.wait(), 1.0)
            pending.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await pending
            await asyncio.wait_for(cancelled.wait(), 1.0)
            self.assertTrue(cancelled.is_set())
            self.assertEqual(reuse_calls[-1], False)

    async def test_aclose_cleans_backing_task_after_keepalive(self):
        started = asyncio.Event()
        cancelled = asyncio.Event()
        reuse_calls = []

        async def worker(**kwargs):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        with self.stream_patches(worker, reuse_calls):
            stream = mod._stream_codex_v2_attempt(**self.make_stream())
            await stream.__anext__()
            keepalive = await stream.__anext__()
            self.assertIn("keepalive", keepalive)
            await asyncio.wait_for(started.wait(), 1.0)
            await stream.aclose()
            await asyncio.wait_for(cancelled.wait(), 1.0)
            self.assertTrue(cancelled.is_set())
            self.assertEqual(reuse_calls[-1], False)

    async def test_normal_completion_does_not_cancel_finished_worker(self):
        completed = asyncio.Event()
        cancelled = asyncio.Event()
        reuse_calls = []

        async def worker(**kwargs):
            try:
                completed.set()
                return 200, {"choices": [], "usage": {}}
            except asyncio.CancelledError:
                cancelled.set()
                raise

        with self.stream_patches(worker, reuse_calls):
            stream = mod._stream_codex_v2_attempt(**self.make_stream())
            events = [event async for event in stream]
            self.assertTrue(completed.is_set())
            self.assertFalse(cancelled.is_set())
            self.assertTrue(any("response.completed" in event for event in events))
            self.assertEqual(reuse_calls[-1], False)


if __name__ == "__main__":
    unittest.main()
'''


def write_regression_test() -> None:
    TEST.parent.mkdir(parents=True, exist_ok=True)
    TEST.write_text(regression_test_text(), encoding="utf-8")
    print("REGRESSION_TEST_WRITTEN=YES")


def local_validation() -> None:
    compile_result = run(
        [sys.executable, "-m", "py_compile", CODE_REL, TEST_REL],
        timeout=60,
    )
    print(f"PY_COMPILE_RC={compile_result.returncode}")
    if compile_result.returncode != 0:
        raise GateError("py_compile_failed")

    test_result = run([sys.executable, TEST_REL], timeout=120)
    print(f"FOCUSED_UNITTEST_RC={test_result.returncode}")
    if test_result.returncode != 0:
        tail = " | ".join((test_result.stderr or "").splitlines()[-3:])
        print("FOCUSED_UNITTEST_ERROR_TAIL=" + tail[:500])
        raise GateError("focused_unittest_failed")

    diff_check = run(["git", "diff", "--check"], timeout=45)
    print(f"GIT_DIFF_CHECK_RC={diff_check.returncode}")
    if diff_check.returncode != 0:
        raise GateError("git_diff_check_failed")

    tracked = set(git_lines("diff", "--name-only"))
    untracked = standard_untracked()
    ignored = ignored_untracked()
    actual = set(tracked)
    if TEST_REL in untracked or TEST_REL in ignored:
        actual.add(TEST_REL)
    print("VALIDATED_CHANGED_PATHS=" + ",".join(sorted(actual)))
    if actual != EXPECTED_PATHS:
        raise GateError("unexpected_validated_change_set")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace_snapshot() -> set[str]:
    if not TRACE_DIR.is_dir():
        return set()
    return {p.name for p in TRACE_DIR.glob("*.json") if p.is_file()}


def review_prompt() -> str:
    return (
        "M4 recovery validation only. You must use the local exec_command tool exactly once. "
        "Do not edit any file. Do not search for Python interpreters or virtual environments. "
        "Do not install anything and do not call any other tool. Run exactly this command in the "
        "current repository: python3 tests/test_codex_v2_stream_cancellation.py && python3 -m "
        "py_compile app/api/codex_responses_v2.py tests/test_codex_v2_stream_cancellation.py && "
        "git diff --check. After the tool result, reply exactly M4_RECOVERY_REVIEW_OK."
    )


def safe_event_summary(stdout: str) -> tuple[list[str], int, bool]:
    event_types: list[str] = []
    tool_items = 0
    marker = False
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
                if "command" in kind or "tool" in kind or "function" in kind:
                    tool_items += 1
        if "M4_RECOVERY_REVIEW_OK" in line:
            marker = True
    return event_types, tool_items, marker


def run_review() -> tuple[int, list[str], int, bool]:
    cmd = ["codex", "exec", "--json", "--skip-git-repo-check", review_prompt()]
    proc = subprocess.Popen(
        cmd,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []

    def drain(pipe, target):
        if pipe is None:
            return
        for line in pipe:
            target.append(line)

    out_thread = threading.Thread(target=drain, args=(proc.stdout, stdout_parts), daemon=True)
    err_thread = threading.Thread(target=drain, args=(proc.stderr, stderr_parts), daemon=True)
    out_thread.start()
    err_thread.start()

    started = time.monotonic()
    next_progress = 15
    while proc.poll() is None:
        elapsed = int(time.monotonic() - started)
        if elapsed >= next_progress:
            print(f"CODEX_RECOVERY_REVIEW_RUNNING_SECONDS={elapsed}", flush=True)
            next_progress += 15
        if elapsed >= REVIEW_TIMEOUT:
            try:
                os.killpg(proc.pid, 15)
            except OSError:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, 9)
                except OSError:
                    pass
                proc.wait(timeout=5)
            rc = 124
            break
        time.sleep(1.0)
    else:
        rc = int(proc.returncode or 0)

    if proc.poll() is not None and 'rc' not in locals():
        rc = int(proc.returncode or 0)

    out_thread.join(timeout=2)
    err_thread.join(timeout=2)
    stdout = "".join(stdout_parts)
    stderr = "".join(stderr_parts)
    events, tool_items, marker = safe_event_summary(stdout)
    low = stderr.lower()
    stderr_kinds: list[str] = []
    for name, needle in (
        ("stream_disconnect", "stream disconnected"),
        ("quota", "usage limit"),
        ("error", "error"),
    ):
        if needle in low and name not in stderr_kinds:
            stderr_kinds.append(name)
    print(f"CODEX_RECOVERY_REVIEW_RC={rc}")
    print("CODEX_RECOVERY_EVENT_TYPES=" + (",".join(events) or "NONE"))
    print(f"CODEX_RECOVERY_TOOL_ITEM_COUNT={tool_items}")
    print("CODEX_RECOVERY_MARKER=" + ("YES" if marker else "NO"))
    print("CODEX_RECOVERY_STDERR_KINDS=" + (",".join(stderr_kinds) or "NONE"))
    return rc, events, tool_items, marker


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


def verify_review_route(before: set[str]) -> None:
    requests, responses = load_new_trace_summaries(before)
    agent_requests = [x for x in requests if x.get("request_kind") == "agent_turn"]
    agent_responses = [x for x in responses if x.get("request_kind") == "agent_turn"]
    exec_calls = sum(
        1 for x in agent_responses if "exec_command" in (x.get("function_call_names") or [])
    )
    completed = sum(
        1 for x in agent_responses if str(x.get("response_status") or "") == "completed"
    )
    correct_route = any(
        str(x.get("model") or "") == "chatgpt"
        and str(x.get("reasoning_effort") or "") == "high"
        for x in agent_requests
    )
    print(f"RECOVERY_AGENT_TRACE_REQUEST_COUNT={len(agent_requests)}")
    print(f"RECOVERY_EXEC_COMMAND_RESPONSE_COUNT={exec_calls}")
    print(f"RECOVERY_COMPLETED_RESPONSE_COUNT={completed}")
    print("RECOVERY_ROUTE_CHATGPT_HIGH=" + ("YES" if correct_route else "NO"))
    if not agent_requests or exec_calls < 1 or completed < 1 or not correct_route:
        raise GateError("recovery_live_route_evidence_failed")

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
    print(f"ROUTE_AUDIT_RC={audit.returncode}")
    if audit.returncode != 0 or "ROUTE_EXPECTATION_PASS=YES" not in audit.stdout:
        raise GateError("route_audit_failed")
    print("ROUTE_EXPECTATION_PASS=YES")


def commit_push() -> None:
    add_code = run(["git", "add", CODE_REL], timeout=45)
    add_test = run(["git", "add", "-f", TEST_REL], timeout=45)
    print(f"GIT_ADD_CODE_RC={add_code.returncode}")
    print(f"GIT_ADD_TEST_RC={add_test.returncode}")
    if add_code.returncode != 0 or add_test.returncode != 0:
        raise GateError("git_add_failed")

    staged = set(git_lines("diff", "--cached", "--name-only"))
    print("STAGED_PATHS=" + ",".join(sorted(staged)))
    if staged != EXPECTED_PATHS:
        raise GateError("unexpected_staged_paths")

    check = run(["git", "diff", "--cached", "--check"], timeout=45)
    print(f"STAGED_DIFF_CHECK_RC={check.returncode}")
    if check.returncode != 0:
        raise GateError("staged_diff_check_failed")

    commit = run(
        ["git", "commit", "-m", "Harden Codex V2 stream cancellation cleanup"],
        timeout=90,
    )
    print(f"GIT_COMMIT_RC={commit.returncode}")
    if commit.returncode != 0:
        raise GateError("git_commit_failed")

    push = run(["git", "push", "origin", BRANCH], timeout=120)
    print(f"GIT_PUSH_RC={push.returncode}")
    if push.returncode != 0:
        raise GateError("git_push_failed")

    head = run(["git", "rev-parse", "HEAD"], timeout=30)
    print("PUSHED_HEAD=" + head.stdout.strip())
    status = git_lines("status", "--porcelain", "--untracked-files=all")
    print(f"POST_PUSH_WORKTREE_DIRTY_COUNT={len(status)}")
    if status:
        raise GateError("post_push_worktree_dirty")


def main() -> int:
    print("M4_TIMEOUT_RECOVERY_BEGIN")
    try:
        require_resume_state()
        provider, model, effort = configured_route()
        print("CONFIGURED_PROVIDER=" + (provider or "UNKNOWN"))
        print("CONFIGURED_MODEL=" + (model or "UNKNOWN"))
        print("CONFIGURED_EFFORT=" + (effort or "UNKNOWN"))
        if (provider, model, effort) != ("uwa", "chatgpt", "high"):
            raise GateError("uwa_chatgpt_high_not_configured")

        ensure_uwa_ready()
        normalize_implementation()
        write_regression_test()
        local_validation()

        before_code = file_hash(CODE)
        before_test = file_hash(TEST)
        mark = run([sys.executable, "tools/codex_route_audit.py", "mark"], timeout=60)
        print(f"ROUTE_MARK_RC={mark.returncode}")
        if mark.returncode != 0:
            raise GateError("route_marker_failed")
        traces_before = trace_snapshot()

        rc, events, tool_items, marker = run_review()
        if rc != 0:
            raise GateError("codex_recovery_review_failed")
        if "turn.completed" not in events:
            raise GateError("codex_recovery_turn_not_completed")
        if tool_items < 2:
            raise GateError("codex_recovery_exec_not_observed")
        if not marker:
            raise GateError("codex_recovery_marker_missing")
        if file_hash(CODE) != before_code or file_hash(TEST) != before_test:
            raise GateError("codex_recovery_modified_files")

        verify_review_route(traces_before)
        after = health()
        print(f"HEALTH_AFTER_RUNNING_COUNT={running_count(after)}")
        print(f"HEALTH_AFTER_BROWSER_CONNECTED={browser_connected(after)}")
        if running_count(after) != 0 or browser_connected(after) is not True:
            raise GateError("uwa_health_postcondition_failed")

        commit_push()
        print("M4_PRIOR_LONG_TASK_TOOL_ACTIVITY=YES")
        print("M4_CANONICAL_CANCELLATION_FIX=PASS")
        print("M4_STDLIB_REGRESSION=PASS")
        print("M4_BOUNDED_RECOVERY_REVIEW=PASS_LIVE")
        print("M4_ROUTE_UWA_CHATGPT_HIGH=YES")
        print("M4_REQUEST_MANAGER_CLEAN_AFTER=YES")
        print("M4_REAL_PROJECT_LONG_TASK_PILOT=PASS_LIVE_CLOSED")
        return 0
    except GateError as exc:
        print("M4_TIMEOUT_RECOVERY=FAIL")
        print("FAILURE_CLASS=" + str(exc))
        return 2
    except Exception as exc:
        print("M4_TIMEOUT_RECOVERY=FAIL")
        print("FAILURE_CLASS=unexpected_" + type(exc).__name__)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
