#!/usr/bin/env python3
"""Safely resume M4 after the bounded long-task timeout.

This wrapper fixes two environment-sensitive recovery issues without broadening
M4's mutation scope:

* unrelated pre-existing ignored files are baseline-local state, not M4 changes;
* validation uses a Python interpreter that can actually import the repository's
  FastAPI/Codex modules, selected locally before the bounded review turn.

The underlying deterministic runner still rebuilds the implementation from HEAD,
writes only the fixed regression-test path, validates, runs a bounded read-only
Codex/UWA review, verifies route/cleanup evidence, and commits/pushes only the two
expected M4 paths after all gates pass.
"""

from __future__ import annotations

import importlib.util
import shlex
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools" / "codex_m4_resume_after_timeout.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("codex_m4_resume_after_timeout", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit("M4_RESUME_SAFE_IMPORT_FAIL")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


module = _load_module()


def safe_require_resume_state() -> None:
    branch = module.run(["git", "branch", "--show-current"], timeout=30)
    print("PROJECT_BRANCH=" + branch.stdout.strip())
    if branch.returncode != 0 or branch.stdout.strip() != module.BRANCH:
        raise module.GateError("wrong_branch")

    staged = set(module.git_lines("diff", "--cached", "--name-only"))
    print(f"STAGED_PATH_COUNT_BEFORE={len(staged)}")
    if staged:
        raise module.GateError("unexpected_staged_state")

    tracked = set(module.git_lines("diff", "--name-only"))
    untracked = {p for p in module.standard_untracked() if not module.transient(p)}
    ignored = {p for p in module.ignored_untracked() if not module.transient(p)}

    print("TRACKED_CHANGED_BEFORE=" + (",".join(sorted(tracked)) or "NONE"))
    print("UNTRACKED_BEFORE=" + (",".join(sorted(untracked)) or "NONE"))
    print(f"IGNORED_BASELINE_NONTRANSIENT_COUNT={len(ignored - {module.TEST_REL})}")
    print("M4_TEST_IGNORED_BEFORE=" + ("YES" if module.TEST_REL in ignored else "NO"))

    if tracked - {module.CODE_REL}:
        raise module.GateError("unexpected_tracked_resume_paths")
    if untracked - {module.TEST_REL}:
        raise module.GateError("unexpected_untracked_resume_paths")

    print("IGNORED_BASELINE_POLICY=ALLOW_UNRELATED_PREEXISTING")


def _candidate_pythons() -> list[Path]:
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
        key = str(path.expanduser())
        if key in seen:
            continue
        seen.add(key)
        if path.exists() and path.is_file():
            out.append(path)
    return out


def select_validation_python() -> str:
    probe = "import fastapi; import app.api.codex_responses_v2"
    tested = 0
    for candidate in _candidate_pythons():
        tested += 1
        result = subprocess.run(
            [str(candidate), "-c", probe],
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            print(f"VALIDATION_PYTHON_CANDIDATES_TESTED={tested}")
            print("VALIDATION_PYTHON_READY=YES")
            return str(candidate)
    print(f"VALIDATION_PYTHON_CANDIDATES_TESTED={tested}")
    print("VALIDATION_PYTHON_READY=NO")
    raise module.GateError("no_repo_capable_python_interpreter")


VALIDATION_PYTHON = ""


def safe_local_validation() -> None:
    global VALIDATION_PYTHON
    VALIDATION_PYTHON = select_validation_python()

    compile_result = module.run(
        [VALIDATION_PYTHON, "-m", "py_compile", module.CODE_REL, module.TEST_REL],
        timeout=60,
    )
    print(f"PY_COMPILE_RC={compile_result.returncode}")
    if compile_result.returncode != 0:
        raise module.GateError("py_compile_failed")

    test_result = module.run([VALIDATION_PYTHON, module.TEST_REL], timeout=120)
    print(f"FOCUSED_UNITTEST_RC={test_result.returncode}")
    if test_result.returncode != 0:
        tail = " | ".join((test_result.stderr or "").splitlines()[-3:])
        print("FOCUSED_UNITTEST_ERROR_TAIL=" + tail[:500])
        raise module.GateError("focused_unittest_failed")

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


def safe_review_prompt() -> str:
    python_cmd = shlex.quote(VALIDATION_PYTHON or select_validation_python())
    command = (
        f"{python_cmd} {shlex.quote(module.TEST_REL)} && "
        f"{python_cmd} -m py_compile {shlex.quote(module.CODE_REL)} {shlex.quote(module.TEST_REL)} && "
        "git diff --check"
    )
    return (
        "M4 recovery validation only. You must use the local exec_command tool exactly once. "
        "Do not edit any file. Do not search for Python interpreters or virtual environments. "
        "Do not install anything and do not call any other tool. Run exactly this command in the "
        f"current repository: {command}. "
        "After the tool result, reply exactly M4_RECOVERY_REVIEW_OK."
    )


module.require_resume_state = safe_require_resume_state
module.local_validation = safe_local_validation
module.review_prompt = safe_review_prompt


if __name__ == "__main__":
    raise SystemExit(module.main())
