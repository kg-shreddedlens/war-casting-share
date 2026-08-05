# -*- coding: utf-8 -*-
"""Copy gallery/media faces into site headshots and wire registry.headshot for every actor."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCSWAMP = ROOT.parent
SITE_HS = ROOT / "site" / "assets" / "headshots"
SITE_GAL = ROOT / "site" / "assets" / "galleries"
MEDIA_HS = DOCSWAMP / "media" / "cast-headshots"
REG = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")


def slugify(name: str) -> str:
    s = name.lower().replace("'", "").replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def main() -> None:
    SITE_HS.mkdir(parents=True, exist_ok=True)
    MEDIA_HS.mkdir(parents=True, exist_ok=True)
    reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {}
    fixed = 0
    missing = []
    for name, rec in sorted(reg.items()):
        if name.startswith("CD Match"):
            continue
        slug = slugify(name)
        dest = SITE_HS / f"{slug}.jpg"
        src = None
        # prefer existing headshot files
        for p in (
            SITE_HS / f"{slug}.jpg",
            SITE_HS / f"{slug}.png",
            MEDIA_HS / f"{slug}.jpg",
            MEDIA_HS / f"{slug}.png",
        ):
            if p.exists() and p.stat().st_size > 2000:
                src = p
                break
        if src is None:
            gal = SITE_GAL / slug
            if gal.exists():
                for p in sorted(gal.glob("*")):
                    if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and p.stat().st_size > 2000:
                        src = p
                        break
        if src is None:
            hs = rec.get("headshot") or ""
            if hs.startswith("media/") and (DOCSWAMP / hs).exists():
                src = DOCSWAMP / hs
        if src is None:
            missing.append(name)
            continue
        if src.suffix.lower() in {".png", ".webp"}:
            dest = SITE_HS / f"{slug}{src.suffix.lower()}"
        try:
            if src.resolve() != dest.resolve():
                shutil.copy2(src, dest)
        except PermissionError:
            # Dropbox lock — use existing dest if present, else skip copy
            if not dest.exists():
                try:
                    dest.write_bytes(src.read_bytes())
                except Exception:
                    missing.append(name)
                    continue
        try:
            media_dest = MEDIA_HS / dest.name
            if not media_dest.exists() or media_dest.stat().st_size != dest.stat().st_size:
                shutil.copy2(dest if dest.exists() else src, media_dest)
        except Exception:
            pass
        rec["headshot"] = f"media/cast-headshots/{dest.name}"
        reg[name] = rec
        fixed += 1
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wired", fixed, "missing", len(missing))
    for n in missing:
        print(" ", n)


if __name__ == "__main__":
    main()
