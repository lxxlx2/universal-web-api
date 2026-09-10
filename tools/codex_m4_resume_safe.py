#!/usr/bin/env python3
"""Run M4 timeout recovery while ignoring unrelated pre-existing ignored files.

The base recovery runner intentionally limits tracked/untracked M4 changes, but its
first version treated every pre-existing non-transient ignored file in the checkout
as an M4 mutation.  That makes a valid local checkout fail before recovery starts.
This wrapper keeps the strict tracked/untracked scope checks and treats unrelated
ignored files as baseline-local state.  The deterministic recovery runner still
writes only the fixed M4 implementation/test paths and validates/stages only those
paths.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools" / "codex_m4_resume_after_timeout.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("codex_m4_resume_after_timeout", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit("M4_RESUME_SAFE_IMPORT_FAIL")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


module.require_resume_state = safe_require_resume_state


if __name__ == "__main__":
    raise SystemExit(module.main())
