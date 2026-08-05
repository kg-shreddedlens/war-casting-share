# -*- coding: utf-8 -*-
"""Rebuild gallery_local.json paths from files already on disk under site/assets/galleries."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GAL = ROOT / "site" / "assets" / "galleries"
OUT = ROOT / "gallery_local.json"
REG = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")


def slugify(name: str) -> str:
    s = name.lower().replace("'", "").replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def main() -> None:
    local = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    names = set(local)
    if REG.exists():
        names |= set(json.loads(REG.read_text(encoding="utf-8")))
    # Also discover folders
    if GAL.exists():
        for d in GAL.iterdir():
            if d.is_dir():
                # reverse-map later via slug match
                pass

    slug_to_name = {slugify(n): n for n in names}
    updated = 0
    for folder in sorted(GAL.iterdir()) if GAL.exists() else []:
        if not folder.is_dir():
            continue
        name = slug_to_name.get(folder.name)
        if not name:
            # try title-case from slug
            continue
        files = sorted(
            [p for p in folder.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}],
            key=lambda p: p.name,
        )
        paths = [f"assets/galleries/{folder.name}/{p.name}" for p in files]
        prev = local.get(name) or []
        if len(paths) > len(prev):
            local[name] = paths
            updated += 1
            print(f"{name}: {len(prev)} -> {len(paths)}")
        elif not prev and paths:
            local[name] = paths
            updated += 1
            print(f"{name}: empty -> {len(paths)}")

    OUT.write_text(json.dumps(local, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = sorted(((k, len(v or [])) for k, v in local.items()), key=lambda x: -x[1])
    print("updated", updated)
    print("at25+", sum(1 for _, n in counts if n >= 25))
    print("under25", sum(1 for _, n in counts if n < 25))
    print("zero", sum(1 for _, n in counts if n == 0))


if __name__ == "__main__":
    main()
