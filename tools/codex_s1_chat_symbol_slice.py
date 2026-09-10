#!/usr/bin/env python3
"""Compute the top-level symbol/import slice of app/api/chat.py used by Codex routes."""

from __future__ import annotations

import ast
from collections import deque
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "app" / "api" / "chat.py"
ROOT_SYMBOLS = {
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


def bound_names(node: ast.AST) -> set[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        out: set[str] = set()
        for target in targets:
            if isinstance(target, ast.Name):
                out.add(target.id)
        return out
    return set()


def main() -> int:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"), filename="app/api/chat.py")
    definitions: dict[str, ast.AST] = {}
    imports: dict[str, tuple[str, str]] = {}

    for node in tree.body:
        for name in bound_names(node):
            definitions[name] = node
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                imports[bound] = (alias.name, "")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                if alias.name == "*":
                    continue
                imports[alias.asname or alias.name] = (module, alias.name)

    missing = sorted(ROOT_SYMBOLS - set(definitions))
    print(f"S1_CHAT_SLICE_ROOT_COUNT={len(ROOT_SYMBOLS)}")
    print("S1_CHAT_SLICE_ROOTS_PRESENT=" + ("YES" if not missing else "NO"))
    for name in missing:
        print(f"S1_CHAT_SLICE_MISSING_ROOT={name}")
    if missing:
        return 1

    selected: set[str] = set()
    used_imports: dict[str, tuple[str, str]] = {}
    queue = deque(sorted(ROOT_SYMBOLS))

    while queue:
        name = queue.popleft()
        if name in selected:
            continue
        node = definitions.get(name)
        if node is None:
            continue
        selected.add(name)
        loaded = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        for dep in sorted(loaded):
            if dep in definitions and dep not in selected:
                queue.append(dep)
            if dep in imports:
                used_imports[dep] = imports[dep]

    local_modules = sorted({module for module, _ in used_imports.values() if module.startswith("app.")})
    external_modules = sorted({module.split(".", 1)[0] for module, _ in used_imports.values() if module and not module.startswith("app.")})

    print(f"S1_CHAT_SLICE_SELECTED_SYMBOL_COUNT={len(selected)}")
    for name in sorted(selected):
        print(f"S1_CHAT_SYMBOL|{name}")
    print(f"S1_CHAT_SLICE_LOCAL_IMPORT_MODULE_COUNT={len(local_modules)}")
    for module in local_modules:
        print(f"S1_CHAT_LOCAL_IMPORT|{module}")
    print(f"S1_CHAT_SLICE_EXTERNAL_MODULE_COUNT={len(external_modules)}")
    for module in external_modules:
        print(f"S1_CHAT_EXTERNAL_IMPORT|{module}")
    print("S1_CHAT_SLICE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
