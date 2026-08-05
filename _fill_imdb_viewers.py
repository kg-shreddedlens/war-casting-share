# -*- coding: utf-8 -*-
"""Append IMDb mediaviewer stills for Lydia / Pearl / Ellora."""
from __future__ import annotations

import json
import re
import shutil
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCSWAMP = ROOT.parent
OUT_LOCAL = ROOT / "gallery_local.json"
CACHE = ROOT / "gallery_cache.json"
REG = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
MIN_BYTES = 8000
TARGET = 20

ACTORS = [
    ("Lydia Wilson", "lydia-wilson", "nm3575723"),
    ("Pearl Chanda", "pearl-chanda", "nm6112124"),
    ("Ellora Torchia", "ellora-torchia", "nm4089168"),
]


def get(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept-Language": "en-US",
            "Referer": "https://www.imdb.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=50) as resp:
        return resp.read()


def get_text(url: str) -> str:
    return get(url).decode("utf-8", "replace")


def mediaviewer_ids(imdb_id: str) -> list[str]:
    html = get_text(f"https://www.imdb.com/name/{imdb_id}/mediaindex/")
    ids: list[str] = []
    for m in re.findall(rf"/name/{imdb_id}/mediaviewer/(rm\d+)/", html):
        if m not in ids:
            ids.append(m)
    return ids


def image_from_viewer(imdb_id: str, rmid: str) -> str | None:
    html = get_text(f"https://www.imdb.com/name/{imdb_id}/mediaviewer/{rmid}/")
    found = re.findall(r"https://m\.media-amazon\.com/images/M/[^\s\"'<>]+", html)
    best = None
    best_score = -1
    for u in found:
        u = u.replace("\\u002F", "/").replace("\\/", "/")
        if "sprite" in u.lower() or "logo" in u.lower():
            continue
        score = len(u)
        if any(x in u for x in ("UX1000", "UY1200", "QL100", "UX1500", "UY2000")):
            score += 1000
        if "UX680" in u or "UY1000" in u:
            score += 500
        if score > best_score:
            best_score = score
            best = u
    if not best:
        return None
    best = re.sub(r"\._V1_.*$", "._V1_.jpg", best)
    if best.endswith("@"):
        best = best + "._V1_.jpg"
    return best


def compact(folder: Path, slug: str) -> list[str]:
    files = sorted(
        [p for p in folder.glob("*") if p.is_file() and p.stat().st_size >= MIN_BYTES],
        key=lambda p: p.name,
    )
    tmp = folder / "__tmp__"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    kept: list[str] = []
    for i, p in enumerate(files[:TARGET]):
        dest = tmp / f"{i:02d}{p.suffix.lower()}"
        dest.write_bytes(p.read_bytes())
    for p in folder.glob("*"):
        if p.is_file():
            p.unlink()
    for p in sorted(tmp.glob("*")):
        final = folder / p.name
        p.rename(final)
        kept.append(f"assets/galleries/{slug}/{final.name}")
    tmp.rmdir()
    return kept


def main() -> None:
    local = json.loads(OUT_LOCAL.read_text(encoding="utf-8"))
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {}

    for name, slug, imdb in ACTORS:
        print("===", name)
        folder = ROOT / "site" / "assets" / "galleries" / slug
        folder.mkdir(parents=True, exist_ok=True)
        kept = [
            f"assets/galleries/{slug}/{p.name}"
            for p in sorted(folder.glob("*"))
            if p.is_file() and p.stat().st_size >= MIN_BYTES
        ]
        seen = {Path(p).name.lower() for p in kept}
        urls = list(cache.get(name) or [])
        try:
            ids = mediaviewer_ids(imdb)
        except Exception as e:
            print(" mediaindex fail", e)
            ids = []
        print(" viewers", len(ids))
        for rmid in ids:
            if len(kept) >= TARGET:
                break
            try:
                img = image_from_viewer(imdb, rmid)
            except Exception as e:
                print(" viewer fail", rmid, type(e).__name__)
                continue
            if not img:
                print(" no img", rmid)
                continue
            if img not in urls:
                urls.append(img)
            key = img.rsplit("/", 1)[-1].lower()[:80]
            if key in seen:
                continue
            seen.add(key)
            dest = folder / f"{len(kept):02d}.jpg"
            try:
                data = get(img)
                if len(data) < MIN_BYTES:
                    print(" small", rmid, len(data))
                    continue
                dest.write_bytes(data)
                kept.append(f"assets/galleries/{slug}/{dest.name}")
                print(" ok", dest.name, len(data), rmid)
            except Exception as e:
                print(" dl fail", rmid, type(e).__name__)
            time.sleep(0.35)

        kept = compact(folder, slug)
        if kept:
            hs = f"{slug}.jpg"
            src = ROOT / "site" / kept[0]
            (ROOT / "site" / "assets" / "headshots").mkdir(parents=True, exist_ok=True)
            (DOCSWAMP / "media" / "cast-headshots").mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, ROOT / "site" / "assets" / "headshots" / hs)
            shutil.copy2(src, DOCSWAMP / "media" / "cast-headshots" / hs)
            rec = reg.get(name) or {"name": name}
            rec["headshot"] = f"media/cast-headshots/{hs}"
            reg[name] = rec
        local[name] = kept
        cache[name] = urls
        print(" kept", len(kept))

    # restore Tracy index if files exist
    tf = ROOT / "site" / "assets" / "galleries" / "tracy-ifeachor"
    if tf.exists():
        tkept = sorted(
            [
                f"assets/galleries/tracy-ifeachor/{p.name}"
                for p in tf.glob("*")
                if p.is_file() and p.stat().st_size >= MIN_BYTES
            ]
        )
        local["Tracy Ifeachor"] = tkept
        print("Tracy index", len(tkept))

    OUT_LOCAL.write_text(json.dumps(local, indent=2), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    REG.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
