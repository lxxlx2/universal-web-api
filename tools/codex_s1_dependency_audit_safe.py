#!/usr/bin/env python3
"""Fail-closed S1 wrapper that ignores syntax errors outside the bridge closure."""

from __future__ import annotations

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
_original_static_graph = base.static_graph


def safe_static_graph(files):
    graph, externals, parse_errors = _original_static_graph(files)
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


base.static_graph = safe_static_graph


if __name__ == "__main__":
    raise SystemExit(base.main())
