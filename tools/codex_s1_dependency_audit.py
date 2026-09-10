#!/usr/bin/env python3
"""S1 dependency/import/runtime audit for the post-main Codex Web Bridge extraction.

The audit is read-only with respect to the repository. It builds a static local import
closure from release-critical bridge entry points, classifies reachable files, records
external import roots, and performs a controlled import-only runtime smoke in a child
Python process. Results are written only to private ~/.uwa state.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
from collections import deque
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "codex-standalone-s1"
PRIVATE_ROOT = Path.home() / ".uwa" / "s1-audit"

SEED_FILES = [
    "app/api/codex_responses_v2.py",
    "app/api/codex_compact.py",
    "app/api/codex_compat.py",
    "app/services/chatgpt_web_mode.py",
    "app/services/chatgpt_web_prepare.py",
    "app/services/client_tool_policy.py",
    "app/services/codex_metadata_helper.py",
    "app/services/codex_network_tuning.py",
    "app/services/codex_remote_compaction_v2.py",
    "app/services/codex_required_tool_language_patch.py",
    "app/services/codex_responses_state.py",
    "app/services/codex_stream_compat.py",
    "app/services/codex_v2_runtime_hardening.py",
    "app/services/codex_web_policy.py",
    "app/services/codex_web_session_affinity.py",
    "app/services/codex_wire_observability.py",
    "app/services/codex_workspace_refusal_language_patch.py",
    "app/services/tool_calling.py",
    "app/core/workflow/executor_send.py",
    "tools/codex_provider_switch.py",
    "tools/codex_uwa_lifecycle.py",
    "tools/install_codex_uwa_commands.py",
    "tools/public_repo_safety_check.py",
]

RUNTIME_SMOKE_MODULES = [
    "app.api.codex_responses_v2",
    "app.api.codex_compact",
    "app.services.codex_remote_compaction_v2",
    "app.services.codex_wire_observability",
    "app.services.codex_web_session_affinity",
    "app.services.client_tool_policy",
]

CORE_PREFIXES = (
    "app/api/codex_",
    "app/services/codex_",
    "app/services/chatgpt_web_",
    "app/services/client_tool_policy.py",
    "app/services/tool_calling.py",
    "app/core/workflow/executor_send.py",
    "tools/codex_",
    "tools/install_codex_uwa_commands.py",
    "tools/public_repo_safety_check.py",
    "tests/test_codex_",
    "tests/test_client_tool_policy",
)

SKIP_PARTS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
}


def run(args: list[str], *, timeout: int = 60, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(REPO),
        text=True,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def git_text(*args: str) -> str:
    result = run(["git", *args], timeout=30)
    if result.returncode != 0:
        raise SystemExit("S1_GIT_COMMAND_FAILED")
    return result.stdout.strip()


def require_repo_state() -> tuple[str, str]:
    branch = git_text("branch", "--show-current")
    dirty = git_text("status", "--porcelain", "--untracked-files=all")
    head = git_text("rev-parse", "HEAD")
    print(f"S1_PROJECT_BRANCH={branch or 'DETACHED'}")
    print("S1_REPOSITORY_CLEAN=" + ("YES" if not dirty else "NO"))
    if branch != EXPECTED_BRANCH:
        raise SystemExit("S1_WRONG_BRANCH")
    if dirty:
        raise SystemExit("S1_DIRTY_REPOSITORY")
    return branch, head


def python_files() -> list[Path]:
    found: list[Path] = []
    for path in REPO.rglob("*.py"):
        try:
            rel = path.relative_to(REPO)
        except ValueError:
            continue
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if path.is_file():
            found.append(path)
    return sorted(found)


def module_name(path: Path) -> str:
    rel = path.relative_to(REPO)
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build_module_index(files: Iterable[Path]) -> tuple[dict[str, Path], dict[Path, str]]:
    by_module: dict[str, Path] = {}
    by_path: dict[Path, str] = {}
    for path in files:
        mod = module_name(path)
        if mod:
            by_module[mod] = path
            by_path[path] = mod
    return by_module, by_path


def imported_candidates(tree: ast.AST, current_module: str) -> set[str]:
    result: set[str] = set()
    package_parts = current_module.split(".")[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.add(alias.name)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            keep = max(0, len(package_parts) - node.level + 1)
            prefix_parts = package_parts[:keep]
            if node.module:
                prefix_parts += node.module.split(".")
            base = ".".join(prefix_parts)
        else:
            base = node.module or ""
        if base:
            result.add(base)
        for alias in node.names:
            if alias.name == "*":
                continue
            candidate = f"{base}.{alias.name}" if base else alias.name
            result.add(candidate)
    return result


def resolve_local(name: str, by_module: dict[str, Path]) -> Path | None:
    candidate = name
    while candidate:
        if candidate in by_module:
            return by_module[candidate]
        if "." not in candidate:
            break
        candidate = candidate.rsplit(".", 1)[0]
    return None


def static_graph(files: list[Path]) -> tuple[dict[Path, set[Path]], dict[Path, set[str]], list[str]]:
    by_module, by_path = build_module_index(files)
    graph: dict[Path, set[Path]] = {path: set() for path in files}
    externals: dict[Path, set[str]] = {path: set() for path in files}
    parse_errors: list[str] = []
    stdlib = set(getattr(sys, "stdlib_module_names", set()))
    for path in files:
        rel = path.relative_to(REPO).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            parse_errors.append(f"{rel}:{type(exc).__name__}")
            continue
        current = by_path.get(path, "")
        for name in imported_candidates(tree, current):
            local = resolve_local(name, by_module)
            if local is not None and local != path:
                graph[path].add(local)
                continue
            root = name.split(".", 1)[0]
            if root and root not in stdlib and root not in {"__future__"}:
                externals[path].add(root)
    return graph, externals, parse_errors


def closure(graph: dict[Path, set[Path]], seeds: list[Path]) -> set[Path]:
    seen: set[Path] = set()
    queue: deque[Path] = deque(seeds)
    while queue:
        path = queue.popleft()
        if path in seen:
            continue
        seen.add(path)
        queue.extend(sorted(graph.get(path, set()) - seen))
    return seen


def classify(path: Path) -> str:
    rel = path.relative_to(REPO).as_posix()
    if rel.startswith(CORE_PREFIXES):
        return "core"
    if rel.startswith("tests/"):
        return "validation"
    if rel.startswith("tools/"):
        return "validation_or_operator"
    if rel.startswith("app/"):
        return "required_upstream_runtime"
    return "required_support"


def parse_requirements() -> list[str]:
    path = REPO / "requirements.txt"
    if not path.is_file():
        return []
    names: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        line = line.split(";", 1)[0].strip()
        match = re.match(r"([A-Za-z0-9_.-]+)", line)
        if match:
            names.append(match.group(1))
    return sorted(dict.fromkeys(names), key=str.lower)


def runtime_smoke(python_executable: str) -> dict[str, object]:
    probe = r'''
import importlib
import json
import pathlib
import sys

repo = pathlib.Path.cwd().resolve()
modules = json.loads(sys.stdin.read())
errors = {}
for name in modules:
    try:
        importlib.import_module(name)
    except Exception as exc:
        errors[name] = type(exc).__name__ + ":" + str(exc)[:240]
local = set()
external_roots = set()
stdlib = set(getattr(sys, "stdlib_module_names", set()))
for name, module in list(sys.modules.items()):
    if not name or module is None:
        continue
    file_value = getattr(module, "__file__", None)
    if file_value:
        try:
            path = pathlib.Path(file_value).resolve()
            path.relative_to(repo)
            local.add(path.relative_to(repo).as_posix())
            continue
        except Exception:
            pass
    root = name.split(".", 1)[0]
    if root and root not in stdlib and root not in {"__main__", "builtins"}:
        external_roots.add(root)
print(json.dumps({"errors": errors, "local_files": sorted(local), "external_roots": sorted(external_roots)}))
'''
    result = run(
        [python_executable, "-c", probe],
        timeout=120,
        input_text=json.dumps(RUNTIME_SMOKE_MODULES),
    )
    payload: dict[str, object]
    if result.returncode != 0:
        payload = {
            "errors": {"probe": f"subprocess_rc_{result.returncode}"},
            "local_files": [],
            "external_roots": [],
        }
    else:
        try:
            payload = json.loads(result.stdout.strip().splitlines()[-1])
        except Exception:
            payload = {"errors": {"probe": "invalid_json"}, "local_files": [], "external_roots": []}
    payload["returncode"] = result.returncode
    return payload


def private_output_dir(head: str) -> Path:
    PRIVATE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        PRIVATE_ROOT.chmod(0o700)
    except OSError:
        pass
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    suffix = hashlib.sha256((head + stamp).encode()).hexdigest()[:8]
    path = PRIVATE_ROOT / f"{stamp}-{suffix}"
    path.mkdir(mode=0o700)
    return path


def write_private(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--no-runtime", action="store_true")
    args = parser.parse_args()

    print("S1_DEPENDENCY_AUDIT_BEGIN")
    _, head = require_repo_state()
    files = python_files()
    graph, externals, parse_errors = static_graph(files)

    missing_seeds = [rel for rel in SEED_FILES if not (REPO / rel).is_file()]
    print(f"S1_PYTHON_FILE_COUNT={len(files)}")
    print(f"S1_SEED_FILE_COUNT={len(SEED_FILES)}")
    print("S1_SEEDS_PRESENT=" + ("YES" if not missing_seeds else "NO"))
    print(f"S1_PARSE_ERROR_COUNT={len(parse_errors)}")
    if missing_seeds or parse_errors:
        print("S1_DEPENDENCY_AUDIT=FAIL")
        return 1

    seed_paths = [REPO / rel for rel in SEED_FILES]
    reachable = closure(graph, seed_paths)
    classified: dict[str, list[str]] = {}
    for path in sorted(reachable):
        classified.setdefault(classify(path), []).append(path.relative_to(REPO).as_posix())

    external_roots = sorted(
        {
            root
            for path in reachable
            for root in externals.get(path, set())
        }
    )
    requirements = parse_requirements()

    runtime: dict[str, object] = {
        "returncode": None,
        "errors": {},
        "local_files": [],
        "external_roots": [],
    }
    if not args.no_runtime:
        runtime = runtime_smoke(args.python)
    runtime_errors = runtime.get("errors") if isinstance(runtime, dict) else {"probe": "unknown"}
    runtime_ok = args.no_runtime or (runtime.get("returncode") == 0 and not runtime_errors)

    print(f"S1_STATIC_REACHABLE_FILE_COUNT={len(reachable)}")
    print(f"S1_CORE_FILE_COUNT={len(classified.get('core', []))}")
    print(f"S1_REQUIRED_UPSTREAM_RUNTIME_FILE_COUNT={len(classified.get('required_upstream_runtime', []))}")
    print(f"S1_REQUIRED_SUPPORT_FILE_COUNT={len(classified.get('required_support', []))}")
    print(f"S1_EXTERNAL_IMPORT_ROOT_COUNT={len(external_roots)}")
    print(f"S1_REQUIREMENTS_ENTRY_COUNT={len(requirements)}")
    print("S1_RUNTIME_SMOKE=" + ("SKIPPED" if args.no_runtime else ("PASS" if runtime_ok else "FAIL")))
    if not args.no_runtime:
        local_runtime = runtime.get("local_files", []) if isinstance(runtime, dict) else []
        ext_runtime = runtime.get("external_roots", []) if isinstance(runtime, dict) else []
        print(f"S1_RUNTIME_LOCAL_FILE_COUNT={len(local_runtime) if isinstance(local_runtime, list) else 0}")
        print(f"S1_RUNTIME_EXTERNAL_ROOT_COUNT={len(ext_runtime) if isinstance(ext_runtime, list) else 0}")
        print(f"S1_RUNTIME_IMPORT_ERROR_COUNT={len(runtime_errors) if isinstance(runtime_errors, dict) else 1}")

    output = private_output_dir(head)
    manifest = {
        "schema": 1,
        "source_head": head,
        "branch": EXPECTED_BRANCH,
        "seed_files": SEED_FILES,
        "runtime_smoke_modules": RUNTIME_SMOKE_MODULES,
        "static_reachable": sorted(path.relative_to(REPO).as_posix() for path in reachable),
        "classification": classified,
        "external_import_roots": external_roots,
        "requirements_entries": requirements,
        "runtime_smoke": runtime,
        "parse_errors": parse_errors,
        "missing_seeds": missing_seeds,
    }
    write_private(output / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    summary_lines = [
        "# S1 private dependency audit summary",
        "",
        f"Source head: `{head}`",
        f"Static reachable Python files: {len(reachable)}",
        f"Core files: {len(classified.get('core', []))}",
        f"Required upstream runtime files: {len(classified.get('required_upstream_runtime', []))}",
        f"External import roots: {len(external_roots)}",
        f"Runtime smoke: {'SKIPPED' if args.no_runtime else ('PASS' if runtime_ok else 'FAIL')}",
        "",
        "The full manifest remains private local audit state and is not intended for commit.",
    ]
    write_private(output / "summary.md", "\n".join(summary_lines) + "\n")
    print("S1_PRIVATE_MANIFEST_WRITTEN=YES")
    print("S1_PRIVATE_OUTPUT_MODE=LOCAL_ONLY")

    passed = not missing_seeds and not parse_errors and runtime_ok and len(reachable) > 0
    print("S1_DEPENDENCY_AUDIT=" + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
