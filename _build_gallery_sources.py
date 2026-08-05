# -*- coding: utf-8 -*-
"""Build gallery_sources.json: per-still online source pages aligned to gallery_local."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / "gallery_local.json"
CACHE = ROOT / "gallery_cache.json"
OUT = ROOT / "gallery_sources.json"

# Known provenance for Dafne Keen adult refill (order matches gallery_local).
DAFNE_SOURCES = [
    "https://www.gettyimages.com/detail/news-photo/2163154052",
    "https://www.gettyimages.com/detail/news-photo/2163154047",
    "https://www.gettyimages.com/detail/news-photo/2163154046",
    "https://www.gettyimages.com/detail/news-photo/2163135365",
    "https://www.themoviedb.org/person/1464650-dafne-keen/images/profiles",
    "https://www.themoviedb.org/person/1464650-dafne-keen/images/profiles",
    "https://www.themoviedb.org/person/1464650-dafne-keen/images/profiles",
    "https://www.themoviedb.org/person/1464650-dafne-keen/images/profiles",
    "https://www.themoviedb.org/person/1464650-dafne-keen/images/profiles",
    "https://www.themoviedb.org/person/1464650-dafne-keen/images/profiles",
    "https://www.gettyimages.com/detail/news-photo/2266056726",
    "https://www.gettyimages.com/detail/news-photo/2265514475",
    "https://www.gettyimages.com/detail/news-photo/2265510813",
    "https://www.gettyimages.com/detail/news-photo/2265510653",
    "https://www.gettyimages.com/detail/news-photo/2265509512",
    "https://www.gettyimages.com/detail/news-photo/2265499876",
    "https://www.gettyimages.com/detail/news-photo/2265495103",
    "https://www.gettyimages.com/detail/news-photo/2265494782",
    "https://www.gettyimages.com/detail/news-photo/2251432058",
    "https://www.gettyimages.com/detail/news-photo/2251431680",
    "https://www.gettyimages.com/detail/news-photo/2251432075",
    "https://www.gettyimages.com/detail/news-photo/2251431596",
    "https://www.gettyimages.com/detail/news-photo/2251441634",
    "https://www.gettyimages.com/detail/news-photo/2251441265",
    "https://www.gettyimages.com/detail/news-photo/2251441431",
]


def mentions_actor(url: str, name: str) -> bool:
    tokens = [t for t in re.findall(r"[a-z]+", name.lower()) if len(t) > 2]
    if not tokens:
        return False
    return tokens[-1] in unquote(url).lower()


def to_page(url: str) -> str:
    u = (url or "").split("?")[0]
    if not u.startswith("http"):
        return ""
    low = u.lower()
    if "upload.wikimedia.org" in low:
        fname = re.sub(r"^\d+px-", "", unquote(u).rstrip("/").split("/")[-1])
        return "https://commons.wikimedia.org/wiki/File:" + quote(fname.replace(" ", "_")) if fname else u
    if "gettyimages.com" in low:
        m = re.search(r"/id/(\d+)/", u)
        return f"https://www.gettyimages.com/detail/news-photo/{m.group(1)}" if m else u
    return u


def main() -> None:
    local = json.loads(LOCAL.read_text(encoding="utf-8")) if LOCAL.exists() else {}
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    out: dict[str, list[str]] = {}
    for name, paths in local.items():
        n = len(paths or [])
        if not n:
            continue
        if name == "Dafne Keen":
            srcs = list(DAFNE_SOURCES[:n])
            while len(srcs) < n:
                srcs.append("https://www.imdb.com/name/nm6748436/mediaindex/")
            out[name] = srcs
            continue
        remotes = [u for u in (cache.get(name) or []) if mentions_actor(u, name)]
        srcs = []
        for i in range(n):
            if i < len(remotes):
                srcs.append(to_page(remotes[i]) or remotes[i])
            else:
                srcs.append("")
        out[name] = srcs
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    filled = sum(1 for v in out.values() for x in v if x)
    total = sum(len(v) for v in out.values())
    print(f"wrote {OUT.name}: {len(out)} actors, {filled}/{total} sources filled")


if __name__ == "__main__":
    main()
