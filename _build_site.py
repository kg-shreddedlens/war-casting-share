# -*- coding: utf-8 -*-
"""Build High-Contrast Editorial casting share site v2.

Features:
- AI character profile circles on overview tiles + character heroes
- Actor headshot circles in shortlists
- IMDb / Wikipedia / Instagram / LinkedIn / Spotlight icons
- Clickable shortlist rows -> actor-in-role detail pages
- Expanded scorecards
- Reel thumbnails when enrichment provides YouTube ids
"""
from __future__ import annotations

import json
import re
import shutil
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DOCSWAMP = ROOT.parent
OUT = ROOT / "site"
ASSETS = OUT / "assets"
REG_PATH = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")
ENRICH_PATH = ROOT / "enrichment.json"
PORTRAIT_SRC = Path(
    r"C:\Users\kengr\.cursor\projects\c-Augen-Studios-Dropbox-Ken-Greenwood-Augen-Shredded-Lens-projects-projects-active-WAR\assets"
)

FONTS = (
    "https://fonts.googleapis.com/css2?family=Bebas+Neue"
    "&family=Newsreader:opsz,wght@6..72,400;6..72,600&display=swap"
)

CHARACTERS = [
    {
        "slug": "sheila",
        "file": "SLS Casting Shred - WAR - Character - Sheila Collier - 2026-08-05.md",
        "title": "Sheila Collier",
        "hero": "SHEILA",
        "tag": "Lead · marriage dread",
        "lede": "Prestige-pair anchor. Grief, suspicion, and the marriage that will not stay still.",
        "portrait": "characters/char-sheila.png",
    },
    {
        "slug": "james",
        "file": "SLS Casting Shred - WAR - Character - James Collier - 2026-08-05.md",
        "title": "James Collier",
        "hero": "JAMES",
        "tag": "Lead · uncanny husband",
        "lede": "Ambiguity craft over marquee default. Cast for the question, not the answer.",
        "portrait": "characters/char-james.png",
    },
    {
        "slug": "samantha",
        "file": "SLS Casting Shred - WAR - Character - Samantha - 2026-08-05.md",
        "title": "Samantha",
        "hero": "SAMANTHA",
        "tag": "Supporting · rational foil",
        "lede": "Sister-read ballast. Clarity that makes the uncanny harder to dismiss.",
        "portrait": "characters/char-samantha.png",
    },
    {
        "slug": "melina",
        "file": "SLS Casting Shred - WAR - Character - Melina - 2026-08-05.md",
        "title": "Melina",
        "hero": "MELINA",
        "tag": "Supporting · soft temptation",
        "lede": "Workplace gravity without vamp. Attraction that stays inside the frame.",
        "portrait": "characters/char-melina.png",
    },
    {
        "slug": "norman",
        "file": "SLS Casting Shred - WAR - Character - Detective Norman - 2026-08-05.md",
        "title": "Detective Norman",
        "hero": "NORMAN",
        "tag": "Supporting · case ballast",
        "lede": "Procedural silence for an ambiguous marriage thriller. Cast for the unfinished file.",
        "portrait": "characters/char-norman.png",
    },
]

ENSEMBLE = {
    "slug": "ensemble",
    "file": "SLS Casting Shred - WAR - Ensemble - 2026-08-05.md",
    "title": "Ensemble Packages",
    "hero": "ENSEMBLE",
    "tag": "Package architecture",
    "lede": "Sales-Max, Balanced, and Lean Discovery packages scored for PoS and ROI.",
}

