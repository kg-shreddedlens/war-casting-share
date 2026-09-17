# -*- coding: utf-8 -*-
"""Fill Dafne Keen from allowlisted adult TMDB + exact Getty thumb URLs (named her)."""
from __future__ import annotations

import json
import re
import shutil
import time
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
MIN_BYTES = 8000

ADULT_TMDB = [
    "g325OIjIHrFr0te8ewPfhKQ2SKj",
    "34BhddK5z2YHjfppOleezVrQ7Jt",
    "gGDU5FPJXF3Psb8TPeTemchQyBR",
    "mkCimIAtCD8GfDfSntE80onoDOQ",
    "dzdZBkWrdZMzElZuMzxG0prl334",
    "pUEGkV7s2dSawhANUIJhyLoJDK3",
]

# Exact Getty CDN URLs from newest search (filenames contain dafne-keen). Prefer solo shots first.
GETTY = [
    # Vanity Fair 2026 — current adult
    "https://media.gettyimages.com/id/2266056726/photo/los-angeles-california-dafne-keen-attends-as-vanity-fair-hosts-vanities-a-night-for-young.jpg?s=612x612&w=0&k=20&c=UeHFiVA4yr9miy11_God-9iA31zOH-GTsLyi_fG53xs=",
    "https://media.gettyimages.com/id/2265514475/photo/dafne-keen-fern%C3%A1ndez-at-vanity-fairs-the-2026-vanities-party-a-night-for-young-hollywood-held.jpg?s=612x612&w=0&k=20&c=hKXzSWhU83nGuwgBhVjxNteLC-TYLt4MYTpdlGdoI-s=",
    "https://media.gettyimages.com/id/2265510813/photo/dafne-keen-fern%C3%A1ndez-at-vanity-fairs-the-2026-vanities-party-a-night-for-young-hollywood-held.jpg?s=612x612&w=0&k=20&c=aSnuYQFnowY98zTg2aiXh611EgwAXUpAMuwecS2oATg=",
    "https://media.gettyimages.com/id/2265510653/photo/dafne-keen-fern%C3%A1ndez-at-vanity-fairs-the-2026-vanities-party-a-night-for-young-hollywood-held.jpg?s=612x612&w=0&k=20&c=TYQjMBjoBZZb5wqEMUfqgfEGx4Q77G9-9h4jWFZOCNo=",
    "https://media.gettyimages.com/id/2265509512/photo/dafne-keen-fern%C3%A1ndez-at-vanity-fairs-the-2026-vanities-party-a-night-for-young-hollywood-held.jpg?s=612x612&w=0&k=20&c=J_oH_Dw7t4w95Lj-9ZFx-901IpDuNpL2UdJE8h7uznI=",
    "https://media.gettyimages.com/id/2265503518/photo/dafne-keen-fern%C3%A1ndez-at-vanity-fairs-the-2026-vanities-party-a-night-for-young-hollywood-held.jpg?s=612x612&w=0&k=20&c=a0ErLy1zeqJiB8KvTlOQf9e_hnqRkO-_6t9vkPiN_qU=",
    "https://media.gettyimages.com/id/2265499876/photo/dafne-keen-fern%C3%A1ndez-at-vanity-fairs-the-2026-vanities-party-a-night-for-young-hollywood-held.jpg?s=612x612&w=0&k=20&c=e-d6cJ4aRyWivC8ROpH7u1cPd3GZ-qsUouz3vY762O8=",
    "https://media.gettyimages.com/id/2265495103/photo/dafne-keen-fern%C3%A1ndez-at-vanity-fairs-the-2026-vanities-party-a-night-for-young-hollywood-held.jpg?s=612x612&w=0&k=20&c=ZF2TAZDtm5GqoJubgLCBmxzDxyWxjELfMsvkpLfOShc=",
    "https://media.gettyimages.com/id/2265494782/photo/dafne-keen-fern%C3%A1ndez-at-vanity-fairs-the-2026-vanities-party-a-night-for-young-hollywood-held.jpg?s=612x612&w=0&k=20&c=YiRZFqXEsup5AxKn3AzA0VAaQehI5fVoHHHhnr7X2j4=",
    # London Critics Circle 2026 — solo-ish
    "https://media.gettyimages.com/id/2251432058/photo/london-england-dafne-keen-attends-the-46th-london-critics-circle-film-awards-nominations.jpg?s=612x612&w=0&k=20&c=XCR6dLcUcwxm7CJRuS7MKhZ1Qamy2Xu9RkEzyIn5YLQ=",
    "https://media.gettyimages.com/id/2251431680/photo/london-england-dafne-keen-attends-the-46th-london-critics-circle-film-awards-nominations.jpg?s=612x612&w=0&k=20&c=rNnchsgtTYXYQr2s-Q0tTqL4xWDNMotRrS2fAfNkBK8=",
    "https://media.gettyimages.com/id/2251432075/photo/london-england-dafne-keen-attends-the-46th-london-critics-circle-film-awards-nominations.jpg?s=612x612&w=0&k=20&c=Ostj43D-ozaXslN5HiMNs2DxLA-C809OB1-ep60b7GY=",
    "https://media.gettyimages.com/id/2251431596/photo/london-england-dafne-keen-attends-the-46th-london-critics-circle-film-awards-nominations.jpg?s=612x612&w=0&k=20&c=sxb37C3YBmlHdqpCtdCQ54WPjFEL-w_g4pnN7zcMaCM=",
    "https://media.gettyimages.com/id/2251441634/photo/london-england-dafne-keen-and-jay-lycurgo-attend-the-46th-london-critics-circle-film-awards.jpg?s=612x612&w=0&k=20&c=LQ0nc-bI9B9-Gs-pXrCLzsdBQra5bDErjSbVzjRQ1lM=",
    "https://media.gettyimages.com/id/2251441265/photo/london-england-dafne-keen-and-jay-lycurgo-attend-the-46th-london-critics-circle-film-awards.jpg?s=612x612&w=0&k=20&c=mjXTsVgl8s3BEd-LfLwUyDNcQT6jGKcR26YaoPueGXk=",
    "https://media.gettyimages.com/id/2251441431/photo/london-england-dafne-keen-and-jay-lycurgo-attend-the-46th-london-critics-circle-film-awards.jpg?s=612x612&w=0&k=20&c=JalnzBUnQ-8uNRJdBXWGLnwhnnULpIVr-ceg1yha-P0=",
    "https://media.gettyimages.com/id/2251441245/photo/london-england-dafne-keen-and-jay-lycurgo-attend-the-46th-london-critics-circle-film-awards.jpg?s=612x612&w=0&k=20&c=dJcpK3lCfhngTsN3_VvZak7Df_2SINJX_spT0MLCoes=",
    "https://media.gettyimages.com/id/2251441308/photo/london-england-dafne-keen-and-jay-lycurgo-attend-the-46th-london-critics-circle-film-awards.jpg?s=612x612&w=0&k=20&c=ttAnM2mcy-tbywQ_Cbk5fCkTm-Wx12T0CHU4W8BTDaE=",
    "https://media.gettyimages.com/id/2251441494/photo/london-england-dafne-keen-and-jay-lycurgo-attend-the-46th-london-critics-circle-film-awards.jpg?s=612x612&w=0&k=20&c=SSCkiyYVGe9qP2n_0SzDqmrVNjbNGl2MYmqOm_XLBoE=",
    "https://media.gettyimages.com/id/2251433735/photo/london-england-dafne-keen-and-jay-lycurgo-attend-the-46th-london-critics-circle-film-awards.jpg?s=612x612&w=0&k=20&c=Z3_ktn3bv0dwfcYcnlf9gg21n67BYhFjhJrn_v3UOxk=",
    "https://media.gettyimages.com/id/2251433403/photo/london-england-dafne-keen-and-jay-lycurgo-attend-the-46th-london-critics-circle-film-awards.jpg?s=612x612&w=0&k=20&c=vCLfKFVGd3G9SI6OaMbDtKm-NagA3y8s6Xhb6rNYH7c=",
    "https://media.gettyimages.com/id/2251433409/photo/london-england-dafne-keen-and-jay-lycurgo-attend-the-46th-london-critics-circle-film-awards.jpg?s=612x612&w=0&k=20&c=CetkviUyzgIm4reF6GupKCZuisN4e5EKaxqymeCgPp4=",
]


