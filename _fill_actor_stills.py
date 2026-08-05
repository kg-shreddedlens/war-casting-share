# -*- coding: utf-8 -*-
"""Fill an actor gallery + headshot from TMDB profiles (+ optional Sensacine/AlloCiné)."""
from __future__ import annotations

import json
import re
import shutil
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCSWAMP = ROOT.parent
SITE_GAL = ROOT / "site" / "assets" / "galleries"
SITE_HS = ROOT / "site" / "assets" / "headshots"
MEDIA_HS = DOCSWAMP / "media" / "cast-headshots"
OUT_LOCAL = ROOT / "gallery_local.json"
CACHE = ROOT / "gallery_cache.json"
REG = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TARGET = 20
MIN_BYTES = 8000


def slugify(name: str) -> str:
    s = name.lower().replace("'", "").replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def get_bytes(url: str, referer: str | None = None) -> bytes:
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=50) as resp:
        return resp.read()


def get_text(url: str, referer: str | None = None) -> str:
    return get_bytes(url, referer).decode("utf-8", "replace")


def tmdb_profile_urls(tmdb_id: int, slug: str) -> list[str]:
    urls: list[str] = []
    page = f"https://www.themoviedb.org/person/{tmdb_id}-{slug}/images/profiles"
    try:
        html = get_text(page)
    except Exception as e:
        print("tmdb profiles fail", e)
        html = ""
    for f in re.findall(r"https://image\.tmdb\.org/t/p/original/([A-Za-z0-9]+)\.jpg", html):
        u = f"https://image.tmdb.org/t/p/w780/{f}.jpg"
        if u not in urls:
            urls.append(u)
    if not urls:
        # fallback: main person page face crops
        try:
            html = get_text(f"https://www.themoviedb.org/person/{tmdb_id}-{slug}")
            for f in re.findall(r"/t/p/w\d+(?:_and_h\d+_face)?/([A-Za-z0-9]+)\.jpg", html):
                u = f"https://image.tmdb.org/t/p/w780/{f}.jpg"
                if u not in urls:
                    urls.append(u)
        except Exception as e:
            print("tmdb main fail", e)
    return urls


def sensacine_actor_id(name: str) -> str | None:
    # AlloCiné/SensaCine search
    for base in (
        "https://www.sensacine.com/buscador/?q=",
        "https://www.allocine.fr/recherche/?q=",
    ):
        try:
            html = get_text(base + urllib.parse.quote(name))
        except Exception:
            continue
        # /actores/actor-123/ or /personne/fichepersonne_gen_cpersonne=123.html
        m = re.search(r"/actores/actor-(\d+)/", html)
        if m:
            return ("sensacine", m.group(1))
        m = re.search(r"fichepersonne_gen_cpersonne=(\d+)", html)
        if m:
            return ("allocine", m.group(1))
        time.sleep(0.3)
    return None


def sensacine_photo_urls(actor_id: str, limit: int = 30) -> list[str]:
    urls: list[str] = []
    index = f"https://www.sensacine.com/actores/actor-{actor_id}/fotos/"
    try:
        html = get_text(index)
    except Exception as e:
        print("sensacine index fail", e)
        return urls
    media_ids = re.findall(r"cmediafile=(\d+)", html)
    seen_ids: list[str] = []
    for mid in media_ids:
        if mid not in seen_ids:
            seen_ids.append(mid)
    for mid in seen_ids[:limit]:
        page = f"https://www.sensacine.com/actores/actor-{actor_id}/fotos/detalle/?cmediafile={mid}"
        try:
            h = get_text(page)
        except Exception:
            continue
        found = re.findall(r"https://[^\"'\s>]+\.acsta\.net/[^\"'\s>]+\.(?:jpg|jpeg|png)", h, re.I)
        found += re.findall(r"//[^\"'\s>]+\.acsta\.net/[^\"'\s>]+\.(?:jpg|jpeg|png)", h, re.I)
        best = None
        best_score = -99
        for u in found:
            if u.startswith("//"):
                u = "https:" + u
            u = u.split("?")[0]
            low = u.lower()
            if any(x in low for x in ("logo", "sprite", "icon", "empty")):
                continue
            score = 0
            if "/r_" in low or "/pictures/" in low or "/img/" in low:
                score += 2
            if re.search(r"/c_\d+_\d+/", low):
                score -= 2
            if any(x in low for x in ("1920", "1200", "1024", "900", "800")):
                score += 3
            if score > best_score:
                best_score = score
                best = u
        if best and best not in urls:
            urls.append(best)
            print("  sensacine", mid, best[:100])
        time.sleep(0.25)
    return urls