# Fallback curated reels / profiles if enrichment.json is incomplete
FALLBACK_ENRICH = {
    "Vanessa Kirby": {
        "wikipedia": "https://en.wikipedia.org/wiki/Vanessa_Kirby",
        "reel": {
            "title": "Pieces of a Woman — Ashamed clip",
            "url": "https://www.youtube.com/watch?v=rVmIwRzEGu0",
            "youtube_id": "rVmIwRzEGu0",
            "relevance": "Grief micro-acting; Sheila emotional register",
        },
    },
    "Florence Pugh": {
        "wikipedia": "https://en.wikipedia.org/wiki/Florence_Pugh",
        "reel": {
            "title": "Midsommar — iconic Florence Pugh moments",
            "url": "https://www.youtube.com/watch?v=UNSUcUNi1ZM",
            "youtube_id": "UNSUcUNi1ZM",
            "relevance": "Contemporary dread / grief release",
        },
    },
    "Claire Foy": {
        "wikipedia": "https://en.wikipedia.org/wiki/Claire_Foy",
        "instagram": "https://www.instagram.com/theclairefoy/",
    },
    "Ruth Wilson": {
        "wikipedia": "https://en.wikipedia.org/wiki/Ruth_Wilson",
        "reel": {
            "title": "Luther — Alice & Luther (Do you believe in Evil?)",
            "url": "https://www.youtube.com/watch?v=-AB_znetvII",
            "youtube_id": "-AB_znetvII",
            "relevance": "Controlled menace / clinical intelligence for Samantha",
        },
    },
    "Ruth Negga": {"wikipedia": "https://en.wikipedia.org/wiki/Ruth_Negga"},
    "Renate Reinsve": {"wikipedia": "https://en.wikipedia.org/wiki/Renate_Reinsve"},
    "Jodie Comer": {"wikipedia": "https://en.wikipedia.org/wiki/Jodie_Comer"},
    "Saoirse Ronan": {"wikipedia": "https://en.wikipedia.org/wiki/Saoirse_Ronan"},
    "Christopher Abbott": {"wikipedia": "https://en.wikipedia.org/wiki/Christopher_Abbott"},
    "Eddie Redmayne": {"wikipedia": "https://en.wikipedia.org/wiki/Eddie_Redmayne"},
    "Josh O'Connor": {"wikipedia": "https://en.wikipedia.org/wiki/Josh_O%27Connor"},
    "Oscar Isaac": {"wikipedia": "https://en.wikipedia.org/wiki/Oscar_Isaac"},
    "Jake Gyllenhaal": {"wikipedia": "https://en.wikipedia.org/wiki/Jake_Gyllenhaal"},
    "Trevante Rhodes": {"wikipedia": "https://en.wikipedia.org/wiki/Trevante_Rhodes"},
    "Aldis Hodge": {"wikipedia": "https://en.wikipedia.org/wiki/Aldis_Hodge"},
    "Tessa Thompson": {"wikipedia": "https://en.wikipedia.org/wiki/Tessa_Thompson"},
    "Zazie Beetz": {"wikipedia": "https://en.wikipedia.org/wiki/Zazie_Beetz"},
    "Mahershala Ali": {
        "wikipedia": "https://en.wikipedia.org/wiki/Mahershala_Ali",
        "reel": {
            "title": "Moonlight — Official Trailer",
            "url": "https://www.youtube.com/watch?v=9NJj12tJzqc",
            "youtube_id": "9NJj12tJzqc",
            "relevance": "Quiet authority / tenderness under pressure",
        },
    },
    "Nnamdi Asomugha": {"wikipedia": "https://en.wikipedia.org/wiki/Nnamdi_Asomugha"},
    "Russell Hornsby": {"wikipedia": "https://en.wikipedia.org/wiki/Russell_Hornsby"},
    "André Holland": {"wikipedia": "https://en.wikipedia.org/wiki/Andr%C3%A9_Holland"},
    "Carrie Coon": {"wikipedia": "https://en.wikipedia.org/wiki/Carrie_Coon"},
    "Rebecca Ferguson": {"wikipedia": "https://en.wikipedia.org/wiki/Rebecca_Ferguson"},
    "Sian Clifford": {"wikipedia": "https://en.wikipedia.org/wiki/Sian_Clifford"},
    "Morfydd Clark": {
        "wikipedia": "https://en.wikipedia.org/wiki/Morfydd_Clark",
        "reel": {
            "title": "Saint Maud — Official Trailer HD — A24",
            "url": "https://www.youtube.com/watch?v=EXs2-TY9qok",
            "youtube_id": "EXs2-TY9qok",
            "relevance": "Possession restraint / psychological horror",
        },
    },
    "Georgina Campbell": {"wikipedia": "https://en.wikipedia.org/wiki/Georgina_Campbell"},
    "Nicole Beharie": {"wikipedia": "https://en.wikipedia.org/wiki/Nicole_Beharie"},
    "Greta Onieogou": {"wikipedia": "https://en.wikipedia.org/wiki/Greta_Onieogou"},
    "Rob Morgan": {"wikipedia": "https://en.wikipedia.org/wiki/Rob_Morgan_(actor)"},
    "Winston Duke": {"wikipedia": "https://en.wikipedia.org/wiki/Winston_Duke"},
    "Sterling K. Brown": {"wikipedia": "https://en.wikipedia.org/wiki/Sterling_K._Brown"},
    "Brian Tyree Henry": {"wikipedia": "https://en.wikipedia.org/wiki/Brian_Tyree_Henry"},
    "Wendell Pierce": {"wikipedia": "https://en.wikipedia.org/wiki/Wendell_Pierce"},
    "Jessie Buckley": {"wikipedia": "https://en.wikipedia.org/wiki/Jessie_Buckley"},
    "Keira Knightley": {"wikipedia": "https://en.wikipedia.org/wiki/Keira_Knightley"},
    "Anya Taylor-Joy": {"wikipedia": "https://en.wikipedia.org/wiki/Anya_Taylor-Joy"},
    "Emma Stone": {"wikipedia": "https://en.wikipedia.org/wiki/Emma_Stone"},
    "Emily Blunt": {"wikipedia": "https://en.wikipedia.org/wiki/Emily_Blunt"},
    "Rosamund Pike": {"wikipedia": "https://en.wikipedia.org/wiki/Rosamund_Pike"},
    "Zoe Kravitz": {"wikipedia": "https://en.wikipedia.org/wiki/Zo%C3%AB_Kravitz"},
    "Janelle Monáe": {"wikipedia": "https://en.wikipedia.org/wiki/Janelle_Mon%C3%A1e"},
    "Myha'la": {"wikipedia": "https://en.wikipedia.org/wiki/Myha%27la_Herrold"},
    "Amin Joseph": {"wikipedia": "https://en.wikipedia.org/wiki/Amin_Joseph"},
    "Andrew Garfield": {"wikipedia": "https://en.wikipedia.org/wiki/Andrew_Garfield"},
    "Adam Driver": {"wikipedia": "https://en.wikipedia.org/wiki/Adam_Driver"},
    "John David Washington": {"wikipedia": "https://en.wikipedia.org/wiki/John_David_Washington"},
    "Kerry Condon": {"wikipedia": "https://en.wikipedia.org/wiki/Kerry_Condon"},
    "Rebecca Hall": {"wikipedia": "https://en.wikipedia.org/wiki/Rebecca_Hall"},
}

