# -*- coding: utf-8 -*-
"""Fill actor galleries to TARGET stills via Commons category, Wikidata depicts, search, Flickr."""
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
REG = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")
UA = "ShreddedLensCastingBot/1.2 (https://shreddedlens.com; casting stills)"
TARGET = 25
SKIP = re.compile(r"(logo|icon|flag|signature|\.svg|commons-logo|wordmark|churchill|marlborough|coat.?of.?arms)", re.I)


def slugify(name: str) -> str:
    s = name.lower().replace("'", "").replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def tokens(name: str) -> list[str]:
    return [p.lower() for p in re.findall(r"[A-Za-z]+", name) if len(p) > 1]


def api(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wikidata_qid(name: str) -> str | None:
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "type": "item",
            "limit": 8,
            "format": "json",
        }
    )
    try:
        data = api(url)
    except Exception:
        return None
    for item in data.get("search") or []:
        label = (item.get("label") or "").lower()
        desc = (item.get("description") or "").lower()
        if label == name.lower() or any(k in desc for k in ("actor", "actress", "filmmaker", "singer", "comedian")):
            return item["id"]
    return (data.get("search") or [{}])[0].get("id")


def name_in_text(text: str, name: str) -> bool:
    t = urllib.parse.unquote(text).lower().replace(" ", "_")
    if SKIP.search(t):
        return False
    toks = tokens(name)
    if len(toks) < 2:
        return bool(toks) and toks[0] in t
    return toks[0] in t and toks[-1] in t


def commons_titles(name: str, qid: str | None) -> list[str]:
    titles: list[str] = []
    # category
    try:
        data = api(
            "https://commons.wikimedia.org/w/api.php?"
            + urllib.parse.urlencode(
                {
                    "action": "query",
                    "list": "categorymembers",
                    "cmtitle": f"Category:{name}",
                    "cmtype": "file",
                    "cmlimit": 100,
                    "format": "json",
                }
            )
        )
        for m in data.get("query", {}).get("categorymembers", []) or []:
            t = m.get("title") or ""
            if t and t not in titles and not SKIP.search(t):
                titles.append(t)
    except Exception:
        pass
    time.sleep(0.8)
    if qid:
        try:
            data = api(
                "https://commons.wikimedia.org/w/api.php?"
                + urllib.parse.urlencode(
                    {
                        "action": "query",
                        "list": "search",
                        "srsearch": f"haswbstatement:P180={qid}",
                        "srnamespace": 6,
                        "srlimit": 50,
                        "format": "json",
                    }
                )
            )
            for h in data.get("query", {}).get("search", []) or []:
                t = h.get("title") or ""
                if t and t not in titles and not SKIP.search(t):
                    titles.append(t)
        except Exception:
            pass
        time.sleep(0.8)
    for q in (f'"{name}"', f"{name} actor"):
        try:
            data = api(
                "https://commons.wikimedia.org/w/api.php?"
                + urllib.parse.urlencode(
                    {
                        "action": "query",
                        "list": "search",
                        "srsearch": q,
                        "srnamespace": 6,
                        "srlimit": 40,
                        "format": "json",
                    }
                )
            )
            for h in data.get("query", {}).get("search", []) or []:
                t = h.get("title") or ""
                if t and t not in titles and name_in_text(t, name):
                    titles.append(t)
        except Exception:
            pass
        time.sleep(0.7)
    return titles


