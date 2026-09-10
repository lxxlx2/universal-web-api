#!/usr/bin/env python3
"""Repair and verify the H3 required-client-tool path in one local run.

This helper is intentionally narrow. It patches only the English required-tool
phrasing detector, adds focused regression coverage, restarts the managed UWA
service to clear any prior stuck browser request, reruns the metadata-only H3
agent-turn probe with a bounded timeout, and commits/pushes the proven detector
repair without asking the operator to perform Git bookkeeping manually.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple


REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "app" / "api" / "codex_responses_v2.py"
TEST_FILE = REPO / "tests" / "test_codex_required_tool_phrasing.py"
BRANCH = "codex-web-bridge-v2"
PROBE_TIMEOUT = os.getenv("UWA_H3_AGENT_PROBE_TIMEOUT", "150")


def run(cmd: List[str], *, timeout: int = 120, env: Dict[str, str] | None = None) -> Tuple[int, str, str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=merged,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return 124, out, err


def require_clean_branch() -> None:
    rc, branch, err = run(["git", "branch", "--show-current"], timeout=20)
    if rc != 0:
        raise SystemExit(f"BRANCH_CHECK_FAILED={type(err).__name__}")
    branch = branch.strip()
    print(f"BRANCH={branch}")
    if branch != BRANCH:
        raise SystemExit("PRECONDITION_FAIL=wrong_branch")

    rc, status, _ = run(["git", "status", "--porcelain"], timeout=20)
    dirty = [line for line in status.splitlines() if line.strip()]
    print(f"WORKTREE_DIRTY_COUNT={len(dirty)}")
    if rc != 0 or dirty:
        raise SystemExit("PRECONDITION_FAIL=dirty_worktree")


def patch_required_tool_detector() -> bool:
    raw = TARGET.read_bytes()
    marker = b'r"\\b(?:must|required\\s+to|have\\s+to)\\s+(?:use|call|invoke)\\s+`?"'
    pos = raw.find(marker)
    if pos < 0:
        if b"client-side|declared" in raw and b"(?:first\\s+)?(?:use|call|invoke)" in raw:
            print("DETECTOR_PATCH_ALREADY_PRESENT=YES")
            return False
        raise SystemExit("PATCH_TARGET_NOT_FOUND")

    line_end = raw.find(b"\n", pos)
    if line_end < 0:
        raise SystemExit("PATCH_LINE_END_NOT_FOUND")
    newline = b"\r\n" if line_end > 0 and raw[line_end - 1:line_end + 1] == b"\r\n" else b"\n"

    old_lines = [
        b"    re.compile(",
        b'        r"\\b(?:must|required\\s+to|have\\s+to)\\s+(?:use|call|invoke)\\s+`?"',
        b'        r"(exec_command|shell_command|local_shell|apply_patch|write_stdin)`?\\b",',
        b"        re.IGNORECASE,",
        b"    ),",
    ]
    new_lines = [
        b"    re.compile(",
        b'        r"\\b(?:must|required\\s+to|have\\s+to)\\s+(?:use|call|invoke)\\s+"',
        b'        r"(?:(?:the|a|an)\\s+)?(?:(?:local|client|client-side|declared)\\s+){0,3}`?"',
        b'        r"(exec_command|shell_command|local_shell|apply_patch|write_stdin)`?\\b",',
        b"        re.IGNORECASE,",
        b"    ),",
        b"    re.compile(",
        b'        r"(?:^|[\\n.!?]\\s+)(?:first\\s+)?(?:use|call|invoke)\\s+"',
        b'        r"(?:(?:the|a|an)\\s+)?(?:(?:local|client|client-side|declared)\\s+){0,3}`?"',
        b'        r"(exec_command|shell_command|local_shell|apply_patch|write_stdin)`?\\b",',
        b"        re.IGNORECASE,",
        b"    ),",
    ]
    old = newline.join(old_lines) + newline
    new = newline.join(new_lines) + newline
    count = raw.count(old)
    print(f"DETECTOR_PATCH_TARGET_COUNT={count}")
    if count != 1:
        raise SystemExit("PATCH_TARGET_COUNT_NOT_ONE")
    TARGET.write_bytes(raw.replace(old, new, 1))
    print("DETECTOR_PATCH_APPLIED=YES")
    return True


def write_regression_test() -> bool:
    content = '''from types import SimpleNamespace\n\nfrom app.api.codex_responses_v2 import required_declared_tool\n\n\nTOOLS = [\n    {\n        "type": "function",\n        "name": "exec_command",\n        "description": "Execute a local command in the client sandbox.",\n        "parameters": {"type": "object", "properties": {}},\n    }\n]\n\n\ndef _body(text: str):\n    return SimpleNamespace(\n        tools=TOOLS,\n        tool_choice="auto",\n        input=[{"role": "user", "content": text}],\n    )\n\n\ndef test_required_tool_accepts_real_h3_qualified_phrase():\n    assert (\n        required_declared_tool(\n            _body("You must use the local exec_command tool. Run exactly pwd.")\n        )\n        == "exec_command"\n    )\n\n\ndef test_required_tool_accepts_imperative_client_phrase():\n    assert (\n        required_declared_tool(\n            _body("First use the local client exec_command tool to inspect the workspace.")\n        )\n        == "exec_command"\n    )\n\n\ndef test_required_tool_accepts_direct_imperative_phrase():\n    assert required_declared_tool(_body("Call exec_command now.")) == "exec_command"\n\n\ndef test_required_tool_does_not_promote_explanatory_optional_phrase():\n    assert (\n        required_declared_tool(\n            _body("The documentation says you can use the local exec_command tool if available.")\n        )\n        == ""\n    )\n'''
    if TEST_FILE.exists() and TEST_FILE.read_text(encoding="utf-8", errors="replace") == content:
        print("REGRESSION_TEST_ALREADY_PRESENT=YES")
        return False
    TEST_FILE.write_text(content, encoding="utf-8", newline="\n")
    print("REGRESSION_TEST_WRITTEN=YES")
    return True


def static_checks() -> None:
    rc, _, err = run([sys.executable, "-m", "py_compile", str(TARGET), str(TEST_FILE)], timeout=30)
    print(f"PY_COMPILE_RC={rc}")
    if rc != 0:
        print(err[-2000:])
        raise SystemExit("STATIC_CHECK_FAIL=py_compile")

    rc, out, err = run(["git", "diff", "--check"], timeout=30)
    print(f"GIT_DIFF_CHECK_RC={rc}")
    if rc != 0:
        print((out + err)[-2000:])
        raise SystemExit("STATIC_CHECK_FAIL=git_diff_check")

    rc, _, _ = run([sys.executable, "-m", "pytest", "--version"], timeout=30)
    if rc == 0:
        rc, out, err = run(
            [sys.executable, "-m", "pytest", str(TEST_FILE.relative_to(REPO)), "-q"],
            timeout=120,
        )
        print(f"FOCUSED_PYTEST_RC={rc}")
        if rc != 0:
            print((out + err)[-3000:])
            raise SystemExit("STATIC_CHECK_FAIL=focused_pytest")
    else:
        print("FOCUSED_PYTEST=SKIPPED_PYTEST_UNAVAILABLE")


def restart_uwa() -> None:
    rc, _, _ = run(["codex-uwa-stop"], timeout=45)
    print(f"UWA_STOP_RC={rc}")
    time.sleep(2)
    rc, out, err = run(["codex-uwa"], timeout=90)
    print(f"UWA_START_RC={rc}")
    if rc != 0:
        print((out + err)[-2500:])
        raise SystemExit("UWA_RESTART_FAIL=start")
    time.sleep(5)


def run_live_probe() -> Tuple[int, str]:
    rc, out, err = run(
        [sys.executable, "tools/codex_h3_agent_turn_probe.py"],
        timeout=int(PROBE_TIMEOUT) + 45,
        env={"UWA_H3_AGENT_PROBE_TIMEOUT": PROBE_TIMEOUT},
    )
    print("===== H3 LIVE PROBE =====")
    print(out.rstrip())
    if err.strip():
        safe_kinds = []
        low = err.lower()
        if "stream disconnected" in low:
            safe_kinds.append("stream_disconnected")
        if "timeout" in low:
            safe_kinds.append("timeout")
        print("H3_LIVE_PROBE_STDERR_KINDS=" + ",".join(safe_kinds))
    print(f"H3_LIVE_PROBE_RC={rc}")
    return rc, out


def commit_and_push() -> None:
    rc, status, _ = run(["git", "status", "--porcelain"], timeout=20)
    changed = [line for line in status.splitlines() if line.strip()]
    print(f"PATCH_CHANGED_FILES={len(changed)}")
    if rc != 0 or not changed:
        print("PATCH_COMMIT=NO_CHANGES")
        return

    rc, _, err = run(
        ["git", "add", "app/api/codex_responses_v2.py", "tests/test_codex_required_tool_phrasing.py"],
        timeout=30,
    )
    if rc != 0:
        print(err[-1000:])
        raise SystemExit("GIT_FAIL=add")

    rc, out, err = run(
        ["git", "commit", "-m", "Recognize qualified Codex client-tool requirements"],
        timeout=60,
    )
    print(f"GIT_COMMIT_RC={rc}")
    if rc != 0:
        print((out + err)[-2000:])
        raise SystemExit("GIT_FAIL=commit")

    rc, out, err = run(["git", "push", "origin", BRANCH], timeout=120)
    print(f"GIT_PUSH_RC={rc}")
    if rc != 0:
        print((out + err)[-2500:])
        raise SystemExit("GIT_FAIL=push")

    rc, head, _ = run(["git", "rev-parse", "HEAD"], timeout=20)
    if rc == 0:
        print("PUSHED_HEAD=" + head.strip())


def main() -> int:
    print("H3_REPAIR_AND_VERIFY_BEGIN")
    require_clean_branch()
    patch_required_tool_detector()
    write_regression_test()
    static_checks()
    restart_uwa()
    probe_rc, probe_out = run_live_probe()
    commit_and_push()

    if "H3_AGENT_TURN_PROBE=PASS" in probe_out and probe_rc == 0:
        print("H3_REQUIRED_TOOL_REPAIR=PASS_LIVE")
        return 0

    print("H3_REQUIRED_TOOL_REPAIR=PATCHED_BUT_LIVE_BLOCKER_REMAINS")
    if "FAILURE_CLASS=" in probe_out:
        for line in probe_out.splitlines():
            if line.startswith("FAILURE_CLASS="):
                print("NEXT_FAILURE_CLASS=" + line.split("=", 1)[1])
                break
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