CSS = r"""
:root{--bg:#fafafa;--ink:#0a0a0a;--muted:#555;--accent:#b10f2e;--line:#0a0a0a;--soft:#ddd}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--bg);color:var(--ink);font-family:Newsreader,serif;min-height:100vh}
a{color:var(--ink)}a:hover{color:var(--accent)}
.wrap{max-width:1100px;margin:0 auto;padding:20px 20px 80px}
.top{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid var(--ink);padding-bottom:10px;margin-bottom:18px;gap:16px;flex-wrap:wrap}
.brand{font-family:"Bebas Neue",sans-serif;font-size:42px;letter-spacing:.04em;line-height:1;text-decoration:none;color:var(--ink)}
.brand span{color:var(--accent)}
.meta{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase}
.nav{display:flex;gap:14px;flex-wrap:wrap;border-bottom:1px solid var(--ink);padding:12px 0 14px;margin-bottom:8px}
.nav a{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;text-decoration:none;color:var(--muted)}
.nav a:hover,.nav a.active{color:var(--accent)}
.hero{padding:28px 0 20px;border-bottom:1px solid var(--ink);display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center}
@media(max-width:800px){.hero{grid-template-columns:1fr}}
.hero-copy h1{font-family:"Bebas Neue",sans-serif;font-size:clamp(3.5rem,10vw,7rem);line-height:.85;margin:0 0 12px;letter-spacing:.02em;max-width:12ch}
.hero-copy p{margin:0;max-width:42ch;font-size:1.15rem;line-height:1.45;color:var(--muted)}
.eyebrow{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 8px}
.cta{display:flex;gap:12px;margin-top:22px;flex-wrap:wrap}
.btn{appearance:none;text-decoration:none;padding:10px 16px;font-family:"Bebas Neue",sans-serif;font-size:16px;letter-spacing:.08em;text-transform:uppercase;cursor:pointer;display:inline-block;background:var(--ink);color:#fff;border:1px solid var(--ink)}
.btn.ghost{background:transparent;color:var(--ink)}
.btn:hover{border-color:var(--accent)}
.avatar{width:148px;height:148px;border-radius:50%;object-fit:cover;border:3px solid var(--ink);background:#eee}
.avatar.lg{width:180px;height:180px}
.avatar.sm{width:44px;height:44px;border-width:2px;flex-shrink:0}
.avatar.tile{width:72px;height:72px;border-width:2px}
.section-head{margin:56px 0 20px}
.section-head h2{font-family:"Bebas Neue",sans-serif;font-size:2.6rem;letter-spacing:.03em;margin:0}
.lede{margin:8px 0 0;max-width:50ch;line-height:1.5;color:var(--muted)}
.profile{display:grid;grid-template-columns:1.1fr .9fr;gap:28px;margin:36px 0;padding-bottom:28px;border-bottom:1px solid var(--soft)}
@media(max-width:800px){.profile{grid-template-columns:1fr}}
.profile dl{margin:0;display:grid;grid-template-columns:140px 1fr;gap:8px 14px;font-size:15px}
.profile dt{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding-top:3px}
.profile dd{margin:0;line-height:1.4}
.fit{font-size:15px;line-height:1.5;color:var(--muted);margin:0}
.table-wrap{overflow:auto;border-bottom:3px solid var(--ink);margin-bottom:8px}
.cast-table{width:100%;border-collapse:collapse;min-width:860px}
.cast-table th,.cast-table td{padding:12px 14px;text-align:left;vertical-align:top}
.cast-table th{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;border-bottom:2px solid var(--ink);font-weight:500}
.cast-table td{border-bottom:1px solid var(--soft);font-size:14px}
.cast-table tbody tr{cursor:pointer;transition:background .2s ease}
.cast-table tbody tr:hover{background:#f0f0f0}
.actor-cell{display:flex;gap:12px;align-items:flex-start}
.actor-cell .name{font-weight:600;margin:0 0 4px}
.actor-cell .bio{color:var(--muted);font-size:13px;line-height:1.35;max-width:34ch;margin:0}
.tier{display:inline-block;padding:2px 8px;font-size:11px;letter-spacing:.08em;border:1px solid var(--ink);font-family:ui-monospace,Consolas,monospace}
.tier-a{background:var(--accent);color:#fff;border-color:var(--accent)}
.num{font-variant-numeric:tabular-nums;font-family:ui-monospace,Consolas,monospace;font-size:12px}
.icon-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.icon-link{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border:1px solid var(--ink);text-decoration:none;background:#fff}
.icon-link:hover{border-color:var(--accent);color:var(--accent)}
.icon-link svg{width:14px;height:14px;display:block}
.scorecards{display:grid;gap:16px;margin-top:18px}
.card{border:1px solid var(--ink);padding:18px 20px;display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:start;text-decoration:none;color:inherit;transition:transform .2s ease,border-color .2s ease}
.card:hover{transform:translateY(-2px);border-color:var(--accent);color:inherit}
.card h3{font-family:"Bebas Neue",sans-serif;font-size:1.7rem;margin:0 0 6px;letter-spacing:.03em}
.card .scores{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.card p{margin:0;line-height:1.45;color:var(--muted)}
.attr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px;margin:12px 0}
.attr{border:1px solid var(--soft);padding:8px 10px}
.attr b{display:block;font-family:ui-monospace,Consolas,monospace;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:500}
.attr span{font-family:"Bebas Neue",sans-serif;font-size:1.4rem}
.pkg-grid{display:grid;gap:12px;margin-top:16px}
.pkg{border:1px solid var(--ink);padding:16px 18px;display:grid;gap:8px}
.pkg.primary{border-width:3px}
.pkg h3{font-family:"Bebas Neue",sans-serif;font-size:1.5rem;margin:0;letter-spacing:.03em}
.pkg .metrics{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase}
.pkg .metrics strong{color:var(--accent)}
.pkg ul{margin:0;padding-left:18px;color:var(--muted);line-height:1.5}
.home-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-top:28px}
.home-card{border:1px solid var(--ink);padding:18px;text-decoration:none;color:var(--ink);display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;min-height:150px;transition:transform .25s ease,border-color .25s ease}
.home-card:hover{transform:translateY(-3px);border-color:var(--accent);color:var(--ink)}
.home-card .n{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.12em;color:var(--accent)}
.home-card h2{font-family:"Bebas Neue",sans-serif;font-size:2rem;margin:6px 0;letter-spacing:.03em;line-height:.95}
.home-card p{margin:0;color:var(--muted);font-size:14px;line-height:1.4}
.footer{margin-top:64px;padding-top:14px;border-top:3px solid var(--ink);font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.reel{display:grid;grid-template-columns:200px 1fr;gap:16px;border:1px solid var(--ink);padding:12px;margin-top:18px;text-decoration:none;color:inherit;align-items:center}
@media(max-width:640px){.reel{grid-template-columns:1fr}}
.reel img{width:100%;aspect-ratio:16/9;object-fit:cover;border:1px solid var(--soft);display:block}
.reel h4{font-family:"Bebas Neue",sans-serif;font-size:1.3rem;margin:0 0 6px;letter-spacing:.03em}
.reel p{margin:0;color:var(--muted);font-size:14px;line-height:1.4}
.detail-grid{display:grid;grid-template-columns:180px 1fr;gap:28px;margin:28px 0}
@media(max-width:800px){.detail-grid{grid-template-columns:1fr}}
.kv{display:grid;grid-template-columns:140px 1fr;gap:8px 14px;margin:0}
.kv dt{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.kv dd{margin:0}
[data-reveal]{opacity:0;transform:translateY(14px);transition:opacity .7s ease,transform .7s ease}
[data-reveal].in{opacity:1;transform:none}
"""

