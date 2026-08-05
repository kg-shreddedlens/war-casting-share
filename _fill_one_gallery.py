# -*- coding: utf-8 -*-
"""Refill one actor from Commons category + Wikidata depicts, slowly."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE_GAL = ROOT / "site" / "assets" / "galleries"
OUT_LOCAL = ROOT / "gallery_local.json"
CACHE = ROOT / "gallery_cache.json"
UA = "ShreddedLensCastingBot/1.2 (https://shreddedlens.com; casting stills)"
TARGET = 25


def slugify(name: str) -> str:
    s = name.lower().replace("'", "").replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


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
    data = api(url)
    for item in data.get("search") or []:
        label = (item.get("label") or "").lower()
        desc = (item.get("description") or "").lower()
        if label == name.lower() or "actor" in desc or "actress" in desc or "filmmaker" in desc:
            return item["id"]
    if data.get("search"):
        return data["search"][0]["id"]
    return None


def commons_titles(name: str, qid: str | None) -> list[str]:
    titles: list[str] = []
    # Category:Name
    for cat in (f"Category:{name}",):
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": cat,
                "cmtype": "file",
                "cmlimit": 100,
                "format": "json",
            }
        )
        try:
            data = api(url)
            for m in data.get("query", {}).get("categorymembers", []) or []:
                t = m.get("title") or ""
                if t and t not in titles:
                    titles.append(t)
        except Exception as e:
            print("cat fail", e)
        time.sleep(1.0)
    if qid:
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "query",
                "list": "search",
                "srsearch": f"haswbstatement:P180={qid}",
                "srnamespace": 6,
                "srlimit": 50,
                "format": "json",
            }
        )
        try:
            data = api(url)
            for h in data.get("query", {}).get("search", []) or []:
                t = h.get("title") or ""
                if t and t not in titles:
                    titles.append(t)
        except Exception as e:
            print("depicts fail", e)
        time.sleep(1.0)
    # name search fallback
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": f'"{name}"',
            "srnamespace": 6,
            "srlimit": 50,
            "format": "json",
        }
    )
    data = api(url)
    tokens = [p.lower() for p in re.findall(r"[A-Za-z]+", name) if len(p) > 1]
    for h in data.get("query", {}).get("search", []) or []:
        t = h.get("title") or ""
        tl = t.lower()
        if any(x in tl for x in ("svg", "pdf", "churchill", "marlborough", "coat of arms")):
            continue
        if len(tokens) >= 2 and tokens[0] in tl and tokens[-1] in tl:
            if t not in titles:
                titles.append(t)
    return titles


def image_urls(titles: list[str]) -> list[str]:
    urls: list[str] = []
    for i in range(0, len(titles), 15):
        chunk = titles[i : i + 15]
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "query",
                "titles": "|".join(chunk),
                "prop": "imageinfo",
                "iiprop": "url|mime|size",
                "iiurlwidth": 500,
                "format": "json",
            }
        )
        data = api(url)
        for p in (data.get("query", {}).get("pages") or {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            mime = (ii.get("mime") or "").lower()
            if "svg" in mime or "pdf" in mime:
                continue
            src = (ii.get("thumburl") or ii.get("url") or "").split("?")[0]
            if src and src not in urls:
                urls.append(src)
        time.sleep(1.2)
    return urls


def download(url: str, dest: Path) -> bool:
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=50) as resp:
                data = resp.read()
            if len(data) < 2500:
                return False
            dest.write_bytes(data)
            return True
        except Exception as e:
            print(f"  retry {attempt+1}: {e}")
            time.sleep(3 + attempt * 2)
    return False


def fill(name: str) -> int:
    qid = wikidata_qid(name)
    print(name, "QID", qid)
    titles = commons_titles(name, qid)
    print("titles", len(titles))
    urls = image_urls(titles)
    print("urls", len(urls))
    slug = slugify(name)
    folder = SITE_GAL / slug
    folder.mkdir(parents=True, exist_ok=True)
    # keep existing good files
    kept: list[str] = []
    seen: set[str] = set()
    for p in sorted(folder.glob("*")):
        if p.stat().st_size > 2000 and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            # renumber later
            pass
    # fresh sequential write into temp then rename — keep uniques by content hash size+name
    for u in urls:
        if len(kept) >= TARGET:
            break
        key = Path(urllib.parse.urlparse(u).path).name.lower()
        if key in seen:
            continue
        seen.add(key)
        ext = ".png" if ".png" in key else ".jpg"
        dest = folder / f"{len(kept):02d}{ext}"
        if dest.exists() and dest.stat().st_size > 2000:
            kept.append(f"assets/galleries/{slug}/{dest.name}")
            continue
        print("dl", len(kept) + 1, key[:70])
        if download(u, dest):
            kept.append(f"assets/galleries/{slug}/{dest.name}")
            time.sleep(1.5)
        else:
            time.sleep(2.5)
    local = json.loads(OUT_LOCAL.read_text(encoding="utf-8")) if OUT_LOCAL.exists() else {}
    local[name] = kept
    OUT_LOCAL.write_text(json.dumps(local, indent=2), encoding="utf-8")
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    cache[name] = urls
    CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    print("kept", len(kept))
    return len(kept)


if __name__ == "__main__":
    import sys

    name = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Winston Duke"
    fill(name)
