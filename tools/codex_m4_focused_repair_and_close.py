#!/usr/bin/env python3
"""Repair the focused M4 cancellation regression and close the bounded pilot.

This wrapper builds on the safe timeout-recovery runner. It replaces the two
remaining unstable assumptions discovered by the focused diagnostic:

* clear the Codex workflow reuse hint before awaiting backing-task cancellation,
  so cancellation-sensitive awaits cannot leave the hint stuck true;
* make the async-generator tests deterministic by using a long heartbeat window
  for consumer-cancellation and accepting either transport keepalive form for
  the explicit aclose path.

The underlying recovery flow still owns preconditions, UWA readiness, local
validation, one bounded read-only Codex/UWA review, route/health verification,
and commit/push of only the implementation and regression-test paths.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SAFE_PATH = REPO / "tools" / "codex_m4_resume_safe.py"


def _load_safe():
    spec = importlib.util.spec_from_file_location("codex_m4_resume_safe_for_focused_close", SAFE_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit("M4_FOCUSED_CLOSE_IMPORT_FAIL")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


safe = _load_safe()
module = safe.module


def final_normalize_implementation() -> None:
    base = module.tracked_base_text()
    old = (
        "    finally:\n"
        "        set_codex_workflow_reuse_hint(False)\n"
    )
    new = (
        "    finally:\n"
        "        set_codex_workflow_reuse_hint(False)\n"
        "        if not task.done():\n"
        "            task.cancel()\n"
        "            try:\n"
        "                await task\n"
        "            except asyncio.CancelledError:\n"
        "                pass\n"
    )
    count = base.count(old)
    print(f"M4_FINAL_PATCH_TARGET_COUNT={count}")
    if count != 1:
        raise module.GateError("m4_final_patch_target_not_unique")
    module.CODE.write_text(base.replace(old, new, 1), encoding="utf-8")
    print("M4_FINAL_IMPLEMENTATION_WRITTEN=YES")


def final_regression_test_text() -> str:
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
    def stream_patches(self, worker, reuse_calls, *, heartbeat_sec: float):
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
        stack.enter_context(patch.object(mod, "_CODEX_SSE_KEEPALIVE_SEC", heartbeat_sec))
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

    async def test_consumer_cancellation_cleans_backing_task_and_propagates(self):
        started = asyncio.Event()
        cancelled = asyncio.Event()
        reuse_calls = []

        async def worker(**kwargs):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        with self.stream_patches(worker, reuse_calls, heartbeat_sec=10.0):
            stream = mod._stream_codex_v2_attempt(**self.make_stream())
            created = await stream.__anext__()
            self.assertIn("response.created", created)
            pending = asyncio.create_task(stream.__anext__())
            await asyncio.wait_for(started.wait(), 1.0)
            pending.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await pending
            await asyncio.wait_for(cancelled.wait(), 1.0)
            self.assertTrue(cancelled.is_set())
            self.assertEqual(reuse_calls[-1], False)

    async def test_aclose_cleans_backing_task_after_progress_event(self):
        started = asyncio.Event()
        cancelled = asyncio.Event()
        reuse_calls = []

        async def worker(**kwargs):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        with self.stream_patches(worker, reuse_calls, heartbeat_sec=0.01):
            stream = mod._stream_codex_v2_attempt(**self.make_stream())
            created = await stream.__anext__()
            self.assertIn("response.created", created)
            progress = await stream.__anext__()
            self.assertTrue(
                "keepalive" in progress or "response.in_progress" in progress,
                progress,
            )
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

        with self.stream_patches(worker, reuse_calls, heartbeat_sec=10.0):
            stream = mod._stream_codex_v2_attempt(**self.make_stream())
            events = [event async for event in stream]
            self.assertTrue(completed.is_set())
            self.assertFalse(cancelled.is_set())
            self.assertTrue(any("response.completed" in event for event in events))
            self.assertEqual(reuse_calls[-1], False)


if __name__ == "__main__":
    unittest.main()
'''


def final_local_validation() -> None:
    safe.VALIDATION_PYTHON = safe.select_validation_python()

    compile_result = module.run(
        [safe.VALIDATION_PYTHON, "-m", "py_compile", module.CODE_REL, module.TEST_REL],
        timeout=60,
    )
    print(f"PY_COMPILE_RC={compile_result.returncode}")
    if compile_result.returncode != 0:
        print("PY_COMPILE_ERROR_TAIL=" + " | ".join((compile_result.stderr or "").splitlines()[-8:])[:1200])
        raise module.GateError("py_compile_failed")

    test_result = module.run([safe.VALIDATION_PYTHON, module.TEST_REL, "-v"], timeout=120)
    print(f"FOCUSED_UNITTEST_RC={test_result.returncode}")
    combined = (test_result.stdout or "") + "\n" + (test_result.stderr or "")
    summary = [line.strip() for line in combined.splitlines() if line.strip().startswith("test_")]
    print("FOCUSED_UNITTEST_CASES=" + (" | ".join(summary[-6:])[:1600] if summary else "NONE"))
    if test_result.returncode != 0:
        tail = " | ".join(combined.splitlines()[-40:])
        print("FOCUSED_UNITTEST_ERROR_DETAIL=" + tail[:4000])
        raise module.GateError("focused_unittest_failed_after_repair")

    diff_check = module.run(["git", "diff", "--check"], timeout=45)
    print(f"GIT_DIFF_CHECK_RC={diff_check.returncode}")
    if diff_check.returncode != 0:
        raise module.GateError("git_diff_check_failed")

    tracked = set(module.git_lines("diff", "--name-only"))
    untracked = module.standard_untracked()
    ignored = module.ignored_untracked()
    actual = set(tracked)
    if module.TEST_REL in untracked or module.TEST_REL in ignored:
        actual.add(module.TEST_REL)
    print("VALIDATED_CHANGED_PATHS=" + ",".join(sorted(actual)))
    if actual != module.EXPECTED_PATHS:
        raise module.GateError("unexpected_validated_change_set")


module.normalize_implementation = final_normalize_implementation
module.regression_test_text = final_regression_test_text
module.local_validation = final_local_validation


if __name__ == "__main__":
    raise SystemExit(module.main())
