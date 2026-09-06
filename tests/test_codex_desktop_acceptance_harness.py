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

    # These fixtures must start red so the live Codex run proves real edits/tests.
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