JS = """
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add('in'); });
}, { threshold: 0.12 });
document.querySelectorAll('[data-reveal]').forEach((el) => io.observe(el));
document.querySelectorAll('tr[data-href]').forEach((tr) => {
  tr.addEventListener('click', () => { location.href = tr.getAttribute('data-href'); });
  tr.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); location.href = tr.getAttribute('data-href'); }
  });
});
"""

ICONS = {
    "imdb": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="1" y="4" width="22" height="16" rx="2" fill="currentColor"/><text x="12" y="15" text-anchor="middle" font-size="7" font-family="ui-monospace,monospace" font-weight="700" fill="#f5c518">IMDb</text></svg>',
    "wiki": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M7 8h2l1.2 5L12 8h0l1.8 5L15 8h2" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>',
    "ig": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>',
    "li": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 10v7M8 7.5v.5M12 17v-4.5a2 2 0 0 1 4 0V17" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>',
    "yt": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="3" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 9.5v5l5-2.5-5-2.5z" fill="currentColor"/></svg>',
    "spot": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19V5h9l5 5v9H5z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M14 5v5h5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>',
}


def slugify(name: str) -> str:
    s = name.lower()
    s = s.replace("'", "").replace("'", "").replace(".", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def parse_pipe_row(line: str) -> list[str] | None:
    line = line.strip()
    if not line.startswith("|"):
        return None
    cells = [c.strip() for c in line.strip("|").split("|")]
    if not cells:
        return None
    if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
        return None
    return cells


def load_registry() -> dict:
    if REG_PATH.exists():
        return json.loads(REG_PATH.read_text(encoding="utf-8"))
    return {}


def load_enrichment() -> dict:
    data = dict(FALLBACK_ENRICH)
    if ENRICH_PATH.exists():
        raw = json.loads(ENRICH_PATH.read_text(encoding="utf-8"))
        actors = raw.get("actors") or raw
        for k, v in actors.items():
            base = data.get(k, {})
            merged = {**base, **{kk: vv for kk, vv in v.items() if vv}}
            if "reel" in v and v["reel"]:
                merged["reel"] = v["reel"]
            data[k] = merged
    return data


def extract_role_profile(md: str) -> dict[str, str]:
    out: dict[str, str] = {}
    in_section = False
    for line in md.splitlines():
        if line.startswith("## Role Profile"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        cells = parse_pipe_row(line)
        if not cells or len(cells) < 2 or cells[0].lower() == "field":
            continue
        out[re.sub(r"\*+", "", cells[0]).strip()] = re.sub(r"\*+", "", cells[1]).strip()
    m = re.search(r"\*\*Fit criteria:\*\*\s*(.+)", md)
    if m:
        out["Fit criteria"] = m.group(1).strip()
    elif "Fit criteria" not in out:
        block = re.search(r"\*\*Fit criteria\*\*\s*\n\n((?:\d+\..+\n?)+)", md)
        if block:
            out["Fit criteria"] = " ".join(x.strip() for x in block.group(1).splitlines() if x.strip())
    return out


def extract_shortlists(md: str) -> list[tuple[str, str, list[dict]]]:
    sections: list[tuple[str, str, list[dict]]] = []
    current_title = current_code = None
    headers: list[str] = []
    rows: list[dict] = []

    def flush():
        nonlocal rows, current_title, current_code, headers
        if current_title and rows:
            sections.append((current_title, current_code or "U", rows))
        rows, headers = [], []

    for line in md.splitlines():
        m = re.match(r"^## Shortlist — (.+)$", line.strip())
        if m:
            flush()
            title = m.group(1).strip()
            current_title = title
            low = title.lower()
            current_code = "A" if low.startswith("a") else "B" if low.startswith("b") else "C" if low.startswith("c") else "U"
            continue
        if current_title is None:
            continue
        if line.startswith("## ") and not line.startswith("## Shortlist"):
            flush()
            current_title = None
            continue
        cells = parse_pipe_row(line)
        if not cells:
            continue
        if cells[0] == "#":
            headers = cells
            continue
        if not headers or not cells[0].isdigit():
            continue
        rows.append({headers[i]: cells[i] if i < len(cells) else "" for i in range(len(headers))})
    flush()
    return sections


def extract_scorecards(md: str) -> list[dict]:
    cards = []
    for m in re.finditer(
        r"^### (.+?) \| Creative: (.+?) \| Risk: (.+?) \| ROI: (.+?) → \*\*(.+?)\*\*\s*(?:\n\n(.+?))?(?=\n### |\n## |\Z)",
        md,
        flags=re.M | re.S,
    ):
        note = (m.group(6) or "").strip().split("\n\n")[0].strip()
        attrs = []
        for am in re.finditer(r"([A-Za-z][A-Za-z /]+?)\s+(\d+)(?:/10)?", note):
            label = am.group(1).strip(" ·")
            if label.lower() in {"creative", "risk", "roi"}:
                continue
            if len(label) < 18:
                attrs.append((label, am.group(2)))
        cards.append(
            {
                "name": m.group(1).strip(),
                "creative": m.group(2).strip(),
                "risk": m.group(3).strip(),
                "roi": m.group(4).strip(),
                "verdict": m.group(5).strip(),
                "note": note,
                "attrs": attrs[:8],
            }
        )
    return cards


def extract_packages(md: str) -> list[dict]:
    packages = []
    scenario = None
    headers: list[str] = []
    for line in md.splitlines():
        sm = re.match(r"^### Scenario (.+)$", line.strip())
        if sm:
            scenario = sm.group(1).strip()
            headers = []
            continue
        if scenario is None:
            continue
        if line.startswith("## ") or (line.startswith("### ") and not line.startswith("### Scenario")):
            scenario = None
            headers = []
            continue
        cells = parse_pipe_row(line)
        if not cells:
            continue
        if cells[0].lower() == "package":
            headers = cells
            continue
        if not headers:
            continue
        row = {headers[i]: cells[i] if i < len(cells) else "" for i in range(len(headers))}
        name = row.get("Package", "")
        primary = "primary" in name.lower() or name.strip().startswith("**B1")
        packages.append(
            {
                "scenario": scenario,
                "name": re.sub(r"\*+", "", name).strip(),
                "primary": primary,
                "sheila": re.sub(r"\*+", "", row.get("Sheila", "")).strip(),
                "james": re.sub(r"\*+", "", row.get("James", "")).strip(),
                "samantha": re.sub(r"\*+", "", row.get("Samantha", "")).strip(),
                "melina": re.sub(r"\*+", "", row.get("Melina", "")).strip(),
                "norman": re.sub(r"\*+", "", row.get("Norman", "")).strip(),
                "pos": re.sub(r"\*+", "", row.get("%PoS", "")).strip(),
                "roi": re.sub(r"\*+", "", row.get("ROI med", "")).strip(),
                "auth": re.sub(r"\*+", "", row.get("Auth", "")).strip(),
            }
        )
    return packages


def actor_slug_path(role_slug: str, actor_name: str) -> str:
    return f"actors/{role_slug}-{slugify(actor_name)}.html"


def shorten_bio(bio: str, n: int = 140) -> str:
    if not bio:
        return ""
    cut = re.split(r"(?<=\.)\s+", bio, maxsplit=1)[0]
    if len(cut) > n:
        cut = cut[: n - 3].rstrip() + "..."
    return cut


def ensure_assets(registry: dict, needed_names: set[str]) -> None:
    (ASSETS / "characters").mkdir(parents=True, exist_ok=True)
    (ASSETS / "headshots").mkdir(parents=True, exist_ok=True)
    for name in ["char-sheila.png", "char-james.png", "char-samantha.png", "char-melina.png", "char-norman.png"]:
        src = PORTRAIT_SRC / name
        dst = ASSETS / "characters" / name
        if src.exists():
            shutil.copy2(src, dst)
    for name in needed_names:
        rec = registry.get(name) or {}
        hs = rec.get("headshot") or ""
        if not hs or hs.startswith("http"):
            continue
        src = DOCSWAMP / hs
        if not src.exists():
            continue
        dest_name = Path(hs).name
        shutil.copy2(src, ASSETS / "headshots" / dest_name)


def headshot_src(name: str, registry: dict, prefix: str = "assets/") -> str | None:
    rec = registry.get(name) or {}
    hs = rec.get("headshot") or ""
    if not hs:
        return None
    if hs.startswith("http"):
        return hs
    local = ASSETS / "headshots" / Path(hs).name
    if local.exists() or (DOCSWAMP / hs).exists():
        return f"{prefix}headshots/{Path(hs).name}"
    return None


def icon_links(name: str, registry: dict, enrich: dict, prefix: str = "") -> str:
    rec = registry.get(name) or {}
    en = enrich.get(name) or {}
    links = []
    imdb = rec.get("imdb_url") or ""
    if not imdb and rec.get("imdb_id"):
        imdb = f"https://www.imdb.com/name/{rec['imdb_id']}/"
    pairs = [
        ("imdb", imdb, "IMDb"),
        ("wiki", en.get("wikipedia") or "", "Wikipedia"),
        ("ig", en.get("instagram") or "", "Instagram"),
        ("li", en.get("linkedin") or "", "LinkedIn"),
        ("spot", en.get("spotlight") or en.get("other_profile") or "", "Profile"),
        ("yt", (en.get("reel") or {}).get("url") or "", "Reel"),
    ]
    for key, url, label in pairs:
        if not url or "pending" in url.lower():
            continue
        links.append(
            f'<a class="icon-link" href="{escape(url)}" target="_blank" rel="noopener" title="{escape(label)}" onclick="event.stopPropagation()">{ICONS[key]}</a>'
        )
    return f'<div class="icon-row">{"".join(links)}</div>' if links else ""


def nav_html(active: str, prefix: str = "") -> str:
    items = [(f"{prefix}index.html", "Overview", "index")]
    for c in CHARACTERS:
        items.append((f"{prefix}{c['slug']}.html", c["title"].split()[0] if c["slug"] != "norman" else "Detective", c["slug"]))
    items.append((f"{prefix}ensemble.html", "Ensemble", "ensemble"))
    links = []
    for href, label, key in items:
        cls = "active" if key == active else ""
        links.append(f'<a class="{cls}" href="{href}">{escape(label)}</a>')
    return '<nav class="nav">' + "".join(links) + "</nav>"


def shell(title: str, active: str, body: str, depth: int = 0) -> str:
    prefix = "../" * depth
    asset_prefix = prefix
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex,nofollow" />
<title>{escape(title)} — WAR Casting · Shredded Lens</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="{FONTS}" rel="stylesheet" />
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <a class="brand" href="{prefix}index.html">SLS <span>WAR</span></a>
    <div class="meta">Casting shred · Confidential · 2026-08-05</div>
  </div>
  {nav_html(active, prefix)}
  {body}
  <footer class="footer">
    <span>Shredded Lens Studios</span>
    <span>Not for redistribution</span>
  </footer>
</div>
<script>{JS}</script>
</body>
</html>
"""


def reel_block(en: dict, depth: int = 0) -> str:
    reel = en.get("reel") or {}
    if not reel.get("youtube_id"):
        return ""
    yid = reel["youtube_id"]
    thumb = f"https://img.youtube.com/vi/{yid}/hqdefault.jpg"
    return f"""
<a class="reel" href="{escape(reel.get('url',''))}" target="_blank" rel="noopener" data-reveal>
  <img src="{escape(thumb)}" alt="" loading="lazy" />
  <div>
    <p class="eyebrow">Performance reel</p>
    <h4>{escape(reel.get('title') or 'Reel')}</h4>
    <p>{escape(reel.get('relevance') or '')}</p>
  </div>
</a>
"""


def render_shortlist_section(role: dict, title: str, code: str, rows: list[dict], registry: dict, enrich: dict) -> str:
    head = f"""
<section class="shortlist" data-reveal>
  <header class="section-head">
    <p class="eyebrow">Shortlist · Tier {escape(code)}</p>
    <h2>{escape(title)}</h2>
    <p class="lede">Click any row for the actor-in-role shred page.</p>
  </header>
  <div class="table-wrap">
    <table class="cast-table">
      <thead>
        <tr>
          <th>#</th><th>Actor</th><th>Tier</th><th>Fit</th><th>Fee</th><th>Flags</th><th>Notes</th>
        </tr>
      </thead>
      <tbody>
"""
    body_rows = []
    for row in rows:
        name = re.sub(r"\*+", "", row.get("Actor", "")).strip()
        if not name or name.startswith("CD Match"):
            # still show but no detail page for placeholders
            href = ""
        else:
            href = actor_slug_path(role["slug"], name)
        fit = row.get("Fit", "")
        fee = row.get("Fee band", "")
        flags = row.get("Flags", "").replace(",", " ·")
        notes = row.get("Notes", "")
        n = row.get("#", "")
        bio = shorten_bio((registry.get(name) or {}).get("bio") or "")
        hs = headshot_src(name, registry)
        avatar = (
            f'<img class="avatar sm" src="{escape(hs)}" alt="" loading="lazy" />'
            if hs
            else '<div class="avatar sm" aria-hidden="true"></div>'
        )
        icons = icon_links(name, registry, enrich)
        name_block = f"""<div class="actor-cell">{avatar}<div>
  <div class="name">{escape(name)}</div>
  <p class="bio">{escape(bio)}</p>
  {icons}
</div></div>"""
        tr_attrs = f' data-href="{escape(href)}" tabindex="0" role="link"' if href else ""
        body_rows.append(
            f"""<tr{tr_attrs} data-reveal>
  <td class="num">{escape(n).zfill(2) if str(n).isdigit() else escape(str(n))}</td>
  <td>{name_block}</td>
  <td><span class="tier tier-{code.lower()}">{escape(code)}</span></td>
  <td class="num">{escape(fit)}</td>
  <td>{escape(fee)}</td>
  <td>{escape(flags)}</td>
  <td>{escape(notes)}</td>
</tr>"""
        )
    return head + "\n".join(body_rows) + "</tbody></table></div></section>"


def render_character(meta: dict, registry: dict, enrich: dict) -> tuple[str, list[tuple[str, dict, dict]]]:
    md = (DOCSWAMP / meta["file"]).read_text(encoding="utf-8")
    profile = extract_role_profile(md)
    shortlists = extract_shortlists(md)
    cards = extract_scorecards(md)
    card_by_name = {c["name"]: c for c in cards}
    actor_pages: list[tuple[str, dict, dict]] = []

    profile_keys = [
        "Character",
        "Role class",
        "Age",
        "Ethnicity / look",
        "Dialogue load",
        "Emotional core",
        "Symbolic function",
        "Chemistry dependents",
    ]
    dl = []
    for k in profile_keys:
        if k in profile:
            dl.append(f"<dt>{escape(k)}</dt><dd>{escape(profile[k])}</dd>")
    fit = profile.get("Fit criteria", "")

    body = f"""
<header class="hero" data-reveal>
  <div class="hero-copy">
    <p class="eyebrow">{escape(meta['tag'])}</p>
    <h1>{escape(meta['hero'])}</h1>
    <p>{escape(meta['lede'])}</p>
    <div class="cta">
      <a class="btn" href="#shortlists">Shortlists</a>
      <a class="btn ghost" href="ensemble.html">Ensemble</a>
    </div>
  </div>
  <img class="avatar lg" src="assets/{escape(meta['portrait'])}" alt="{escape(meta['title'])} concept portrait" />
</header>
<section class="profile" data-reveal>
  <dl>{''.join(dl)}</dl>
  <p class="fit"><strong>Fit criteria.</strong> {escape(fit)}</p>
</section>
<div id="shortlists">
{''.join(render_shortlist_section(meta, t, c, rows, registry, enrich) for t, c, rows in shortlists)}
</div>
"""
    if cards:
        card_html = []
        for c in cards:
            href = actor_slug_path(meta["slug"], c["name"])
            hs = headshot_src(c["name"], registry)
            avatar = f'<img class="avatar" src="{escape(hs)}" alt="" />' if hs else '<div class="avatar" aria-hidden="true"></div>'
            attrs = ""
            if c["attrs"]:
                attrs = '<div class="attr-grid">' + "".join(
                    f'<div class="attr"><b>{escape(a)}</b><span>{escape(v)}</span></div>' for a, v in c["attrs"]
                ) + "</div>"
            card_html.append(
                f"""<a class="card" href="{escape(href)}" data-reveal>
  {avatar}
  <div>
    <h3>{escape(c['name'])}</h3>
    <div class="scores">Creative {escape(c['creative'])} · Risk {escape(c['risk'])} · ROI {escape(c['roi'])} · {escape(c['verdict'])}</div>
    {attrs}
    <p>{escape(c['note'])}</p>
    {icon_links(c['name'], registry, enrich)}
  </div>
</a>"""
            )
        body += f"""
<section data-reveal>
  <header class="section-head">
    <p class="eyebrow">Priority picks</p>
    <h2>Scorecards</h2>
    <p class="lede">Fully expanded creative / risk / ROI with attribute breakdown where scored.</p>
  </header>
  <div class="scorecards">{''.join(card_html)}</div>
</section>
"""

    # collect actor detail page payloads
    for title, code, rows in shortlists:
        for row in rows:
            name = re.sub(r"\*+", "", row.get("Actor", "")).strip()
            if not name or name.startswith("CD Match") or "(pending)" in (row.get("IMDb") or ""):
                continue
            payload = {
                "role": meta,
                "tier_title": title,
                "tier": code,
                "row": row,
                "scorecard": card_by_name.get(name),
                "profile": profile,
            }
            actor_pages.append((name, payload, enrich.get(name) or {}))

    return shell(meta["title"], meta["slug"], body), actor_pages


def render_actor_page(name: str, payload: dict, enrich_one: dict, registry: dict) -> str:
    role = payload["role"]
    row = payload["row"]
    sc = payload["scorecard"]
    profile = payload["profile"]
    hs = headshot_src(name, registry, prefix="../assets/")
    avatar = f'<img class="avatar lg" src="{escape(hs)}" alt="{escape(name)}" />' if hs else '<div class="avatar lg" aria-hidden="true"></div>'
    bio = (registry.get(name) or {}).get("bio") or ""
    # expanded scorecard defaults from row if no scorecard
    if sc:
        creative, risk, roi, verdict, note, attrs = sc["creative"], sc["risk"], sc["roi"], sc["verdict"], sc["note"], sc["attrs"]
    else:
        fit = row.get("Fit", "")
        creative = f"{int(fit)*10}/100" if str(fit).isdigit() else "—/100"
        risk = "—/100"
        roi = "—/100"
        verdict = "SHORTLIST ENTRY"
        note = row.get("Notes", "") or "See role fit criteria and fee/leverage bands."
        attrs = [("Fit", str(fit))] if fit else []

    attr_html = ""
    if attrs:
        attr_html = '<div class="attr-grid">' + "".join(
            f'<div class="attr"><b>{escape(a)}</b><span>{escape(v)}</span></div>' for a, v in attrs
        ) + "</div>"

    # synthesize missing attribute scaffold for "fully expanded"
    if not attrs:
        attr_html = '<div class="attr-grid">' + "".join(
            f'<div class="attr"><b>{escape(a)}</b><span>—</span></div>'
            for a in ["Alignment", "Presence", "Chemistry", "Commercial", "Strategic", "Artistic", "Cost Fit"]
        ) + "</div>"

    body = f"""
<header class="hero" data-reveal>
  <div class="hero-copy">
    <p class="eyebrow">{escape(role['title'])} · Tier {escape(payload['tier'])}</p>
    <h1>{escape(name.upper())}</h1>
    <p>Actor-in-role shred for <strong>{escape(role['title'])}</strong> in WAR.</p>
    <div class="cta">
      <a class="btn" href="../{escape(role['slug'])}.html">Back to {escape(role['hero'])}</a>
      <a class="btn ghost" href="../index.html">Overview</a>
    </div>
  </div>
  {avatar}
</header>
<section class="detail-grid" data-reveal>
  {avatar}
  <div>
    <dl class="kv">
      <dt>Role</dt><dd>{escape(role['title'])}</dd>
      <dt>Tier</dt><dd>{escape(payload['tier_title'])}</dd>
      <dt>Fit</dt><dd>{escape(row.get('Fit',''))}</dd>
      <dt>Fee band</dt><dd>{escape(row.get('Fee band',''))}</dd>
      <dt>Leverage</dt><dd>{escape(row.get('Leverage',''))}</dd>
      <dt>Flags</dt><dd>{escape(row.get('Flags','').replace(',', ' ·'))}</dd>
      <dt>Avail risk</dt><dd>{escape(row.get('Avail risk',''))}</dd>
      <dt>Role age</dt><dd>{escape(profile.get('Age',''))}</dd>
      <dt>Look lock</dt><dd>{escape(profile.get('Ethnicity / look',''))}</dd>
    </dl>
    {icon_links(name, registry, {name: enrich_one})}
  </div>
</section>
<section data-reveal>
  <header class="section-head">
    <p class="eyebrow">Expanded scorecard</p>
    <h2>{escape(verdict)}</h2>
    <p class="lede">Creative {escape(creative)} · Risk {escape(risk)} · ROI {escape(roi)}</p>
  </header>
  {attr_html}
  <p class="fit">{escape(note)}</p>
  <p class="fit" style="margin-top:14px"><strong>Bio.</strong> {escape(shorten_bio(bio, 420) or 'Profile pending.')}</p>
  <p class="fit" style="margin-top:14px"><strong>Role emotional core.</strong> {escape(profile.get('Emotional core',''))}</p>
  <p class="fit" style="margin-top:14px"><strong>Why this lane.</strong> {escape(row.get('Notes',''))}</p>
  {reel_block(enrich_one)}
</section>
"""
    return shell(f"{name} · {role['title']}", role["slug"], body, depth=1)


def render_ensemble(registry: dict) -> str:
    meta = ENSEMBLE
    md = (DOCSWAMP / meta["file"]).read_text(encoding="utf-8")
    packages = extract_packages(md)
    pkg_html = []
    for p in packages:
        cls = "pkg primary" if p["primary"] else "pkg"
        pkg_html.append(
            f"""<article class="{cls}" data-reveal>
  <h3>{escape(p['name'])}</h3>
  <div class="metrics">{escape(p['scenario'])} · <strong>{escape(p['pos'])}% PoS</strong> · ROI {escape(p['roi'])} · Auth {escape(p['auth'])}</div>
  <ul>
    <li>Sheila — {escape(p['sheila'])}</li>
    <li>James — {escape(p['james'])}</li>
    <li>Samantha — {escape(p['samantha'])}</li>
    <li>Melina — {escape(p['melina'])}</li>
    <li>Norman — {escape(p['norman'])}</li>
  </ul>
</article>"""
        )
    body = f"""
<header class="hero" data-reveal>
  <div class="hero-copy">
    <p class="eyebrow">{escape(meta['tag'])}</p>
    <h1>{escape(meta['hero'])}</h1>
    <p>{escape(meta['lede'])}</p>
    <div class="cta"><a class="btn" href="#packages">Packages</a><a class="btn ghost" href="index.html">Overview</a></div>
  </div>
  <div class="avatar lg" style="display:grid;place-items:center;font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:.06em">B1</div>
</header>
<section id="packages" data-reveal>
  <header class="section-head">
    <p class="eyebrow">Scenario grid</p>
    <h2>Recommended packages</h2>
    <p class="lede">Primary Balanced package B1 is marked with a heavier rule.</p>
  </header>
  <div class="pkg-grid">{''.join(pkg_html)}</div>
</section>
"""
    return shell(meta["title"], "ensemble", body)


def render_index() -> str:
    cards = []
    for i, c in enumerate(CHARACTERS, 1):
        cards.append(
            f"""<a class="home-card" href="{c['slug']}.html" data-reveal>
  <div>
    <span class="n">{str(i).zfill(2)}</span>
    <h2>{escape(c['hero'])}</h2>
    <p>{escape(c['tag'])}</p>
  </div>
  <img class="avatar tile" src="assets/{escape(c['portrait'])}" alt="" />
</a>"""
        )
    cards.append(
        """<a class="home-card" href="ensemble.html" data-reveal>
  <div>
    <span class="n">06</span>
    <h2>ENSEMBLE</h2>
    <p>Package architecture</p>
  </div>
  <div class="avatar tile" style="display:grid;place-items:center;font-family:'Bebas Neue',sans-serif">B1</div>
</a>"""
    )
    body = f"""
<header class="hero" data-reveal>
  <div class="hero-copy">
    <p class="eyebrow">Shredded Lens · Character &amp; ensemble casting</p>
    <h1>WAR CASTING</h1>
    <p>Confidential shortlists and package architecture for Russell K. Reed’s WAR — High-Contrast Editorial share format.</p>
    <div class="cta"><a class="btn" href="sheila.html">Open leads</a><a class="btn ghost" href="ensemble.html">Packages</a></div>
  </div>
  <img class="avatar lg" src="assets/characters/char-sheila.png" alt="Sheila concept portrait" />
</header>
<div class="home-grid">{''.join(cards)}</div>
"""
    return shell("WAR Casting Overview", "index", body)


def expand_markdown_scorecards() -> None:
    """Append actor-detail index sections into character shred MDs."""
    enrich = load_enrichment()
    registry = load_registry()
    for meta in CHARACTERS:
        path = DOCSWAMP / meta["file"]
        md = path.read_text(encoding="utf-8")
        if "## Actor Detail Index" in md:
            continue
        shortlists = extract_shortlists(md)
        lines = [
            "",
            "---",
            "",
            "## Actor Detail Index",
            "",
            "HTML share pages expand each shortlist row into an actor-in-role shred with scorecard, profiles, and reels when available.",
            "",
            "| Actor | Tier | Detail slug | Profiles | Reel |",
            "| --- | --- | --- | --- | --- |",
        ]
        for title, code, rows in shortlists:
            for row in rows:
                name = re.sub(r"\*+", "", row.get("Actor", "")).strip()
                if not name or name.startswith("CD Match"):
                    continue
                en = enrich.get(name) or {}
                profiles = []
                rec = registry.get(name) or {}
                if rec.get("imdb_url") or rec.get("imdb_id"):
                    profiles.append("IMDb")
                if en.get("wikipedia"):
                    profiles.append("Wikipedia")
                if en.get("instagram"):
                    profiles.append("Instagram")
                if en.get("linkedin"):
                    profiles.append("LinkedIn")
                if en.get("spotlight") or en.get("other_profile"):
                    profiles.append("Network")
                reel = "yes" if (en.get("reel") or {}).get("youtube_id") else "(n/a)"
                lines.append(
                    f"| {name} | {code} | `{meta['slug']}-{slugify(name)}` | {', '.join(profiles) or '(pending)'} | {reel} |"
                )
        path.write_text(md.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
        print("expanded MD index:", path.name)


def render_gate() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex,nofollow" />
<title>WAR Casting · Access</title>
<link href="{FONTS}" rel="stylesheet" />
<style>{CSS}
.lock-body{{min-height:100vh;display:grid;place-items:center;padding:24px}}
.lock{{width:min(420px,100%);border:3px solid var(--ink);padding:28px 24px;background:#fff}}
.lock h1{{font-family:"Bebas Neue",sans-serif;font-size:2.8rem;margin:0 0 8px;letter-spacing:.04em}}
.lock p{{color:var(--muted);margin:0 0 18px;line-height:1.45}}
.lock label{{display:block;font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px}}
.lock input{{width:100%;padding:12px 14px;border:1px solid var(--ink);font:inherit;font-size:16px;margin-bottom:12px}}
.lock .err{{color:var(--accent);font-size:14px;min-height:1.2em;margin:0 0 8px}}
</style>
</head>
<body class="lock-body">
  <form class="lock" id="gate" autocomplete="off">
    <div class="brand" style="font-size:28px;margin-bottom:12px">SLS <span>WAR</span></div>
    <h1>CASTING ACCESS</h1>
    <p>Password-protected casting shred.</p>
    <label for="pw">Access password</label>
    <input id="pw" type="password" required />
    <p class="err" id="err"></p>
    <button class="btn" type="submit" style="width:100%;border:0">Enter</button>
  </form>
<script>
const HASH = "__HASH_PLACEHOLDER__";
async function sha256(text) {{
  const data = new TextEncoder().encode(text);
  const buf = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2,'0')).join('');
}}
document.getElementById('gate').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const pw = document.getElementById('pw').value;
  const h = await sha256(pw);
  if (h === HASH) {{
    sessionStorage.setItem('sls_war_cast_ok', '1');
    location.href = 'index.html';
  }} else {{
    document.getElementById('err').textContent = 'Incorrect password.';
  }}
}});
</script>
</body>
</html>
"""


def main() -> None:
    registry = load_registry()
    enrich = load_enrichment()
    expand_markdown_scorecards()

    # gather needed actor names
    needed: set[str] = set()
    all_actor_pages: list[tuple[str, dict, dict]] = []
    character_html: dict[str, str] = {}
    for meta in CHARACTERS:
        html, pages = render_character(meta, registry, enrich)
        character_html[meta["slug"]] = html
        for name, payload, en in pages:
            needed.add(name)
            all_actor_pages.append((name, payload, en))

    OUT.mkdir(parents=True, exist_ok=True)
    ensure_assets(registry, needed)
    (OUT / "actors").mkdir(parents=True, exist_ok=True)

    (OUT / "index.html").write_text(render_index(), encoding="utf-8")
    for slug, html in character_html.items():
        (OUT / f"{slug}.html").write_text(html, encoding="utf-8")
    (OUT / "ensemble.html").write_text(render_ensemble(registry), encoding="utf-8")
    (OUT / "gate.html").write_text(render_gate(), encoding="utf-8")

    written = 0
    for name, payload, en in all_actor_pages:
        path = OUT / actor_slug_path(payload["role"]["slug"], name)
        path.write_text(render_actor_page(name, payload, en, registry), encoding="utf-8")
        written += 1

    # rewrite character html AFTER assets copied so headshots resolve — already referenced
    print(f"wrote site to {OUT} with {written} actor detail pages")


if __name__ == "__main__":
    main()
