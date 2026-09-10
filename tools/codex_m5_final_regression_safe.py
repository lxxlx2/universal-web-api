#!/usr/bin/env python3
"""Run M5 with a private pytest bootstrap when the runtime Python lacks pytest.

Production requirements intentionally do not include pytest. The M5 validator
must therefore select a Python that can import the running project first, then
add pytest only under private ~/.uwa state when needed. Repository files are not
modified by this bootstrap.
"""

from __future__ import annotations

import importlib.util
import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "tools" / "codex_m5_final_regression.py"
PRIVATE_ROOT = Path.home() / ".uwa" / "m5-validation-deps"


def _load_base():
    spec = importlib.util.spec_from_file_location("codex_m5_final_regression_base", BASE)
    if spec is None or spec.loader is None:
        raise SystemExit("M5_SAFE_IMPORT_FAIL")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


base = _load_base()


def _run(cmd: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def _runtime_ready(candidate: Path) -> bool:
    probe = (
        "import fastapi; "
        "import app.api.codex_responses_v2; "
        "import app.services.codex_remote_compaction_v2"
    )
    return _run([str(candidate), "-c", probe], timeout=45).returncode == 0


def _pytest_ready(executable: str) -> bool:
    probe = (
        "import fastapi, pytest; "
        "import app.api.codex_responses_v2; "
        "import app.services.codex_remote_compaction_v2"
    )
    return _run([executable, "-c", probe], timeout=45).returncode == 0


def _python_tag(candidate: Path) -> str:
    result = _run(
        [str(candidate), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
        timeout=20,
    )
    if result.returncode != 0:
        raise base.GateError("validation_python_version_probe_failed")
    value = result.stdout.strip()
    if not value or any(ch not in "0123456789." for ch in value):
        raise base.GateError("validation_python_version_invalid")
    return value


def _write_launcher(candidate: Path, target: Path) -> Path:
    launcher = target / "validation-python"
    payload = (
        "#!/bin/sh\n"
        "export PYTHONPATH="
        + shlex.quote(str(target))
        + "${PYTHONPATH:+:$PYTHONPATH}\n"
        + "exec "
        + shlex.quote(str(candidate))
        + " \"$@\"\n"
    )
    launcher.write_text(payload, encoding="utf-8")
    launcher.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    return launcher


def _private_pytest_python(candidate: Path) -> str:
    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        PRIVATE_ROOT.chmod(0o700)
    except OSError:
        pass

    tag = _python_tag(candidate)
    target = PRIVATE_ROOT / ("py" + tag)
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    launcher = _write_launcher(candidate, target)

    if _pytest_ready(str(launcher)):
        print("M5_PRIVATE_PYTEST_BOOTSTRAP=CACHED")
        return str(launcher)

    pip_probe = _run([str(candidate), "-m", "pip", "--version"], timeout=30)
    print("M5_VALIDATION_PIP_READY=" + ("YES" if pip_probe.returncode == 0 else "NO"))
    if pip_probe.returncode != 0:
        raise base.GateError("validation_python_pip_missing")

    install = _run(
        [
            str(candidate),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--target",
            str(target),
            "pytest>=8,<10",
        ],
        timeout=240,
    )
    print(f"M5_PRIVATE_PYTEST_INSTALL_RC={install.returncode}")
    if install.returncode != 0:
        raise base.GateError("private_pytest_install_failed")

    if not _pytest_ready(str(launcher)):
        raise base.GateError("private_pytest_import_failed")

    print("M5_PRIVATE_PYTEST_BOOTSTRAP=PASS")
    return str(launcher)


def select_validation_python() -> str:
    tested = 0
    runtime_candidate: Path | None = None

    for candidate in base.candidate_pythons():
        tested += 1
        if not _runtime_ready(candidate):
            continue
        runtime_candidate = candidate
        if _pytest_ready(str(candidate)):
            print(f"VALIDATION_PYTHON_CANDIDATES_TESTED={tested}")
            print("VALIDATION_RUNTIME_READY=YES")
            print("VALIDATION_PYTEST_SOURCE=EXISTING")
            print("VALIDATION_PYTHON_READY=YES")
            return str(candidate)
        break

    print(f"VALIDATION_PYTHON_CANDIDATES_TESTED={tested}")
    if runtime_candidate is None:
        print("VALIDATION_RUNTIME_READY=NO")
        print("VALIDATION_PYTHON_READY=NO")
        raise base.GateError("no_repo_runtime_python")

    print("VALIDATION_RUNTIME_READY=YES")
    print("VALIDATION_PYTEST_SOURCE=PRIVATE_BOOTSTRAP")
    executable = _private_pytest_python(runtime_candidate)
    print("VALIDATION_PYTHON_READY=YES")
    return executable


base.select_validation_python = select_validation_python


if __name__ == "__main__":
    raise SystemExit(base.main())
