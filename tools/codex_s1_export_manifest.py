#!/usr/bin/env python3
"""Export a sanitized standalone-candidate manifest from the newest S1 audit."""

from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = Path.home() / ".uwa" / "s1-audit"
OUTPUT = REPO / "s1-public-manifest.json"
SKIP_PARTS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}


def latest_manifest() -> Path:
    candidates = sorted(PRIVATE_ROOT.glob("*/manifest.json"))
    if not candidates:
        raise SystemExit("S1_EXPORT_NO_PRIVATE_MANIFEST")
    return candidates[-1]


def safe_paths(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        text = str(value)
        path = Path(text)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit("S1_EXPORT_UNSAFE_PATH")
        out.append(path.as_posix())
    return sorted(dict.fromkeys(out))


def safe_names(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def repo_python_files() -> list[str]:
    result: list[str] = []
    for path in REPO.rglob("*.py"):
        rel = path.relative_to(REPO)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if path.is_file():
            result.append(rel.as_posix())
    return sorted(result)


def validation_files(all_python: list[str]) -> list[str]:
    result: list[str] = []
    for path in all_python:
        if path.startswith("tests/test_codex_"):
            result.append(path)
        elif path.startswith("tests/test_chatgpt_web_"):
            result.append(path)
        elif path.startswith("tests/test_client_tool_policy"):
            result.append(path)
        elif path in {"tests/test_install_codex_uwa_commands.py", "tests/test_security_hardening.py"}:
            result.append(path)
    return sorted(dict.fromkeys(result))


def main() -> int:
    private = json.loads(latest_manifest().read_text(encoding="utf-8"))
    classification = private.get("classification") or {}
    runtime = private.get("runtime_smoke") or {}
    if not isinstance(classification, dict) or not isinstance(runtime, dict):
        raise SystemExit("S1_EXPORT_BAD_PRIVATE_MANIFEST")

    core = safe_paths(classification.get("core", []))
    required_upstream = safe_paths(classification.get("required_upstream_runtime", []))
    required_support = safe_paths(classification.get("required_support", []))
    static_reachable = safe_paths(private.get("static_reachable", []))
    runtime_local = safe_paths(runtime.get("local_files", []))
    static_external = safe_names(private.get("external_import_roots", []))
    runtime_external = safe_names(runtime.get("external_roots", []))
    all_python = repo_python_files()
    validation = validation_files(all_python)

    static_set = set(static_reachable)
    runtime_set = set(runtime_local)
    validation_set = set(validation)
    runtime_only = sorted(runtime_set - static_set)
    exclude_python = sorted(set(all_python) - static_set - runtime_set - validation_set)

    generic_api_shell = sorted(
        path for path in (static_set | runtime_set)
        if path in {
            "app/api/anthropic_routes.py",
            "app/api/browser_routes.py",
            "app/api/cmd_routes.py",
            "app/api/config_routes.py",
            "app/api/provider.py",
            "app/api/routes.py",
            "app/api/system.py",
            "app/api/tab_routes.py",
        }
    )

    payload = {
        "schema": 2,
        "source_baseline": "main:a140002e65a02a3323abcde3e1fdb8674710c996",
        "audit_branch": "codex-standalone-s1",
        "core": core,
        "required_upstream_runtime_provisional": required_upstream,
        "required_support_provisional": required_support,
        "static_reachable": static_reachable,
        "runtime_loaded": runtime_local,
        "runtime_only_side_effect_candidates": runtime_only,
        "validation": validation,
        "generic_api_shell_coupling_candidates": generic_api_shell,
        "python_exclusion_candidates": exclude_python,
        "static_external_import_roots": static_external,
        "runtime_external_import_roots": runtime_external,
        "requirements_current": safe_names(private.get("requirements_entries", [])),
        "counts": {
            "all_python": len(all_python),
            "core": len(core),
            "required_upstream_runtime_provisional": len(required_upstream),
            "required_support_provisional": len(required_support),
            "static_reachable": len(static_reachable),
            "runtime_loaded": len(runtime_local),
            "runtime_only_side_effect_candidates": len(runtime_only),
            "validation": len(validation),
            "generic_api_shell_coupling_candidates": len(generic_api_shell),
            "python_exclusion_candidates": len(exclude_python),
            "static_external_import_roots": len(static_external),
            "runtime_external_import_roots": len(runtime_external),
        },
        "notes": [
            "required_upstream_runtime_provisional is an integration-tree closure, not the final standalone keep-set",
            "runtime_only_side_effect_candidates records import-time package/registry side effects that need explicit review",
            "python_exclusion_candidates are evidence-backed candidates only; S2 must still preserve non-Python runtime assets and licensing",
        ],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("S1_EXPORT_PATH=s1-public-manifest.json")
    for key, value in payload["counts"].items():
        print(f"S1_EXPORT_{key.upper()}={value}")
    print("S1_EXPORT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
