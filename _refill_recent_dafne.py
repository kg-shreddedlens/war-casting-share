# -*- coding: utf-8 -*-
"""Wipe Dafne Keen childhood stills; refill with recent adult/premiere photos only."""
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
SITE_GAL = ROOT / "site" / "assets" / "galleries" / "dafne-keen"
SITE_HS = ROOT / "site" / "assets" / "headshots"
MEDIA_HS = DOCSWAMP / "media" / "cast-headshots"
LOCAL = ROOT / "gallery_local.json"
REG = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TARGET = 25
MIN_BYTES = 9000

# Prefer pages/events from recent adult era (Deadpool 2024, Acolyte 2024, etc.)
SEED_PAGES = [
    ("https://www.imdb.com/name/nm6748436/mediaindex", "https://www.imdb.com/"),
    ("https://www.imdb.com/name/nm6748436/", "https://www.imdb.com/"),
    ("https://en.wikipedia.org/wiki/Dafne_Keen", None),
    ("https://www.themoviedb.org/person/1397778-dafne-keen", "https://www.themoviedb.org/"),
    ("https://www.themoviedb.org/person/1397778-dafne-keen/images/profiles", "https://www.themoviedb.org/"),
    ("https://www.rottentomatoes.com/celebrity/dafne_keen/pictures", None),
]

# Direct known-good recent CDN patterns / search pages
EXTRA_QUERIES = [
    "https://www.themoviedb.org/search/person?query=Dafne%20Keen",
]


def get(url: str, referer: str | None = None) -> bytes:
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=50) as resp:
        return resp.read()


def find_tmdb_id() -> tuple[int, str] | None:
    html = get("https://www.themoviedb.org/search/person?query=Dafne%20Keen").decode("utf-8", "replace")
    for pid, slug in re.findall(r'href="/person/(\d+)-([a-z0-9\-]+)"', html):
        if "dafne" in slug and "keen" in slug:
            return int(pid), slug
    # fallback first
    m = re.search(r'href="/person/(\d+)-(dafne-keen[^"]*)"', html, re.I)
    if m:
        return int(m.group(1)), m.group(2)
    return None


def collect_urls() -> list[str]:
    urls: list[str] = []
    hit = find_tmdb_id()
    print("tmdb", hit)
    pages = list(SEED_PAGES)
    if hit:
        pid, slug = hit
        pages = [
            (f"https://www.themoviedb.org/person/{pid}-{slug}/images/profiles", "https://www.themoviedb.org/"),
            (f"https://www.themoviedb.org/person/{pid}-{slug}", "https://www.themoviedb.org/"),
        ] + pages

    for url, ref in pages:
        try:
            html = get(url, ref).decode("utf-8", "replace")
        except Exception as e:
            print("page fail", url, e)
            continue
        # TMDB
        for f in re.findall(
            r"image\.tmdb\.org/t/p/(?:original|w\d+(?:_and_h\d+_face)?)/([A-Za-z0-9]+)\.jpg",
            html,
        ):
            u = f"https://image.tmdb.org/t/p/w780/{f}.jpg"
            if u not in urls:
                urls.append(u)
        # Amazon / IMDb
        for u in re.findall(r"https://m\.media-amazon\.com/images/[^\"'\s]+", html):
            u = u.split("?")[0]
            u = re.sub(r"\._V1_[^.]+\.", "._V1_QL75_UX600_.", u)
            if u not in urls:
                urls.append(u)
        # Wikimedia / wiki thumbs
        for u in re.findall(r"https://upload\.wikimedia\.org/[^\"'\s]+\.(?:jpg|jpeg|png)", html, re.I):
            u = u.split("?")[0]
            if u not in urls:
                urls.append(u)
        # generic jpg from recent-looking hosts
        for u in re.findall(
            r"https://(?:media\.gettyimages\.com|images\.bauersecure\.com|cdn\.[^\"'\s]+)/[^\"'\s]+\.(?:jpg|jpeg)",
            html,
            re.I,
        ):
            u = u.split("?")[0]
            if u not in urls:
                urls.append(u)
        print(" ", url[:60], "->", len(urls), "total")
        time.sleep(0.3)

    # Wikipedia API pageimage + commons search with recent keywords
    try:
        api = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "query",
                "titles": "Dafne Keen",
                "prop": "pageimages|images",
                "pithumbsize": 900,
                "imlimit": 30,
                "format": "json",
            }
        )
        data = json.loads(get(api).decode())
        for page in (data.get("query", {}).get("pages") or {}).values():
            thumb = (page.get("thumbnail") or {}).get("source")
            if thumb and thumb not in urls:
                urls.append(thumb)
            for im in page.get("images") or []:
                title = im.get("title") or ""
                # skip logos
                if not title.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                if any(x in title.lower() for x in ("logo", "icon", "commons-logo")):
                    continue
                # fetch url
                api2 = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
                    {
                        "action": "query",
                        "titles": title,
                        "prop": "imageinfo",
                        "iiprop": "url|size",
                        "iiurlwidth": 800,
                        "format": "json",
                    }
                )
                d2 = json.loads(get(api2).decode())
                for p2 in (d2.get("query", {}).get("pages") or {}).values():
                    info = (p2.get("imageinfo") or [{}])[0]
                    u = info.get("thumburl") or info.get("url")
                    if u and u not in urls:
                        urls.append(u)
                time.sleep(0.15)
    except Exception as e:
        print("wiki fail", e)

    # Commons search biased to recent years / Deadpool
    for q in (
        "Dafne Keen 2024",
        "Dafne Keen 2025",
        "Dafne Keen Deadpool",
        "Dafne Keen Acolyte",
    ):
        try:
            api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
                {
                    "action": "query",
                    "list": "search",
                    "srsearch": q,
                    "srnamespace": 6,
                    "srlimit": 20,
                    "format": "json",
                }
            )
            data = json.loads(
                get(api).decode(),
            )
            titles = [h["title"] for h in data.get("query", {}).get("search", [])]
            if not titles:
                continue
            api2 = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
                {
                    "action": "query",
                    "titles": "|".join(titles[:15]),
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "iiurlwidth": 800,
                    "format": "json",
                }
            )
            d2 = json.loads(get(api2).decode())
            for p in (d2.get("query", {}).get("pages") or {}).values():
                info = (p.get("imageinfo") or [{}])[0]
                u = info.get("thumburl") or info.get("url")
                if u and "svg" not in u.lower() and u not in urls:
                    urls.append(u)
            print(" commons", q, "->", len(urls))
            time.sleep(0.4)
        except Exception as e:
            print("commons fail", q, e)
    return urls


