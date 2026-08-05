# -*- coding: utf-8 -*-
"""Build High-Contrast Editorial casting share site from WAR shreds."""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCSWAMP = ROOT.parent
OUT = ROOT / "site"
REG_PATH = Path(r"C:\Users\kengr\AppData\Local\Temp\war_actor_registry.json")

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
    },
    {
        "slug": "james",
        "file": "SLS Casting Shred - WAR - Character - James Collier - 2026-08-05.md",
        "title": "James Collier",
        "hero": "JAMES",
        "tag": "Lead · uncanny husband",
        "lede": "Ambiguity craft over marquee default. Cast for the question, not the answer.",
    },
    {
        "slug": "samantha",
        "file": "SLS Casting Shred - WAR - Character - Samantha - 2026-08-05.md",
        "title": "Samantha",
        "hero": "SAMANTHA",
        "tag": "Supporting · rational foil",
        "lede": "Sister-read ballast. Clarity that makes the uncanny harder to dismiss.",
    },
    {
        "slug": "melina",
        "file": "SLS Casting Shred - WAR - Character - Melina - 2026-08-05.md",
        "title": "Melina",
        "hero": "MELINA",
        "tag": "Supporting · soft temptation",
        "lede": "Workplace gravity without vamp. Attraction that stays inside the frame.",
    },
    {
        "slug": "norman",
        "file": "SLS Casting Shred - WAR - Character - Detective Norman - 2026-08-05.md",
        "title": "Detective Norman",
        "hero": "NORMAN",
        "tag": "Supporting · case ballast",
        "lede": "Procedural silence for an ambiguous marriage thriller. Cast for the unfinished file.",
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

CSS = """
:root{--bg:#fafafa;--ink:#0a0a0a;--muted:#555;--accent:#b10f2e;--line:#0a0a0a;--soft:#ddd}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--bg);color:var(--ink);font-family:Newsreader,serif;min-height:100vh}
a{color:var(--ink)}a:hover{color:var(--accent)}
.wrap{max-width:1040px;margin:0 auto;padding:20px 20px 80px}
.top{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid var(--ink);padding-bottom:10px;margin-bottom:18px;gap:16px;flex-wrap:wrap}
.brand{font-family:"Bebas Neue",sans-serif;font-size:42px;letter-spacing:.04em;line-height:1;text-decoration:none;color:var(--ink)}
.brand span{color:var(--accent)}
.meta{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase}
.nav{display:flex;gap:14px;flex-wrap:wrap;border-bottom:1px solid var(--ink);padding:12px 0 14px;margin-bottom:8px}
.nav a{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;text-decoration:none;color:var(--muted)}
.nav a:hover,.nav a.active{color:var(--accent)}
.hero{padding:28px 0 20px;border-bottom:1px solid var(--ink)}
.hero h1{font-family:"Bebas Neue",sans-serif;font-size:clamp(3.5rem,10vw,7rem);line-height:.85;margin:0 0 12px;letter-spacing:.02em;max-width:12ch}
.hero p{margin:0;max-width:42ch;font-size:1.15rem;line-height:1.45;color:var(--muted)}
.eyebrow{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 8px}
.cta{display:flex;gap:12px;margin-top:22px;flex-wrap:wrap}
.btn{appearance:none;text-decoration:none;padding:10px 16px;font-family:"Bebas Neue",sans-serif;font-size:16px;letter-spacing:.08em;text-transform:uppercase;cursor:pointer;display:inline-block;background:var(--ink);color:#fff;border:1px solid var(--ink)}
.btn.ghost{background:transparent;color:var(--ink)}
.btn:hover{border-color:var(--accent)}
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
.cast-table{width:100%;border-collapse:collapse;min-width:720px}
.cast-table th,.cast-table td{padding:12px 14px;text-align:left;vertical-align:top}
.cast-table th{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;border-bottom:2px solid var(--ink);font-weight:500}
.cast-table td{border-bottom:1px solid var(--soft);font-size:14px}
.cast-table .name{font-weight:600}
.cast-table .name a{text-decoration:none;border-bottom:1px solid transparent}
.cast-table .name a:hover{border-bottom-color:var(--accent);color:var(--accent)}
.tier{display:inline-block;padding:2px 8px;font-size:11px;letter-spacing:.08em;border:1px solid var(--ink);font-family:ui-monospace,Consolas,monospace}
.tier-a{background:var(--accent);color:#fff;border-color:var(--accent)}
.tier-b,.tier-c,.tier-u{background:transparent}
.num{font-variant-numeric:tabular-nums;font-family:ui-monospace,Consolas,monospace;font-size:12px}
.bio{color:var(--muted);font-size:13px;line-height:1.4;max-width:36ch}
.scorecards{display:grid;gap:14px;margin-top:18px}
.card{border:1px solid var(--ink);padding:16px 18px}
.card h3{font-family:"Bebas Neue",sans-serif;font-size:1.6rem;margin:0 0 6px;letter-spacing:.03em}
.card .scores{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.card p{margin:0;line-height:1.45;color:var(--muted)}
.pkg-grid{display:grid;gap:12px;margin-top:16px}
.pkg{border:1px solid var(--ink);padding:16px 18px;display:grid;gap:8px}
.pkg.primary{border-width:3px}
.pkg h3{font-family:"Bebas Neue",sans-serif;font-size:1.5rem;margin:0;letter-spacing:.03em}
.pkg .metrics{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase}
.pkg .metrics strong{color:var(--accent)}
.pkg ul{margin:0;padding-left:18px;color:var(--muted);line-height:1.5}
.home-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-top:28px}
.home-card{border:1px solid var(--ink);padding:18px;text-decoration:none;color:var(--ink);display:flex;flex-direction:column;gap:8px;min-height:150px;transition:transform .25s ease,border-color .25s ease}
.home-card:hover{transform:translateY(-3px);border-color:var(--accent);color:var(--ink)}
.home-card .n{font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.12em;color:var(--accent)}
.home-card h2{font-family:"Bebas Neue",sans-serif;font-size:2rem;margin:0;letter-spacing:.03em;line-height:.95}
.home-card p{margin:0;color:var(--muted);font-size:14px;line-height:1.4}
.footer{margin-top:64px;padding-top:14px;border-top:3px solid var(--ink);font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
[data-reveal]{opacity:0;transform:translateY(14px);transition:opacity .7s ease,transform .7s ease}
[data-reveal].in{opacity:1;transform:none}
.cast-table tbody tr{transition:background .25s ease}
.cast-table tbody tr:hover{background:#f0f0f0}
.lock-body{min-height:100vh;display:grid;place-items:center;padding:24px}
.lock{width:min(420px,100%);border:3px solid var(--ink);padding:28px 24px;background:#fff}
.lock h1{font-family:"Bebas Neue",sans-serif;font-size:2.8rem;margin:0 0 8px;letter-spacing:.04em}
.lock p{color:var(--muted);margin:0 0 18px;line-height:1.45}
.lock label{display:block;font-family:ui-monospace,Consolas,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px}
.lock input{width:100%;padding:12px 14px;border:1px solid var(--ink);font:inherit;font-size:16px;margin-bottom:12px}
.lock .err{color:var(--accent);font-size:14px;min-height:1.2em;margin:0 0 8px}
"""

JS = """
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add('in'); });
}, { threshold: 0.12 });
document.querySelectorAll('[data-reveal]').forEach((el) => io.observe(el));
"""


def load_registry() -> dict:
    if REG_PATH.exists():
        return json.loads(REG_PATH.read_text(encoding="utf-8"))
    return {}


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
        if not cells or len(cells) < 2:
            continue
        if cells[0].lower() == "field":
            continue
        key = re.sub(r"\*+", "", cells[0]).strip()
        val = re.sub(r"\*+", "", cells[1]).strip()
        out[key] = val
    m = re.search(r"\*\*Fit criteria:\*\*\s*(.+)", md)
    if m:
        out["Fit criteria"] = m.group(1).strip()
    return out


def extract_shortlists(md: str) -> list[tuple[str, str, list[dict]]]:
    """Return list of (tier_label, tier_code, rows)."""
    sections: list[tuple[str, str, list[dict]]] = []
    current_title = None
    current_code = None
    headers: list[str] = []
    rows: list[dict] = []

    def flush():
        nonlocal rows, current_title, current_code, headers
        if current_title and rows:
            sections.append((current_title, current_code or "U", rows))
        rows = []
        headers = []

    for line in md.splitlines():
        m = re.match(r"^## Shortlist — (.+)$", line.strip())
        if m:
            flush()
            title = m.group(1).strip()
            current_title = title
            low = title.lower()
            if low.startswith("a"):
                current_code = "A"
            elif low.startswith("b"):
                current_code = "B"
            elif low.startswith("c"):
                current_code = "C"
            else:
                current_code = "U"
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
        row = {headers[i]: cells[i] if i < len(cells) else "" for i in range(len(headers))}
        rows.append(row)
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
        cards.append(
            {
                "name": m.group(1).strip(),
                "creative": m.group(2).strip(),
                "risk": m.group(3).strip(),
                "roi": m.group(4).strip(),
                "verdict": m.group(5).strip(),
                "note": note,
            }
        )
    return cards


def extract_packages(md: str) -> list[dict]:
    """Pull scenario package tables from ensemble shred."""
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
        if not headers or cells[0].lower() in {"package", "---"}:
            continue
        if "takeaway" in cells[0].lower():
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
                "ceiling": re.sub(r"\*+", "", row.get("Ceiling", row.get("Cost eff.", ""))).strip(),
            }
        )
    return packages


