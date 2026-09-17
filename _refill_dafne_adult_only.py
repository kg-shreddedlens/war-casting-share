# -*- coding: utf-8 -*-
"""Rebuild Dafne Keen gallery with adult/recent stills only (no Logan-era, no wrong IDs)."""
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
MIN_BYTES = 12000

# Vision-audited adult TMDB profile hashes (person 1464650 only). Child hashes excluded.
ADULT_TMDB = [
    "g325OIjIHrFr0te8ewPfhKQ2SKj",  # studio adult
    "34BhddK5z2YHjfppOleezVrQ7Jt",  # red carpet adult
    "gGDU5FPJXF3Psb8TPeTemchQyBR",  # glam adult
    "mkCimIAtCD8GfDfSntE80onoDOQ",  # smiling adult
    "dzdZBkWrdZMzElZuMzxG0prl334",  # Calgary adult
    "pUEGkV7s2dSawhANUIJhyLoJDK3",  # updo adult
]

# Explicitly banned (child / teen / wrong person)
BANNED_HASH = {
    "8aLVAImifonO7hWT8A6z3Xbt34F",  # child
    "slXRbJPIim9yTXa5gteqDbrF8zr",  # child
    "nr4NvVPoVdv7T5dghJiyn4B4taB",  # child
    "7pKDzZeunquNqdfs01AG8xn088R",  # mid-teen HDM
}

PAGES = [
    ("https://wwd.com/fashion-news/fashion-scoops/gallery/deadpool-and-wolverine-premiere-red-carpet-style-photos-1236501342/", None),
    ("https://www.forbes.com/sites/timlammers/2024/07/23/deadpool--wolverine-scenes-from-the-red-carpet-premiere/", None),
    ("https://www.cinemablend.com/superheroes/marvel-cinematic-universe/dafne-keen-grown-deadpool-wolverine-red-carpet-reunion-photos", None),
    ("https://www.famousbirthdays.com/people/dafne-keen.html", None),
    ("https://www.gettyimages.com/photos/dafne-keen?assettype=image&sort=newest&phrase=dafne%20keen", "https://www.gettyimages.com/"),
    ("https://www.gettyimages.com/photos/dafne-keen-deadpool?assettype=image&sort=newest&phrase=dafne%20keen%20deadpool", "https://www.gettyimages.com/"),
    ("https://www.gettyimages.com/photos/dafne-keen-acolyte?assettype=image&sort=newest&phrase=dafne%20keen%20acolyte", "https://www.gettyimages.com/"),
    ("https://en.wikipedia.org/wiki/Dafne_Keen", None),
    ("https://www.imdb.com/name/nm6748436/mediaindex/?refine=still_frame", "https://www.imdb.com/"),
    ("https://www.sensacine.com/actores/actor-686204/fotos/", None),
    ("https://www.allocine.fr/personne/fichepersonne_gen_cpersonne=686204.html", None),
]


def get(url: str, referer: str | None = None) -> bytes:
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=55) as resp:
        return resp.read()