def imageinfo(titles: list[str]) -> list[str]:
    urls: list[str] = []
    for i in range(0, len(titles), 15):
        chunk = titles[i : i + 15]
        try:
            data = api(
                "https://commons.wikimedia.org/w/api.php?"
                + urllib.parse.urlencode(
                    {
                        "action": "query",
                        "titles": "|".join(chunk),
                        "prop": "imageinfo",
                        "iiprop": "url|mime",
                        "iiurlwidth": 500,
                        "format": "json",
                    }
                )
            )
        except Exception:
            time.sleep(2)
            continue
        for p in (data.get("query", {}).get("pages") or {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            mime = (ii.get("mime") or "").lower()
            if "svg" in mime or "pdf" in mime:
                continue
            src = (ii.get("thumburl") or ii.get("url") or "").split("?")[0]
            if src and src not in urls:
                urls.append(src)
        time.sleep(0.9)
    return urls


def flickr_urls(name: str) -> list[str]:
    out: list[str] = []
    tag = re.sub(r"[^A-Za-z0-9]+", "", name)
    for tags in (tag, name):
        feed = "https://www.flickr.com/services/feeds/photos_public.gne?" + urllib.parse.urlencode(
            {"tags": tags, "format": "json", "nojsoncallback": 1}
        )
        try:
            req = urllib.request.Request(feed, headers={"User-Agent": UA})
            data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore"))
            for item in data.get("items") or []:
                media = item.get("media", {}).get("m", "")
                big = re.sub(r"_[mst]\.jpg", "_b.jpg", media)
                title = item.get("title", "")
                if big and name_in_text(title + " " + big, name):
                    out.append(big)
        except Exception:
            pass
        time.sleep(0.6)
    return out


def download(url: str, dest: Path) -> bool:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=50) as resp:
                data = resp.read()
            if len(data) < 2500:
                return False
            dest.write_bytes(data)
            return True
        except Exception:
            time.sleep(2 + attempt * 2)
    return False


def actor_names() -> list[str]:
    names: set[str] = set()
    if REG.exists():
        names.update(json.loads(REG.read_text(encoding="utf-8")).keys())
    if OUT_LOCAL.exists():
        names.update(json.loads(OUT_LOCAL.read_text(encoding="utf-8")).keys())
    if CACHE.exists():
        names.update(json.loads(CACHE.read_text(encoding="utf-8")).keys())
    return sorted(names)


def fill_actor(name: str, local: dict, cache: dict) -> int:
    slug = slugify(name)
    folder = SITE_GAL / slug
    folder.mkdir(parents=True, exist_ok=True)
    kept: list[str] = []
    seen: set[str] = set()
    for p in sorted(folder.glob("*")):
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and p.stat().st_size > 2000:
            # compact renumber later by rebuilding list from files already sequential
            pass
    # Prefer existing gallery_local paths that still exist
    for rel in local.get(name) or []:
        cand = ROOT / "site" / rel
        if cand.exists() and cand.stat().st_size > 2000:
            kept.append(rel)
            seen.add(cand.name.lower())
    if len(kept) >= TARGET:
        local[name] = kept[:TARGET]
        return len(kept)

    qid = wikidata_qid(name)
    titles = commons_titles(name, qid)
    urls = imageinfo(titles)
    urls.extend(u for u in flickr_urls(name) if u not in urls)
    cache[name] = urls

    for u in urls:
        if len(kept) >= TARGET:
            break
        key = Path(urllib.parse.urlparse(u).path).name.lower()
        key_norm = re.sub(r"^\d+px-", "", key)
        if key in seen or key_norm in seen:
            continue
        seen.add(key)
        seen.add(key_norm)
        ext = ".png" if ".png" in key else ".jpg"
        dest = folder / f"{len(kept):02d}{ext}"
        if dest.exists() and dest.stat().st_size > 2000:
            kept.append(f"assets/galleries/{slug}/{dest.name}")
            continue
        if download(u, dest):
            kept.append(f"assets/galleries/{slug}/{dest.name}")
            time.sleep(0.9)
        else:
            time.sleep(1.5)

    local[name] = kept[:TARGET]
    return len(kept)


def main() -> None:
    SITE_GAL.mkdir(parents=True, exist_ok=True)
    local = json.loads(OUT_LOCAL.read_text(encoding="utf-8")) if OUT_LOCAL.exists() else {}
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    names = actor_names()
    names = sorted(names, key=lambda n: (len(local.get(n) or []), n))
    for i, name in enumerate(names, 1):
        before = len(local.get(name) or [])
        if before >= TARGET:
            continue
        try:
            n = fill_actor(name, local, cache)
            print(f"[{i}/{len(names)}] {name}: {before} -> {n}")
        except Exception as e:
            print(f"[{i}/{len(names)}] {name}: FAIL {e}")
            time.sleep(2)
        if i % 3 == 0:
            OUT_LOCAL.write_text(json.dumps(local, indent=2), encoding="utf-8")
            CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
        time.sleep(0.4)
    OUT_LOCAL.write_text(json.dumps(local, indent=2), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    g25 = sum(1 for v in local.values() if len(v or []) >= 25)
    g10 = sum(1 for v in local.values() if len(v or []) >= 10)
    print(f"done: {g25} with 25+; {g10} with 10+; tracked {len(local)}")


if __name__ == "__main__":
    main()
