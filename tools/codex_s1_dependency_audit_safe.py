#!/usr/bin/env python3
"""Fail-closed S1 wrapper with BOM-safe parsing and reachability-aware errors."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BASE = REPO / "tools" / "codex_s1_dependency_audit.py"


def load_base():
    spec = importlib.util.spec_from_file_location("codex_s1_dependency_audit_base", BASE)
    if spec is None or spec.loader is None:
        raise SystemExit("S1_SAFE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_base()


def bom_safe_static_graph(files):
    by_module, by_path = base.build_module_index(files)
    graph = {path: set() for path in files}
    externals = {path: set() for path in files}
    parse_errors = []
    stdlib = set(getattr(sys, "stdlib_module_names", set()))

    for path in files:
        rel = path.relative_to(base.REPO).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=rel)
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            parse_errors.append(f"{rel}:{type(exc).__name__}")
            continue
        current = by_path.get(path, "")
        for name in base.imported_candidates(tree, current):
            local = base.resolve_local(name, by_module)
            if local is not None and local != path:
                graph[path].add(local)
                continue
            root = name.split(".", 1)[0]
            if root and root not in stdlib and root not in {"__future__"}:
                externals[path].add(root)

    seed_paths = [base.REPO / rel for rel in base.SEED_FILES if (base.REPO / rel).is_file()]
    reachable = base.closure(graph, seed_paths)
    reachable_rel = {path.relative_to(base.REPO).as_posix() for path in reachable}

    blocking = []
    ignored = []
    for item in parse_errors:
        rel = item.split(":", 1)[0]
        if rel in reachable_rel:
            blocking.append(item)
        else:
            ignored.append(item)

    print(f"S1_GLOBAL_PARSE_ERROR_COUNT={len(parse_errors)}")
    print(f"S1_UNREACHABLE_PARSE_ERROR_COUNT={len(ignored)}")
    for item in ignored:
        print(f"S1_UNREACHABLE_PARSE_ERROR={item}")
    print(f"S1_REACHABLE_PARSE_ERROR_COUNT={len(blocking)}")
    for item in blocking:
        print(f"S1_REACHABLE_PARSE_ERROR={item}")
    return graph, externals, blocking


base.static_graph = bom_safe_static_graph


if __name__ == "__main__":
    raise SystemExit(base.main())
