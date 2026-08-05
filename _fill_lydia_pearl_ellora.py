# -*- coding: utf-8 -*-
"""Fill Lydia Wilson / Pearl Chanda / Ellora Torchia galleries from TMDB + Commons + Flickr + IMDb."""
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

ACTORS = [
    {"name": "Lydia Wilson", "tmdb": 1095524, "slug": "lydia-wilson", "imdb": "nm3575723"},
    {"name": "Pearl Chanda", "tmdb": 1754638, "slug": "pearl-chanda", "imdb": "nm6112124"},
    {"name": "Ellora Torchia", "tmdb": 1457454, "slug": "ellora-torchia", "imdb": "nm4089168"},
]


def get_bytes(url: str, ref: str | None = None) -> bytes:
    headers = {
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if ref:
        headers["Referer"] = ref
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=50) as resp:
        return resp.read()


def get(url: str, ref: str | None = None) -> str:
    return get_bytes(url, ref).decode("utf-8", "replace")


def name_match(text: str, name: str) -> bool:
    t = urllib.parse.unquote(text).lower().replace(" ", "_")
    toks = [p.lower() for p in re.findall(r"[A-Za-z]+", name) if len(p) > 1]
    if len(toks) < 2:
        return bool(toks) and toks[0] in t
    return toks[0] in t and toks[-1] in t


def tmdb_profiles(tid: int, slug: str) -> list[str]:
    urls: list[str] = []
    try:
        html = get(f"https://www.themoviedb.org/person/{tid}-{slug}/images/profiles")
        for f in re.findall(r"https://image\.tmdb\.org/t/p/original/([A-Za-z0-9]+)\.jpg", html):
            u = f"https://image.tmdb.org/t/p/w780/{f}.jpg"
            if u not in urls:
                urls.append(u)
    except Exception as e:
        print(" tmdb fail", e)
    return urls


