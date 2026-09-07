#!/usr/bin/env python3
"""Switch Codex between UWA override and normal ChatGPT-account mode.

The ``official`` action is intentionally operator-light on macOS:

1. quit ChatGPT Desktop / Codex if running;
2. stop the UWA process actually listening on TCP 8199, but only when its cwd
   matches this repository;
3. restore the pre-UWA Codex Memories settings;
4. remove only top-level provider/model/reasoning pins from config.toml;
5. reopen ChatGPT Desktop automatically.

Authentication is never modified. The ``[model_providers.uwa]`` definition is
kept so switching back to UWA remains cheap. A timestamped config backup is
written before provider/model pins are changed.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

try:
    from tools.codex_uwa_memory_guard import restore as restore_memories
except ModuleNotFoundError:  # direct execution: python3 tools/codex_provider_switch.py
    from codex_uwa_memory_guard import restore as restore_memories

ROOT_KEYS = {"model_provider", "model", "model_reasoning_effort"}
REPO_ROOT = Path(__file__).resolve().parents[1]
UWA_PORT = 8199
DESKTOP_APPS = ("ChatGPT", "Codex")

Runner = Callable[..., subprocess.CompletedProcess[str]]
Sleeper = Callable[[float], None]


def default_config_path() -> Path:
    return Path.home() / ".codex" / "config.toml"


def _split_root_and_sections(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.lstrip().startswith("["):
            return lines[:index], lines[index:]
    return lines, []


def _key_name(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return ""
    return stripped.split("=", 1)[0].strip()


def official_text(text: str) -> str:
    root, sections = _split_root_and_sections(text)
    cleaned = [line for line in root if _key_name(line) not in ROOT_KEYS]
    return "".join(cleaned + sections)


def write_official(config_path: Path) -> tuple[Path | None, bool]:
    if not config_path.exists():
        return None, False

    original = config_path.read_text(encoding="utf-8")
    updated = official_text(original)
    if updated == original:
        return None, False

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = config_path.with_name(f"{config_path.name}.before-official-{timestamp}")
    shutil.copy2(config_path, backup)
    config_path.write_text(updated, encoding="utf-8")
    return backup, True


def top_level_status(text: str) -> dict[str, str]:
    root, _ = _split_root_and_sections(text)
    result: dict[str, str] = {}
    for line in root:
        key = _key_name(line)
        if key in ROOT_KEYS:
            result[key] = line.split("=", 1)[1].strip()
    return result


def _run(
    args: Sequence[str],
    *,
    runner: Runner = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    return runner(
        list(args),
        capture_output=True,
        text=True,
        check=False,
    )


def _process_running(app_name: str, *, runner: Runner = subprocess.run) -> bool:
    return _run(["pgrep", "-x", app_name], runner=runner).returncode == 0


def quit_desktop_apps(
    *,
    runner: Runner = subprocess.run,
    sleeper: Sleeper = time.sleep,
    timeout_sec: float = 10.0,
) -> list[str]:
    """Gracefully quit known Codex-capable desktop apps, then enforce shutdown."""

    if platform.system() != "Darwin":
        return []

    stopped: list[str] = []
    for app_name in DESKTOP_APPS:
        if not _process_running(app_name, runner=runner):
            continue

        _run(
            ["osascript", "-e", f'tell application "{app_name}" to quit'],
            runner=runner,
        )

        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            if not _process_running(app_name, runner=runner):
                break
            sleeper(0.25)

        if _process_running(app_name, runner=runner):
            _run(["pkill", "-TERM", "-x", app_name], runner=runner)
            sleeper(0.5)

        if _process_running(app_name, runner=runner):
            _run(["pkill", "-KILL", "-x", app_name], runner=runner)
            sleeper(0.25)

        if _process_running(app_name, runner=runner):
            raise RuntimeError(f"failed to stop desktop application: {app_name}")
        stopped.append(app_name)

    return stopped


def _listener_pids(*, runner: Runner = subprocess.run) -> list[int]:
    result = _run(
        ["lsof", "-nP", f"-tiTCP:{UWA_PORT}", "-sTCP:LISTEN"],
        runner=runner,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"failed to inspect TCP {UWA_PORT} listener")
    pids: list[int] = []
    for line in result.stdout.splitlines():
        try:
            pids.append(int(line.strip()))
        except ValueError:
            continue
    return pids


def _listener_cwd(pid: int, *, runner: Runner = subprocess.run) -> Path | None:
    result = _run(
        ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
        runner=runner,
    )
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("n") and len(line) > 1:
            return Path(line[1:]).expanduser()
    return None


def stop_uwa_listener(
    *,
    repo_root: Path = REPO_ROOT,
    runner: Runner = subprocess.run,
    sleeper: Sleeper = time.sleep,
    timeout_sec: float = 10.0,
) -> list[int]:
    """Stop only UWA listeners whose cwd proves they belong to this checkout."""

    repo_root = repo_root.resolve()
    pids = _listener_pids(runner=runner)
    if not pids:
        return []

    for pid in pids:
        cwd = _listener_cwd(pid, runner=runner)
        if cwd is None or cwd.resolve() != repo_root:
            raise RuntimeError(
                f"refusing to stop TCP {UWA_PORT} listener {pid}: "
                f"cwd={cwd!s} expected={repo_root}"
            )

    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if not _listener_pids(runner=runner):
            return pids
        sleeper(0.25)

    for pid in _listener_pids(runner=runner):
        cwd = _listener_cwd(pid, runner=runner)
        if cwd is None or cwd.resolve() != repo_root:
            raise RuntimeError(
                f"refusing SIGKILL for TCP {UWA_PORT} listener {pid}: "
                f"cwd={cwd!s} expected={repo_root}"
            )
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    sleeper(0.25)
    remaining = _listener_pids(runner=runner)
    if remaining:
        raise RuntimeError(f"TCP {UWA_PORT} listener still alive: {remaining}")
    return pids


def open_desktop_app(*, runner: Runner = subprocess.run) -> str:
    """Open ChatGPT Desktop, falling back to a standalone Codex app if present."""

    if platform.system() != "Darwin":
        return "SKIPPED_NON_MACOS"

    errors: list[str] = []
    for app_name in DESKTOP_APPS:
        result = _run(["open", "-a", app_name], runner=runner)
        if result.returncode == 0:
            return app_name
        detail = (result.stderr or result.stdout or "not found").strip()
        errors.append(f"{app_name}: {detail}")
    raise RuntimeError("unable to open ChatGPT/Codex Desktop; " + "; ".join(errors))


def switch_to_official(
    config_path: Path,
    *,
    automate_desktop: bool = True,
    automate_uwa_stop: bool = True,
    quit_fn: Callable[[], list[str]] | None = None,
    stop_fn: Callable[[], list[int]] | None = None,
    restore_fn: Callable[[Path], None] | None = None,
    open_fn: Callable[[], str] | None = None,
) -> tuple[Path | None, bool, list[str], list[int], str]:
    """Perform the full official-account mode switch with minimal operator work."""

    quit_fn = quit_fn or quit_desktop_apps
    stop_fn = stop_fn or stop_uwa_listener
    restore_fn = restore_fn or restore_memories
    open_fn = open_fn or open_desktop_app

    stopped_apps: list[str] = []
    stopped_pids: list[int] = []

    if automate_desktop:
        stopped_apps = quit_fn()
    if automate_uwa_stop:
        stopped_pids = stop_fn()

    restore_fn(config_path)
    backup, changed = write_official(config_path)

    reopened = "SKIPPED"
    if automate_desktop:
        reopened = open_fn()

    return backup, changed, stopped_apps, stopped_pids, reopened


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["official", "status"])
    parser.add_argument("--config", type=Path, default=default_config_path())
    parser.add_argument(
        "--no-desktop-restart",
        action="store_true",
        help="do not automatically quit/reopen ChatGPT Desktop",
    )
    parser.add_argument(
        "--no-stop-uwa",
        action="store_true",
        help="do not automatically stop the verified TCP 8199 UWA listener",
    )
    args = parser.parse_args()

    path: Path = args.config.expanduser()

    if args.action == "status":
        if not path.exists():
            print(f"CONFIG={path}")
            print("STATUS=missing")
            return 0
        status = top_level_status(path.read_text(encoding="utf-8"))
        print(f"CONFIG={path}")
        for key in sorted(ROOT_KEYS):
            print(f"{key}={status.get(key, '<default>')}")
        return 0

    try:
        backup, changed, stopped_apps, stopped_pids, reopened = switch_to_official(
            path,
            automate_desktop=not args.no_desktop_restart,
            automate_uwa_stop=not args.no_stop_uwa,
        )
    except Exception as exc:
        print(f"OFFICIAL_MODE_SWITCH=FAIL")
        print(f"ERROR={exc}")
        return 1

    print(f"CONFIG={path}")
    print(f"OFFICIAL_MODE_CHANGED={'YES' if changed else 'NO'}")
    if backup is not None:
        print(f"BACKUP={backup}")
    print(f"UWA_LISTENER_STOPPED={','.join(map(str, stopped_pids)) if stopped_pids else 'NONE'}")
    print(f"DESKTOP_APPS_STOPPED={','.join(stopped_apps) if stopped_apps else 'NONE'}")
    print(f"DESKTOP_REOPENED={reopened}")
    print("AUTH=UNCHANGED")
    print("MODEL_SELECTION=ACCOUNT_DEFAULT_UI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