def actor_link(name: str, imdb_cell: str, registry: dict) -> str:
    url = ""
    m = re.search(r"\((https://www\.imdb\.com/name/[^)]+)\)", imdb_cell or "")
    if m:
        url = m.group(1)
    else:
        rec = registry.get(name) or {}
        url = rec.get("imdb_url") or ""
        if not url and rec.get("imdb_id"):
            url = f"https://www.imdb.com/name/{rec['imdb_id']}/"
    safe = escape(name)
    if url:
        return f'<a href="{escape(url)}" target="_blank" rel="noopener">{safe}</a>'
    return safe


def actor_bio(name: str, registry: dict) -> str:
    bio = (registry.get(name) or {}).get("bio") or ""
    if not bio:
        return ""
    # first sentence-ish
    cut = re.split(r"(?<=\.)\s+", bio, maxsplit=1)[0]
    if len(cut) > 160:
        cut = cut[:157].rstrip() + "..."
    return escape(cut)


def nav_html(active: str) -> str:
    items = [("index.html", "Overview", "index")]
    for c in CHARACTERS:
        items.append((f"{c['slug']}.html", c["title"].split()[0], c["slug"]))
    items.append(("ensemble.html", "Ensemble", "ensemble"))
    links = []
    for href, label, key in items:
        cls = " active" if key == active else ""
        links.append(f'<a class="{cls.strip()}" href="{href}">{escape(label)}</a>')
    return '<nav class="nav">' + "".join(links) + "</nav>"


