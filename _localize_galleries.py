# -*- coding: utf-8 -*-
"""Download unique, name-matched actor stills into local assets/galleries/."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE_GAL = ROOT / "site" / "assets" / "galleries"
CACHE = ROOT / "gallery_cache.json"
OUT_LOCAL = ROOT / "gallery_local.json"
UA = "ShreddedLensCastingBot/1.0 (https://shreddedlens.com; casting research mirror)"
SKIP = re.compile(r"(logo|icon|flag|signature|svg|commons-logo|map|poster\.svg|wordmark)", re.I)

PRIORITY = [
    "Florence Pugh", "Saoirse Ronan", "Jodie Comer", "Emma Stone", "Vanessa Kirby",
    "Claire Foy", "Ruth Negga", "Renate Reinsve", "Nicole Beharie", "Eddie Redmayne",
    "Christopher Abbott", "Josh O'Connor", "Oscar Isaac", "Jake Gyllenhaal",
    "Trevante Rhodes", "Aldis Hodge", "Ruth Wilson", "Carrie Coon", "Rebecca Ferguson",
    "Sian Clifford", "Tessa Thompson", "Greta Onieogou", "Zazie Beetz", "Myha'la",
    "Zoe Kravitz", "Nnamdi Asomugha", "Russell Hornsby", "Mahershala Ali",
    "André Holland", "Rob Morgan", "Morfydd Clark", "Georgina Campbell",
    "Keira Knightley", "Anya Taylor-Joy", "Jessie Buckley", "Winston Duke",
    "John David Washington", "Andrew Garfield", "Adam Driver", "Kerry Condon",
    "Rebecca Hall", "Phoebe Dynevor", "Odessa Young", "Janelle Monáe",
    "Idris Elba", "Katherine Waterston",
]


def slugify(name: str) -> str:
    s = name.lower().replace("'", "").replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def name_tokens(name: str) -> list[str]:
    parts = re.findall(r"[A-Za-z]+", name)
    return [p.lower() for p in parts if len(p) > 2]


def url_matches_actor(url: str, name: str) -> bool:
    tokens = name_tokens(name)
    if not tokens:
        return False
    path = urllib.parse.unquote(url).lower()
    return tokens[-1] in path


def to_thumb(url: str, width: int = 500) -> str:
    """Normalize Commons URL to an allowed thumbnail width (500px works; 800 does not)."""
    url = (url or "").split("?")[0]
    if "/thumb/" in url:
        return re.sub(r"/\d+px-", f"/{width}px-", url)
    # original file → construct thumb path
    m = re.match(
        r"https://upload\.wikimedia\.org/wikipedia/(\w+)/([0-9a-f])/([0-9a-f]{2})/([^/]+)$",
        url,
        flags=re.I,
    )
    if m:
        project, a, ab, name = m.groups()
        return (
            f"https://upload.wikimedia.org/wikipedia/{project}/thumb/{a}/{ab}/{name}/"
            f"{width}px-{name}"
        )
    return url


def to_original(url: str) -> str:
    """Strip query params; prefer allowed 500px thumbs for download stability."""
    return to_thumb(url, 500)

def rest_media(title: str) -> list[str]:
    slug = title.replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/media-list/{urllib.parse.quote(slug)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    urls: list[str] = []
    for item in data.get("items") or []:
        if item.get("type") and item.get("type") != "image":
            continue
        if SKIP.search(item.get("title") or ""):
            continue
        src = item.get("src") or ""
        if not src and item.get("srcset"):
            src = sorted(item["srcset"], key=lambda x: x.get("scale", 1), reverse=True)[0].get("src") or ""
        if src.startswith("//"):
            src = "https:" + src
        src = to_original(src)
        if not src or SKIP.search(src) or ".svg" in src.lower():
            continue
        if not url_matches_actor(src, title):
            continue
        if src not in urls:
            urls.append(src)
        if len(urls) >= 10:
            break
    return urls


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read()
        if len(data) < 2000:
            return False
        dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"  dl fail {url[-60:]}: {e}")
        return False


def main() -> None:
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    # refill sparse priority entries (slow to avoid 429)
    for name in PRIORITY:
        if len(cache.get(name) or []) >= 3:
            continue
        try:
            urls = rest_media(name)
            if len(urls) < 2 and "é" in name:
                urls = rest_media(name.replace("é", "e")) or urls
            if urls:
                cache[name] = urls
                print(f"fetched {name}: {len(urls)}")
                CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
            else:
                print(f"empty {name}")
            time.sleep(1.6)
        except Exception as e:
            print(f"fail {name}: {e}")
            time.sleep(3.0)

    SITE_GAL.mkdir(parents=True, exist_ok=True)
    localized: dict[str, list[str]] = {}
    # Prefer priority first so key actors get local mirrors
    names = list(PRIORITY) + [n for n in sorted(cache) if n not in PRIORITY]
    for name in names:
        urls = cache.get(name) or []
        slug = slugify(name)
        folder = SITE_GAL / slug
        folder.mkdir(parents=True, exist_ok=True)
        kept: list[str] = []
        seen: set[str] = set()
        for raw in urls:
            if len(kept) >= 10:
                break
            u = to_original(raw)
            if not u or SKIP.search(u) or not url_matches_actor(u, name):
                continue
            key = Path(urllib.parse.urlparse(u).path).name.lower()
            if key in seen:
                continue
            seen.add(key)
            ext = ".jpg"
            if key.endswith(".png"):
                ext = ".png"
            elif key.endswith(".webp"):
                ext = ".webp"
            dest = folder / f"{len(kept):02d}{ext}"
            rel = f"assets/galleries/{slug}/{dest.name}"
            if dest.exists() and dest.stat().st_size > 2000:
                kept.append(rel)
                continue
            if download(u, dest):
                kept.append(rel)
                time.sleep(0.35)
        localized[name] = kept
        if kept:
            print(f"local {name}: {len(kept)}")

    # keep empty keys from prior run for completeness
    for name in cache:
        localized.setdefault(name, [])

    OUT_LOCAL.write_text(json.dumps(localized, indent=2), encoding="utf-8")
    ok = sum(1 for v in localized.values() if v)
    print(f"wrote {OUT_LOCAL}; {ok}/{len(localized)} with local stills")


if __name__ == "__main__":
    main()
