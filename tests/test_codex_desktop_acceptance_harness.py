import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "codex_desktop_acceptance.py"


def _run(*args: str, cwd: Path | None = None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd or REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def test_setup_generates_intentionally_failing_but_valid_fixture(tmp_path):
    root = tmp_path / "acceptance"
    result = _run("setup", "--root", str(root))
    assert result.returncode == 0, result.stdout
    assert "SETUP_PASS" in result.stdout
    assert (root / ".uwa_codex_acceptance").is_file()
    assert (root / ".git").is_dir()
    assert (root / "PROMPTS.md").is_file()

    compile_result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", str(root)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert compile_result.returncode == 0, compile_result.stdout

    for suite in ("multi_file", "failure_recovery", "git_diff"):
        test_result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", f"{suite}/tests", "-v"],
            cwd=str(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert test_result.returncode != 0, f"{suite} unexpectedly started green\n{test_result.stdout}"


def test_setup_refuses_to_delete_unmarked_existing_directory(tmp_path):
    root = tmp_path / "existing"
    root.mkdir()
    sentinel = root / "do-not-delete.txt"
    sentinel.write_text("keep\n", encoding="utf-8")

    result = _run("setup", "--root", str(root))
    assert result.returncode != 0
    assert "Refusing to touch an existing unmarked directory" in result.stdout
    assert sentinel.read_text(encoding="utf-8") == "keep\n"


def test_context_prompts_are_two_round_same_thread_protocol(tmp_path):
    root = tmp_path / "acceptance"
    setup_result = _run("setup", "--root", str(root))
    assert setup_result.returncode == 0, setup_result.stdout

    first = _run("prompts", "--root", str(root), "--scenario", "context_1")
    second = _run("prompts", "--root", str(root), "--scenario", "context_2")
    assert first.returncode == 0
    assert second.returncode == 0
    assert "EMBER-7319" in first.stdout
    assert "不要向我询问上一轮令牌" in second.stdout


def test_failure_recovery_prompt_guards_current_workspace(tmp_path):
    root = tmp_path / "acceptance"
    assert _run("setup", "--root", str(root)).returncode == 0

    prompt = _run("prompts", "--root", str(root), "--scenario", "failure_recovery")
    assert prompt.returncode == 0, prompt.stdout
    assert ".uwa_codex_acceptance" in prompt.stdout
    assert "ACCEPTANCE_WORKSPACE_MISMATCH" in prompt.stdout
    assert "不要探测其他绝对路径" in prompt.stdout
    assert "/Users/" not in prompt.stdout


def test_prepare_restores_only_selected_scenario_and_preflight_proves_red(tmp_path):
    root = tmp_path / "acceptance"
    assert _run("setup", "--root", str(root)).returncode == 0

    preserved = root / "multi_file" / "math_ops.py"
    preserved.write_text("LOCAL_STAGE_A_RESULT\n", encoding="utf-8")
    target = root / "failure_recovery"
    for path in sorted(target.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    target.rmdir()

    prepared = _run(
        "prepare",
        "--root",
        str(root),
        "--scenario",
        "failure_recovery",
    )
    assert prepared.returncode == 0, prepared.stdout
    assert "PREPARE_PASS scenario=failure_recovery" in prepared.stdout
    assert preserved.read_text(encoding="utf-8") == "LOCAL_STAGE_A_RESULT\n"
    assert (root / "failure_recovery" / "parser.py").is_file()

    preflight = _run(
        "preflight",
        "--root",
        str(root),
        "--scenario",
        "failure_recovery",
    )
    assert preflight.returncode == 0, preflight.stdout
    assert "PREFLIGHT_EXPECTED_RED scenario=failure_recovery" in preflight.stdout
    assert "PREFLIGHT_PASS scenario=failure_recovery" in preflight.stdout


def test_prepare_creates_missing_acceptance_workspace(tmp_path):
    root = tmp_path / "missing"
    prepared = _run(
        "prepare",
        "--root",
        str(root),
        "--scenario",
        "failure_recovery",
    )
    assert prepared.returncode == 0, prepared.stdout
    assert "SETUP_PASS" in prepared.stdout
    assert "PREPARE_PASS scenario=failure_recovery created_workspace=true" in prepared.stdout
    assert (root / ".uwa_codex_acceptance").is_file()