def shell(title: str, active: str, body: str) -> str:
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
    <a class="brand" href="index.html">SLS <span>WAR</span></a>
    <div class="meta">Casting shred · Confidential · 2026-08-05</div>
  </div>
  {nav_html(active)}
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


def render_shortlist_section(title: str, code: str, rows: list[dict], registry: dict) -> str:
    head = f"""
<section class="shortlist" data-reveal>
  <header class="section-head">
    <p class="eyebrow">Shortlist · Tier {escape(code)}</p>
    <h2>{escape(title)}</h2>
    <p class="lede">Client-facing field for packaging and outreach.</p>
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
        fit = row.get("Fit", "")
        fee = row.get("Fee band", "")
        flags = row.get("Flags", "").replace(",", " ·")
        notes = row.get("Notes", "")
        imdb = row.get("IMDb", "")
        n = row.get("#", "")
        bio = actor_bio(name, registry)
        name_html = actor_link(name, imdb, registry)
        if bio:
            name_html = f'<div class="name">{name_html}</div><div class="bio">{bio}</div>'
        else:
            name_html = f'<div class="name">{name_html}</div>'
        body_rows.append(
            f"""<tr data-reveal>
  <td class="num">{escape(n).zfill(2) if n.isdigit() else escape(n)}</td>
  <td>{name_html}</td>
  <td><span class="tier tier-{code.lower()}">{escape(code)}</span></td>
  <td class="num">{escape(fit)}</td>
  <td>{escape(fee)}</td>
  <td>{escape(flags)}</td>
  <td>{escape(notes)}</td>
