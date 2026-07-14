#!/usr/bin/env python3
"""Initialize a durable founder workspace from the plugin templates."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    plugin_root = Path(__file__).resolve().parents[1]
    templates = plugin_root / "assets" / "templates"
    if not templates.is_dir():
        raise SystemExit(f"template directory missing: {templates}")

    args.target.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    skipped: list[str] = []
    for source in sorted(templates.iterdir()):
        if not source.is_file():
            continue
        destination = args.target / source.name
        if destination.exists() and not args.force:
            skipped.append(source.name)
            continue
        shutil.copy2(source, destination)
        created.append(source.name)

    print(f"target: {args.target.resolve()}")
    print(f"created_or_replaced: {len(created)}")
    for name in created:
        print(f"  + {name}")
    print(f"skipped_existing: {len(skipped)}")
    for name in skipped:
        print(f"  = {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