def get(url: str, referer: str = "https://www.gettyimages.com/") -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
            "Referer": referer,
        },
    )
    with urllib.request.urlopen(req, timeout=55) as resp:
        return resp.read()


def main() -> None:
    # Headshot-first: recent Getty solo, then TMDB adult, then more Getty
    urls: list[str] = []
    urls.extend(GETTY[:4])
    urls.extend([f"https://image.tmdb.org/t/p/w780/{h}.jpg" for h in ADULT_TMDB])
    urls.extend(GETTY[4:])

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
    for u in urls:
        if len(kept) >= TARGET:
            break
        mid = re.search(r"/id/(\d+)/", u)
        key = mid.group(1) if mid else u.rsplit("/", 1)[-1][:40]
        if key in seen:
            continue
        try:
            data = get(u, "https://www.themoviedb.org/" if "tmdb" in u else "https://www.gettyimages.com/")
        except Exception as e:
            print("fail", key, e)
            continue
        if len(data) < MIN_BYTES:
            continue
        if not (data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n"):
            print("skip type", key)
            continue
        seen.add(key)
        dest = SITE_GAL / f"{len(kept):02d}.jpg"
        dest.write_bytes(data)
        kept.append(f"assets/galleries/dafne-keen/{dest.name}")
        print("ok", dest.name, len(data), key)
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
