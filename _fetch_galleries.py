# -*- coding: utf-8 -*-
"""Fetch actor image galleries via Wikipedia REST media-list (gentler than Commons search)."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCSWAMP = ROOT.parent
OUT = ROOT / "gallery_cache.json"
UA = "ShreddedLensCastingBot/1.0 (casting research)"
SKIP = re.compile(r"(logo|icon|flag|signature|svg|commons-logo|wikidata|edit-clear|symbol)", re.I)


def rest_media(title: str) -> list[str]:
    slug = title.replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/media-list/{urllib.parse.quote(slug)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    urls = []
    for item in data.get("items") or []:
        if item.get("type") and item.get("type") != "image":
            continue
        title_f = item.get("title") or ""
        if SKIP.search(title_f):
            continue
        src = item.get("src") or ""
        if not src and item.get("srcset"):
            # pick largest
            srcset = sorted(item["srcset"], key=lambda x: x.get("scale", 1), reverse=True)
            src = srcset[0].get("src") or ""
        if src.startswith("//"):
            src = "https:" + src
        # bump thumb size
        src = re.sub(r"/\d+px-", "/800px-", src)
        if not src:
            continue
        if SKIP.search(src):
            continue
        if any(x in src.lower() for x in [".svg", "signature"]):
            continue
        if src not in urls:
            urls.append(src)
        if len(urls) >= 10:
            break
    return urls[:10]


def names() -> list[str]:
    out = set()
    for path in DOCSWAMP.glob("SLS Casting Shred - WAR - Character*.md"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2 or not cells[0].isdigit():
                continue
            actor = re.sub(r"\*+", "", cells[1]).strip()
            if actor and not actor.startswith("CD Match") and actor != "Actor":
                out.add(actor)
    return sorted(out)


def main() -> None:
    cache = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    all_names = names()
    print(f"{len(all_names)} actors")
    for i, name in enumerate(all_names, 1):
        if len(cache.get(name) or []) >= 5:
            continue
        try:
            urls = rest_media(name)
            # try alternate titles
            if len(urls) < 3 and "'" in name:
                urls = rest_media(name.replace("'", "")) or urls
            cache[name] = urls
            print(f"[{i}/{len(all_names)}] {name}: {len(urls)}")
            if i % 5 == 0:
                OUT.write_text(json.dumps(cache, indent=2), encoding="utf-8")
            time.sleep(0.9)
        except Exception as e:
            print(f"[{i}/{len(all_names)}] {name}: {e}")
            cache.setdefault(name, [])
            time.sleep(1.5)
    OUT.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    ok = sum(1 for v in cache.values() if len(v) >= 3)
    print(f"done; {ok}/{len(cache)} with >=3 images")


if __name__ == "__main__":
    main()
