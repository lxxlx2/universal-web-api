#!/usr/bin/env python3
"""Safely switch Codex config between UWA override and normal ChatGPT-account mode.

The `official` action removes only top-level UWA/provider/model pins from
`~/.codex/config.toml`. It deliberately keeps the `[model_providers.uwa]`
definition so switching back to UWA remains cheap, and it does not touch auth.
A timestamped backup is written before any modification.
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

ROOT_KEYS = {"model_provider", "model", "model_reasoning_effort"}


def default_config_path() -> Path:
    return Path.home() / ".codex" / "config.toml"


def _split_root_and_sections(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.lstrip().startswith("["):
            return lines[:index], lines[index:]
    return lines, []


def _key_name(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return ""
    return stripped.split("=", 1)[0].strip()


def official_text(text: str) -> str:
    root, sections = _split_root_and_sections(text)
    cleaned = [line for line in root if _key_name(line) not in ROOT_KEYS]
    return "".join(cleaned + sections)


def write_official(config_path: Path) -> tuple[Path | None, bool]:
    if not config_path.exists():
        return None, False

    original = config_path.read_text(encoding="utf-8")
    updated = official_text(original)
    if updated == original:
        return None, False

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = config_path.with_name(f"{config_path.name}.before-official-{timestamp}")
    shutil.copy2(config_path, backup)
    config_path.write_text(updated, encoding="utf-8")
    return backup, True


def top_level_status(text: str) -> dict[str, str]:
    root, _ = _split_root_and_sections(text)
    result: dict[str, str] = {}
    for line in root:
        key = _key_name(line)
        if key in ROOT_KEYS:
            result[key] = line.split("=", 1)[1].strip()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["official", "status"])
    parser.add_argument("--config", type=Path, default=default_config_path())
    args = parser.parse_args()

    path: Path = args.config.expanduser()

    if args.action == "status":
        if not path.exists():
            print(f"CONFIG={path}")
            print("STATUS=missing")
            return 0
        status = top_level_status(path.read_text(encoding="utf-8"))
        print(f"CONFIG={path}")
        for key in sorted(ROOT_KEYS):
            print(f"{key}={status.get(key, '<default>')}")
        return 0

    backup, changed = write_official(path)
    print(f"CONFIG={path}")
    print(f"OFFICIAL_MODE_CHANGED={'YES' if changed else 'NO'}")
    if backup is not None:
        print(f"BACKUP={backup}")
    print("NEXT=fully quit and reopen ChatGPT Desktop/Codex; sign in with ChatGPT if prompted; choose any model available to the account in the UI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