def extract_urls(html: str) -> list[str]:
    found: list[str] = []
    patterns = [
        r"https://image\.tmdb\.org/t/p/(?:original|w\d+)/([A-Za-z0-9]+)\.jpg",
        r"https://media\.gettyimages\.com/[^\"'\s]+\.(?:jpg|jpeg|png)",
        r"https://[^\"'\s]*gettyimages[^\"'\s]+\.(?:jpg|jpeg)",
        r"https://m\.media-amazon\.com/images/[^\"'\s]+",
        r"https://upload\.wikimedia\.org/[^\"'\s]+\.(?:jpg|jpeg|png)",
        r"https://[^\"'\s]+\.acsta\.net/[^\"'\s]+\.(?:jpg|jpeg|png)",
        r"https://cdn\.famousbirthdays\.com/[^\"'\s]+\.(?:jpg|jpeg|png|webp)",
        r"https://[^\"'\s]*wwd[^\"'\s]+\.(?:jpg|jpeg|png)",
        r"https://[^\"'\s]*forbesimg[^\"'\s]+\.(?:jpg|jpeg)",
        r"https://[^\"'\s]*cinemablend[^\"'\s]+\.(?:jpg|jpeg|png)",
        r"https://[^\"'\s]*static[^\"'\s]*(?:dafne|keen)[^\"'\s]*\.(?:jpg|jpeg|png|webp)",
        r"srcset=\"([^\"]+)\"",
        r"data-src=\"(https://[^\"]+)\"",
        r"content=\"(https://[^\"]+\.(?:jpg|jpeg|png|webp)[^\"]*)\"",
    ]
    for pat in patterns:
        for m in re.findall(pat, html, re.I):
            if pat.startswith("https://image.tmdb"):
                h = m
                if h in BANNED_HASH:
                    continue
                u = f"https://image.tmdb.org/t/p/w780/{h}.jpg"
            elif "srcset=" in pat or pat.startswith("srcset"):
                # take largest candidate from srcset
                parts = [p.strip().split(" ")[0] for p in m.split(",")]
                u = parts[-1] if parts else ""
            else:
                u = m
            if not u.startswith("http"):
                continue
            u = u.split("?")[0]
            if any(x in u.lower() for x in ("logo", "sprite", "icon", "avatar-default", ".svg")):
                continue
            # Prefer Dafne-related paths when host is generic CDN, else keep
            if u not in found:
                found.append(u)
    # Amazon normalize
    out: list[str] = []
    for u in found:
        if "media-amazon.com" in u:
            u = re.sub(r"\._V1_[^.]+\.", "._V1_QL75_UX800_.", u)
        if "gettyimages" in u and "/photos/" in u:
            continue
        out.append(u)
    return out


def commons_recent() -> list[str]:
    urls: list[str] = []
    for q in (
        'Dafne Keen 2024 filetype:bitmap',
        'Dafne Keen 2025',
        'Dafne Keen Deadpool',
        'Dafne Keen Acolyte',
        'File:Dafne Keen',
    ):
        try:
            api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
                {
                    "action": "query",
                    "list": "search",
                    "srsearch": q,
                    "srnamespace": 6,
                    "srlimit": 25,
                    "format": "json",
                }
            )
            data = json.loads(get(api).decode())
            titles = [h["title"] for h in data.get("query", {}).get("search", [])]
            if not titles:
                continue
            api2 = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
                {
                    "action": "query",
                    "titles": "|".join(titles[:20]),
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata",
                    "iiurlwidth": 900,
                    "format": "json",
                }
            )
            d2 = json.loads(get(api2).decode())
            for p in (d2.get("query", {}).get("pages") or {}).values():
                title = (p.get("title") or "").lower()
                # skip logan-era commons if filename screams it
                if any(x in title for x in ("logan", "2017", "berlinale", "x-23")) and "2024" not in title and "2025" not in title:
                    continue
                info = (p.get("imageinfo") or [{}])[0]
                u = info.get("thumburl") or info.get("url")
                if u and "svg" not in u.lower():
                    urls.append(u)
            time.sleep(0.25)
        except Exception as e:
            print("commons", q, e)
    return urls


