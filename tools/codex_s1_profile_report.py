#!/usr/bin/env python3
"""Export a compact, sanitized coupling profile for standalone extraction planning."""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SAFE = REPO / "tools" / "codex_s1_dependency_audit_safe.py"
CHAT = REPO / "app" / "api" / "chat.py"
OUTPUT = REPO / "s1-profile-report.json"
TARGETS = [
    "app/api/__init__.py",
    "app/api/routes.py",
    "app/api/chat.py",
    "app/api/anthropic_routes.py",
    "app/api/browser_routes.py",
    "app/api/cmd_routes.py",
    "app/api/config_routes.py",
    "app/api/provider.py",
    "app/api/system.py",
    "app/api/tab_routes.py",
    "app/services/catalog_routing.py",
    "app/services/command_engine.py",
    "app/services/arena_direct_models.py",
    "app/core/parsers/__init__.py",
    "app/core/parsers/registry.py",
]
CHAT_ROOTS = {
    "ResponsesRequest",
    "_build_responses_object",
    "_load_responses_state",
    "_new_response_id",
    "_responses_completion_status_from_chat_payload",
    "_responses_error_payload",
    "_responses_request_to_chat_request",
    "_run_chat_completion_final",
    "_store_responses_state",
    "create_response",
    "verify_auth",
}


def load_safe():
    spec = importlib.util.spec_from_file_location("codex_s1_safe_profile", SAFE)
    if spec is None or spec.loader is None:
        raise SystemExit("S1_PROFILE_IMPORT_FAIL")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def shortest(graph, seeds, target):
    queue = deque((seed, [seed]) for seed in seeds)
    seen = set()
    while queue:
        node, path = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        if node == target:
            return [rel(item) for item in path]
        for nxt in sorted(graph.get(node, set())):
            if nxt not in seen:
                queue.append((nxt, path + [nxt]))
    return []


def bound_names(node: ast.AST) -> set[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return {target.id for target in targets if isinstance(target, ast.Name)}
    return set()


def chat_slice():
    tree = ast.parse(CHAT.read_text(encoding="utf-8-sig"), filename="app/api/chat.py")
    definitions = {}
    imports = {}
    for node in tree.body:
        for name in bound_names(node):
            definitions[name] = node
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.asname or alias.name.split(".", 1)[0]] = (alias.name, "")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if alias.name != "*":
                    imports[alias.asname or alias.name] = (module, alias.name)

    missing = sorted(CHAT_ROOTS - set(definitions))
    if missing:
        raise SystemExit("S1_PROFILE_CHAT_ROOT_MISSING")

    selected = set()
    used_imports = {}
    queue = deque(sorted(CHAT_ROOTS))
    while queue:
        name = queue.popleft()
        if name in selected or name not in definitions:
            continue
        selected.add(name)
        loaded = {
            item.id
            for item in ast.walk(definitions[name])
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        }
        for dep in loaded:
            if dep in definitions and dep not in selected:
                queue.append(dep)
            if dep in imports:
                used_imports[dep] = imports[dep]

    local = sorted({module for module, _ in used_imports.values() if module.startswith("app.")})
    external = sorted({module.split(".", 1)[0] for module, _ in used_imports.values() if module and not module.startswith("app.")})
    return {
        "root_symbols": sorted(CHAT_ROOTS),
        "selected_symbols": sorted(selected),
        "local_import_modules": local,
        "external_import_roots": external,
    }


def main() -> int:
    safe = load_safe()
    base = safe.base
    files = base.python_files()
    graph, _, parse_errors = safe.bom_safe_static_graph(files)
    if parse_errors:
        raise SystemExit("S1_PROFILE_PARSE_ERROR")
    seeds = [REPO / item for item in base.SEED_FILES if (REPO / item).is_file()]

    paths = {}
    for target_text in TARGETS:
        target = REPO / target_text
        paths[target_text] = shortest(graph, seeds, target) if target.is_file() else []

    payload = {
        "schema": 1,
        "source_baseline": "main:a140002e65a02a3323abcde3e1fdb8674710c996",
        "dependency_paths": paths,
        "chat_symbol_slice": chat_slice(),
        "package_side_effect_findings": {
            "app/api/__init__.py": "imports app.api.routes at package import time",
            "app/core/parsers/__init__.py": "imports and registers every built-in parser at package import time",
        },
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"S1_PROFILE_TARGET_COUNT={len(paths)}")
    print(f"S1_PROFILE_CHAT_SYMBOL_COUNT={len(payload['chat_symbol_slice']['selected_symbols'])}")
    print(f"S1_PROFILE_CHAT_LOCAL_IMPORT_COUNT={len(payload['chat_symbol_slice']['local_import_modules'])}")
    print("S1_PROFILE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
