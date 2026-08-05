# -*- coding: utf-8 -*-
"""Ensure every real shortlist actor has a local headshot + gallery seed."""
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
SITE_HS = ROOT / "site" / "assets" / "headshots"
SITE_GAL = ROOT / "site" / "assets" / "galleries"
MEDIA_HS = DOCSWAMP / "media" / "cast-headshots"
REG = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")
GALLERY_LOCAL = ROOT / "gallery_local.json"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
MIN_BYTES = 6000
TARGET_GAL = 25

SKIP_PREFIXES = ("CD Match",)


def slugify(name: str) -> str:
    s = name.lower().replace("'", "").replace("'", "").replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def get_bytes(url: str, referer: str | None = None) -> bytes:
    headers = {"User-Agent": UA, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=50) as resp:
        return resp.read()


def get_text(url: str, referer: str | None = None) -> str:
    return get_bytes(url, referer).decode("utf-8", "replace")


def has_headshot(name: str, rec: dict) -> Path | None:
    slug = slugify(name)
    candidates = [
        SITE_HS / f"{slug}.jpg",
        SITE_HS / f"{slug}.png",
        MEDIA_HS / f"{slug}.jpg",
        MEDIA_HS / f"{slug}.png",
    ]
    hs = rec.get("headshot") or ""
    if hs.startswith("media/"):
        candidates.insert(0, DOCSWAMP / hs)
    elif hs.startswith("assets/"):
        candidates.insert(0, ROOT / "site" / hs)
    for p in candidates:
        if p.exists() and p.stat().st_size >= MIN_BYTES:
            return p
    # gallery first frame
    gal = SITE_GAL / slug
    if gal.exists():
        for p in sorted(gal.glob("*")):
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and p.stat().st_size >= MIN_BYTES:
                return p
    return None


def tmdb_search(name: str) -> tuple[int, str] | None:
    q = urllib.parse.quote(name)
    html = get_text(f"https://www.themoviedb.org/search/person?query={q}")
    pats = re.findall(r'href="/person/(\d+)-([a-z0-9\-]+)"', html, re.I)
    if not pats:
        return None
    want = slugify(name)
    for pid, slug in pats:
        if slug == want or want in slug or slug.replace("-", "") in want.replace("-", ""):
            return int(pid), slug
    return int(pats[0][0]), pats[0][1]


def tmdb_urls(tmdb_id: int, slug: str) -> list[str]:
    urls: list[str] = []
    for page in (
        f"https://www.themoviedb.org/person/{tmdb_id}-{slug}/images/profiles",
        f"https://www.themoviedb.org/person/{tmdb_id}-{slug}",
    ):
        try:
            html = get_text(page)
        except Exception:
            continue
        for f in re.findall(
            r"image\.tmdb\.org/t/p/(?:original|w\d+(?:_and_h\d+_face)?)/([A-Za-z0-9]+)\.jpg",
            html,
        ):
            u = f"https://image.tmdb.org/t/p/w780/{f}.jpg"
            if u not in urls:
                urls.append(u)
        time.sleep(0.25)
    return urls


def imdb_primary_url(imdb_id: str | None) -> str | None:
    if not imdb_id:
        return None
    # Media viewer JSON-ish endpoints often blocked; try name page og:image
    try:
        html = get_text(f"https://www.imdb.com/name/{imdb_id}/", referer="https://www.imdb.com/")
    except Exception:
        return None
    m = re.search(
        r'property="og:image"\s+content="(https://[^"]+)"',
        html,
    ) or re.search(r'content="(https://m\.media-amazon\.com/images/[^"]+)"', html)
    if not m:
        return None
    u = m.group(1).split("?")[0]
    # bump size
    u = re.sub(r"\._V1_[^.]+\.", "._V1_QL75_UX500_.", u)
    if "media-amazon.com" in u or "amazon" in u:
        return u
    return u