def sensacine_recent() -> list[str]:
    urls: list[str] = []
    # try discover id
    try:
        html = get("https://www.sensacine.com/buscador/?q=Dafne%20Keen").decode("utf-8", "replace")
        m = re.search(r"/actores/actor-(\d+)/", html)
        if not m:
            return urls
        aid = m.group(1)
        print("sensacine", aid)
        index = get(f"https://www.sensacine.com/actores/actor-{aid}/fotos/").decode("utf-8", "replace")
        media_ids = []
        for mid in re.findall(r"cmediafile=(\d+)", index):
            if mid not in media_ids:
                media_ids.append(mid)
        for mid in media_ids[:40]:
            page = f"https://www.sensacine.com/actores/actor-{aid}/fotos/detalle/?cmediafile={mid}"
            try:
                h = get(page).decode("utf-8", "replace")
            except Exception:
                continue
            # skip if page text mentions Logan childhood heavily without 2024
            low = h.lower()
            if "logan" in low and "2024" not in low and "deadpool" not in low and "acolyte" not in low and "matière" not in low:
                # still may be adult HDM — keep but deprioritize via order
                pass
            found = re.findall(r"https://[^\"'\s>]+\.acsta\.net/[^\"'\s>]+\.(?:jpg|jpeg|png)", h, re.I)
            best = None
            for u in found:
                u = u.split("?")[0]
                if "ux1280" in u or "ux1024" in u or "ux800" in u or "/picturesheet/" not in u:
                    if best is None or len(u) > len(best):
                        best = u
            if best and best not in urls:
                # Prefer URLs with year folders 2023/2024/2025 if present
                urls.append(best)
            time.sleep(0.12)
    except Exception as e:
        print("sensacine fail", e)
    # Prefer recent year path segments first
    def score(u: str) -> int:
        s = 0
        for y in ("2025", "2024", "2023", "2022"):
            if y in u:
                s += int(y)
        if any(x in u.lower() for x in ("2017", "2018", "2016")):
            s -= 5000
        return s

    urls.sort(key=score, reverse=True)
    return urls


def main() -> None:
    ordered: list[str] = []
    for h in ADULT_TMDB:
        ordered.append(f"https://image.tmdb.org/t/p/w780/{h}.jpg")

    for url, ref in PAGES:
        try:
            html = get(url, ref).decode("utf-8", "replace")
        except Exception as e:
            print("page fail", url[:70], e)
            continue
        got = extract_urls(html)
        # On Getty/WWD pages, keep only if surrounding context mentions Dafne when possible
        added = 0
        for u in got:
            if any(b in u for b in BANNED_HASH):
                continue
            # Drop Anya-looking TMDB that aren't in allowlist when from wrong page
            m = re.search(r"image\.tmdb\.org/t/p/w\d+/([A-Za-z0-9]+)\.jpg", u)
            if m and m.group(1) not in ADULT_TMDB and "tmdb.org" in url:
                continue
            if u not in ordered:
                ordered.append(u)
                added += 1
        print("page", url[:70], "added", added, "total", len(ordered))
        time.sleep(0.35)

    for u in commons_recent():
        if u not in ordered:
            ordered.append(u)
    print("after commons", len(ordered))

    for u in sensacine_recent():
        if u not in ordered:
            ordered.append(u)
    print("after sensacine", len(ordered))

    # Wipe gallery
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
    for u in ordered:
        if len(kept) >= TARGET:
            break
        key = re.sub(r"\W+", "", u.lower())[-80:]
        if key in seen:
            continue
        seen.add(key)
        low = u.lower()
        if any(x in low for x in ("logan", "berlinale", "2017", "x-23-young")):
            print("skip era", u[:90])
            continue
        try:
            data = get(u, referer="https://www.google.com/")
        except Exception as e:
            print("dl fail", str(e)[:80])
            continue
        if len(data) < MIN_BYTES:
            continue
        # skip tiny icons / webp that aren't photos
        if data[:3] not in (b"\xff\xd8\xff", b"\x89PN") and data[:4] != b"RIFF":
            # allow webp
            if data[:4] != b"RIFF" and b"WEBP" not in data[:16]:
                # jpeg/png only preferred
                if not (data[:2] == b"\xff\xd8" or data[:8] == b"\x89PNG\r\n\x1a\n"):
                    print("skip nonimage", u[:70])
                    continue
        dest = SITE_GAL / f"{len(kept):02d}.jpg"
        dest.write_bytes(data)
        kept.append(f"assets/galleries/dafne-keen/{dest.name}")
        print("ok", dest.name, len(data), u[:85])
        time.sleep(0.1)

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
