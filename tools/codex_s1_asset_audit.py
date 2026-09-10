#!/usr/bin/env python3
"""Audit non-Python path literals referenced by the S1 bridge closure."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = Path.home() / ".uwa" / "s1-audit"
OUTPUT = REPO / "s1-asset-report.json"
PATH_HINT = re.compile(r"(?:^|/)(?:config|scripts|static|templates|assets|resources)/|\.(?:json|js|html|css)$", re.I)


def latest_manifest() -> Path:
    candidates = sorted(PRIVATE_ROOT.glob("*/manifest.json"))
    if not candidates:
        raise SystemExit("S1_ASSET_NO_MANIFEST")
    return candidates[-1]


def safe_rel(value: str) -> str | None:
    text = str(value or "").strip().replace("\\", "/")
    if not text or text.startswith(("http://", "https://", "data:")):
        return None
    if text.startswith("./"):
        text = text[2:]
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path.as_posix()


def main() -> int:
    manifest = json.loads(latest_manifest().read_text(encoding="utf-8"))
    reachable = manifest.get("static_reachable") or []
    if not isinstance(reachable, list):
        raise SystemExit("S1_ASSET_BAD_MANIFEST")

    literals: set[str] = set()
    owners: dict[str, set[str]] = {}
    for rel in reachable:
        source = REPO / str(rel)
        if not source.is_file() or source.suffix != ".py":
            continue
        try:
            tree = ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(rel))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            raw = node.value.strip()
            if not PATH_HINT.search(raw):
                continue
            normalized = safe_rel(raw)
            if normalized is None:
                continue
            literals.add(normalized)
            owners.setdefault(normalized, set()).add(str(rel))

    existing = []
    missing = []
    for item in sorted(literals):
        path = REPO / item
        record = {"path": item, "owners": sorted(owners.get(item, set()))}
        if path.exists():
            record["kind"] = "directory" if path.is_dir() else "file"
            existing.append(record)
        else:
            missing.append(record)

    config_files = sorted(
        path.relative_to(REPO).as_posix()
        for path in (REPO / "config").glob("*")
        if path.is_file()
    ) if (REPO / "config").is_dir() else []

    payload = {
        "schema": 1,
        "source_baseline": "main:a140002e65a02a3323abcde3e1fdb8674710c996",
        "referenced_existing_paths": existing,
        "referenced_missing_or_dynamic_paths": missing,
        "current_config_files": config_files,
        "counts": {
            "path_literals": len(literals),
            "referenced_existing_paths": len(existing),
            "referenced_missing_or_dynamic_paths": len(missing),
            "current_config_files": len(config_files),
        },
        "note": "Literal scan is conservative. Dynamic config-derived assets remain required until S2 parity tests prove they can be reduced.",
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for key, value in payload["counts"].items():
        print(f"S1_ASSET_{key.upper()}={value}")
    print("S1_ASSET_AUDIT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
