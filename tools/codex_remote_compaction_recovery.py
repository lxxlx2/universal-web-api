#!/usr/bin/env python3
"""P1.2 same-thread recovery after a proven remote-V2 compaction run.

This gate intentionally reuses an already-completed private trigger-probe trace.
It never prints the Codex thread id, rollout path, prompts, command bodies, or
private trace contents.  The model must recover the conversation-only synthetic
token from compacted conversational context, then use real local Codex tools to
validate the workspace, write the token, and read it back.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

if __package__:
    from tools import codex_auto_compact_trigger_probe as trigger_probe
    from tools import codex_large_context_acceptance as base
else:
    import codex_auto_compact_trigger_probe as trigger_probe
    import codex_large_context_acceptance as base


RECOVERY_REPLY = "POST_REMOTE_RECOVERY_PASS"
RECOVERY_EVIDENCE_RELATIVE = Path(base.SCENARIO) / "remote_recovery_evidence.json"
DEFAULT_TIMEOUT_SEC = 900


def build_recovery_prompt() -> str:
    prompt = (
        "这是同一个 P1.2 remote-compaction Codex thread 的最终恢复轮。"
        "不要向我询问第一轮合成令牌，也不要从本机 Codex session/history、"
        "~/.codex、~/.uwa、rollout、日志、SQLite、PROMPTS.md、memory store 或其他文件中搜索令牌。"
        f"第一步必须单独调用一次客户端 exec_command，只执行 pwd && test -f {base.MARKER} "
        f"&& test -d {base.SCENARIO}。如果失败，只回复 ACCEPTANCE_WORKSPACE_MISMATCH。"
        f"第二步必须再单独调用一次 exec_command，只使用你从对话上下文保留的合成令牌创建 "
        f"{base.RESULT_RELATIVE.as_posix()}，文件必须精确包含该令牌和一个换行。"
        f"第三步必须再单独调用一次 exec_command，实际读取 {base.RESULT_RELATIVE.as_posix()} "
        "确认内容；不要读取任何其他文件。"
        f"三步都成功后只回复 {RECOVERY_REPLY}。"
    )
    if base.TOKEN in prompt:
        raise AssertionError("recovery prompt must not repeat the conversation-only token")
    return prompt


def _guard_trace_dir(path: Path) -> Path:
    private_root = base.DEFAULT_PRIVATE_TRACE_ROOT.expanduser().resolve()
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError("trace directory does not exist")
    if not resolved.is_relative_to(private_root):
        raise ValueError("trace directory must stay under the private P1.2 trace root")
    if not (resolved / "trigger-probe-seed.jsonl").is_file():
        raise ValueError("missing trigger-probe seed trace")
    if not (resolved / "trigger-probe-final-trigger.jsonl").is_file():
        raise ValueError("missing final trigger trace")
    return resolved


def _parse_trace(path: Path) -> base.ExecObservation:
    return base.parse_exec_jsonl(path.read_text(encoding="utf-8", errors="replace"), 0)


def _recover_thread_id(trace_dir: Path) -> str | None:
    ids: list[str] = []
    for path in sorted(trace_dir.glob("trigger-probe-*.jsonl")):
        ids.extend(_parse_trace(path).thread_ids)
    unique = list(dict.fromkeys(value for value in ids if value))
    return unique[0] if len(unique) == 1 else None


def _validate_prior_trigger(trace_dir: Path, thread_id: str) -> bool:
    observation = _parse_trace(trace_dir / "trigger-probe-final-trigger.jsonl")
    return (
        base._verify_thread(observation, thread_id)
        and observation.final_message == trigger_probe.TRIGGER_ACK
        and observation.tool_effect_count == 0
    )


def _command_contract(commands: list[str]) -> dict[str, bool]:
    safe = base._final_commands_safe(commands)
    guard = any(
        "pwd" in command and base.MARKER in command and base.SCENARIO in command
        for command in commands
    )
    result_ref_count = sum(
        base.RESULT_RELATIVE.as_posix() in command for command in commands
    )
    read_markers = ("cat ", "sed ", "head ", "tail ", "awk ", "python", "perl ", "ruby ")
    read_back = any(
        base.RESULT_RELATIVE.as_posix() in command
        and any(marker in command for marker in read_markers)
        for command in commands
    )
    return {
        "safe": safe,
        "three_separate_execs": len(commands) >= 3,
        "workspace_guard": guard,
        "result_referenced_twice": result_ref_count >= 2,
        "read_back": read_back,
    }


def _write_evidence(root: Path, payload: dict[str, Any]) -> None:
    path = root / RECOVERY_EVIDENCE_RELATIVE
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(root: Path, *, codex: str, trace_dir: Path, timeout_sec: int) -> int:
    root = base._guard_root(root)
    try:
        trace_dir = _guard_trace_dir(trace_dir)
    except ValueError as exc:
        print(f"RUN_FAIL trace_contract={exc}")
        return 1

    codex_path = shutil.which(codex) if os.sep not in codex else codex
    if not codex_path or not Path(codex_path).exists():
        print(f"RUN_FAIL codex_not_found={codex}")
        return 1

    thread_id = _recover_thread_id(trace_dir)
    print(f"PRIVATE_TRACE_DIR_VALID=YES")
    print(f"PRIVATE_THREAD_RECOVERED={'YES' if thread_id else 'NO'}")
    if not thread_id:
        print("RUN_FAIL thread_contract")
        return 1

    prior_trigger_ok = _validate_prior_trigger(trace_dir, thread_id)
    print(f"PRIOR_TRIGGER_CONTRACT={'PASS' if prior_trigger_ok else 'FAIL'}")
    if not prior_trigger_ok:
        print("RUN_FAIL prior_trigger_contract")
        return 1

    rollout = trigger_probe._wait_for_rollout(thread_id)
    compact_markers = trigger_probe.count_rollout_compact_markers(rollout) if rollout else 0
    print(f"ROLLOUT_COMPACT_MARKERS_PRE_RECOVERY={compact_markers}")
    if compact_markers < 1:
        print("RUN_FAIL compacted_rollout_not_observed")
        return 1

    token_hits = base._workspace_contains_token(root)
    workspace_clean = not token_hits
    print(f"TOKEN_LEAK_BEFORE_RECOVERY={'NO' if workspace_clean else 'YES'}")
    if not workspace_clean:
        print("RUN_FAIL conversation_token_already_in_workspace")
        return 1

    try:
        final = base._run_codex_turn(
            codex=str(codex_path),
            root=root,
            prompt=build_recovery_prompt(),
            trace_path=trace_dir / "post-remote-recovery.jsonl",
            thread_id=thread_id,
            timeout_sec=timeout_sec,
        )
    except RuntimeError as exc:
        print(f"RUN_FAIL recovery_turn={exc}")
        return 1

    same_thread = base._verify_thread(final, thread_id)
    reply_exact = final.final_message == RECOVERY_REPLY
    command_contract = _command_contract(final.commands)
    result_path = root / base.RESULT_RELATIVE
    result_bytes = result_path.read_bytes() if result_path.exists() else b""
    result_exact = result_bytes == (base.TOKEN + "\n").encode("utf-8")

    print(f"SAME_THREAD={'YES' if same_thread else 'NO'}")
    print(f"RECOVERY_REPLY_EXACT={'YES' if reply_exact else 'NO'}")
    print(f"RECOVERY_EXEC_COMMAND_COUNT={len(final.commands)}")
    print(f"RECOVERY_COMMANDS_SAFE={'YES' if command_contract['safe'] else 'NO'}")
    print(f"WORKSPACE_GUARD_OBSERVED={'YES' if command_contract['workspace_guard'] else 'NO'}")
    print(f"SEPARATE_EXEC_STEPS={'YES' if command_contract['three_separate_execs'] else 'NO'}")
    print(f"RESULT_REFERENCED_TWICE={'YES' if command_contract['result_referenced_twice'] else 'NO'}")
    print(f"READ_BACK_OBSERVED={'YES' if command_contract['read_back'] else 'NO'}")
    print(f"RESULT_EXACT={'YES' if result_exact else 'NO'}")

    passed = (
        same_thread
        and reply_exact
        and result_exact
        and all(command_contract.values())
    )

    _write_evidence(
        root,
        {
            "schema_version": 1,
            "scenario": "post_remote_compaction_recovery",
            "private_thread_id_not_recorded": True,
            "private_trace_path_not_recorded": True,
            "prior_trigger_contract": prior_trigger_ok,
            "rollout_compact_markers_pre_recovery": compact_markers,
            "workspace_token_clean_before_recovery": workspace_clean,
            "same_thread": same_thread,
            "recovery_reply_exact": reply_exact,
            "exec_command_count": len(final.commands),
            "commands_safe": command_contract["safe"],
            "workspace_guard_observed": command_contract["workspace_guard"],
            "separate_exec_steps": command_contract["three_separate_execs"],
            "result_referenced_twice": command_contract["result_referenced_twice"],
            "read_back_observed": command_contract["read_back"],
            "result_exact": result_exact,
        },
    )

    if not passed:
        print("POST_REMOTE_RECOVERY_FAIL")
        return 1

    print("POST_REMOTE_RECOVERY_PASS")
    print("P1_2_REMOTE_COMPACTION_RECOVERY_PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "prompt"])
    parser.add_argument("--root", type=Path, default=base.DEFAULT_ROOT)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--trace-dir", type=Path)
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    args = parser.parse_args()

    if args.command == "prompt":
        print(build_recovery_prompt())
        return 0
    if args.trace_dir is None:
        raise SystemExit("--trace-dir is required for run")
    if args.timeout_sec < 1:
        raise SystemExit("--timeout-sec must be positive")
    return run(
        args.root,
        codex=args.codex,
        trace_dir=args.trace_dir,
        timeout_sec=args.timeout_sec,
    )


if __name__ == "__main__":
    raise SystemExit(main())
