#!/usr/bin/env python3
"""Print sanitized shortest static dependency paths for S1 coupling review."""

from __future__ import annotations

import importlib.util
import sys
from collections import deque
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SAFE = REPO / "tools" / "codex_s1_dependency_audit_safe.py"
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
    "app/core/parsers/registry.py",
]


def load_safe():
    spec = importlib.util.spec_from_file_location("codex_s1_safe_trace", SAFE)
    if spec is None or spec.loader is None:
        raise SystemExit("S1_TRACE_IMPORT_FAIL")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def shortest(graph, seeds, target):
    queue = deque((seed, [seed]) for seed in seeds)
    seen = set()
    while queue:
        node, path = queue.popleft()
        if node in seen:
            continue
        seen.add(node)
        if node == target:
            return path
        for nxt in sorted(graph.get(node, set())):
            if nxt not in seen:
                queue.append((nxt, path + [nxt]))
    return None


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def main() -> int:
    safe = load_safe()
    base = safe.base
    files = base.python_files()
    graph, _, parse_errors = safe.bom_safe_static_graph(files)
    if parse_errors:
        print(f"S1_TRACE_PARSE_ERROR_COUNT={len(parse_errors)}")
        return 1
    seeds = [REPO / item for item in base.SEED_FILES if (REPO / item).is_file()]
    print("S1_TRACE_BEGIN")
    for target_text in TARGETS:
        target = REPO / target_text
        path = shortest(graph, seeds, target)
        if path is None:
            print(f"S1_TRACE|{target_text}|UNREACHABLE")
        else:
            print("S1_TRACE|" + target_text + "|" + " -> ".join(rel(item) for item in path))
    print("S1_TRACE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
