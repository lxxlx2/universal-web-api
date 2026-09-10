#!/usr/bin/env python3
"""Diagnose the focused M4 cancellation regression without mutating the checkout.

This helper is intentionally read-only. It selects a repository-capable Python,
runs the generated stdlib regression test verbosely, prints sanitized failure
names/traceback details, and shows only the tracked M4 implementation diff hunk.
It never stages, commits, restores, resets, edits, or pushes local files.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BRANCH = "codex-web-bridge-v2"
CODE_REL = "app/api/codex_responses_v2.py"
TEST_REL = "tests/test_codex_v2_stream_cancellation.py"
HOME = str(Path.home())


def run(cmd: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def sanitize(text: str) -> str:
    value = str(text or "").replace(HOME, "~")
    value = re.sub(r"thread[_ -]?id[=: ]+[A-Za-z0-9-]+", "thread_id=<redacted>", value, flags=re.I)
    return value


def candidate_pythons() -> list[Path]:
    raw = [
        Path(sys.executable),
        REPO / ".venv" / "bin" / "python",
        REPO / "venv" / "bin" / "python",
        REPO / "env" / "bin" / "python",
        Path("/opt/homebrew/bin/python3"),
        Path("/usr/local/bin/python3"),
        Path("/usr/bin/python3"),
    ]
    out: list[Path] = []
    seen: set[str] = set()
    for path in raw:
        expanded = path.expanduser()
        key = str(expanded)
        if key in seen:
            continue
        seen.add(key)
        if expanded.exists() and expanded.is_file():
            out.append(expanded)
    return out


def select_python() -> str:
    probe = "import fastapi; import app.api.codex_responses_v2"
    tested = 0
    for candidate in candidate_pythons():
        tested += 1
        result = run([str(candidate), "-c", probe], timeout=30)
        if result.returncode == 0:
            print(f"VALIDATION_PYTHON_CANDIDATES_TESTED={tested}")
            print("VALIDATION_PYTHON_READY=YES")
            return str(candidate)
    print(f"VALIDATION_PYTHON_CANDIDATES_TESTED={tested}")
    print("VALIDATION_PYTHON_READY=NO")
    raise SystemExit(3)


def print_failure_details(output: str) -> None:
    lines = output.splitlines()
    names: list[str] = []
    for line in lines:
        match = re.match(r"^(test_[^ ]+).*\.\.\.\s+(FAIL|ERROR)$", line.strip())
        if match:
            names.append(f"{match.group(1)}:{match.group(2)}")
    print("FAILED_TESTS=" + (",".join(names) if names else "UNKNOWN"))

    interesting: list[str] = []
    in_block = False
    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith("=" * 20):
            in_block = True
        if in_block:
            interesting.append(stripped)
        elif re.match(r"^(FAIL|ERROR): ", stripped):
            interesting.append(stripped)
        if len(interesting) >= 160:
            break

    print("DETAIL_BEGIN")
    if interesting:
        for line in interesting:
            print(sanitize(line))
    else:
        for line in lines[-80:]:
            print(sanitize(line))
    print("DETAIL_END")


def main() -> int:
    print("M4_FOCUSED_UNITTEST_DIAG_BEGIN")

    branch = run(["git", "branch", "--show-current"], timeout=30)
    current_branch = branch.stdout.strip()
    print("PROJECT_BRANCH=" + current_branch)
    if branch.returncode != 0 or current_branch != BRANCH:
        print("M4_FOCUSED_UNITTEST_DIAG=FAIL")
        print("FAILURE_CLASS=wrong_branch")
        return 2

    code_changed = run(["git", "diff", "--quiet", "--", CODE_REL], timeout=30).returncode == 1
    test_exists = (REPO / TEST_REL).is_file()
    print("M4_CODE_DIRTY=" + ("YES" if code_changed else "NO"))
    print("M4_TEST_PRESENT=" + ("YES" if test_exists else "NO"))
    if not code_changed or not test_exists:
        print("M4_FOCUSED_UNITTEST_DIAG=FAIL")
        print("FAILURE_CLASS=expected_resume_artifacts_missing")
        return 2

    python = select_python()

    compile_result = run([python, "-m", "py_compile", CODE_REL, TEST_REL], timeout=60)
    print(f"PY_COMPILE_RC={compile_result.returncode}")
    if compile_result.returncode != 0:
        print("COMPILE_DETAIL_BEGIN")
        print(sanitize((compile_result.stderr or compile_result.stdout)[-4000:]))
        print("COMPILE_DETAIL_END")
        print("M4_FOCUSED_UNITTEST_DIAG=FAIL")
        print("FAILURE_CLASS=py_compile_failed")
        return 2

    result = run([python, TEST_REL, "-v"], timeout=120)
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    print(f"FOCUSED_UNITTEST_RC={result.returncode}")
    print_failure_details(combined)

    diff = run(["git", "diff", "--unified=12", "--", CODE_REL], timeout=45)
    print("IMPLEMENTATION_DIFF_BEGIN")
    diff_lines = sanitize(diff.stdout).splitlines()
    for line in diff_lines[:160]:
        print(line)
    print("IMPLEMENTATION_DIFF_END")

    print("M4_FOCUSED_UNITTEST_DIAG=" + ("PASS" if result.returncode == 0 else "FAIL"))
    if result.returncode != 0:
        print("FAILURE_CLASS=focused_unittest_failed_detailed")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