def wikipedia_thumb(name: str) -> str | None:
    try:
        api = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "query",
                "titles": name,
                "prop": "pageimages",
                "pithumbsize": 800,
                "format": "json",
            }
        )
        req = urllib.request.Request(api, headers={"User-Agent": "ShreddedLensCastingBot/1.4"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for page in (data.get("query", {}).get("pages") or {}).values():
            thumb = (page.get("thumbnail") or {}).get("source")
            if thumb:
                return thumb
    except Exception:
        return None
    return None


def save_headshot(name: str, data: bytes) -> Path:
    slug = slugify(name)
    SITE_HS.mkdir(parents=True, exist_ok=True)
    MEDIA_HS.mkdir(parents=True, exist_ok=True)
    dest = SITE_HS / f"{slug}.jpg"
    dest.write_bytes(data)
    shutil.copy2(dest, MEDIA_HS / f"{slug}.jpg")
    return dest


def seed_gallery(name: str, urls: list[str], local: dict) -> None:
    slug = slugify(name)
    folder = SITE_GAL / slug
    folder.mkdir(parents=True, exist_ok=True)
    existing = sorted(
        [p for p in folder.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}],
        key=lambda p: p.name,
    )
    kept = [f"assets/galleries/{slug}/{p.name}" for p in existing]
    seen = {p.name.lower() for p in existing}
    idx = len(existing)
    for u in urls:
        if len(kept) >= TARGET_GAL:
            break
        key = u.rsplit("/", 1)[-1].lower()[:80]
        if key in seen:
            continue
        try:
            data = get_bytes(u, referer="https://www.themoviedb.org/")
            if len(data) < MIN_BYTES:
                continue
            dest = folder / f"{idx:02d}.jpg"
            dest.write_bytes(data)
            kept.append(f"assets/galleries/{slug}/{dest.name}")
            seen.add(dest.name.lower())
            idx += 1
            time.sleep(0.12)
        except Exception:
            continue
    local[name] = kept


def fill_one(name: str, rec: dict, local: dict) -> bool:
    print(f"\n=== {name} ===")
    existing = has_headshot(name, rec)
    urls: list[str] = []
    try:
        hit = tmdb_search(name)
    except Exception as e:
        print(" tmdb search fail", e)
        hit = None
    if hit:
        print(" tmdb", hit)
        urls = tmdb_urls(*hit)
    imdb_u = imdb_primary_url(rec.get("imdb_id"))
    if imdb_u:
        print(" imdb og", imdb_u[:90])
        urls.insert(0, imdb_u)
    wiki = wikipedia_thumb(name)
    if wiki:
        print(" wiki", wiki[:90])
        urls.append(wiki)

    if not urls and not existing:
        print(" NO URLS")
        return False

    # Prefer fresh download for headshot if missing
    if not existing:
        saved = False
        for u in urls:
            try:
                data = get_bytes(
                    u,
                    referer="https://www.imdb.com/" if "amazon" in u else "https://www.themoviedb.org/",
                )
                if len(data) < MIN_BYTES:
                    continue
                path = save_headshot(name, data)
                rec["headshot"] = f"media/cast-headshots/{path.name}"
                print(" headshot", path.name, len(data))
                saved = True
                break
            except Exception as e:
                print(" fail", e)
        if not saved:
            print(" could not save headshot")
            return False
    else:
        # ensure site+media copies exist
        slug = slugify(name)
        site_p = SITE_HS / f"{slug}.jpg"
        if not site_p.exists():
            shutil.copy2(existing, site_p)
        media_p = MEDIA_HS / f"{slug}.jpg"
        if not media_p.exists():
            shutil.copy2(existing, media_p)
        rec["headshot"] = f"media/cast-headshots/{slug}.jpg"
        print(" already had", existing.name)

    seed_gallery(name, urls, local)
    print(" gallery", len(local.get(name) or []))
    return True


def main() -> None:
    reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {}
    local = json.loads(GALLERY_LOCAL.read_text(encoding="utf-8")) if GALLERY_LOCAL.exists() else {}
    names = sorted(reg)
    # Also include gallery keys / shortlist-only names
    for n in list(local):
        if n not in reg:
            reg[n] = {"name": n}

    missing = []
    for name in sorted(reg):
        if any(name.startswith(p) for p in SKIP_PREFIXES):
            continue
        if name in {"Anderson Paulo", "Brandon Mendez Harper", "Derek Morgan"} and not (
            reg.get(name) or {}
        ).get("imdb_id"):
            # still try
            pass
        if not has_headshot(name, reg.get(name) or {}):
            missing.append(name)

    print("missing headshots:", len(missing))
    for name in missing:
        rec = reg.get(name) or {"name": name}
        ok = fill_one(name, rec, local)
        reg[name] = rec
        REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
        GALLERY_LOCAL.write_text(json.dumps(local, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if not ok:
            print(" STILL MISSING", name)

    # Final audit
    still = [n for n in sorted(reg) if not any(n.startswith(p) for p in SKIP_PREFIXES) and not has_headshot(n, reg[n])]
    print("\nREMAINING", len(still))
    for n in still:
        print(" ", n)


if __name__ == "__main__":
    main()
