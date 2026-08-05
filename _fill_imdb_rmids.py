# -*- coding: utf-8 -*-
"""Download IMDb mediaviewer stills using known rm IDs from Bright Data scrape."""
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

VIEWERS = {
    "Lydia Wilson": (
        "lydia-wilson",
        "nm3575723",
        [
            "rm968907520",
            "rm2889211137",
            "rm1809061120",
            "rm2470009600",
            "rm4287254784",
            "rm3950595328",
            "rm904818176",
            "rm602828288",
            "rm552496640",
            "rm770600448",
            "rm3521998336",
            "rm3656216064",
            "rm2531468544",
            "rm3279822336",
            "rm4185792000",
            "rm4085128704",
            "rm4135460352",
            "rm4001242624",
            "rm2558402048",
            "rm2373852672",
            "rm3610103808",
            "rm1961024512",
            "rm394642946",
            "rm3735126018",
            "rm3051782146",
            "rm1692827650",
            "rm1726382082",
            "rm3487924226",
            "rm2967830530",
            "rm2850390018",
        ],
    ),
    "Pearl Chanda": (
        "pearl-chanda",
        "nm6112124",
        [
            "rm742853889",
            "rm3132692225",
            "rm3115915009",
            "rm675745025",
            "rm3183023873",
            "rm2492667137",
            "rm2985629697",
            "rm2772288769",
            "rm1349094401",
            "rm3934358529",
            "rm2939093761",
            "rm754713345",
            "rm3553886721",
            "rm1889340673",
            "rm1201147137",
            "rm3591375873",
            "rm3723169281",
        ],
    ),
    "Ellora Torchia": (
        "ellora-torchia",
        "nm4089168",
        [
            "rm157466626",
            "rm2835994626",
            "rm3291977729",
            "rm2202652417",
            "rm3116264193",
            "rm3539658240",
        ],
    ),
}


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


def image_from_viewer(imdb_id: str, rmid: str) -> str | None:
    html = get_text(f"https://www.imdb.com/name/{imdb_id}/mediaviewer/{rmid}/")
    # JSON blobs often contain image urls
    found = re.findall(r"https://m\.media-amazon\.com/images/M/[A-Za-z0-9@._+-]+", html)
    found += re.findall(r"https:\\+/\\+/m\.media-amazon\.com\\+/images\\+/M\\+/[A-Za-z0-9@._+-]+", html)
    cleaned: list[str] = []
    for u in found:
        u = u.replace("\\/", "/").replace("\\u002F", "/")
        cleaned.append(u)
    best = None
    best_score = -1
    for u in cleaned:
        if any(x in u.lower() for x in ("sprite", "logo", "icon")):
            continue
        score = len(u)
        if any(x in u for x in ("UX1000", "UY1200", "QL100", "UX1500", "UY2000", "SX1000")):
            score += 2000
        if "UX680" in u or "UY1000" in u:
            score += 800
        if score > best_score:
            best_score = score
            best = u
    if not best:
        # try next-data style path
        m = re.search(r'"url"\s*:\s*"(https://m\.media-amazon\.com/images/M/[^"]+)"', html)
        if m:
            best = m.group(1)
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
    )[:TARGET]
    staging = folder.parent / f".stage-{slug}-{int(time.time())}"
    staging.mkdir(parents=True, exist_ok=True)
    kept: list[str] = []
    for i, p in enumerate(files):
        dest = staging / f"{i:02d}{p.suffix.lower()}"
        dest.write_bytes(p.read_bytes())
    for p in folder.glob("*"):
        if p.is_file():
            try:
                p.unlink()
            except OSError:
                pass
    for p in sorted(staging.glob("*")):
        final = folder / p.name
        shutil.move(str(p), str(final))
        kept.append(f"assets/galleries/{slug}/{final.name}")
    try:
        staging.rmdir()
    except OSError:
        shutil.rmtree(staging, ignore_errors=True)
    return kept


def main() -> None:
    local = json.loads(OUT_LOCAL.read_text(encoding="utf-8"))
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {}

    for name, (slug, imdb, rmids) in VIEWERS.items():
        print("===", name)
        folder = ROOT / "site" / "assets" / "galleries" / slug
        folder.mkdir(parents=True, exist_ok=True)
        kept = [
            f"assets/galleries/{slug}/{p.name}"
            for p in sorted(folder.glob("*"))
            if p.is_file() and p.stat().st_size >= MIN_BYTES
        ]
        seen_names = {Path(p).name.lower() for p in kept}
        urls = list(cache.get(name) or [])
        for rmid in rmids:
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
            key = img.rsplit("/", 1)[-1].lower()[:90]
            if key in seen_names:
                continue
            seen_names.add(key)
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
            time.sleep(0.3)

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

    tf = ROOT / "site" / "assets" / "galleries" / "tracy-ifeachor"
    if tf.exists():
        local["Tracy Ifeachor"] = sorted(
            [
                f"assets/galleries/tracy-ifeachor/{p.name}"
                for p in tf.glob("*")
                if p.is_file() and p.stat().st_size >= MIN_BYTES
            ]
        )
        print("Tracy index", len(local["Tracy Ifeachor"]))

    OUT_LOCAL.write_text(json.dumps(local, indent=2), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    REG.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
