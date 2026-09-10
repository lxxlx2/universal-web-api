#!/usr/bin/env python3
"""Emit a sanitized, CI-readable summary of the newest private S1 audit manifest."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path


PRIVATE_ROOT = Path.home() / ".uwa" / "s1-audit"


def latest_manifest() -> Path:
    candidates = sorted(PRIVATE_ROOT.glob("*/manifest.json"))
    if not candidates:
        raise SystemExit("S1_PUBLIC_REPORT_NO_MANIFEST")
    return candidates[-1]


def distributions_for_root(root: str) -> list[str]:
    try:
        mapping = importlib.metadata.packages_distributions()
    except Exception:
        return []
    return sorted(mapping.get(root, []) or [])


def safe_paths(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        text = str(value)
        if text.startswith("/") or ".." in Path(text).parts:
            raise SystemExit("S1_PUBLIC_REPORT_UNSAFE_PATH")
        result.append(text)
    return sorted(dict.fromkeys(result))


def main() -> int:
    payload = json.loads(latest_manifest().read_text(encoding="utf-8"))
    classification = payload.get("classification") or {}
    if not isinstance(classification, dict):
        raise SystemExit("S1_PUBLIC_REPORT_BAD_CLASSIFICATION")

    print("S1_PUBLIC_REPORT_BEGIN")
    for category in (
        "core",
        "required_upstream_runtime",
        "required_support",
        "validation",
        "validation_or_operator",
    ):
        paths = safe_paths(classification.get(category, []))
        print(f"S1_CATEGORY_{category.upper()}_COUNT={len(paths)}")
        for path in paths:
            print(f"S1_PATH|{category}|{path}")

    static_paths = safe_paths(payload.get("static_reachable", []))
    runtime = payload.get("runtime_smoke") or {}
    runtime_paths = safe_paths(runtime.get("local_files", []) if isinstance(runtime, dict) else [])
    print(f"S1_STATIC_REACHABLE_COUNT={len(static_paths)}")
    print(f"S1_RUNTIME_LOCAL_COUNT={len(runtime_paths)}")
    for path in runtime_paths:
        print(f"S1_RUNTIME_PATH|{path}")

    external_roots = sorted(str(x) for x in (payload.get("external_import_roots") or []))
    runtime_roots = sorted(
        str(x)
        for x in (
            runtime.get("external_roots", []) if isinstance(runtime, dict) else []
        )
    )
    all_roots = sorted(set(external_roots) | set(runtime_roots))
    print(f"S1_EXTERNAL_ROOT_COUNT={len(all_roots)}")
    for root in all_roots:
        dists = distributions_for_root(root)
        print(f"S1_EXTERNAL|{root}|{','.join(dists) if dists else 'UNMAPPED'}")

    requirements = sorted(str(x) for x in (payload.get("requirements_entries") or []))
    print(f"S1_REQUIREMENTS_COUNT={len(requirements)}")
    for item in requirements:
        print(f"S1_REQUIREMENT|{item}")

    print("S1_PUBLIC_REPORT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
