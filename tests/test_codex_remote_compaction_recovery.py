from pathlib import Path

from tools import codex_remote_compaction_recovery as recovery


def test_recovery_prompt_keeps_token_conversation_only():
    prompt = recovery.build_recovery_prompt()
    assert recovery.base.TOKEN not in prompt
    assert recovery.RECOVERY_REPLY in prompt
    assert "~/.codex" in prompt
    assert "~/.uwa" in prompt
    assert recovery.base.RESULT_RELATIVE.as_posix() in prompt


def test_command_contract_requires_guard_write_reference_and_readback():
    commands = [
        f"pwd && test -f {recovery.base.MARKER} && test -d {recovery.base.SCENARIO}",
        f"printf '%s\\n' '<remembered-token>' > {recovery.base.RESULT_RELATIVE.as_posix()}",
        f"cat {recovery.base.RESULT_RELATIVE.as_posix()}",
    ]
    result = recovery._command_contract(commands)
    assert all(result.values())


def test_command_contract_rejects_private_history_search():
    commands = [
        f"pwd && test -f {recovery.base.MARKER} && test -d {recovery.base.SCENARIO}",
        "rg ORBIT ~/.codex",
        f"cat {recovery.base.RESULT_RELATIVE.as_posix()}",
    ]
    result = recovery._command_contract(commands)
    assert result["safe"] is False


def test_guard_trace_dir_rejects_non_private_root(tmp_path: Path):
    outside = tmp_path / "trace"
    outside.mkdir()
    try:
        recovery._guard_trace_dir(outside)
    except ValueError as exc:
        assert "private P1.2 trace root" in str(exc)
    else:
        raise AssertionError("outside trace dir should be rejected")


def test_recover_thread_id_requires_one_unique_thread(tmp_path: Path):
    trace = tmp_path
    (trace / "trigger-probe-seed.jsonl").write_text(
        '{"type":"thread.started","thread_id":"thread-one"}\n',
        encoding="utf-8",
    )
    (trace / "trigger-probe-final-trigger.jsonl").write_text(
        '{"type":"thread.started","thread_id":"thread-one"}\n',
        encoding="utf-8",
    )
    assert recovery._recover_thread_id(trace) == "thread-one"

    (trace / "trigger-probe-extra.jsonl").write_text(
        '{"type":"thread.started","thread_id":"thread-two"}\n',
        encoding="utf-8",
    )
    assert recovery._recover_thread_id(trace) is None
