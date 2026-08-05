# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import shutil
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCSWAMP = ROOT.parent
SITE_HS = ROOT / "site" / "assets" / "headshots"
MEDIA = DOCSWAMP / "media" / "cast-headshots"
REG = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")
UA = "ShreddedLensCastingBot/1.5 (casting headshots)"

TARGETS = [
    ("Zoe Kravitz", "nm1204442", "Zoë Kravitz"),
    ("Arica Himmel", "nm8585540", "Arica Himmel"),
    ("Anderson Paulo", None, "Anderson Paulo"),
    ("Brandon Mendez Harper", None, "Brandon Mendez Harper"),
]


def slugify(name: str) -> str:
    s = name.lower().replace("'", "").replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def get(url: str, referer: str | None = None) -> bytes:
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read()


def wiki_thumb(title: str) -> str | None:
    api = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "titles": title,
            "prop": "pageimages",
            "pithumbsize": 900,
            "format": "json",
        }
    )
    data = json.loads(get(api).decode())
    for p in (data.get("query", {}).get("pages") or {}).values():
        t = (p.get("thumbnail") or {}).get("source")
        if t:
            return t
    return None


def commons_first(q: str) -> str | None:
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": q,
            "srnamespace": 6,
            "srlimit": 12,
            "format": "json",
        }
    )
    data = json.loads(get(api).decode())
    titles = [h["title"] for h in data.get("query", {}).get("search", [])]
    if not titles:
        return None
    api2 = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "titles": "|".join(titles[:10]),
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 800,
            "format": "json",
        }
    )
    data2 = json.loads(get(api2).decode())
    for p in (data2.get("query", {}).get("pages") or {}).values():
        info = (p.get("imageinfo") or [{}])[0]
        u = info.get("thumburl") or info.get("url")
        if u and "svg" not in u.lower():
            return u
    return None


def imdb_og(imdb_id: str) -> str | None:
    html = get(f"https://www.imdb.com/name/{imdb_id}/", referer="https://www.imdb.com/").decode(
        "utf-8", "replace"
    )
    m = re.search(r'property="og:image"\s+content="(https://[^"]+)"', html)
    if not m:
        return None
    u = m.group(1).split("?")[0]
    return re.sub(r"\._V1_[^.]+\.", "._V1_QL75_UX600_.", u)


def tmdb_face(name: str) -> str | None:
    html = get(
        "https://www.themoviedb.org/search/person?query=" + urllib.parse.quote(name)
    ).decode("utf-8", "replace")
    m = re.search(r'href="/person/(\d+)-([a-z0-9\-]+)"', html)
    if not m:
        return None
    pid, slug = m.group(1), m.group(2)
    for path in (f"/person/{pid}-{slug}/images/profiles", f"/person/{pid}-{slug}"):
        page = get("https://www.themoviedb.org" + path).decode("utf-8", "replace")
        fs = re.findall(
            r"image\.tmdb\.org/t/p/(?:original|w\d+(?:_and_h\d+_face)?)/([A-Za-z0-9]+)\.jpg",
            page,
        )
        if fs:
            return f"https://image.tmdb.org/t/p/w780/{fs[0]}.jpg"
    return None


def save(name: str, url: str) -> bool:
    SITE_HS.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    data = get(url, referer="https://www.imdb.com/")
    if len(data) < 4000:
        print(name, "too small", len(data))
        return False
    dest = SITE_HS / f"{slugify(name)}.jpg"
    dest.write_bytes(data)
    shutil.copy2(dest, MEDIA / dest.name)
    print(name, "OK", len(data))
    return True


def main() -> None:
    reg = json.loads(REG.read_text(encoding="utf-8"))
    for name, imdb_id, wiki_title in TARGETS:
        slug = slugify(name)
        if (SITE_HS / f"{slug}.jpg").exists() and (SITE_HS / f"{slug}.jpg").stat().st_size > 4000:
            print(name, "already present")
            rec = reg.get(name) or {"name": name}
            rec["headshot"] = f"media/cast-headshots/{slug}.jpg"
            if imdb_id:
                rec["imdb_id"] = imdb_id
                rec["imdb_url"] = f"https://www.imdb.com/name/{imdb_id}/"
            reg[name] = rec
            continue
        urls = []
        for fn in (
            (lambda: imdb_og(imdb_id) if imdb_id else None),
            (lambda: tmdb_face(name)),
            (lambda: tmdb_face(wiki_title)),
            (lambda: wiki_thumb(wiki_title)),
            (lambda: commons_first(wiki_title)),
            (lambda: commons_first(name + " actor")),
        ):
            try:
                u = fn()
            except Exception as e:
                print(name, "source fail", e)
                u = None
            if u:
                urls.append(u)
        ok = False
        for u in urls:
            try:
                if save(name, u):
                    ok = True
                    break
            except Exception as e:
                print(name, "dl fail", e)
        rec = reg.get(name) or {"name": name}
        if ok:
            rec["headshot"] = f"media/cast-headshots/{slugify(name)}.jpg"
            if imdb_id:
                rec["imdb_id"] = imdb_id
                rec["imdb_url"] = f"https://www.imdb.com/name/{imdb_id}/"
        reg[name] = rec
        print(name, "DONE" if ok else "FAILED", "candidates", len(urls))
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