def allocine_photo_urls(person_id: str, limit: int = 25) -> list[str]:
    urls: list[str] = []
    index = f"https://www.allocine.fr/personne/fichepersonne-{person_id}/photos/"
    try:
        html = get_text(index)
    except Exception as e:
        print("allocine index fail", e)
        return urls
    media_ids = re.findall(r"cmediafile=(\d+)", html)
    seen: list[str] = []
    for mid in media_ids:
        if mid not in seen:
            seen.append(mid)
    for mid in seen[:limit]:
        page = f"https://www.allocine.fr/personne/fichepersonne-{person_id}/photos/detail/?cmediafile={mid}"
        try:
            h = get_text(page)
        except Exception:
            continue
        found = re.findall(r"https://[^\"'\s>]+\.acsta\.net/[^\"'\s>]+\.(?:jpg|jpeg|png)", h, re.I)
        for u in found:
            u = u.split("?")[0]
            low = u.lower()
            if any(x in low for x in ("logo", "sprite", "icon", "empty")):
                continue
            if re.search(r"/c_\d+_\d+/", low):
                continue
            if u not in urls:
                urls.append(u)
                print("  allocine", mid, u[:100])
                break
        time.sleep(0.25)
    return urls


def fill(name: str, tmdb_id: int, tmdb_slug: str | None = None) -> int:
    slug = slugify(name)
    tmdb_slug = tmdb_slug or slug
    print(f"\n=== {name} (TMDB {tmdb_id}) ===")
    urls = tmdb_profile_urls(tmdb_id, tmdb_slug)
    print("tmdb profiles", len(urls))

    hit = sensacine_actor_id(name)
    if hit:
        kind, aid = hit
        print("found", kind, aid)
        if kind == "sensacine":
            urls.extend(u for u in sensacine_photo_urls(aid) if u not in urls)
        else:
            urls.extend(u for u in allocine_photo_urls(aid) if u not in urls)
    else:
        print("no sensacine/allocine id")

    folder = SITE_GAL / slug
    folder.mkdir(parents=True, exist_ok=True)
    for p in folder.glob("*"):
        p.unlink()
    SITE_HS.mkdir(parents=True, exist_ok=True)
    MEDIA_HS.mkdir(parents=True, exist_ok=True)

    kept: list[str] = []
    seen_keys: set[str] = set()
    for u in urls:
        if len(kept) >= TARGET:
            break
        key = u.rsplit("/", 1)[-1].lower()
        if key in seen_keys:
            continue
        seen_keys.add(key)
        ext = ".png" if ".png" in key else ".jpg"
        dest = folder / f"{len(kept):02d}{ext}"
        try:
            data = get_bytes(u, referer="https://www.themoviedb.org/")
            if len(data) < MIN_BYTES:
                print("skip small", key, len(data))
                continue
            dest.write_bytes(data)
            kept.append(f"assets/galleries/{slug}/{dest.name}")
            print("ok", dest.name, len(data))
            time.sleep(0.2)
        except Exception as e:
            print("fail", key, e)

    if kept:
        hs_name = f"{slug}.jpg"
        src = ROOT / "site" / kept[0]
        shutil.copy2(src, SITE_HS / hs_name)
        shutil.copy2(src, MEDIA_HS / hs_name)
        if REG.exists():
            reg = json.loads(REG.read_text(encoding="utf-8"))
            rec = reg.get(name) or {"name": name}
            rec["headshot"] = f"media/cast-headshots/{hs_name}"
            reg[name] = rec
            REG.write_text(json.dumps(reg, indent=2), encoding="utf-8")

    local = json.loads(OUT_LOCAL.read_text(encoding="utf-8")) if OUT_LOCAL.exists() else {}
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    local[name] = kept
    cache[name] = urls
    OUT_LOCAL.write_text(json.dumps(local, indent=2), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    print("kept", len(kept))
    return len(kept)


ACTORS = [
    ("Lydia Wilson", 1095524, "lydia-wilson"),
    ("Pearl Chanda", 1754638, "pearl-chanda"),
    ("Ellora Torchia", 1457454, "ellora-torchia"),
]


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3 and sys.argv[1].isdigit():
        # python _fill_actor_stills.py 1095524 "Lydia Wilson"
        fill(sys.argv[2], int(sys.argv[1]), slugify(sys.argv[2]))
    else:
        for name, tid, tslug in ACTORS:
            fill(name, tid, tslug)
