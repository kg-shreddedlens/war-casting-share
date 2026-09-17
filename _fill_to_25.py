# -*- coding: utf-8 -*-
"""Top every casting-share actor gallery up to 25 stills via TMDB (+ keep existing files)."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GAL = ROOT / "site" / "assets" / "galleries"
OUT = ROOT / "gallery_local.json"
REG = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TARGET = 25
MIN_BYTES = 7000


def slugify(name: str) -> str:
    s = name.lower().replace("'", "").replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def get_bytes(url: str, referer: str | None = None) -> bytes:
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read()


def get_text(url: str) -> str:
    return get_bytes(url).decode("utf-8", "replace")


def tmdb_search(name: str) -> tuple[int, str] | None:
    q = urllib.parse.quote(name)
    html = get_text(f"https://www.themoviedb.org/search/person?query={q}")
    # /person/123-slug
    pats = re.findall(r'href="/person/(\d+)-([a-z0-9\-]+)"', html, re.I)
    if not pats:
        return None
    # Prefer exact slug-ish match
    want = slugify(name)
    for pid, slug in pats:
        if slug == want or want in slug or slug in want:
            return int(pid), slug
    return int(pats[0][0]), pats[0][1]


def tmdb_profile_urls(tmdb_id: int, slug: str) -> list[str]:
    urls: list[str] = []
    pages = [
        f"https://www.themoviedb.org/person/{tmdb_id}-{slug}/images/profiles",
        f"https://www.themoviedb.org/person/{tmdb_id}-{slug}",
    ]
    for page in pages:
        try:
            html = get_text(page)
        except Exception as e:
            print("  tmdb page fail", page, e)
            continue
        for f in re.findall(r"image\.tmdb\.org/t/p/(?:original|w\d+(?:_and_h\d+_face)?)/([A-Za-z0-9]+)\.jpg", html):
            u = f"https://image.tmdb.org/t/p/w780/{f}.jpg"
            if u not in urls:
                urls.append(u)
        time.sleep(0.35)
    return urls


def ddg_image_urls(name: str, limit: int = 40) -> list[str]:
    """DuckDuckGo image results (vqd token flow)."""
    urls: list[str] = []
    try:
        landing = get_text("https://duckduckgo.com/?" + urllib.parse.urlencode({"q": name, "iax": "images", "ia": "images"}))
        m = re.search(r"vqd(?:=|\\\":\\\")([0-9-]+)", landing)
        if not m:
            m = re.search(r"vqd='([0-9-]+)'", landing)
        if not m:
            # alternate: html homepage cookie-less
            html = get_text(
                "https://duckduckgo.com/i.js?"
                + urllib.parse.urlencode({"q": f"{name} actress OR actor", "o": "json", "p": "1", "s": "0"})
            )
            for u in re.findall(r'"image"\s*:\s*"(https?://[^"]+)"', html):
                u = u.encode("utf-8").decode("unicode_escape") if "\\u" in u else u
                if u not in urls:
                    urls.append(u)
            return urls[:limit]
        vqd = m.group(1)
        api = (
            "https://duckduckgo.com/i.js?"
            + urllib.parse.urlencode(
                {
                    "l": "us-en",
                    "o": "json",
                    "q": name,
                    "vqd": vqd,
                    "f": ",,,,,",
                    "p": "1",
                }
            )
        )
        raw = get_bytes(api, referer="https://duckduckgo.com/").decode("utf-8", "replace")
        for u in re.findall(r'"image"\s*:\s*"(https?://[^"]+)"', raw):
            u = bytes(u, "utf-8").decode("unicode_escape") if "\\u" in u else u
            low = u.lower()
            if any(x in low for x in ("svg", "logo", "sprite", "icon", "pixel")):
                continue
            if u not in urls:
                urls.append(u)
            if len(urls) >= limit:
                break
    except Exception as e:
        print("  ddg fail", e)
    return urls


def existing_paths(name: str, local: dict) -> list[str]:
    slug = slugify(name)
    folder = GAL / slug
    disk: list[str] = []
    if folder.exists():
        for p in sorted(folder.iterdir(), key=lambda x: x.name):
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                disk.append(f"assets/galleries/{slug}/{p.name}")
    prev = [u for u in (local.get(name) or []) if u]
    # Prefer disk truth
    return disk if len(disk) >= len(prev) else prev


def next_index(folder: Path) -> int:
    nums = []
    for p in folder.glob("*"):
        m = re.match(r"^(\d+)", p.stem)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 0


def fill_one(name: str, local: dict) -> int:
    have = existing_paths(name, local)
    if len(have) >= TARGET:
        local[name] = have[:TARGET]
        return len(have)
    print(f"\n=== {name} have={len(have)} ===")
    try:
        hit = tmdb_search(name)
    except Exception as e:
        print("  search fail", e)
        local[name] = have
        return len(have)
    if not hit:
        print("  no tmdb")
        local[name] = have
        return len(have)
    tid, slug = hit
    print(f"  tmdb {tid}-{slug}")
    urls = tmdb_profile_urls(tid, slug)
    if len(urls) < TARGET:
        extra = ddg_image_urls(name, limit=50)
        print(f"  ddg +{len(extra)}")
        for u in extra:
            if u not in urls:
                urls.append(u)
    print(f"  urls {len(urls)}")

    folder = GAL / slugify(name)
    folder.mkdir(parents=True, exist_ok=True)
    kept = list(have)
    seen = {Path(p).name.lower() for p in kept}
    seen |= {u.rsplit("/", 1)[-1].lower() for u in urls[:0]}
    idx = next_index(folder)

    for u in urls:
        if len(kept) >= TARGET:
            break
        key = u.rsplit("/", 1)[-1].lower()
        if key in seen:
            continue
        seen.add(key)
        ext = ".png" if key.endswith(".png") else ".jpg"
        dest = folder / f"{idx:02d}{ext}"
        idx += 1
        try:
            data = get_bytes(u, referer="https://www.themoviedb.org/")
            if len(data) < MIN_BYTES:
                continue
            dest.write_bytes(data)
            kept.append(f"assets/galleries/{folder.name}/{dest.name}")
            print("  ok", dest.name, len(data))
            time.sleep(0.15)
        except Exception as e:
            print("  fail", key, e)
    local[name] = kept[:TARGET]
    print(f"  -> {len(local[name])}")
    return len(local[name])


def main() -> None:
    import sys

    local = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    names = sorted(local)
    if REG.exists():
        for n in json.loads(REG.read_text(encoding="utf-8")):
            if n not in local:
                local[n] = []
                names.append(n)
    names = sorted(set(names))
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    if only:
        names = [n for n in names if n in only or slugify(n) in only]
    # Prioritize sparse
    names.sort(key=lambda n: len(existing_paths(n, local)))
    for name in names:
        if only is None and len(existing_paths(name, local)) >= TARGET:
            local[name] = existing_paths(name, local)[:TARGET]
            continue
        fill_one(name, local)
        OUT.write_text(json.dumps(local, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # final sync write
    OUT.write_text(json.dumps(local, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    under = sum(1 for n in local if len(local[n] or []) < TARGET)
    print("\nDONE under25=", under, "at25+=", sum(1 for n in local if len(local[n] or []) >= TARGET))


if __name__ == "__main__":
    main()
