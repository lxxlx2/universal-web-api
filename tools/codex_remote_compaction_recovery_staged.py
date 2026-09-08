#!/usr/bin/env python3
"""Deterministic staged P1.2 recovery gate for an already-proven compacted thread.

The core remote-compaction and conversation-token continuity properties are
proven by the dedicated live evidence.  This runner validates the remaining
client-tool orchestration deterministically by resuming the same compacted Codex
thread in three bounded turns: workspace guard, result write, and result read.

It never prints the private thread id, prompts, command bodies, token value, or
tool output.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable

if __package__:
    from tools import codex_auto_compact_trigger_probe as trigger_probe
    from tools import codex_large_context_acceptance as base
    from tools import codex_remote_compaction_recovery as legacy
else:
    import codex_auto_compact_trigger_probe as trigger_probe
    import codex_large_context_acceptance as base
    import codex_remote_compaction_recovery as legacy


GUARD_REPLY = "POST_REMOTE_RECOVERY_GUARD_PASS"
WRITE_REPLY = "POST_REMOTE_RECOVERY_WRITE_PASS"
READ_REPLY = "POST_REMOTE_RECOVERY_PASS"
EVIDENCE_RELATIVE = Path(base.SCENARIO) / "remote_recovery_staged_evidence.json"
DEFAULT_TIMEOUT_SEC = 120


def _common_safety_prefix() -> str:
    return (
        "这是同一个 P1.2 remote-compaction Codex thread 的分阶段恢复验收。"
        "不要向我询问第一轮合成令牌，也不要从本机 Codex session/history、"
        "~/.codex、~/.uwa、rollout、日志、SQLite、PROMPTS.md、memory store 或其他文件中搜索令牌。"
    )


def build_guard_prompt() -> str:
    prompt = (
        _common_safety_prefix()
        + f"必须单独调用一次客户端 exec_command，只执行 pwd && test -f {base.MARKER} "
        + f"&& test -d {base.SCENARIO}。不要执行其他命令。"
        + f"成功后只回复 {GUARD_REPLY}；失败只回复 ACCEPTANCE_WORKSPACE_MISMATCH。"
    )
    _assert_token_not_embedded(prompt)
    return prompt


def build_write_prompt() -> str:
    prompt = (
        _common_safety_prefix()
        + "基于你在同一对话上下文中已经保留的原始合成令牌继续，不要在最终文本中复述令牌。"
        + "必须单独调用一次客户端 exec_command，只使用该对话上下文中的合成令牌创建 "
        + f"{base.RESULT_RELATIVE.as_posix()}，文件必须精确包含该令牌和一个换行；不要读取其他文件。"
        + f"成功后只回复 {WRITE_REPLY}。"
    )
    _assert_token_not_embedded(prompt)
    return prompt


def build_read_prompt() -> str:
    prompt = (
        _common_safety_prefix()
        + f"必须单独调用一次客户端 exec_command，只实际读取 {base.RESULT_RELATIVE.as_posix()}，"
        + "不要读取任何其他文件，也不要修改文件。"
        + f"确认成功后只回复 {READ_REPLY}。"
    )
    _assert_token_not_embedded(prompt)
    return prompt


def _assert_token_not_embedded(prompt: str) -> None:
    if base.TOKEN in prompt:
        raise AssertionError("staged recovery prompt must not repeat the conversation-only token")


def _clean_owned_result(root: Path) -> bool:
    result_path = root / base.RESULT_RELATIVE
    existed = result_path.exists()
    if existed:
        result_path.unlink()
    evidence = root / EVIDENCE_RELATIVE
    if evidence.exists():
        evidence.unlink()
    return existed


def _trace_readback_exact(path: Path) -> bool:
    if not path.exists():
        return False
    raw = legacy._private_trace_text(path)
    outputs: list[str] = []
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        output = item.get("aggregated_output")
        if output is None:
            output = item.get("output")
        if isinstance(output, str):
            outputs.append(output)
    return bool(outputs) and outputs[-1].strip() == base.TOKEN


def _run_stage(
    *,
    stage: str,
    codex_path: str,
    root: Path,
    prompt: str,
    trace_path: Path,
    thread_id: str,
    timeout_sec: int,
    expected_reply: str,
    validator: Callable[[dict[str, Any]], bool],
) -> tuple[bool, base.ExecObservation | None, dict[str, Any] | None]:
    try:
        observation = base._run_codex_turn(
            codex=codex_path,
            root=root,
            prompt=prompt,
            trace_path=trace_path,
            thread_id=thread_id,
            timeout_sec=timeout_sec,
        )
    except RuntimeError as exc:
        if trace_path.exists():
            legacy._print_partial_timeout_summary(
                legacy._partial_timeout_summary(trace_path, thread_id, root)
            )
        print(f"STAGE_{stage.upper()}_FAIL={exc}")
        return False, None, None

    same_thread = base._verify_thread(observation, thread_id)
    reply_exact = observation.final_message == expected_reply
    command_count_ok = len(observation.commands) == 1
    commands_safe = base._final_commands_safe(observation.commands)
    semantics = (
        legacy._command_semantics(observation.commands[0])
        if len(observation.commands) == 1
        else None
    )
    semantic_ok = semantics is not None and validator(semantics)

    prefix = f"STAGE_{stage.upper()}"
    print(f"{prefix}_SAME_THREAD={'YES' if same_thread else 'NO'}")
    print(f"{prefix}_REPLY_EXACT={'YES' if reply_exact else 'NO'}")
    print(f"{prefix}_EXEC_COUNT={len(observation.commands)}")
    print(f"{prefix}_COMMANDS_SAFE={'YES' if commands_safe else 'NO'}")
    print(f"{prefix}_SEMANTIC_PASS={'YES' if semantic_ok else 'NO'}")

    passed = same_thread and reply_exact and command_count_ok and commands_safe and semantic_ok
    return passed, observation, semantics


def _guard_semantics(semantics: dict[str, Any]) -> bool:
    return (
        semantics["is_workspace_guard"]
        and not semantics["refs_result_path"]
        and not semantics["contains_conversation_token"]
        and not semantics["write_like"]
        and not semantics["read_like"]
        and not semantics["private_search"]
    )


def _write_semantics(semantics: dict[str, Any]) -> bool:
    return (
        not semantics["is_workspace_guard"]
        and semantics["refs_result_path"]
        and semantics["contains_conversation_token"]
        and semantics["write_like"]
        and not semantics["read_like"]
        and not semantics["private_search"]
    )


def _read_semantics(semantics: dict[str, Any]) -> bool:
    return (
        not semantics["is_workspace_guard"]
        and semantics["refs_result_path"]
        and not semantics["contains_conversation_token"]
        and not semantics["write_like"]
        and semantics["read_like"]
        and not semantics["private_search"]
    )


def _write_evidence(root: Path, payload: dict[str, Any]) -> None:
    path = root / EVIDENCE_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run(root: Path, *, codex: str, trace_dir: Path, timeout_sec: int) -> int:
    root = base._guard_root(root)
    try:
        trace_dir = legacy._guard_trace_dir(trace_dir)
    except ValueError as exc:
        print(f"RUN_FAIL trace_contract={exc}")
        return 1

    codex_path = shutil.which(codex) if os.sep not in codex else codex
    if not codex_path or not Path(codex_path).exists():
        print(f"RUN_FAIL codex_not_found={codex}")
        return 1

    thread_id = legacy._recover_thread_id(trace_dir)
    print("PRIVATE_TRACE_DIR_VALID=YES")
    print(f"PRIVATE_THREAD_RECOVERED={'YES' if thread_id else 'NO'}")
    if not thread_id:
        print("RUN_FAIL thread_contract")
        return 1

    prior_trigger_ok = legacy._validate_prior_trigger(trace_dir, thread_id)
    print(f"PRIOR_TRIGGER_CONTRACT={'PASS' if prior_trigger_ok else 'FAIL'}")
    if not prior_trigger_ok:
        print("RUN_FAIL prior_trigger_contract")
        return 1

    rollout = trigger_probe._wait_for_rollout(thread_id)
    compact_pre = trigger_probe.count_rollout_compact_markers(rollout) if rollout else 0
    print(f"ROLLOUT_COMPACT_MARKERS_PRE_STAGED_RECOVERY={compact_pre}")
    if compact_pre < 1:
        print("RUN_FAIL compacted_rollout_not_observed")
        return 1

    reset = _clean_owned_result(root)
    print(f"OWNED_RESULT_RESET={'YES' if reset else 'NO'}")

    token_hits = base._workspace_contains_token(root)
    workspace_clean = not token_hits
    print(f"TOKEN_LEAK_BEFORE_STAGED_RECOVERY={'NO' if workspace_clean else 'YES'}")
    if not workspace_clean:
        print("RUN_FAIL conversation_token_already_in_workspace")
        return 1

    guard_trace = trace_dir / "post-remote-recovery-staged-guard.jsonl"
    write_trace = trace_dir / "post-remote-recovery-staged-write.jsonl"
    read_trace = trace_dir / "post-remote-recovery-staged-read.jsonl"

    guard_ok, _, _ = _run_stage(
        stage="guard",
        codex_path=str(codex_path),
        root=root,
        prompt=build_guard_prompt(),
        trace_path=guard_trace,
        thread_id=thread_id,
        timeout_sec=timeout_sec,
        expected_reply=GUARD_REPLY,
        validator=_guard_semantics,
    )
    if not guard_ok:
        print("POST_REMOTE_STAGED_RECOVERY_FAIL")
        return 1

    write_ok, _, _ = _run_stage(
        stage="write",
        codex_path=str(codex_path),
        root=root,
        prompt=build_write_prompt(),
        trace_path=write_trace,
        thread_id=thread_id,
        timeout_sec=timeout_sec,
        expected_reply=WRITE_REPLY,
        validator=_write_semantics,
    )
    result_path = root / base.RESULT_RELATIVE
    result_exact = result_path.exists() and result_path.read_bytes() == (base.TOKEN + "\n").encode("utf-8")
    print(f"STAGE_WRITE_RESULT_EXACT={'YES' if result_exact else 'NO'}")
    if not write_ok or not result_exact:
        print("POST_REMOTE_STAGED_RECOVERY_FAIL")
        return 1

    read_ok, _, _ = _run_stage(
        stage="read",
        codex_path=str(codex_path),
        root=root,
        prompt=build_read_prompt(),
        trace_path=read_trace,
        thread_id=thread_id,
        timeout_sec=timeout_sec,
        expected_reply=READ_REPLY,
        validator=_read_semantics,
    )
    readback_exact = _trace_readback_exact(read_trace)
    print(f"STAGE_READ_OUTPUT_EXACT={'YES' if readback_exact else 'NO'}")

    rollout_post = trigger_probe._wait_for_rollout(thread_id)
    compact_post = trigger_probe.count_rollout_compact_markers(rollout_post) if rollout_post else compact_pre
    compact_stable = compact_post == compact_pre
    print(f"ROLLOUT_COMPACT_MARKERS_POST_STAGED_RECOVERY={compact_post}")
    print(f"COMPACTION_GREW_DURING_STAGED_RECOVERY={'NO' if compact_stable else 'YES'}")

    passed = guard_ok and write_ok and read_ok and result_exact and readback_exact and compact_stable

    _write_evidence(
        root,
        {
            "schema_version": 1,
            "scenario": "post_remote_compaction_recovery_staged",
            "private_thread_id_not_recorded": True,
            "private_trace_paths_not_recorded": True,
            "token_value_not_recorded": True,
            "prior_trigger_contract": prior_trigger_ok,
            "rollout_compact_markers_pre": compact_pre,
            "rollout_compact_markers_post": compact_post,
            "compaction_stable": compact_stable,
            "workspace_token_clean_before_staged_recovery": workspace_clean,
            "guard_stage_pass": guard_ok,
            "write_stage_pass": write_ok,
            "read_stage_pass": read_ok,
            "result_exact": result_exact,
            "readback_output_exact": readback_exact,
        },
    )

    if not passed:
        print("POST_REMOTE_STAGED_RECOVERY_FAIL")
        return 1

    print("POST_REMOTE_STAGED_RECOVERY_PASS")
    print("P1_2_REMOTE_COMPACTION_STAGED_RECOVERY_PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "prompts"])
    parser.add_argument("--root", type=Path, default=base.DEFAULT_ROOT)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--trace-dir", type=Path)
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    args = parser.parse_args()

    if args.command == "prompts":
        print("GUARD=" + build_guard_prompt())
        print("WRITE=" + build_write_prompt())
        print("READ=" + build_read_prompt())
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
