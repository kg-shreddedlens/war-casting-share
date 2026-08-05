# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCSWAMP = ROOT.parent
SITE_HS = ROOT / "site" / "assets" / "headshots"
MEDIA = DOCSWAMP / "media" / "cast-headshots"
REG = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"


def get(url: str, referer: str | None = None) -> bytes:
    h = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        h["Referer"] = referer
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=50) as resp:
        return resp.read()


def save(name: str, data: bytes) -> Path:
    SITE_HS.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    dest = SITE_HS / f"{slug}.jpg"
    dest.write_bytes(data)
    shutil.copy2(dest, MEDIA / dest.name)
    reg = json.loads(REG.read_text(encoding="utf-8"))
    rec = reg.get(name) or {"name": name}
    rec["headshot"] = f"media/cast-headshots/{dest.name}"
    reg[name] = rec
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    print(name, "saved", len(data))
    return dest


def extract_imgs(html: str) -> list[str]:
    urls = []
    for u in re.findall(r"https://[^\"'\s>]+\.(?:jpg|jpeg|png|webp)", html, re.I):
        u = u.split("?")[0]
        low = u.lower()
        if any(x in low for x in ("logo", "sprite", "icon", "emoji", "svg", "1x1", "pixel")):
            continue
        if u not in urls:
            urls.append(u)
    # amazon media special
    for u in re.findall(r"https://m\.media-amazon\.com/images/[^\"'\s]+", html):
        u = u.split("?")[0]
        if u not in urls:
            urls.append(u)
    return urls


def try_pages(name: str, pages: list[tuple[str, str | None]]) -> bool:
    for url, ref in pages:
        try:
            html = get(url, ref).decode("utf-8", "replace")
        except Exception as e:
            print("fail page", url, e)
            continue
        for img in extract_imgs(html)[:30]:
            try:
                data = get(img, referer=url)
                if len(data) < 8000:
                    continue
                # skip tiny/icons
                if len(data) > 2_500_000:
                    continue
                save(name, data)
                print(" from", img[:100])
                return True
            except Exception:
                continue
    return False


def main() -> None:
    ok_a = try_pages(
        "Arica Himmel",
        [
            ("https://www.imdb.com/name/nm8585540/", "https://www.imdb.com/"),
            ("https://www.famousbirthdays.com/people/arica-himmel.html", None),
            ("https://www.earnthenecklace.com/arica-himmel-wiki/", None),
            ("https://www.themoviedb.org/person/3991351-arica-himmel", "https://www.themoviedb.org/"),
        ],
    )
    ok_b = try_pages(
        "Brandon Mendez Harper",
        [
            ("https://www.google.com/search?q=Brandon+Mendez+Harper+actor&tbm=isch", None),
            ("https://duckduckgo.com/?q=Brandon+Mendez+Harper+actor&iax=images&ia=images", None),
            ("https://www.imdb.com/find/?q=Brandon+Mendez+Harper", "https://www.imdb.com/"),
        ],
    )
    print("Arica", ok_a, "Brandon", ok_b)


if __name__ == "__main__":
    main()
