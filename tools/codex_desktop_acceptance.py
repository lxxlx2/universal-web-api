#!/usr/bin/env python3
"""Safe, repeatable live acceptance harness for the Codex Desktop web bridge.

The harness creates an isolated workspace under the current user's home directory.
It never touches an existing directory unless that directory contains this tool's
marker file. The generated fixture is intentionally small and contains no secrets.

Typical use:
    python3 tools/codex_desktop_acceptance.py setup
    python3 tools/codex_desktop_acceptance.py prompts
    python3 tools/codex_desktop_acceptance.py check
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


DEFAULT_ROOT = Path.home() / "uwa-codex-acceptance"
MARKER = ".uwa_codex_acceptance"
CONTEXT_TOKEN = "EMBER-7319"


PROMPTS: Dict[str, str] = {
    "multi_file": (
        "先检查当前工作区的 multi_file。修复其中的实现，使 "
        "python3 -m unittest discover -s multi_file/tests -v 全部通过。"
        "必须实际读取文件、修改至少两个实现文件并实际运行测试。"
        "不要修改测试文件。完成后简要汇报修改和测试结果。"
    ),
    "failure_recovery": (
        "处理 failure_recovery：先原样运行 "
        "python3 -m unittest discover -s failure_recovery/tests -v 获取真实失败，"
        "再根据失败定位并修复实现，最后重新运行同一测试直到通过。"
        "不要修改测试。必须保留首次失败和最终成功这两个真实执行步骤。"
    ),
    "git_diff": (
        "处理 git_diff：按 git_diff/REQUIREMENTS.txt 修改实现并运行 "
        "python3 -m unittest discover -s git_diff/tests -v。"
        "随后实际运行 git diff --check 和 git diff -- git_diff，确认只有预期实现文件变化。"
        "不要提交 git commit，也不要修改测试或 REQUIREMENTS.txt。"
    ),
    "interactive": (
        "验证长命令和交互工具：从当前工作区启动 python3 interactive/worker.py。"
        "它会输出 READY 后等待标准输入。不要终止它；使用客户端提供的持续进程/写入标准输入工具"
        "向同一进程发送 GO 加换行，等待它退出并输出 INTERACTIVE_PASS。"
        "最后读取 interactive/result.txt 确认内容为 INTERACTIVE_PASS。"
    ),
    "context_1": (
        f"这是上下文连续性测试第一轮。只记住令牌 {CONTEXT_TOKEN}，不要把它写入任何文件，"
        "不要调用工具，只回复 CONTEXT_READY。"
    ),
    "context_2": (
        "这是同一个 Codex 对话的第二轮。不要向我询问上一轮令牌。"
        "使用上一轮上下文记住的令牌，创建 context/result.txt，文件只包含该令牌和一个换行。"
        "然后实际读取文件确认内容，并回复 CONTEXT_PASS。"
    ),
}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(
    args: List[str],
    *,
    cwd: Path,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def _guard_root(root: Path, *, allow_create: bool) -> None:
    root = root.expanduser().resolve()
    if not root.exists():
        if allow_create:
            return
        raise SystemExit(f"Acceptance workspace does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Acceptance workspace path is not a directory: {root}")
    if not (root / MARKER).is_file():
        raise SystemExit(
            "Refusing to touch an existing unmarked directory. "
            f"Choose another --root or remove it yourself: {root}"
        )


def _reset_root(root: Path) -> Path:
    root = root.expanduser().resolve()
    _guard_root(root, allow_create=True)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    _write(root / MARKER, "UWA Codex Desktop acceptance workspace\n")
    return root


def _build_multi_file(root: Path) -> None:
    _write(root / "multi_file" / "__init__.py", "")
    _write(
        root / "multi_file" / "math_ops.py",
        "def add(a, b):\n    return a - b\n\n\ndef multiply(a, b):\n    return a + b\n",
    )
    _write(
        root / "multi_file" / "summary.py",
        "def render_total(value):\n    return f\"TOTAL={value}\"\n",
    )
    _write(
        root / "multi_file" / "tests" / "test_multi_file.py",
        "import unittest\n\n"
        "from multi_file.math_ops import add, multiply\n"
        "from multi_file.summary import render_total\n\n\n"
        "class MultiFileTests(unittest.TestCase):\n"
        "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n\n"
        "    def test_multiply(self):\n        self.assertEqual(multiply(4, 5), 20)\n\n"
        "    def test_summary(self):\n        self.assertEqual(render_total(20), \"Total: 20\")\n\n\n"
        "if __name__ == \"__main__\":\n    unittest.main()\n",
    )


def _build_failure_recovery(root: Path) -> None:
    _write(root / "failure_recovery" / "__init__.py", "")
    _write(
        root / "failure_recovery" / "parser.py",
        "def parse_port(value):\n"
        "    if not isinstance(value, str) or not value.isdigit():\n"
        "        raise ValueError(\"invalid port\")\n"
        "    port = int(value)\n"
        "    if port < 1 or port > 65535:\n"
        "        raise ValueError(\"invalid port\")\n"
        "    return port\n",
    )
    _write(
        root / "failure_recovery" / "tests" / "test_parser.py",
        "import unittest\n\n"
        "from failure_recovery.parser import parse_port\n\n\n"
        "class ParserTests(unittest.TestCase):\n"
        "    def test_accepts_surrounding_whitespace(self):\n"
        "        self.assertEqual(parse_port(\" 8199 \"), 8199)\n\n"
        "    def test_rejects_out_of_range(self):\n"
        "        with self.assertRaises(ValueError):\n"
        "            parse_port(\"70000\")\n\n\n"
        "if __name__ == \"__main__\":\n    unittest.main()\n",
    )


def _build_git_diff(root: Path) -> None:
    _write(root / "git_diff" / "__init__.py", "")
    _write(root / "git_diff" / "config.py", 'MODE = "dev"\nTIMEOUT = 5\n')
    _write(
        root / "git_diff" / "REQUIREMENTS.txt",
        "MODE must be prod.\nTIMEOUT must be 30 seconds.\n",
    )
    _write(
        root / "git_diff" / "tests" / "test_config.py",
        "import unittest\n\n"
        "from git_diff.config import MODE, TIMEOUT\n\n\n"
        "class ConfigTests(unittest.TestCase):\n"
        "    def test_mode(self):\n        self.assertEqual(MODE, \"prod\")\n\n"
        "    def test_timeout(self):\n        self.assertEqual(TIMEOUT, 30)\n\n\n"
        "if __name__ == \"__main__\":\n    unittest.main()\n",
    )


def _build_interactive(root: Path) -> None:
    _write(
        root / "interactive" / "worker.py",
        "from pathlib import Path\n"
        "import sys\n\n"
        "print(\"READY\", flush=True)\n"
        "line = sys.stdin.readline().strip()\n"
        "if line != \"GO\":\n"
        "    print(f\"EXPECTED_GO_GOT={line!r}\", flush=True)\n"
        "    raise SystemExit(2)\n"
        "Path(\"interactive/result.txt\").write_text(\"INTERACTIVE_PASS\\n\", encoding=\"utf-8\")\n"
        "print(\"INTERACTIVE_PASS\", flush=True)\n",
    )


def _build_context(root: Path) -> None:
    (root / "context").mkdir(parents=True, exist_ok=True)


def _write_prompt_file(root: Path) -> None:
    lines = [
        "# Codex Desktop live acceptance prompts",
        "",
        "Run each scenario from a fresh Codex thread unless the prompt explicitly says otherwise.",
        "The two context prompts MUST be sent in the same thread.",
        "",
    ]
    for name, prompt in PROMPTS.items():
        lines.extend([f"## {name}", "", prompt, ""])
    _write(root / "PROMPTS.md", "\n".join(lines).rstrip() + "\n")


def _init_git(root: Path) -> None:
    if shutil.which("git") is None:
        raise SystemExit("git is required for the acceptance harness")
    _run(["git", "init", "-q"], cwd=root, check=True)
    _run(["git", "config", "user.name", "UWA Acceptance"], cwd=root, check=True)
    _run(["git", "config", "user.email", "uwa-acceptance@invalid.local"], cwd=root, check=True)
    _run(["git", "config", "commit.gpgsign", "false"], cwd=root, check=True)
    _run(["git", "add", "."], cwd=root, check=True)
    _run(["git", "commit", "-q", "-m", "acceptance baseline"], cwd=root, check=True)


def setup(root: Path) -> None:
    root = _reset_root(root)
    _build_multi_file(root)
    _build_failure_recovery(root)
    _build_git_diff(root)
    _build_interactive(root)
    _build_context(root)
    _write_prompt_file(root)
    _init_git(root)
    print(f"ACCEPTANCE_WORKSPACE={root}")
    print("SETUP_PASS")
    print(f"Open this folder as the Codex Desktop project: {root}")
    print(f"Prompts: {root / 'PROMPTS.md'}")


def show_prompts(root: Path, scenario: str | None = None) -> None:
    _guard_root(root, allow_create=False)
    if scenario:
        if scenario not in PROMPTS:
            raise SystemExit(f"Unknown scenario: {scenario}")
        print(PROMPTS[scenario])
        return
    for name, prompt in PROMPTS.items():
        print(f"===== {name} =====")
        print(prompt)
        print()


def _unit_test(root: Path, suite_dir: str) -> Tuple[bool, str]:
    result = _run(
        [sys.executable, "-m", "unittest", "discover", "-s", f"{suite_dir}/tests", "-v"],
        cwd=root,
    )
    return result.returncode == 0, result.stdout


def _changed_paths(root: Path) -> List[str]:
    result = _run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=root)
    changed: List[str] = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed.append(path)
    return changed


def _check_git_diff(root: Path) -> Tuple[bool, str]:
    expected = root / "git_diff" / "config.py"
    text = expected.read_text(encoding="utf-8") if expected.exists() else ""
    values_ok = 'MODE = "prod"' in text and "TIMEOUT = 30" in text

    diff_check = _run(["git", "diff", "--check"], cwd=root)
    changed = _changed_paths(root)
    allowed = {
        "git_diff/config.py",
        "multi_file/math_ops.py",
        "multi_file/summary.py",
        "failure_recovery/parser.py",
        "interactive/result.txt",
        "context/result.txt",
    }
    unexpected = sorted(name for name in changed if name not in allowed)
    ok = values_ok and diff_check.returncode == 0 and not unexpected
    detail = (
        f"values_ok={values_ok} diff_check={diff_check.returncode} "
        f"changed={changed} unexpected={unexpected}"
    )
    return ok, detail


def _check_interactive(root: Path) -> Tuple[bool, str]:
    path = root / "interactive" / "result.txt"
    actual = path.read_text(encoding="utf-8") if path.exists() else ""
    return actual == "INTERACTIVE_PASS\n", f"actual={actual!r}"


def _check_context(root: Path) -> Tuple[bool, str]:
    path = root / "context" / "result.txt"
    actual = path.read_text(encoding="utf-8") if path.exists() else ""
    return actual == CONTEXT_TOKEN + "\n", f"actual={actual!r}"


def check(root: Path, scenario: str | None = None) -> int:
    _guard_root(root, allow_create=False)
    checks = {
        "multi_file": lambda: _unit_test(root, "multi_file"),
        "failure_recovery": lambda: _unit_test(root, "failure_recovery"),
        "git_diff": lambda: _check_git_diff(root),
        "interactive": lambda: _check_interactive(root),
        "context": lambda: _check_context(root),
    }
    selected: Iterable[str]
    if scenario:
        normalized = "context" if scenario in {"context_1", "context_2"} else scenario
        if normalized not in checks:
            raise SystemExit(f"Unknown check scenario: {scenario}")
        selected = [normalized]
    else:
        selected = checks.keys()

    failed = 0
    for name in selected:
        ok, detail = checks[name]()
        status = "PASS" if ok else "FAIL"
        print(f"{name}: {status}")
        if not ok:
            failed += 1
            print(detail.rstrip())
    print("ACCEPTANCE_PASS" if failed == 0 else f"ACCEPTANCE_FAIL count={failed}")
    return 0 if failed == 0 else 1


def status(root: Path) -> None:
    _guard_root(root, allow_create=False)
    head = _run(["git", "rev-parse", "--short", "HEAD"], cwd=root)
    names = _run(["git", "status", "--short", "--untracked-files=all"], cwd=root)
    print(f"ROOT={root.expanduser().resolve()}")
    print(f"BASELINE={head.stdout.strip()}")
    print("WORKTREE:")
    print(names.stdout.rstrip() or "(clean)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "prompts", "check", "status"])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--scenario", default=None)
    args = parser.parse_args()

    if args.command == "setup":
        setup(args.root)
        return 0
    if args.command == "prompts":
        show_prompts(args.root, args.scenario)
        return 0
    if args.command == "check":
        return check(args.root, args.scenario)
    status(args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
