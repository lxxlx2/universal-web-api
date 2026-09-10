#!/usr/bin/env python3
"""One-shot M5 final regression for the Codex Web Bridge V2 release gate.

The runner is validation-only. It keeps private prompts, raw Codex JSONL, the
runtime continuity token and the raw thread id under ~/.uwa and never prints
those values. It does not edit, stage, commit, push, reset or switch providers.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import codex_route_audit as route_audit
import codex_uwa_lifecycle as lifecycle


BRANCH = "codex-web-bridge-v2"
M4_COMMIT = "38554bd9d2301783d1bc2d9aff8005c60c70f389"
REMOTE_COMPACTION_FIX_COMMIT = "e6f7578f67d2759b13992a259dff6c9bf9527632"
CONFIG = Path.home() / ".codex" / "config.toml"
ACCEPTANCE_ROOT = Path.home() / "uwa-codex-acceptance"
ACCEPTANCE_MARKER = ".uwa_codex_acceptance"
PRIVATE_PARENT = Path.home() / ".uwa" / "m5-final-regression"
SMOKE_MARKER = ".uwa_m5_restart_smoke"
RESULT_NAME = "result.txt"
SEED_REPLY = "M5_RESTART_SEED_READY"
FINAL_REPLY = "M5_RESTART_CONTINUITY_PASS"
CODEX_TIMEOUT = int(os.getenv("UWA_M5_CODEX_TIMEOUT", "360"))
PYTEST_TIMEOUT = int(os.getenv("UWA_M5_PYTEST_TIMEOUT", "900"))
HEALTH_URL = "http://127.0.0.1:8199/health"

REQUIRED_TESTS = {
    "tests/test_codex_auto_compact_trigger_probe.py",
    "tests/test_codex_continuation_identity_fencing.py",
    "tests/test_codex_lost_affinity_restart_fallback.py",
    "tests/test_codex_metadata_helper_isolation.py",
    "tests/test_codex_provider_switch.py",
    "tests/test_codex_remote_compaction_compat.py",
    "tests/test_codex_remote_compaction_recovery.py",
    "tests/test_codex_remote_compaction_recovery_staged.py",
    "tests/test_codex_remote_compaction_trigger_probe.py",
    "tests/test_codex_remote_compaction_v2.py",
    "tests/test_codex_remote_compaction_stream_cancellation.py",
    "tests/test_codex_responses_compact.py",
    "tests/test_codex_responses_state.py",
    "tests/test_codex_route_audit.py",
    "tests/test_codex_stream_compat.py",
    "tests/test_codex_uncertain_tool_effect_retry.py",
    "tests/test_codex_uwa_lifecycle.py",
    "tests/test_codex_v2_stream_cancellation.py",
    "tests/test_codex_web_session_affinity.py",
}


class GateError(RuntimeError):
    pass


@dataclass
class CodexObservation:
    returncode: int
    thread_ids: list[str]
    event_types: list[str]
    agent_messages: list[str]
    completed_commands: list[str]
    turn_completed: bool
    tool_item_count: int


@dataclass
class HealthSnapshot:
    service: str
    browser_connected: bool | None
    running_count: int


def run(
    cmd: list[str],
    *,
    cwd: Path = REPO,
    timeout: int = 120,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        input=input_text,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def git_lines(*args: str) -> list[str]:
    result = run(["git", *args], timeout=30)
    if result.returncode != 0:
        raise GateError("git_inspection_failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def require_clean_branch() -> None:
    branch = run(["git", "branch", "--show-current"], timeout=30)
    current = branch.stdout.strip()
    print("PROJECT_BRANCH=" + (current or "UNKNOWN"))
    if branch.returncode != 0 or current != BRANCH:
        raise GateError("wrong_branch")

    dirty = git_lines("status", "--porcelain", "--untracked-files=all")
    print(f"PROJECT_WORKTREE_DIRTY_COUNT={len(dirty)}")
    if dirty:
        raise GateError("project_worktree_dirty")


def require_ancestor(commit: str, label: str) -> None:
    result = run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], timeout=30)
    passed = result.returncode == 0
    print(f"{label}=" + ("YES" if passed else "NO"))
    if not passed:
        raise GateError(label.lower())


def configured_route() -> tuple[str, str, str]:
    if not CONFIG.is_file():
        return "", "", ""
    data = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    return (
        str(data.get("model_provider") or "").strip(),
        str(data.get("model") or "").strip(),
        str(data.get("model_reasoning_effort") or "").strip(),
    )


def require_uwa_route() -> None:
    provider, model, effort = configured_route()
    print("CONFIGURED_PROVIDER=" + (provider or "UNKNOWN"))
    print("CONFIGURED_MODEL=" + (model or "UNKNOWN"))
    print("CONFIGURED_EFFORT=" + (effort or "UNKNOWN"))
    if (provider, model, effort) != ("uwa", "chatgpt", "high"):
        raise GateError("route_not_uwa_chatgpt_high")


def _health_payload() -> dict[str, Any]:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=3.0) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _running_count(payload: dict[str, Any]) -> int:
    manager = payload.get("request_manager")
    if isinstance(manager, dict) and isinstance(manager.get("running_count"), int):
        return int(manager["running_count"])
    stats = payload.get("stats")
    if isinstance(stats, dict) and isinstance(stats.get("running_requests"), int):
        return int(stats["running_requests"])
    return -1


def _browser_connected(payload: dict[str, Any]) -> bool | None:
    browser = payload.get("browser")
    if isinstance(browser, dict) and isinstance(browser.get("connected"), bool):
        return bool(browser["connected"])
    value = payload.get("browser_connected")
    return value if isinstance(value, bool) else None


def health_snapshot() -> HealthSnapshot:
    payload = _health_payload()
    service = str(payload.get("service") or payload.get("status") or "").strip().lower()
    return HealthSnapshot(
        service=service,
        browser_connected=_browser_connected(payload),
        running_count=_running_count(payload),
    )


def wait_clean_health(timeout_sec: float = 20.0) -> HealthSnapshot:
    deadline = time.monotonic() + timeout_sec
    latest = HealthSnapshot("", None, -1)
    while time.monotonic() < deadline:
        latest = health_snapshot()
        if (
            latest.service == "healthy"
            and latest.browser_connected is True
            and latest.running_count == 0
        ):
            return latest
        time.sleep(0.5)
    return latest


def print_health(prefix: str, snapshot: HealthSnapshot) -> None:
    print(f"{prefix}_SERVICE=" + (snapshot.service or "UNKNOWN"))
    print(
        f"{prefix}_BROWSER_CONNECTED="
        + ("YES" if snapshot.browser_connected is True else "NO" if snapshot.browser_connected is False else "UNKNOWN")
    )
    print(f"{prefix}_RUNNING_COUNT={snapshot.running_count}")


def require_clean_health(prefix: str) -> None:
    snapshot = wait_clean_health()
    print_health(prefix, snapshot)
    if not (
        snapshot.service == "healthy"
        and snapshot.browser_connected is True
        and snapshot.running_count == 0
    ):
        raise GateError(prefix.lower() + "_health_failed")


def restart_uwa(label: str) -> None:
    started = time.monotonic()
    try:
        lifecycle.restart_uwa(repo_root=REPO)
        rc = 0
    except Exception:
        rc = 1
    elapsed = int(time.monotonic() - started)
    print(f"{label}_RC={rc}")
    print(f"{label}_ELAPSED_SECONDS={elapsed}")
    if rc != 0:
        raise GateError(label.lower() + "_failed")
    require_clean_health(label + "_HEALTH")


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
    for item in raw:
        path = item.expanduser()
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.is_file():
            out.append(path)
    return out


def select_validation_python() -> str:
    probe = (
        "import fastapi, pytest; "
        "import app.api.codex_responses_v2; "
        "import app.services.codex_remote_compaction_v2"
    )
    tested = 0
    for candidate in candidate_pythons():
        tested += 1
        result = run([str(candidate), "-c", probe], timeout=45)
        if result.returncode == 0:
            print(f"VALIDATION_PYTHON_CANDIDATES_TESTED={tested}")
            print("VALIDATION_PYTHON_READY=YES")
            return str(candidate)
    print(f"VALIDATION_PYTHON_CANDIDATES_TESTED={tested}")
    print("VALIDATION_PYTHON_READY=NO")
    raise GateError("no_repo_capable_python")


def require_acceptance_workspace() -> None:
    guarded = (
        ACCEPTANCE_ROOT.is_dir()
        and (ACCEPTANCE_ROOT / ACCEPTANCE_MARKER).is_file()
        and (ACCEPTANCE_ROOT / ".git").is_dir()
    )
    print("M5_STAGE_A_F_WORKSPACE_GUARDED=" + ("YES" if guarded else "NO"))
    if not guarded:
        raise GateError("stage_a_f_workspace_missing_or_unguarded")


def run_stage_a_f_aggregate(python_executable: str) -> None:
    result = run(
        [python_executable, "tools/codex_desktop_acceptance.py", "check"],
        timeout=180,
    )
    passed = result.returncode == 0 and "ACCEPTANCE_PASS" in result.stdout
    print(f"M5_STAGE_A_F_AGGREGATE_RC={result.returncode}")
    print("M5_STAGE_A_F_AGGREGATE=" + ("PASS" if passed else "FAIL"))
    if not passed:
        scenario_lines = []
        for line in result.stdout.splitlines():
            text = line.strip()
            if re.match(r"^(multi_file|failure_recovery|git_diff|interactive|context):", text):
                scenario_lines.append(text)
        if scenario_lines:
            print("M5_STAGE_A_F_SAFE_SUMMARY=" + " | ".join(scenario_lines)[:500])
        raise GateError("stage_a_f_aggregate_failed")


def codex_test_files() -> list[str]:
    paths = sorted(
        path.relative_to(REPO).as_posix()
        for path in (REPO / "tests").glob("test_codex_*.py")
        if path.is_file()
    )
    missing = sorted(REQUIRED_TESTS - set(paths))
    print(f"M5_CODEX_TEST_FILE_COUNT={len(paths)}")
    print("M5_REQUIRED_TEST_FILES_PRESENT=" + ("YES" if not missing else "NO"))
    if missing:
        print("M5_REQUIRED_TEST_FILES_MISSING=" + ",".join(missing))
        raise GateError("required_codex_regression_missing")
    return paths


def run_codex_regression(python_executable: str, test_files: list[str]) -> None:
    compile_targets = [
        "app/api/codex_responses_v2.py",
        "app/services/codex_remote_compaction_v2.py",
        "tools/codex_uwa_lifecycle.py",
        "tools/codex_route_audit.py",
        "tools/codex_desktop_acceptance.py",
        "tools/codex_m5_final_regression.py",
        *test_files,
    ]
    compile_result = run(
        [python_executable, "-m", "py_compile", *compile_targets],
        timeout=180,
    )
    print(f"M5_PY_COMPILE_RC={compile_result.returncode}")
    print("M5_PY_COMPILE=" + ("PASS" if compile_result.returncode == 0 else "FAIL"))
    if compile_result.returncode != 0:
        raise GateError("py_compile_failed")

    result = run(
        [python_executable, "-m", "pytest", "-q", *test_files],
        timeout=PYTEST_TIMEOUT,
    )
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    passed_match = re.search(r"(\d+)\s+passed", combined)
    failed_match = re.search(r"(\d+)\s+failed", combined)
    passed_count = int(passed_match.group(1)) if passed_match else -1
    failed_count = int(failed_match.group(1)) if failed_match else 0
    print(f"M5_CODEX_REGRESSION_RC={result.returncode}")
    print(f"M5_CODEX_REGRESSION_PASSED_COUNT={passed_count}")
    print(f"M5_CODEX_REGRESSION_FAILED_COUNT={failed_count}")
    print("M5_CODEX_REGRESSION=" + ("PASS" if result.returncode == 0 else "FAIL"))
    if result.returncode != 0:
        failed_nodes: list[str] = []
        for line in combined.splitlines():
            text = line.strip()
            if text.startswith("FAILED "):
                failed_nodes.append(text[7:].split(" - ", 1)[0])
        if failed_nodes:
            print("M5_CODEX_REGRESSION_FAILED_NODES=" + ",".join(failed_nodes[:12]))
        raise GateError("codex_regression_failed")

    diff_check = run(["git", "diff", "--check"], timeout=60)
    print(f"M5_GIT_DIFF_CHECK_RC={diff_check.returncode}")
    if diff_check.returncode != 0:
        raise GateError("git_diff_check_failed")

    dirty = git_lines("status", "--porcelain", "--untracked-files=all")
    print(f"M5_REPOSITORY_DIRTY_AFTER_TESTS={len(dirty)}")
    if dirty:
        raise GateError("tests_mutated_repository")


def make_private_workspace() -> Path:
    PRIVATE_PARENT.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        PRIVATE_PARENT.chmod(0o700)
    except OSError:
        pass
    suffix = time.strftime("%Y%m%dT%H%M%S", time.gmtime()) + "-" + secrets.token_hex(4)
    path = PRIVATE_PARENT / suffix
    path.mkdir(mode=0o700)
    (path / SMOKE_MARKER).write_text("M5 synthetic restart-continuity workspace\n", encoding="utf-8")
    try:
        (path / SMOKE_MARKER).chmod(0o600)
    except OSError:
        pass
    return path


def write_private(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def parse_codex_jsonl(text: str, returncode: int) -> CodexObservation:
    thread_ids: list[str] = []
    event_types: list[str] = []
    agent_messages: list[str] = []
    completed_commands: list[str] = []
    turn_completed = False
    tool_item_count = 0

    for raw in text.splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or "").strip()
        if event_type and event_type not in event_types:
            event_types.append(event_type)
        if event_type == "thread.started":
            value = event.get("thread_id")
            if isinstance(value, str) and value:
                thread_ids.append(value)
        if event_type == "turn.completed":
            turn_completed = True
        if event_type not in {"item.started", "item.completed"}:
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "").strip().lower()
        if any(word in item_type for word in ("command", "tool", "function")):
            tool_item_count += 1
        if event_type == "item.completed" and item_type == "agent_message":
            value = item.get("text")
            if isinstance(value, str):
                agent_messages.append(value.strip())
        if event_type == "item.completed" and item_type == "command_execution":
            command = item.get("command")
            if isinstance(command, str):
                completed_commands.append(command)

    return CodexObservation(
        returncode=returncode,
        thread_ids=thread_ids,
        event_types=event_types,
        agent_messages=agent_messages,
        completed_commands=completed_commands,
        turn_completed=turn_completed,
        tool_item_count=tool_item_count,
    )


def run_codex_turn(
    *,
    workspace: Path,
    prompt: str,
    private_stem: str,
    thread_id: str | None,
) -> CodexObservation:
    args = [
        "codex",
        "exec",
        "--json",
        "--color",
        "never",
        "--skip-git-repo-check",
    ]
    if thread_id is None:
        args.append("-")
    else:
        args.extend(["resume", thread_id, "-"])

    started = time.monotonic()
    try:
        result = run(
            args,
            cwd=workspace,
            timeout=CODEX_TIMEOUT,
            input_text=prompt,
        )
        rc = result.returncode
        stdout = result.stdout or ""
        stderr = result.stderr or ""
    except subprocess.TimeoutExpired as exc:
        rc = 124
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else str(exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else str(exc.stderr or "")

    elapsed = int(time.monotonic() - started)
    write_private(workspace / f"{private_stem}.jsonl", stdout)
    write_private(workspace / f"{private_stem}.stderr.txt", stderr)
    observation = parse_codex_jsonl(stdout, rc)

    stderr_low = stderr.lower()
    kinds: list[str] = []
    for label, needle in (
        ("timeout", "timed out"),
        ("stream_disconnect", "stream disconnected"),
        ("quota", "usage limit"),
        ("transport", "connection reset"),
    ):
        if needle in stderr_low:
            kinds.append(label)

    prefix = private_stem.upper().replace("-", "_")
    print(f"{prefix}_RC={rc}")
    print(f"{prefix}_ELAPSED_SECONDS={elapsed}")
    print(f"{prefix}_TURN_COMPLETED=" + ("YES" if observation.turn_completed else "NO"))
    print(f"{prefix}_TOOL_ITEM_COUNT={observation.tool_item_count}")
    print(f"{prefix}_COMPLETED_COMMAND_COUNT={len(observation.completed_commands)}")
    print(f"{prefix}_STDERR_KINDS=" + (",".join(kinds) or "NONE"))
    return observation


def seed_prompt(token: str) -> str:
    return (
        "M5 final restart-continuity seed. Keep the following runtime synthetic token only in "
        f"this Codex conversation context: {token}. Do not call any tool. Do not write the token "
        f"to files. Reply with exactly {SEED_REPLY} and nothing else."
    )


def final_prompt() -> str:
    return (
        "This is the same M5 Codex thread after a real UWA process restart. Do not ask for the "
        "runtime synthetic token. Do not search Codex session/history, ~/.codex, ~/.uwa, logs, "
        "SQLite, rollout files, memory stores or any other external source for it. Use only the "
        "token retained from this conversation. You must use the local exec_command tool. First "
        f"call exec_command only to run: pwd && test -f {SMOKE_MARKER} && test ! -e {RESULT_NAME}. "
        "Do not set workdir. If that guard fails, reply only M5_WORKSPACE_MISMATCH. Then call "
        "exec_command a second time to create result.txt containing exactly the remembered token "
        "plus one newline and read result.txt back in that same command. Do not call any other "
        f"tool and do not modify any other file. After success reply with exactly {FINAL_REPLY}."
    )


def workspace_contains_token(workspace: Path, token: str) -> bool:
    token_bytes = token.encode("utf-8")
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        if path.name.endswith((".jsonl", ".stderr.txt")):
            continue
        try:
            if token_bytes in path.read_bytes():
                return True
        except OSError:
            continue
    return False


def verify_seed(observation: CodexObservation) -> str:
    unique_threads = list(dict.fromkeys(observation.thread_ids))
    exact = bool(observation.agent_messages) and observation.agent_messages[-1] == SEED_REPLY
    no_tools = observation.tool_item_count == 0 and not observation.completed_commands
    passed = (
        observation.returncode == 0
        and observation.turn_completed
        and exact
        and no_tools
        and len(unique_threads) == 1
    )
    print("M5_SEED_REPLY_EXACT=" + ("YES" if exact else "NO"))
    print("M5_SEED_ZERO_TOOL_ACTIVITY=" + ("YES" if no_tools else "NO"))
    print("M5_SEED_THREAD_CAPTURED=" + ("YES" if len(unique_threads) == 1 else "NO"))
    print("M5_SEED_TURN=" + ("PASS" if passed else "FAIL"))
    if not passed:
        raise GateError("seed_turn_failed")
    return unique_threads[0]


def command_contract(commands: list[str]) -> bool:
    if len(commands) < 2:
        return False
    lowered = [command.lower() for command in commands]
    forbidden = (".codex", "sqlite", "rollout", "session/history", "memory store")
    safe = all(not any(term in command for term in forbidden) for command in lowered)
    guard = any("pwd" in command and SMOKE_MARKER.lower() in command for command in lowered)
    result = any(RESULT_NAME in command for command in lowered)
    return safe and guard and result


def verify_final(observation: CodexObservation, workspace: Path, token: str, thread_id: str) -> None:
    same_thread = bool(observation.thread_ids) and all(value == thread_id for value in observation.thread_ids)
    exact_reply = bool(observation.agent_messages) and observation.agent_messages[-1] == FINAL_REPLY
    commands_ok = command_contract(observation.completed_commands)
    result_path = workspace / RESULT_NAME
    result_exact = result_path.is_file() and result_path.read_bytes() == (token + "\n").encode("utf-8")
    passed = (
        observation.returncode == 0
        and observation.turn_completed
        and same_thread
        and exact_reply
        and commands_ok
        and result_exact
    )
    print("M5_RESTART_SAME_CODEX_THREAD=" + ("YES" if same_thread else "NO"))
    print("M5_FINAL_REPLY_EXACT=" + ("YES" if exact_reply else "NO"))
    print("M5_REAL_CLIENT_TOOL_ACTIVITY=" + ("YES" if commands_ok else "NO"))
    print("M5_CONTINUITY_RESULT_EXACT=" + ("YES" if result_exact else "NO"))
    print("M5_RESTART_CONTINUITY=" + ("PASS" if passed else "FAIL"))
    if not passed:
        raise GateError("restart_continuity_failed")


def verify_route_after_marker() -> None:
    since = route_audit.load_marker()
    session = route_audit.latest_session_route(since_epoch=since)
    wire = route_audit.scan_wire_activity(since_epoch=since)
    expectation, failures = route_audit.expectation_result(
        session,
        wire,
        expect_provider="uwa",
        expect_model="chatgpt",
        expect_effort="high",
    )
    latest_completed = wire.latest_status == "completed"
    enough_wire = wire.request_count >= 2 and wire.response_count >= 2
    passed = expectation is True and latest_completed and enough_wire
    print(f"M5_POST_MARKER_AGENT_REQUEST_COUNT={wire.request_count}")
    print(f"M5_POST_MARKER_AGENT_RESPONSE_COUNT={wire.response_count}")
    print("M5_POST_MARKER_LATEST_STATUS=" + (wire.latest_status or "UNKNOWN"))
    print("M5_ROUTE_EXPECTATION_FAILURES=" + (",".join(failures) or "NONE"))
    print("M5_ROUTE_UWA_CHATGPT_HIGH=" + ("YES" if passed else "NO"))
    if not passed:
        raise GateError("route_audit_failed")


def cleanup_workspace(workspace: Path) -> None:
    try:
        resolved_parent = PRIVATE_PARENT.resolve()
        resolved = workspace.resolve()
        if resolved.parent != resolved_parent or not (resolved / SMOKE_MARKER).is_file():
            raise GateError("private_workspace_cleanup_guard_failed")
        shutil.rmtree(resolved)
        print("M5_PRIVATE_WORKSPACE_CLEANED=YES")
    except GateError:
        raise
    except Exception as exc:
        raise GateError("private_workspace_cleanup_failed") from exc


def main() -> int:
    workspace: Path | None = None
    try:
        print("M5_FINAL_REGRESSION_BEGIN")
        require_clean_branch()
        require_ancestor(M4_COMMIT, "M5_M4_COMMIT_PRESENT")
        require_ancestor(REMOTE_COMPACTION_FIX_COMMIT, "M5_REMOTE_COMPACTION_FIX_PRESENT")
        require_uwa_route()
        if shutil.which("codex") is None:
            print("M5_CODEX_CLI_PRESENT=NO")
            raise GateError("codex_cli_missing")
        print("M5_CODEX_CLI_PRESENT=YES")

        require_acceptance_workspace()
        validation_python = select_validation_python()
        run_stage_a_f_aggregate(validation_python)
        test_files = codex_test_files()
        run_codex_regression(validation_python, test_files)

        restart_uwa("M5_FIRST_RESTART")
        require_uwa_route()
        marker_epoch = route_audit.write_marker()
        print("M5_ROUTE_MARKER_WRITTEN=YES")
        print("M5_ROUTE_MARKER_PRIVATE_MODE=0600")
        print("M5_ROUTE_MARKER_EPOCH_PRESENT=" + ("YES" if marker_epoch > 0 else "NO"))

        workspace = make_private_workspace()
        token = "M5-" + secrets.token_urlsafe(24)
        seed = run_codex_turn(
            workspace=workspace,
            prompt=seed_prompt(token),
            private_stem="m5-seed",
            thread_id=None,
        )
        thread_id = verify_seed(seed)
        token_leaked = workspace_contains_token(workspace, token)
        print("M5_TOKEN_LEAK_BEFORE_RESTART=" + ("YES" if token_leaked else "NO"))
        if token_leaked:
            raise GateError("seed_token_leaked_into_workspace")
        require_clean_health("M5_AFTER_SEED_HEALTH")

        restart_uwa("M5_SECOND_RESTART")
        require_uwa_route()
        final = run_codex_turn(
            workspace=workspace,
            prompt=final_prompt(),
            private_stem="m5-resume",
            thread_id=thread_id,
        )
        verify_final(final, workspace, token, thread_id)
        verify_route_after_marker()
        require_clean_health("M5_FINAL_HEALTH")

        final_dirty = git_lines("status", "--porcelain", "--untracked-files=all")
        print(f"M5_FINAL_REPOSITORY_DIRTY_COUNT={len(final_dirty)}")
        print("M5_REPOSITORY_STILL_CLEAN=" + ("YES" if not final_dirty else "NO"))
        if final_dirty:
            raise GateError("repository_dirty_after_live_smoke")

        cleanup_workspace(workspace)
        workspace = None
        print("M5_STAGE_A_F_AGGREGATE=PASS")
        print("M5_CODEX_REGRESSION=PASS")
        print("M5_PY_COMPILE=PASS")
        print("M5_FIRST_RESTART=PASS")
        print("M5_SEED_TURN=PASS")
        print("M5_SECOND_RESTART=PASS")
        print("M5_RESTART_CONTINUITY=PASS")
        print("M5_REAL_CLIENT_TOOL_ACTIVITY=YES")
        print("M5_ROUTE_UWA_CHATGPT_HIGH=YES")
        print("M5_REQUEST_MANAGER_CLEAN_AFTER=YES")
        print("M5_REPOSITORY_STILL_CLEAN=YES")
        print("M5_FINAL_REGRESSION=PASS_LIVE_CLOSED")
        return 0
    except GateError as exc:
        print("M5_FINAL_REGRESSION=FAIL")
        print("M5_FAILURE_CLASS=" + str(exc))
        if workspace is not None:
            print("M5_PRIVATE_EVIDENCE_PRESERVED=YES")
        return 1
    except subprocess.TimeoutExpired:
        print("M5_FINAL_REGRESSION=FAIL")
        print("M5_FAILURE_CLASS=subprocess_timeout")
        if workspace is not None:
            print("M5_PRIVATE_EVIDENCE_PRESERVED=YES")
        return 1
    except Exception as exc:
        print("M5_FINAL_REGRESSION=FAIL")
        print("M5_FAILURE_CLASS=unexpected_" + type(exc).__name__)
        if workspace is not None:
            print("M5_PRIVATE_EVIDENCE_PRESERVED=YES")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