def commons_urls(name: str) -> list[str]:
    urls: list[str] = []
    try:
        data = json.loads(
            get(
                "https://commons.wikimedia.org/w/api.php?"
                + urllib.parse.urlencode(
                    {
                        "action": "query",
                        "list": "search",
                        "srsearch": f'"{name}"',
                        "srnamespace": 6,
                        "srlimit": 20,
                        "format": "json",
                    }
                )
            )
        )
    except Exception:
        data = {}
    titles: list[str] = []
    skip = (".svg", ".pdf", "benchmark", "genealogy", "memorial", "woodd", "geograph")
    for hit in data.get("query", {}).get("search", []) or []:
        t = hit.get("title") or ""
        if any(x in t.lower() for x in skip):
            continue
        if name_match(t, name):
            titles.append(t)
    try:
        wiki = json.loads(
            get(
                "https://en.wikipedia.org/w/api.php?"
                + urllib.parse.urlencode(
                    {
                        "action": "query",
                        "titles": name,
                        "prop": "pageimages",
                        "piprop": "original",
                        "format": "json",
                    }
                )
            )
        )
        for p in (wiki.get("query", {}).get("pages") or {}).values():
            src = (p.get("original") or {}).get("source")
            if src:
                urls.append(src.split("?")[0])
    except Exception:
        pass
    if titles:
        info = json.loads(
            get(
                "https://commons.wikimedia.org/w/api.php?"
                + urllib.parse.urlencode(
                    {
                        "action": "query",
                        "titles": "|".join(titles[:15]),
                        "prop": "imageinfo",
                        "iiprop": "url|mime",
                        "iiurlwidth": 780,
                        "format": "json",
                    }
                )
            )
        )
        for p in (info.get("query", {}).get("pages") or {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            mime = (ii.get("mime") or "").lower()
            if "svg" in mime or "pdf" in mime:
                continue
            src = (ii.get("thumburl") or ii.get("url") or "").split("?")[0]
            if src and src not in urls:
                urls.append(src)
    return urls


def flickr_urls(name: str) -> list[str]:
    urls: list[str] = []
    for tags in (name, name.replace(" ", "")):
        feed = "https://www.flickr.com/services/feeds/photos_public.gne?" + urllib.parse.urlencode(
            {"tags": tags, "format": "json", "nojsoncallback": 1}
        )
        try:
            data = json.loads(get(feed))
            for item in data.get("items") or []:
                title = item.get("title") or ""
                media = item.get("media", {}).get("m", "")
                if not media:
                    continue
                if not (name_match(title, name) or name.lower() in title.lower()):
                    continue
                big = re.sub(r"_[mst]\.jpg", "_b.jpg", media)
                if big not in urls:
                    urls.append(big)
        except Exception:
            pass
        time.sleep(0.3)
    try:
        html = get("https://www.flickr.com/search/?" + urllib.parse.urlencode({"text": f'"{name}"'}))
        for u in re.findall(r"https://live\.staticflickr\.com/\d+/[0-9]+_[a-f0-9]+(?:_[a-z])?\.jpg", html):
            big = re.sub(r"_[mst]\.jpg", "_b.jpg", u)
            if big not in urls:
                urls.append(big)
    except Exception:
        pass
    return urls


def imdb_urls(imdb_id: str) -> list[str]:
    urls: list[str] = []
    for path in (
        f"https://www.imdb.com/name/{imdb_id}/mediaindex/",
        f"https://www.imdb.com/name/{imdb_id}/",
    ):
        try:
            html = get(path, ref="https://www.imdb.com/")
        except Exception as e:
            print(" imdb fail", path, e)
            continue
        found = re.findall(r"https://m\.media-amazon\.com/images/M/[A-Za-z0-9@._+-]+", html)
        for u in found:
            if u.endswith("@"):
                u = u + "._V1_QL75_UX680_.jpg"
            else:
                u = re.sub(r"\._V1_.*$", "._V1_QL75_UX680_.jpg", u)
            if u not in urls:
                urls.append(u)
        time.sleep(0.4)
    return urls


def fill(actor: dict) -> int:
    name = actor["name"]
    tid = actor["tmdb"]
    slug = actor["slug"]
    imdb = actor["imdb"]
    print(f"\n=== {name} ===")
    urls: list[str] = []
    for u in tmdb_profiles(tid, slug):
        if u not in urls:
            urls.append(u)
    print(" tmdb", len(urls))
    for u in commons_urls(name):
        if u not in urls:
            urls.append(u)
    print(" +commons", len(urls))
    for u in flickr_urls(name):
        if u not in urls:
            urls.append(u)
    print(" +flickr", len(urls))
    for u in imdb_urls(imdb):
        if u not in urls:
            urls.append(u)
    print(" +imdb", len(urls))

    folder = SITE_GAL / slug
    folder.mkdir(parents=True, exist_ok=True)
    for p in folder.glob("*"):
        p.unlink()

    kept: list[str] = []
    seen: set[str] = set()
    for u in urls:
        if len(kept) >= TARGET:
            break
        key = u.rsplit("/", 1)[-1].lower()[:90]
        if key in seen:
            continue
        seen.add(key)
        ext = ".png" if ".png" in key else ".jpg"
        dest = folder / f"{len(kept):02d}{ext}"
        try:
            data = get_bytes(u)
            if len(data) < MIN_BYTES:
                print(" skip small", key[:40], len(data))
                continue
            dest.write_bytes(data)
            kept.append(f"assets/galleries/{slug}/{dest.name}")
            print(" ok", dest.name, len(data))
            time.sleep(0.2)
        except Exception as e:
            print(" fail", key[:40], type(e).__name__)

    if kept:
        hs = f"{slug}.jpg"
        src = ROOT / "site" / kept[0]
        SITE_HS.mkdir(parents=True, exist_ok=True)
        MEDIA_HS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, SITE_HS / hs)
        shutil.copy2(src, MEDIA_HS / hs)
        reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {}
        rec = reg.get(name) or {"name": name}
        rec["headshot"] = f"media/cast-headshots/{hs}"
        reg[name] = rec
        REG.write_text(json.dumps(reg, indent=2), encoding="utf-8")

    local = json.loads(OUT_LOCAL.read_text(encoding="utf-8")) if OUT_LOCAL.exists() else {}
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    local[name] = kept
    cache[name] = urls
    OUT_LOCAL.write_text(json.dumps(local, indent=2), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    print(" kept", len(kept))
    return len(kept)


if __name__ == "__main__":
    for actor in ACTORS:
        fill(actor)