def looks_like_child_group_or_junk(path: Path) -> bool:
    """Heuristic using file size only is weak; we rely on source filtering + manual vision later."""
    return path.stat().st_size < MIN_BYTES


def main() -> None:
    urls = collect_urls()
    print("candidates", len(urls))

    # wipe old gallery
    if SITE_GAL.exists():
        for p in SITE_GAL.glob("*"):
            try:
                p.unlink()
            except Exception:
                pass
    else:
        SITE_GAL.mkdir(parents=True, exist_ok=True)

    kept: list[str] = []
    seen: set[str] = set()
    for u in urls:
        if len(kept) >= TARGET:
            break
        key = u.rsplit("/", 1)[-1].lower()[:100]
        if key in seen:
            continue
        seen.add(key)
        # Skip obvious Logan-era media filenames if present
        low = u.lower()
        if any(x in low for x in ("logan", "x-23-young", "child", "2017")):
            print("skip era", u[:90])
            continue
        try:
            data = get(u, referer="https://www.themoviedb.org/")
        except Exception as e:
            print("dl fail", e)
            continue
        if len(data) < MIN_BYTES:
            continue
        dest = SITE_GAL / f"{len(kept):02d}.jpg"
        dest.write_bytes(data)
        kept.append(f"assets/galleries/dafne-keen/{dest.name}")
        print("ok", dest.name, len(data), u[:80])
        time.sleep(0.12)

    # headshot = first kept
    if kept:
        src = ROOT / "site" / kept[0]
        SITE_HS.mkdir(parents=True, exist_ok=True)
        MEDIA_HS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, SITE_HS / "dafne-keen.jpg")
        shutil.copy2(src, MEDIA_HS / "dafne-keen.jpg")
        if REG.exists():
            reg = json.loads(REG.read_text(encoding="utf-8"))
            rec = reg.get("Dafne Keen") or {"name": "Dafne Keen"}
            rec["headshot"] = "media/cast-headshots/dafne-keen.jpg"
            reg["Dafne Keen"] = rec
            REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")

    local = json.loads(LOCAL.read_text(encoding="utf-8")) if LOCAL.exists() else {}
    local["Dafne Keen"] = kept
    LOCAL.write_text(json.dumps(local, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("KEPT", len(kept))


if __name__ == "__main__":
    main()