</tr>"""
        )
    return head + "\n".join(body_rows) + "</tbody></table></div></section>"


def render_character(meta: dict, registry: dict) -> str:
    md = (DOCSWAMP / meta["file"]).read_text(encoding="utf-8")
    profile = extract_role_profile(md)
    shortlists = extract_shortlists(md)
    cards = extract_scorecards(md)

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
  <p class="eyebrow">{escape(meta['tag'])}</p>
  <h1>{escape(meta['hero'])}</h1>
  <p>{escape(meta['lede'])}</p>
  <div class="cta">
    <a class="btn" href="#shortlists">Shortlists</a>
    <a class="btn ghost" href="ensemble.html">Ensemble</a>
  </div>
</header>
<section class="profile" data-reveal>
  <dl>{''.join(dl)}</dl>
  <p class="fit"><strong>Fit criteria.</strong> {escape(fit)}</p>
</section>
<div id="shortlists">
{''.join(render_shortlist_section(t, c, rows, registry) for t, c, rows in shortlists)}
</div>
"""
    if cards:
        card_html = []
        for c in cards[:6]:
            card_html.append(
                f"""<article class="card" data-reveal>
  <h3>{escape(c['name'])}</h3>
  <div class="scores">Creative {escape(c['creative'])} · Risk {escape(c['risk'])} · ROI {escape(c['roi'])} · {escape(c['verdict'])}</div>
  <p>{escape(c['note'])}</p>
</article>"""
            )
        body += f"""
<section data-reveal>
  <header class="section-head">
    <p class="eyebrow">Priority picks</p>
    <h2>Scorecards</h2>
  </header>
  <div class="scorecards">{''.join(card_html)}</div>
</section>
"""
    return shell(meta["title"], meta["slug"], body)


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
  <p class="eyebrow">{escape(meta['tag'])}</p>
  <h1>{escape(meta['hero'])}</h1>
  <p>{escape(meta['lede'])}</p>
  <div class="cta"><a class="btn" href="#packages">Packages</a><a class="btn ghost" href="index.html">Overview</a></div>
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
  <span class="n">{str(i).zfill(2)}</span>
  <h2>{escape(c['hero'])}</h2>
  <p>{escape(c['tag'])}</p>
</a>"""
        )
    cards.append(
        """<a class="home-card" href="ensemble.html" data-reveal>
  <span class="n">06</span>
  <h2>ENSEMBLE</h2>
  <p>Package architecture</p>
</a>"""
    )
    body = f"""
<header class="hero" data-reveal>
  <p class="eyebrow">Shredded Lens · Character &amp; ensemble casting</p>
  <h1>WAR CASTING</h1>
  <p>Confidential shortlists and package architecture for Russell K. Reed’s WAR — High-Contrast Editorial share format.</p>
  <div class="cta"><a class="btn" href="sheila.html">Open leads</a><a class="btn ghost" href="ensemble.html">Packages</a></div>
</header>
<div class="home-grid">{''.join(cards)}</div>
"""
    return shell("WAR Casting Overview", "index", body)


def render_gate(password_hint: str = "Ask your SLS contact") -> str:
    # Soft gate: SHA-256 of password checked client-side; content pages still need separate encrypt for real secrecy.
    # Used as landing UX; staticrypt wraps the real payload.
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex,nofollow" />
<title>WAR Casting · Access</title>
<link href="{FONTS}" rel="stylesheet" />
<style>{CSS}</style>
</head>
<body class="lock-body">
  <form class="lock" id="gate" autocomplete="off">
    <div class="brand" style="font-size:28px;margin-bottom:12px">SLS <span>WAR</span></div>
    <h1>CASTING ACCESS</h1>
    <p>Password-protected casting shred. {escape(password_hint)}.</p>
    <label for="pw">Access password</label>
    <input id="pw" type="password" required />
    <p class="err" id="err"></p>
    <button class="btn" type="submit" style="width:100%;border:0">Enter</button>
  </form>
<script>
const HASH = window.__SLS_HASH__;
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
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(render_index(), encoding="utf-8")
    for c in CHARACTERS:
        (OUT / f"{c['slug']}.html").write_text(render_character(c, registry), encoding="utf-8")
    (OUT / "ensemble.html").write_text(render_ensemble(registry), encoding="utf-8")
    # Placeholder gate; password hash injected by protect script
    (OUT / "gate.html").write_text(
        render_gate().replace("window.__SLS_HASH__", '"__HASH_PLACEHOLDER__"'),
        encoding="utf-8",
    )
    print(f"wrote site to {OUT}")


if __name__ == "__main__":
    main()
