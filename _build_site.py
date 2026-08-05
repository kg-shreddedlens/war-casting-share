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

import calendar
import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import quote

from _scorecard import (
    SECTION1,
    SHORT_TO_FULL,
    build_full_scorecard,
    full_scorecard_html,
    justify_section1,
    money,
    sc_panel,
    sc_row,
    score_num as sc_score_num,
    weighted as sc_weighted,
)

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
    "&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400"
    "&display=swap"
)

GALLERY_PATH = ROOT / "gallery_cache.json"
GALLERY_LOCAL_PATH = ROOT / "gallery_local.json"
NOTES_EXPAND_PATH = ROOT / "notes_expand.json"

# Shortlist Flags tokens → full sentences (shreds keep shorthand; site expands)
FLAG_SENTENCES = {
    "Verbal": "Strong dialogue and verbal delivery.",
    "Presence": "Strong on-screen presence.",
    "Budget": "Fits the target fee and budget lane.",
    "Familiarity": "Useful audience familiarity and recognition.",
    "Gravitas": "Brings weight and gravitas.",
    "Restraint": "Controlled, restrained performance style.",
    "Discovery": "Discovery and rising-talent upside.",
    "Look lock": "Matches the locked look.",
    "Press": "Press and PR value.",
    "Artistic": "Artistic, elevated interpretation of the role.",
    "Ambiguity": "Useful tonal ambiguity for the role.",
    "Horror": "Horror and dread fluency.",
    "Stage": "Strong stage craft.",
    "Commercial": "Commercial draw.",
    "Symbolic": "Symbolic or iconic casting value.",
    "Range": "Wide performance range.",
    "Press rising": "Rising press profile.",
    "Presence rising": "Rising on-screen presence.",
    "Familiarity rising": "Rising audience familiarity.",
    "Familiarity adjacent": "Adjacent familiarity without overexposure.",
}

# Buffalo 8-style fee quantification used in shortlists / actor shreds
FEE_BAND_DOLLARS = [
    ("extremely high", "Extremely High", ">$1M"),
    ("med-high", "Med-High", "~$250–750K"),
    ("med/high", "Med/High", "~$250–750K"),
    ("low-med", "Low-Med", "~$50–150K"),
    ("low/med", "Low/Med", "~$50–150K"),
    ("high", "High", "$500K–$1M"),
    ("med", "Med", "$100–500K"),
    ("low", "Low", "<$100K"),
]

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

# Per-package briefing for the Ensemble share page (from Ensemble shred §3–§8).
# Keys match cleaned Package column values (e.g. "B1 (primary)", "A1").
PACKAGE_BRIEFS: dict[str, dict] = {
    "A1": {
        "verdict": "Sales peak — fee volatile",
        "why": (
            "Highest ranked PoS (84%) with dual marquee gravity for the Spector / "
            "acquisitions conversation. Maximum heat across all five roles."
        ),
        "good": [
            "Peak sales chatter and prestige ceiling (Prestige 10).",
            "Pugh microscopic lead energy + Gyllenhaal name gravity.",
            "Wilson / Thompson / Ali is a premium supporting spine.",
        ],
        "bad": [
            "Dual A-list fee risk can erase the low–mid budget advantage the deck sells.",
            "Ceiling reads High / volatile — packaging can price itself out of the thesis.",
        ],
        "ugly": [
            "Ali only works if Norman stays cameo-structured; a full detective arc lets a star demand closure and break the inconclusive file.",
        ],
        "caveats": [
            "Prefer A3 or B1 for risk-adjusted packaging unless acquisitions explicitly need this heat.",
            "Run parallel LOI waves — franchise / schedule conflicts are real on Pugh-class names.",
        ],
    },
    "A2": {
        "verdict": "Acquisitions — gate the fees",
        "why": (
            "Sales-Max with better median ROI than A1 (3.1x) and higher authenticity (9). "
            "Comer intensity paired with Isaac ambiguity is a strong acquisitions story."
        ),
        "good": [
            "Comer / Isaac carries both dread craft and buyer recognition.",
            "Ferguson is a clinical Samantha foil; Brown anchors Norman without crusading.",
            "Still a High ceiling without A1’s Prestige-10 fee panic.",
        ],
        "bad": [
            "Fee stack remains high — only recommend if fees are gated (P2 posture).",
            "Kravitz Melina can tip vampier than the soft-temptation lock.",
        ],
        "ugly": [
            "Comer / Isaac schedule and franchise conflicts can stall LOIs for months.",
        ],
        "caveats": [
            "Treat as RECOMMEND only when backend / quote discipline is locked.",
            "Keep a Melina look check against writer references before soft-offer.",
        ],
    },
    "A3": {
        "verdict": "Best risk-adjusted Sales-Max",
        "why": (
            "Matches the valuation sheet and the Skydance husband note (Redmayne) without "
            "stacking two Extremely High lead fees. Strongest disciplined Sales-Max."
        ),
        "good": [
            "Kirby Med/High Sheila leverage + Redmayne financing pull.",
            "Asomugha keeps the writer-locked Norman; Wilson locks the sister foil.",
            "ROI 3.3x with Auth 9 — better efficiency than A1.",
        ],
        "bad": [
            "PoS 80 sits under A1/A2; Prestige 8 is strong but not max heat.",
            "Redmayne alone can still stretch a mid-high model.",
        ],
        "ugly": [
            "If Redmayne quotes like an Extremely High feeler, you quietly recreate the A1 fee problem on one side of the marriage.",
        ],
        "caveats": [
            "Default Sales-Max if buyers demand marquee without dual A-list insanity.",
            "Keep B1 live in parallel — same Sheila, cheaper James ambiguity craft.",
        ],
    },
    "B1 (primary)": {
        "verdict": "RECOMMEND PACKAGE",
        "why": (
            "Primary Balanced default: sheet-aligned Sheila leverage, James as an ambiguity "
            "engine (not a charm lead), writer-locked Norman, and Melina look efficiency. "
            "Best PoS × efficiency in the grid (83% / 3.5x)."
        ),
        "good": [
            "Chemistry pairs score ≥8 (Kirby↔Abbott 9; sister and interrogation pairs 8).",
            "PR cluster stays clean; Package Risk Low–Moderate.",
            "Nnamdi single-role rule respected — Norman only, not James.",
        ],
        "bad": [
            "Abbott is craft-first, not a Spector “bigger name” headline by himself.",
            "Onieogou needs a chemistry read with Abbott before the workplace gravity locks.",
        ],
        "ugly": [
            "If Kirby declines and no Foy parallel is live, the whole investor narrative has to be rewritten mid-outreach.",
        ],
        "caveats": [
            "Keep James off comic-charm casting — tone clash risk stays Low only on this read.",
            "LOI order starts Kirby → Foy parallel → Abbott → Asomugha → Wilson → Onieogou.",
        ],
    },
    "B2": {
        "verdict": "Kirby-decline parallel",
        "why": (
            "Prestige-pair alternate when Kirby is unavailable: Foy↔O’Connor chemistry scores 9 "
            "and keeps Balanced efficiency (81% / 3.4x) without dropping into Lean."
        ),
        "good": [
            "Foy Med/High Sheila value per Buffalo 8 / sales feedback.",
            "Coon is an overqualified Samantha instrument; Hornsby holds inconclusive Norman.",
            "Beetz Melina keeps soft presence without forcing vamp.",
        ],
        "bad": [
            "Slightly under B1 on PoS and ROI.",
            "Crown associations can telegraph prestige TV before marriage-horror.",
        ],
        "ugly": [
            "Stacking too much Crown DNA (Foy + O’Connor adjacency in buyer brains) can make the package feel like a royal-drama leftover, not doppelgänger dread.",
        ],
        "caveats": [
            "Run as the live Sheila parallel while Kirby LOIs are out.",
            "Tone materials should lead with Invisible Man / Us comps, not Crown stills.",
        ],
    },
    "B3": {
        "verdict": "Awards-forward alternate",
        "why": (
            "Negga↔Redmayne tells an awards-capable marriage story with Auth 9 and solid "
            "ROI (3.3x). Financing narrative shifts from sheet leverage to craft prestige."
        ),
        "good": [
            "Negga awards credibility; Redmayne still carries the Skydance husband note.",
            "Condon / Thompson / Holland is a high-craft supporting set.",
            "Strong if the desk is filmmaker-forward rather than Spector-marquee.",
        ],
        "bad": [
            "Leverage 7 — weaker sheet pull than Kirby/Foy lanes.",
            "PoS 80 is fine, not primary.",
        ],
        "ugly": [
            "Ethnicity / look story must be intentional versus writer guidance — do not accidentally sell two conflicting Sheila theses at once.",
        ],
        "caveats": [
            "Align Russell on the James / Sheila ethnicity branch before dual LOI stories.",
            "Use when awards packaging matters more than Buffalo 8 peak leverage.",
        ],
    },
    "B4": {
        "verdict": "Wildcard craft — CONSIDER",
        "why": (
            "Festival / SPC filmmaker-forward package with the grid’s best median ROI (3.6x) "
            "and Auth 10. Discovery story is the point, not marquee gravity."
        ),
        "good": [
            "Reinsve + Abbott is pure ambiguity craft; Clifford Samantha is efficient.",
            "Myha’la Melina and Asomugha Norman keep locks honest.",
            "Highest authenticity score in the scenario grid.",
        ],
        "bad": [
            "Leverage 6 and PoS 77 — Spector “bigger names” path is weak here.",
            "Ceiling Moderate+; acquisitions desks may shrug without a lead marquee.",
        ],
        "ugly": [
            "Pitching B4 to a Grindstone-style buyer as if it were A1 is how packages die in the room.",
        ],
        "caveats": [
            "CONSIDER for SPC / filmmaker-forward capital only (P4).",
            "Keep A/B feelers alive if this is a creative preference, not the financing spine.",
        ],
    },
    "C1": {
        "verdict": "Lean efficiency — CONSIDER",
        "why": (
            "Cost-controlled discovery with horror-fluent Sheila (Clark) and Moonlight-depth "
            "James (Rhodes), while retaining Asomugha’s Norman lock and Coon’s Samantha steel."
        ),
        "good": [
            "Cost efficiency 9; ROI 3.2x still healthy for Lean.",
            "Concept-led capital can buy this without erasing budget advantage.",
            "Auth 9 — craft does not collapse when marquee leaves.",
        ],
        "bad": [
            "PoS 74; marquee gravity target is (not met) for Spector-style buyers.",
            "Ceiling Moderate — sales chat gets quieter.",
        ],
        "ugly": [
            "Rings of Power heat on Clark can fight a contained marriage-horror sell if materials are lazy.",
        ],
        "caveats": [
            "Works when investor thesis is concept + prior film success, not marquee.",
            "Do not pretend this is a Sales-Max package.",
        ],
    },
    "C2": {
        "verdict": "Lean authenticity path",
        "why": (
            "Lowest-cost authenticity package: Campbell / Hodge leads with Clifford / Myha’la / "
            "Morgan support. Built for tax/stream efficiency and discovery narrative."
        ),
        "good": [
            "Cost efficiency 9; Hodge carries James-or-Norman lane flexibility in the wider shred.",
            "UK / working-actor credibility without fake prestige.",
        ],
        "bad": [
            "PoS 71 — weakest ranked package on probability of success.",
            "Almost no acquisitions gravity without a lead marquee.",
        ],
        "ugly": [
            "If this is the only package in the room, you are asking capital to fund a concept with almost no talent insurance.",
        ],
        "caveats": [
            "Discovery packaging only — keep B1 faces in the pitch deck even if C2 is the close.",
            "Morgan Norman must stay inconclusive; no crusading-star rewrite.",
        ],
    },
    "C3": {
        "verdict": "Ethnicity-branch lean",
        "why": (
            "Lean package that retains Abbott’s uncanny James craft while testing a Beharie "
            "Sheila ethnicity-branch read (72% PoS / 3.3x ROI / Auth 9)."
        ),
        "good": [
            "Abbott continuity with Balanced James thinking.",
            "Doherty / Clemons / Joseph keeps cost efficiency high.",
            "Useful if Russell locks a non-default ethnicity story early.",
        ],
        "bad": [
            "Beharie Sheila leverage is Low on the valuation sheet.",
            "PoS 72 — still under Balanced defaults.",
        ],
        "ugly": [
            "Running C3 and B1 outreach simultaneously without an ethnicity decision creates two movies in buyers’ heads.",
        ],
        "caveats": [
            "Align Russell on White-mix vs Black/AA-mix James/Sheila branches before dual LOI stories.",
            "Treat as a deliberate branch, not a silent backup.",
        ],
    },
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
:root{--bg:#f7f7f5;--ink:#0a0a0a;--muted:#5c5c5c;--accent:#b10f2e;--line:#0a0a0a;--soft:#e2e2e0;--radius:12px}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans",system-ui,sans-serif;min-height:100vh;font-optical-sizing:auto}
a{color:var(--ink)}a:hover{color:var(--accent)}
.wrap{max-width:1140px;margin:0 auto;padding:20px 20px 80px}
.top{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid var(--ink);padding-bottom:10px;margin-bottom:18px;gap:16px;flex-wrap:wrap}
.brand{font-family:"Bebas Neue",sans-serif;font-size:42px;letter-spacing:.04em;line-height:1;text-decoration:none;color:var(--ink)}
.brand span{color:var(--accent)}
.meta{font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.1em;text-transform:uppercase;font-weight:600;color:var(--muted)}
.nav{display:flex;gap:14px;flex-wrap:wrap;border-bottom:1px solid var(--ink);padding:12px 0 14px;margin-bottom:8px}
.nav a{font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.12em;text-transform:uppercase;text-decoration:none;color:var(--muted);font-weight:600}
.nav a:hover,.nav a.active{color:var(--accent)}
.hero{padding:28px 0 20px;border-bottom:1px solid var(--ink);display:grid;grid-template-columns:1fr auto;gap:28px;align-items:center}
@media(max-width:800px){.hero{grid-template-columns:1fr}}
.hero-copy h1{font-family:"Bebas Neue",sans-serif;font-size:clamp(3.5rem,10vw,7rem);line-height:.85;margin:0 0 12px;letter-spacing:.02em;max-width:14ch}
.hero-copy p{margin:0;max-width:44ch;font-size:1.05rem;line-height:1.5;color:var(--muted);font-weight:500}
.eyebrow{font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin:0 0 8px;font-weight:700}
.cta{display:flex;gap:12px;margin-top:22px;flex-wrap:wrap}
.btn{appearance:none;text-decoration:none;padding:10px 16px;font-family:"Bebas Neue",sans-serif;font-size:16px;letter-spacing:.08em;text-transform:uppercase;cursor:pointer;display:inline-block;background:var(--ink);color:#fff;border:1px solid var(--ink)}
.btn.ghost{background:transparent;color:var(--ink)}
.btn:hover{border-color:var(--accent)}
.avatar-wrap{position:relative;display:inline-block;flex-shrink:0;z-index:1}
.avatar-wrap:hover{z-index:40}
.avatar{width:160px;height:160px;border-radius:var(--radius);object-fit:cover;object-position:center 18%;border:2px solid var(--ink);background:#eee;display:block;transition:transform .25s ease,box-shadow .25s ease}
.avatar-wrap:hover .avatar{transform:scale(1.85);box-shadow:0 18px 50px rgba(0,0,0,.28)}
.avatar.lg{width:200px;height:200px}
.avatar.sm{width:80px;height:80px;border-width:2px}
.avatar.tile{width:84px;height:84px}
.avatar.main{width:100%;max-width:280px;height:auto;aspect-ratio:1;border-radius:var(--radius)}
.section-head{margin:56px 0 20px}
.section-head h2{font-family:"Bebas Neue",sans-serif;font-size:2.6rem;letter-spacing:.03em;margin:0}
.lede{margin:8px 0 0;max-width:52ch;line-height:1.5;color:var(--muted);font-weight:500}
.profile{display:grid;grid-template-columns:1.1fr .9fr;gap:28px;margin:36px 0;padding-bottom:28px;border-bottom:1px solid var(--soft)}
@media(max-width:800px){.profile{grid-template-columns:1fr}}
.profile dl{margin:0;display:grid;grid-template-columns:150px 1fr;gap:10px 16px;font-size:15px}
.profile dt{font-family:"DM Sans",sans-serif;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding-top:2px;font-weight:700}
.profile dd{margin:0;line-height:1.45;font-weight:500}
.fit{font-size:15px;line-height:1.55;color:var(--muted);margin:0;font-weight:500}
.fit-block{margin:0}
.fit-block > strong{display:block;font-family:"DM Sans",sans-serif;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink);margin-bottom:10px}
.fit-list{margin:0;padding-left:1.2rem;color:var(--muted);font-size:15px;line-height:1.45;font-weight:500}
.fit-list li{margin:0 0 10px;padding-left:4px}
.fit-list li::marker{font-weight:700;color:var(--ink)}
.table-wrap{overflow:auto;border-bottom:3px solid var(--ink);margin-bottom:8px}
.slist-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;margin-top:8px}
.slist-tile{display:flex;flex-direction:column;gap:14px;border:1px solid var(--ink);border-radius:var(--radius);background:#fff;padding:16px 16px 18px;text-decoration:none;color:inherit;min-height:100%;transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease;cursor:pointer}
.slist-tile:hover{transform:translateY(-3px);border-color:var(--accent);color:inherit;box-shadow:0 12px 28px rgba(0,0,0,.08)}
.slist-tile:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.slist-top{display:flex;justify-content:space-between;align-items:center;gap:10px}
.slist-rank{font-family:"DM Sans",sans-serif;font-size:12px;letter-spacing:.12em;text-transform:uppercase;font-weight:700;color:var(--muted)}
.slist-head{display:flex;gap:14px;align-items:center}
.slist-head .text{min-width:0}
.slist-name{font-family:"Bebas Neue",sans-serif;font-size:1.65rem;letter-spacing:.03em;margin:0;line-height:.95}
.slist-bio{color:var(--muted);font-size:13.5px;line-height:1.4;margin:6px 0 0;font-weight:500;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.slist-bio-list{margin:6px 0 0;padding-left:1.1rem;color:var(--muted);font-size:13px;line-height:1.4;font-weight:500}
.slist-bio-list li{margin:0 0 4px;padding-left:2px}
.slist-bio-list li:last-child{margin-bottom:0}
.slist-bio-list li::marker{color:var(--ink);font-weight:700}
.slist-metrics{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:auto;padding-top:12px;border-top:1px solid var(--soft)}
.slist-metric{min-width:0}
.slist-metric .lbl{display:block;font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:var(--muted);margin-bottom:4px}
.slist-metric .val{font-weight:700;font-size:15px;line-height:1.3}
.slist-metric .val.fit-n{font-family:"Bebas Neue",sans-serif;font-size:2.2rem;font-weight:400;letter-spacing:.02em;line-height:1;color:var(--ink)}
.slist-metric.span-2{grid-column:1 / -1}
.slist-notes{margin:0;color:var(--muted);font-size:14px;line-height:1.45;font-weight:500}
.slist-tile .icon-row{margin-top:2px}
.fee-cell{line-height:1.35}
.fee-cell .fee-band{display:block;font-weight:700}
.fee-cell .fee-dollars{display:block;font-size:12px;color:var(--muted);font-weight:500;margin-top:2px}
.tier{display:inline-block;padding:3px 9px;font-size:11px;letter-spacing:.08em;border:1px solid var(--ink);font-family:"DM Sans",sans-serif;font-weight:700;border-radius:6px}
.tier-a{background:var(--accent);color:#fff;border-color:var(--accent)}
.num{font-variant-numeric:tabular-nums;font-family:"DM Sans",sans-serif;font-size:12px;font-weight:600}
.icon-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}
.icon-link{display:inline-flex;align-items:center;gap:7px;width:auto;height:auto;padding:6px 10px;border-radius:8px;text-decoration:none;background:#111;color:#fff;font-family:"DM Sans",sans-serif;font-size:12px;font-weight:600;letter-spacing:.02em;transition:transform .2s ease,background .2s ease,color .2s ease}
.icon-link:hover{transform:translateY(-2px);background:var(--accent);color:#fff}
.icon-link.imdb{background:#f5c518;color:#0a0a0a}
.icon-link.imdb:hover{background:#ffd84a;color:#0a0a0a}
.icon-link.wiki{background:#111}
.icon-link.ig{background:linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888)}
.icon-link.yt{background:#ff0000}
.icon-link.li{background:#0a66c2}
.icon-link.spot{background:#222}
.icon-link svg{width:14px;height:14px;display:block;flex-shrink:0}
.icon-link .lbl{line-height:1;white-space:nowrap}
.roi-box{border:1px solid var(--ink);border-radius:var(--radius);padding:18px 20px;margin:0;background:#fff}
.roi-box h3{font-family:"Bebas Neue",sans-serif;font-size:1.55rem;margin:0 0 14px;letter-spacing:.03em;line-height:1;padding-bottom:10px;border-bottom:1px solid var(--soft)}
.roi-box .roi-metrics{font-family:"DM Sans",sans-serif;font-size:13px;letter-spacing:.06em;text-transform:uppercase;font-weight:700;margin:0 0 10px;color:var(--muted)}
.roi-box .roi-metrics strong{color:var(--ink)}
.roi-box p{margin:0;color:var(--muted);font-size:15px;line-height:1.5;font-weight:500}
.roi-mini-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:0 0 12px}
@media(max-width:700px){.roi-mini-grid{grid-template-columns:repeat(2,1fr)}}
.roi-mini{border:1px solid var(--soft);border-radius:10px;padding:12px 12px 11px;background:#fafaf8;min-width:0}
.roi-mini .rm-lbl{display:block;font-family:"DM Sans",sans-serif;font-size:10px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:var(--muted);margin-bottom:6px}
.roi-mini .rm-val{font-family:"Bebas Neue",sans-serif;font-size:1.65rem;letter-spacing:.02em;line-height:1;color:var(--ink)}
.roi-mini .rm-sub{display:block;margin-top:5px;font-size:12px;color:var(--muted);font-weight:500;line-height:1.35}
.roi-box .roi-note{margin:0;padding-top:10px;border-top:1px solid var(--soft);color:var(--muted);font-size:13.5px;line-height:1.45;font-weight:500}
.info-tile .slist-bio-list{margin-top:4px}
.info-tile .info-prose{margin:0;color:var(--muted);font-size:14.5px;line-height:1.5;font-weight:500}
.scorecards{display:grid;gap:16px;margin-top:18px}
.card{border:1px solid var(--ink);padding:18px 20px;display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:start;text-decoration:none;color:inherit;transition:transform .2s ease,border-color .2s ease;border-radius:2px}
.card:hover{transform:translateY(-2px);border-color:var(--accent);color:inherit}
.card h3{font-family:"Bebas Neue",sans-serif;font-size:1.7rem;margin:0 0 6px;letter-spacing:.03em}
.card .scores{font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:10px;font-weight:700}
.card p{margin:0;line-height:1.45;color:var(--muted);font-weight:500}
.attr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px;margin:14px 0}
.attr{border:1px solid var(--ink);padding:10px 12px;background:#fff}
.attr b{display:block;font-family:"DM Sans",sans-serif;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:700}
.attr span{font-family:"Bebas Neue",sans-serif;font-size:1.55rem}
.scorecard-full{margin-top:8px;max-width:980px}
.sc-panel{border:1px solid var(--ink);border-bottom:4px solid var(--ink);background:#fff;margin:28px 0 0;overflow:hidden}
.sc-panel-head{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:end;padding:22px 22px 18px;border-bottom:2px solid var(--ink);background:#fafaf8}
.sc-panel-titles{min-width:0}
.sc-h{font-family:"Bebas Neue",sans-serif;font-size:clamp(1.85rem,4vw,2.35rem);letter-spacing:.03em;margin:0;line-height:.95}
.sc-note{margin:10px 0 0;color:var(--muted);font-size:15px;font-weight:500;line-height:1.45;max-width:52ch}
.sc-badge{text-align:right;line-height:1;font-variant-numeric:tabular-nums}
.sc-badge-n{font-family:"Bebas Neue",sans-serif;font-size:clamp(2.8rem,6vw,3.6rem);letter-spacing:.02em;display:block}
.sc-badge-den{font-family:"DM Sans",sans-serif;font-size:14px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.sc-rows{list-style:none;margin:0;padding:0}
.sc-row{display:grid;grid-template-columns:minmax(160px,1.05fr) minmax(200px,1.45fr) auto;gap:18px 22px;align-items:start;padding:18px 22px;border-bottom:1px solid var(--soft)}
@media(max-width:720px){.sc-row{grid-template-columns:1fr auto}.sc-why{grid-column:1 / -1;order:3}.sc-score{order:2}}
.sc-row:last-child{border-bottom:0}
.sc-row:hover{background:#f7f7f5}
.sc-cat{font-family:"Bebas Neue",sans-serif;font-size:clamp(1.35rem,3vw,1.7rem);letter-spacing:.03em;margin:0;line-height:1}
.sc-prompt{margin:8px 0 0;color:var(--muted);font-size:15px;line-height:1.45;font-weight:500;max-width:36ch}
.sc-meta{margin:8px 0 0;font-family:"DM Sans",sans-serif;font-size:12px;letter-spacing:.07em;text-transform:uppercase;font-weight:700;color:var(--muted)}
.sc-why{min-width:0;padding-top:2px}
.sc-why-label{display:block;font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:var(--muted);margin-bottom:6px}
.sc-why p{margin:0;color:var(--ink);font-size:14.5px;line-height:1.45;font-weight:500}
.sc-score{text-align:right;line-height:1;font-variant-numeric:tabular-nums;min-width:4.5rem;padding-top:2px}
.sc-score-n{font-family:"Bebas Neue",sans-serif;font-size:clamp(2.4rem,5vw,3.1rem);letter-spacing:.02em}
.sc-score-den{font-family:"DM Sans",sans-serif;font-size:13px;font-weight:700;color:var(--muted);letter-spacing:.04em;margin-left:2px}
.sc-panel-foot{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;padding:16px 22px;background:#111;color:#fff;border-top:2px solid var(--ink)}
.sc-foot-label{font-family:"DM Sans",sans-serif;font-size:12px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;opacity:.75}
.sc-foot-value{font-family:"Bebas Neue",sans-serif;font-size:clamp(1.7rem,4vw,2.2rem);letter-spacing:.03em;line-height:1}
.sc-foot-value strong{font-weight:400}
.sc-foot-den{font-family:"DM Sans",sans-serif;font-size:14px;font-weight:700;letter-spacing:.04em;opacity:.7;margin-left:2px}
.sc-foot-extra{font-family:"DM Sans",sans-serif;font-size:13px;font-weight:600;letter-spacing:.02em;opacity:.8;margin-left:6px}
.sc-preview{margin-top:14px;max-width:100%}
.sc-preview .sc-panel{margin-top:0}
.sc-preview .sc-panel-head{padding:14px 16px 12px}
.sc-preview .sc-h{font-size:1.45rem}
.sc-preview .sc-note{font-size:13px;margin-top:6px}
.sc-preview .sc-badge-n{font-size:2.2rem}
.sc-preview .sc-row{padding:12px 16px;gap:12px}
.sc-preview .sc-cat{font-size:1.2rem}
.sc-preview .sc-prompt{font-size:13.5px;margin-top:5px}
.sc-preview .sc-meta{font-size:11px;margin-top:5px}
.sc-preview .sc-score-n{font-size:2rem}
.sc-preview .sc-panel-foot{padding:12px 16px}
.sc-preview .sc-foot-value{font-size:1.45rem}
@media(max-width:560px){
  .sc-panel-head{grid-template-columns:1fr;align-items:start}
  .sc-badge{text-align:left}
  .sc-row{grid-template-columns:1fr;gap:10px}
  .sc-score{text-align:left}
}
.pkg-grid{display:grid;gap:18px;margin-top:16px}
.pkg{border:1px solid var(--ink);padding:20px 22px;display:grid;gap:14px;background:#fff;border-radius:var(--radius)}
.pkg.primary{border-width:3px}
.pkg-head{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:10px 18px}
.pkg h3{font-family:"Bebas Neue",sans-serif;font-size:1.85rem;margin:0;letter-spacing:.03em}
.pkg-verdict{margin:0;font-family:"DM Sans",sans-serif;font-size:12px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;color:var(--accent)}
.pkg .metrics{font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.06em;text-transform:uppercase;font-weight:700;width:100%}
.pkg .metrics strong{color:var(--accent)}
.pkg-body{display:grid;grid-template-columns:minmax(180px,.85fr) minmax(240px,1.4fr);gap:22px 28px;align-items:start}
@media(max-width:800px){.pkg-body{grid-template-columns:1fr}}
.pkg-cast h4,.pkg-analysis h4,.pkg-gbu h5,.ens-block h3{font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;margin:0 0 8px;color:var(--ink)}
.pkg-cast ul,.pkg-analysis ul,.ens-block ul{margin:0;padding-left:1.15rem;color:var(--muted);line-height:1.45;font-weight:500;font-size:14px}
.pkg-cast li,.pkg-analysis li,.ens-block li{margin:0 0 6px}
.pkg-why{margin:0 0 12px;color:var(--muted);font-size:14.5px;line-height:1.5;font-weight:500}
.pkg-gbu{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:12px 0}
@media(max-width:900px){.pkg-gbu{grid-template-columns:1fr}}
.pkg-gbu .gbu-good h5{color:#1a6b3c}
.pkg-gbu .gbu-bad h5{color:#8a5a00}
.pkg-gbu .gbu-ugly h5{color:var(--accent)}
.pkg-caveats{margin-top:4px;padding-top:12px;border-top:1px solid var(--soft)}
.ens-stack{display:grid;gap:28px;margin-top:40px}
.ens-block{border-top:1px solid var(--soft);padding-top:22px}
.ens-block p{margin:0;color:var(--muted);font-size:15px;line-height:1.55;font-weight:500;max-width:70ch}
.ens-two{display:grid;grid-template-columns:1fr 1fr;gap:22px}
@media(max-width:800px){.ens-two{grid-template-columns:1fr}}
.chem-table,.risk-table{width:100%;border-collapse:collapse;font-size:14px}
.chem-table th,.risk-table th{text-align:left;font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.1em;text-transform:uppercase;padding:8px 10px 8px 0;border-bottom:1px solid var(--ink);color:var(--muted)}
.chem-table td,.risk-table td{padding:10px 10px 10px 0;border-bottom:1px solid var(--soft);vertical-align:top;color:var(--muted);font-weight:500;line-height:1.4}
.chem-table td:first-child,.risk-table td:first-child{color:var(--ink);font-weight:700;white-space:nowrap}
.loi-list{margin:0;padding-left:1.2rem;color:var(--muted);font-size:14.5px;line-height:1.5;font-weight:500;columns:2;gap:28px}
@media(max-width:700px){.loi-list{columns:1}}
.loi-list li{margin:0 0 8px;break-inside:avoid}
.home-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-top:28px}
.home-card{border:1px solid var(--ink);padding:18px;text-decoration:none;color:var(--ink);display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;min-height:150px;transition:transform .25s ease,border-color .25s ease}
.home-card:hover{transform:translateY(-3px);border-color:var(--accent);color:var(--ink)}
.home-card .n{font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.12em;color:var(--accent);font-weight:700}
.home-card h2{font-family:"Bebas Neue",sans-serif;font-size:2rem;margin:6px 0;letter-spacing:.03em;line-height:.95}
.home-card p{margin:0;color:var(--muted);font-size:14px;line-height:1.4;font-weight:500}
.footer{margin-top:64px;padding-top:14px;border-top:3px solid var(--ink);font-family:"DM Sans",sans-serif;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-weight:600}
.reel{display:grid;grid-template-columns:200px 1fr;gap:16px;border:1px solid var(--ink);padding:12px;margin-top:18px;text-decoration:none;color:inherit;align-items:center}
@media(max-width:640px){.reel{grid-template-columns:1fr}}
.reel img{width:100%;aspect-ratio:16/9;object-fit:cover;border:1px solid var(--soft);display:block;border-radius:8px}
.reel h4{font-family:"Bebas Neue",sans-serif;font-size:1.3rem;margin:0 0 6px;letter-spacing:.03em}
.reel p{margin:0;color:var(--muted);font-size:14px;line-height:1.4;font-weight:500}
.detail-layout{display:grid;grid-template-columns:minmax(220px,280px) 1fr;gap:28px;margin:28px 0;align-items:start}
@media(max-width:900px){.detail-layout{grid-template-columns:1fr}}
.info-tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:0}
@media(max-width:720px){.info-tiles{grid-template-columns:1fr}}
.info-tile{border:1px solid var(--ink);border-radius:var(--radius);background:#fff;padding:16px 18px 18px;min-width:0}
.info-tile.span-2{grid-column:1 / -1}
.info-tile-title{font-family:"Bebas Neue",sans-serif;font-size:1.45rem;letter-spacing:.03em;margin:0 0 14px;line-height:1;padding-bottom:10px;border-bottom:1px solid var(--soft)}
.info-tile .icon-row{margin-top:0}
.kv{display:grid;grid-template-columns:min(38%,150px) 1fr;gap:12px 14px;margin:0}
.kv dt{font-family:"DM Sans",sans-serif;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:700;padding-top:3px}
.kv dd{margin:0;font-weight:600;line-height:1.4;font-size:16px;max-width:42ch;overflow-wrap:anywhere}
.gallery-block{margin:8px 0 28px;width:100%}
.carousel{display:flex;gap:12px;overflow-x:auto;padding:6px 2px 14px;scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch;width:100%}
.carousel::-webkit-scrollbar{height:6px}
.carousel::-webkit-scrollbar-thumb{background:#bbb;border-radius:99px}
.carousel figure{margin:0;flex:0 0 clamp(160px,18vw,220px);scroll-snap-align:start}
.carousel img{width:100%;aspect-ratio:1;height:auto;object-fit:cover;object-position:center 18%;border-radius:var(--radius);border:2px solid var(--ink);display:block;transition:transform .25s ease}
.carousel .avatar-wrap:hover img{transform:scale(1.28)}
.carousel-empty{border:1px dashed var(--soft);padding:18px;color:var(--muted);font-size:14px;font-weight:500}
[data-reveal]{opacity:0;transform:translateY(14px);transition:opacity .7s ease,transform .7s ease}
[data-reveal].in{opacity:1;transform:none}
"""

JS = """
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add('in'); });
}, { threshold: 0.12 });
document.querySelectorAll('[data-reveal]').forEach((el) => io.observe(el));
document.querySelectorAll('[data-href]').forEach((el) => {
  el.addEventListener('click', (e) => {
    if (e.target.closest('a')) return;
    location.href = el.getAttribute('data-href');
  });
  el.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); location.href = el.getAttribute('data-href'); }
  });
});
"""

ICONS = {
    "imdb": '<svg viewBox="0 0 24 24" aria-hidden="true"><text x="12" y="16" text-anchor="middle" font-size="8" font-family="Arial Black,Arial,sans-serif" font-weight="900" fill="currentColor">IMDb</text></svg>',
    "wiki": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3c.4 0 .7.2.9.5l2.2 4.2 2.4-4.2c.2-.3.5-.5.9-.5h1.7l-3.5 5.8L20 21h-2.1l-2.5-5.1L12.8 21h-1.6l2.6-5.1L11.3 21H9.2l3.4-6.5L9.1 8.7h1.8L12 12l1.2-3.3h1.7L12.6 13 15 21h.1L19.2 3H12z"/></svg>',
    "ig": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 3h10a4 4 0 0 1 4 4v10a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4zm10 2H7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm-5 3.5A4.5 4.5 0 1 1 7.5 13 4.5 4.5 0 0 1 12 8.5zm0 2A2.5 2.5 0 1 0 14.5 13 2.5 2.5 0 0 0 12 10.5zM17.8 6.2a1 1 0 1 1-1 1 1 1 0 0 1 1-1z"/></svg>',
    "li": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6.5 9.5H4V20h2.5zm-1.2-4.2a1.6 1.6 0 1 0 0 3.2 1.6 1.6 0 0 0 0-3.2zM20 20h-2.5v-5.3c0-1.5-.6-2.4-1.8-2.4-1.1 0-1.7.7-2 1.5-.1.3-.1.6-.1.9V20H11v-7.8c0-1.5 0-2.7-.1-3.7h2.2l.1 1.6h.1c.4-.8 1.5-2 3.4-2 2.3 0 4 1.5 4 5.1z"/></svg>',
    "yt": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M23 12.2s0-3.2-.4-4.7c-.2-.9-.9-1.6-1.8-1.8C18.5 5.2 12 5.2 12 5.2s-6.5 0-8.8.5c-.9.2-1.6.9-1.8 1.8C1 9 1 12.2 1 12.2s0 3.2.4 4.7c.2.9.9 1.6 1.8 1.8 2.3.5 8.8.5 8.8.5s6.5 0 8.8-.5c.9-.2 1.6-.9 1.8-1.8.4-1.5.4-4.7.4-4.7zM9.8 15.5v-6.6l6.3 3.3-6.3 3.3z"/></svg>',
    "spot": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6 3h9l5 5v13H6zm9 1.5V9h4.5z"/></svg>',
}


def slugify(name: str) -> str:
    s = name.lower()
    s = s.replace("'", "").replace("'", "").replace(".", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


_NOTES_EXPAND: dict[str, str] | None = None


def load_notes_expand() -> dict[str, str]:
    global _NOTES_EXPAND
    if _NOTES_EXPAND is None:
        if NOTES_EXPAND_PATH.exists():
            _NOTES_EXPAND = json.loads(NOTES_EXPAND_PATH.read_text(encoding="utf-8"))
        else:
            _NOTES_EXPAND = {}
    return _NOTES_EXPAND


def expand_flags(raw: str) -> str:
    """Turn shred flag tokens into readable sentences for the share site."""
    if not (raw or "").strip():
        return ""
    parts = [p.strip() for p in re.split(r"[,/]+", raw) if p.strip()]
    sentences: list[str] = []
    for part in parts:
        mapped = FLAG_SENTENCES.get(part) or FLAG_SENTENCES.get(part.title())
        sentences.append(mapped or f"{part} is a casting strength here.")
    return " ".join(sentences)


def expand_notes(raw: str) -> str:
    """Turn shred note shorthand into a full sentence when possible."""
    text = (raw or "").strip()
    if not text:
        return ""
    mapped = load_notes_expand().get(text)
    if mapped:
        return mapped
    if text.endswith(".") and len(text) > 24:
        return text
    if text.lower().startswith(("prefer ", "if ", "alt ")):
        return text if text.endswith(".") else f"{text}."
    return text if text.endswith(".") else f"{text}."


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
            out["Fit criteria"] = "\n".join(x.strip() for x in block.group(1).splitlines() if x.strip())
    return out


def fee_parts(fee: str) -> tuple[str, str]:
    """Return (band label, dollar range) for Buffalo 8-style fee bands."""
    raw = (fee or "").strip()
    if not raw:
        return ("—", "")
    key = raw.lower().replace(" ", "")
    for needle, label, dollars in FEE_BAND_DOLLARS:
        if needle.replace(" ", "") in key:
            return (label if label.lower() in raw.lower() else raw, dollars)
    return (raw, "")


def info_tile(title: str, rows: list[tuple[str, str]], *, span2: bool = False, extra: str = "") -> str:
    """Titled rounded info tile with key/value rows."""
    items = "".join(
        f"<dt>{escape(k)}</dt><dd>{v}</dd>" for k, v in rows if v not in (None, "")
    )
    span = " span-2" if span2 else ""
    body = f'<dl class="kv">{items}</dl>' if items else ""
    return f"""<article class="info-tile{span}">
  <h3 class="info-tile-title">{escape(title)}</h3>
  {body}
  {extra}
</article>"""


def fee_quantified(fee: str) -> str:
    band, dollars = fee_parts(fee)
    if dollars:
        return f"{band} · {dollars}"
    return band


def fee_cell_html(fee: str) -> str:
    band, dollars = fee_parts(fee)
    if dollars:
        return (
            f'<div class="fee-cell"><span class="fee-band">{escape(band)}</span>'
            f'<span class="fee-dollars">{escape(dollars)}</span></div>'
        )
    return escape(band)


def fit_criteria_html(fit: str) -> str:
    if not fit:
        return ""
    items = [ln.strip() for ln in fit.splitlines() if re.match(r"^\d+\.", ln.strip())]
    if not items:
        items = re.findall(r"\d+\.\s*([^0-9]+?)(?=\s*\d+\.|$)", fit)
        items = [i.strip(" ·;") for i in items if i.strip()]
    if not items:
        return f'<div class="fit-block"><strong>Fit criteria</strong><p class="fit">{escape(fit)}</p></div>'
    lis = []
    for item in items:
        text = re.sub(r"^\d+\.\s*", "", item).strip()
        if text:
            lis.append(f"<li>{escape(text)}</li>")
    return f'<div class="fit-block"><strong>Fit criteria</strong><ol class="fit-list">{"".join(lis)}</ol></div>'


def score_num(text: str) -> int | None:
    m = re.search(r"(\d+)", text or "")
    return int(m.group(1)) if m else None


def _roi_mini(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<span class="rm-sub">{sub}</span>' if sub else ""
    return (
        f'<div class="roi-mini"><span class="rm-lbl">{escape(label)}</span>'
        f'<div class="rm-val">{value}</div>{sub_html}</div>'
    )


def roi_explain_html(creative: str, risk: str, roi: str, fee: str, fit: str, card: dict | None = None) -> str:
    """Fee-efficiency tile only — Creative / Risk live in Score snapshot (no duplicate)."""
    if card:
        delta = card["roi_delta_usd"]
        sign = "+" if delta >= 0 else "−"
        uplift = card["roi_uplift_pct"]
        uplift_sign = "+" if uplift >= 0 else ""
        cost_100 = card.get("cost_100", 0)
        value_100 = card.get("value_100", 0)
        fee_q = fee_quantified(fee)
        minis = "".join(
            [
                _roi_mini("ROI score", f"{card['roi']}<span class='sc-score-den'>/100</span>", "Higher is better"),
                _roi_mini("Fee midpoint", escape(money(card["fee_mid"])), escape(fee_q or "Band midpoint")),
                _roi_mini(
                    "Fee delta",
                    f"{sign}{escape(money(abs(delta)))}",
                    f"{uplift_sign}{uplift}% vs midpoint",
                ),
                _roi_mini(
                    "Cost efficiency",
                    f"{cost_100}<span class='sc-score-den'>/100</span>",
                    "Higher = cheaper / easier",
                ),
                _roi_mini(
                    "Value index",
                    f"{value_100}<span class='sc-score-den'>/100</span>",
                    "Higher = more packaging value",
                ),
                _roi_mini(
                    "Spread",
                    f"{value_100 - cost_100:+d}",
                    "Value − cost (normalized pts)",
                ),
            ]
        )
        note = (
            "ROI is packaging efficiency at the fee-band midpoint "
            "(rubric: Value − Cost + 35 → 0–100). "
            "Bands: Low &lt;$100K · Med $100–500K · High $500K–$1M · Extremely High &gt;$1M."
        )
        return f"""
<div class="info-tile span-2 roi-box" data-reveal>
  <h3>ROI · fee efficiency</h3>
  <div class="roi-mini-grid">{minis}</div>
  <p class="roi-note">{note}</p>
</div>
"""
    # fallback legacy
    fee_q = fee_quantified(fee)
    return f"""
<div class="info-tile span-2 roi-box" data-reveal>
  <h3>ROI · fee efficiency</h3>
  <div class="roi-mini-grid">
    {_roi_mini("ROI", escape(roi or "—"))}
    {_roi_mini("Fee", escape(fee_q))}
  </div>
</div>
"""

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


def load_gallery() -> dict:
    """Prefer locally mirrored stills; fall back to cleaned remote URLs."""
    local: dict = {}
    if GALLERY_LOCAL_PATH.exists():
        local = json.loads(GALLERY_LOCAL_PATH.read_text(encoding="utf-8"))
    remote: dict = {}
    if GALLERY_PATH.exists():
        remote = json.loads(GALLERY_PATH.read_text(encoding="utf-8"))
    merged: dict[str, list[str]] = {}
    for name in set(local) | set(remote):
        locs = [u for u in (local.get(name) or []) if u]
        if locs:
            merged[name] = locs
            continue
        cleaned: list[str] = []
        for u in remote.get(name) or []:
            u = (u or "").split("?")[0]
            if not u or "svg" in u.lower():
                continue
            # Wikimedia rejects arbitrary px sizes (e.g. 800); 500px is allowed
            if "upload.wikimedia.org" in u and "/thumb/" in u:
                u = re.sub(r"/\d+px-", "/500px-", u)
            if u not in cleaned:
                cleaned.append(u)
        merged[name] = cleaned
    return merged


def extract_scorecards(md: str) -> list[dict]:
    cards = []
    for m in re.finditer(
        r"^### (.+?) \| Creative: (.+?) \| Risk: (.+?) \| ROI: (.+?) → \*\*(.+?)\*\*\s*(?:\n\n([\s\S]*?))?(?=\n### |\n## |\Z)",
        md,
        flags=re.M,
    ):
        body = (m.group(6) or "").strip()
        attrs = []
        # Prefer full rubric table: Category | Weight | **Score** | ...
        for am in re.finditer(
            r"^\| ([^|]+?) \|[^|]*\| \*\*(\d+)\*\* \|",
            body,
            flags=re.M,
        ):
            label = am.group(1).strip().lstrip("0123456789. ").strip()
            if label.lower() in {"category", "total weighted score", "**total weighted score**"}:
                continue
            if "total" in label.lower():
                continue
            short = (
                label.replace("Character Alignment", "Alignment")
                .replace("On-Screen Presence", "Presence")
                .replace("Chemistry Potential", "Chemistry")
                .replace("Commercial Viability", "Commercial")
                .replace("Strategic Value", "Strategic")
                .replace("Artistic Contribution", "Artistic")
                .replace("Availability & Cost Fit", "Cost Fit")
            )
            attrs.append((short, am.group(2)))
        if not attrs:
            # Legacy two-column: Category | **Score**
            for am in re.finditer(r"^\| ([^|]+?) \| \*\*(\d+)\*\* \|", body, flags=re.M):
                label = am.group(1).strip()
                if label.lower() == "category":
                    continue
                short = (
                    label.replace("Character Alignment", "Alignment")
                    .replace("On-Screen Presence", "Presence")
                    .replace("Chemistry Potential", "Chemistry")
                    .replace("Commercial Viability", "Commercial")
                    .replace("Strategic Value", "Strategic")
                    .replace("Artistic Contribution", "Artistic")
                    .replace("Availability & Cost Fit", "Cost Fit")
                )
                attrs.append((short, am.group(2)))
        if not attrs:
            for am in re.finditer(r"([A-Za-z][A-Za-z /&]+?)\s+(\d+)(?:/10)?", body):
                label = am.group(1).strip(" ·")
                if label.lower() in {"creative", "risk", "roi", "category", "score"}:
                    continue
                if len(label) < 28:
                    attrs.append((label, am.group(2)))
        # note = non-table lines
        note_lines = []
        for line in body.splitlines():
            if line.startswith("|"):
                continue
            if line.strip():
                note_lines.append(line.strip())
        note = " ".join(note_lines)
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


def synthesize_attrs(row: dict) -> list[tuple[str, str]]:
    fit = int(row["Fit"]) if str(row.get("Fit", "")).isdigit() else 7
    fee = (row.get("Fee band") or "").lower()
    cost = 9 if "low" in fee and "high" not in fee else 7 if "med" in fee and "extremely" not in fee else 4 if "extremely" in fee else 5
    commercial = 9 if "extremely" in fee or "high" in fee else 6
    return [
        ("Alignment", str(fit)),
        ("Presence", str(min(10, fit))),
        ("Chemistry", str(max(1, fit - 1))),
        ("Commercial", str(commercial)),
        ("Strategic", str(max(1, fit - 1))),
        ("Artistic", str(fit)),
        ("Cost Fit", str(cost)),
    ]


def avatar_html(src: str | None, cls: str = "", alt: str = "") -> str:
    if src:
        return (
            f'<span class="avatar-wrap"><img class="avatar {cls}" src="{escape(src)}" alt="{escape(alt)}" loading="lazy" /></span>'
        )
    return f'<span class="avatar-wrap"><span class="avatar {cls}" aria-hidden="true"></span></span>'


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
            f'<a class="icon-link {key}" href="{escape(url)}" target="_blank" rel="noopener" '
            f'title="{escape(label)}" onclick="event.stopPropagation()">'
            f'{ICONS[key]}<span class="lbl">{escape(label)}</span></a>'
        )
    return f'<div class="icon-row">{"".join(links)}</div>' if links else ""


def carousel_html(name: str, main_src: str | None, gallery: dict, depth: int = 0) -> str:
    """Unique actor-only stills. Never pad with role portraits or duplicate cycles."""
    prefix = "../" * depth
    urls: list[str] = []
    for u in gallery.get(name) or []:
        if not u:
            continue
        src = u
        if src.startswith("assets/"):
            src = f"{prefix}{src}"
        if src not in urls and "svg" not in src.lower():
            urls.append(src)
    board = [u for u in urls if u != main_src]
    if not board and main_src:
        board = [main_src]
    board = board[:25]
    if not board:
        return f"""
<div class="gallery-block" data-reveal>
  <p class="eyebrow">Image board</p>
  <p class="carousel-empty">No verified stills for {escape(name)} yet — headshot only above.</p>
</div>
"""
    figs = [
        f'<figure class="avatar-wrap"><img src="{escape(u)}" alt="{escape(name)}" loading="lazy" /></figure>'
        for u in board
    ]
    plural = "s" if len(board) != 1 else ""
    return f"""
<div class="gallery-block" data-reveal>
  <p class="eyebrow">Image board · {len(board)} still{plural}</p>
  <div class="carousel">{''.join(figs)}</div>
</div>
"""


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


_MONTH_LOOKUP = {
    **{name: i for i, name in enumerate(calendar.month_name) if name},
    **{name: i for i, name in enumerate(calendar.month_abbr) if name},
}
_MONTH_LOOKUP.update({k.lower(): v for k, v in list(_MONTH_LOOKUP.items())})

_BORN_RE = re.compile(
    r"born\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",
    re.I,
)


def parse_birthdate(bio: str) -> date | None:
    m = _BORN_RE.search(bio or "")
    if not m:
        return None
    day = int(m.group(1))
    month = _MONTH_LOOKUP.get(m.group(2)) or _MONTH_LOOKUP.get(m.group(2).lower())
    year = int(m.group(3))
    if not month:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def age_years(born: date, today: date | None = None) -> int:
    today = today or date.today()
    years = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        years -= 1
    return years


def bio_bullet_items(bio: str) -> list[str]:
    """Turn a Wikipedia lead into short bullets, including current age."""
    if not (bio or "").strip():
        return []
    items: list[str] = []
    born = parse_birthdate(bio)
    if born:
        born_label = f"{born.day} {born.strftime('%B')} {born.year}"
        items.append(f"Age {age_years(born)} (born {born_label})")

    first = re.split(r"(?<=\.)\s+", bio.strip(), maxsplit=1)[0]
    # Drop parenthetical born clause before extracting profession line
    cleaned = re.sub(r"\s*\([^)]*born[^)]*\)\s*", " ", first, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    m = re.search(r"\bis an?\s+(.+?)\.?$", cleaned, re.I)
    if m:
        desc = m.group(1).strip().rstrip(".")
        # Keep the profession line short on tiles
        desc = re.split(r"[,;]", desc, maxsplit=1)[0].strip()
        if desc:
            items.append(desc[0].upper() + desc[1:] if desc[0].islower() else desc)
    elif not items:
        short = shorten_bio(bio)
        if short:
            items.append(short)

    return items[:3]


def bio_bullets_html(bio: str) -> str:
    items = bio_bullet_items(bio)
    if not items:
        return ""
    lis = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f'<ul class="slist-bio-list">{lis}</ul>'


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
    # Fit descending (ties keep original relative order via original #)
    def fit_key(r: dict) -> tuple:
        f = r.get("Fit", "")
        fit_n = int(f) if str(f).isdigit() else -1
        orig = int(r["#"]) if str(r.get("#", "")).isdigit() else 999
        return (-fit_n, orig)

    rows = sorted(rows, key=fit_key)
    tiles = []
    for i, row in enumerate(rows, 1):
        name = re.sub(r"\*+", "", row.get("Actor", "")).strip()
        if not name or name.startswith("CD Match"):
            href = ""
        else:
            href = actor_slug_path(role["slug"], name)
        fit = row.get("Fit", "")
        fee = row.get("Fee band", "")
        flags = expand_flags(row.get("Flags", ""))
        notes = expand_notes(row.get("Notes", ""))
        bio_html = bio_bullets_html((registry.get(name) or {}).get("bio") or "")
        hs = headshot_src(name, registry)
        avatar = avatar_html(hs, "sm", name)
        icons = icon_links(name, registry, enrich)
        clickable = f' data-href="{escape(href)}" tabindex="0" role="link"' if href else ""
        notes_html = (
            f'<div class="slist-metric span-2"><span class="lbl">Notes</span>'
            f'<p class="slist-notes">{escape(notes)}</p></div>'
            if notes
            else ""
        )
        flags_html = (
            f'<div class="slist-metric span-2"><span class="lbl">Flags</span>'
            f'<p class="slist-notes">{escape(flags)}</p></div>'
            if flags
            else ""
        )
        tiles.append(
            f"""<article class="slist-tile"{clickable} data-reveal>
  <div class="slist-top">
    <span class="slist-rank">{str(i).zfill(2)}</span>
    <span class="tier tier-{code.lower()}">{escape(code)}</span>
  </div>
  <div class="slist-head">
    {avatar}
    <div class="text">
      <h3 class="slist-name">{escape(name)}</h3>
      {bio_html}
    </div>
  </div>
  <div class="slist-metrics">
    <div class="slist-metric">
      <span class="lbl">Fit</span>
      <div class="val fit-n">{escape(fit) or "—"}</div>
    </div>
    <div class="slist-metric">
      <span class="lbl">Fee</span>
      <div class="val">{fee_cell_html(fee)}</div>
    </div>
    {flags_html}
    {notes_html}
  </div>
  {icons}
</article>"""
        )

    return f"""
<section class="shortlist" data-reveal>
  <header class="section-head">
    <p class="eyebrow">Shortlist · Tier {escape(code)}</p>
    <h2>{escape(title)}</h2>
    <p class="lede">Ordered by Fit descending. Click any tile for the actor-in-role shred page.</p>
  </header>
  <div class="slist-grid">
    {"".join(tiles)}
  </div>
</section>
"""


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
  {avatar_html('assets/' + meta['portrait'], 'lg', meta['title'] + ' concept portrait')}
</header>
<section class="profile" data-reveal>
  <dl>{''.join(dl)}</dl>
  {fit_criteria_html(fit)}
</section>
<div id="shortlists">
{''.join(render_shortlist_section(meta, t, c, rows, registry, enrich) for t, c, rows in shortlists)}
</div>
"""
    if cards:
        # Map actor -> shortlist row for justification context
        short_by_name: dict[str, dict] = {}
        for _t, _c, rows in shortlists:
            for r in rows:
                an = re.sub(r"\*+", "", r.get("Actor", "")).strip()
                if an:
                    short_by_name[an] = r
        card_html = []
        for c in cards:
            href = actor_slug_path(meta["slug"], c["name"])
            hs = headshot_src(c["name"], registry)
            avatar = avatar_html(hs, "", c["name"])
            # Build compact Section 1 preview rows from attrs
            preview_rows = []
            score_map = {}
            for label, val in (c.get("attrs") or []):
                full = SHORT_TO_FULL.get(label.lower().strip(), label.strip())
                n = sc_score_num(val)
                if n is not None:
                    score_map[full] = n
            row_ctx = short_by_name.get(c["name"]) or {}
            for name_cat, weight, prompt in SECTION1:
                score = score_map.get(name_cat, "—")
                if str(score).isdigit():
                    wscore = sc_weighted(int(score), weight)
                    row_meta = f"Weight {weight} · Weighted {wscore:g}"
                    why = justify_section1(name_cat, int(score), row_ctx, prompt=prompt)
                else:
                    row_meta = f"Weight {weight}"
                    why = ""
                preview_rows.append(sc_row(name_cat, prompt, score, meta=row_meta, why=why))
            m = re.search(r"(\d+)", c.get("creative") or "")
            creative_preview = int(m.group(1)) if m else None
            badge = (
                f"<span class='sc-badge-n'>{creative_preview}</span><span class='sc-badge-den'>/100</span>"
                if creative_preview is not None
                else ""
            )
            foot_val = (
                f"<strong>{creative_preview}</strong><span class='sc-foot-den'>/100</span>"
                if creative_preview is not None
                else "<strong>—</strong>"
            )
            preview = f"""
<div class="sc-preview">
  {sc_panel(
      "Section 1 · Creative + Commercial Fit",
      "Open actor shred for Sections 2–3 (Risk + ROI) and full fee $/%.",
      "".join(preview_rows),
      "Total Weighted Score",
      foot_val,
      badge=badge,
  )}
</div>
"""
            card_html.append(
                f"""<a class="card" href="{escape(href)}" data-reveal style="grid-template-columns:auto 1fr">
  {avatar}
  <div>
    <h3>{escape(c['name'])}</h3>
    <div class="scores">Creative {escape(c['creative'])} · Risk {escape(c['risk'])} · ROI {escape(c['roi'])} · {escape(c['verdict'])}</div>
    {preview}
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
    <p class="lede">Full SLS Casting Scorecard Rubric V1 — Section 1 preview here; open each actor for Risk + ROI tables.</p>
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


def render_actor_page(name: str, payload: dict, enrich_one: dict, registry: dict, gallery: dict) -> str:
    role = payload["role"]
    row = payload["row"]
    sc = payload["scorecard"]
    profile = payload["profile"]
    hs = headshot_src(name, registry, prefix="../assets/")
    avatar = avatar_html(hs, "main", name)
    bio = (registry.get(name) or {}).get("bio") or ""

    existing = None
    attrs = None
    note = expand_notes(row.get("Notes", "") or "")
    if sc:
        existing = {
            "creative": sc.get("creative"),
            "risk": sc.get("risk"),
            "roi": sc.get("roi"),
            "verdict": sc.get("verdict"),
            "note": sc.get("note"),
        }
        attrs = sc.get("attrs")
        note = expand_notes(sc.get("note") or note)

    card = build_full_scorecard(row, attrs=attrs, note=note, existing=existing)
    sc_html = full_scorecard_html(card)
    # Compact ROI box in the header kv (full tables below already include ROI $/%)
    fee_raw = row.get("Fee band", "")
    roi_box = roi_explain_html(
        f"{card['creative']}/100",
        f"{card['risk_norm']}/100 ({card['risk_level']})",
        f"{card['roi']}/100",
        fee_raw,
        row.get("Fit", ""),
        card=card,
    )

    car = carousel_html(name, hs, gallery, depth=1)

    links = icon_links(name, registry, {name: enrich_one}, prefix="../")
    lane_note = card.get("note") or note or expand_notes(row.get("Notes", "") or "")
    casting_tile = info_tile(
        "Casting lane",
        [
            ("Role", escape(role["title"])),
            ("Tier", escape(payload["tier_title"])),
            ("Fit", escape(row.get("Fit", ""))),
            ("Fee band", escape(fee_quantified(fee_raw))),
            ("Leverage", escape(row.get("Leverage", ""))),
            ("Flags", escape(expand_flags(row.get("Flags", "")))),
            ("Avail risk", escape(row.get("Avail risk", ""))),
        ],
    )
    score_tile = info_tile(
        "Score snapshot",
        [
            ("Creative", f"{card['creative']}/100"),
            (
                "Risk clearance",
                f"{card.get('risk_clearance', 100 - card['risk_norm'])}/100 "
                f"({escape(card['risk_level'])} residual)",
            ),
            ("ROI", f"{card['roi']}/100"),
        ],
    )
    lock_tile = info_tile(
        "Role lock",
        [
            ("Role age", escape(profile.get("Age", ""))),
            ("Look lock", escape(profile.get("Ethnicity / look", ""))),
            ("Emotional core", escape(profile.get("Emotional core", ""))),
        ],
    )
    why_tile = info_tile(
        "Why this lane",
        [],
        extra=f'<p class="info-prose">{escape(lane_note or "—")}</p>',
    )
    bio_tile = info_tile(
        "Bio",
        [],
        extra=bio_bullets_html(bio) or '<p class="info-prose">Profile pending.</p>',
    )
    profiles_tile = (
        info_tile("Profiles", [], extra=links) if links else ""
    )

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
</header>
<section class="detail-layout" data-reveal>
  <div>
    {avatar}
  </div>
  <div class="info-tiles">
    {casting_tile}
    {score_tile}
    {lock_tile}
    {why_tile}
    {bio_tile}
    {profiles_tile}
    {roi_box}
  </div>
</section>
{car}
{reel_block(enrich_one)}
<section data-reveal>
  {sc_html}
</section>
"""
    return shell(f"{name} · {role['title']}", role["slug"], body, depth=1)


def _brief_for_package(name: str) -> dict:
    key = re.sub(r"\*+", "", name or "").strip()
    if key in PACKAGE_BRIEFS:
        return PACKAGE_BRIEFS[key]
    # Allow "B1 (primary)" vs "B1"
    short = key.split()[0] if key else ""
    return PACKAGE_BRIEFS.get(short) or PACKAGE_BRIEFS.get(key.replace(" (primary)", "")) or {}


def _ul(items: list[str]) -> str:
    if not items:
        return "<p class=\"pkg-why\">—</p>"
    return "<ul>" + "".join(f"<li>{escape(x)}</li>" for x in items) + "</ul>"


def render_package_card(p: dict) -> str:
    brief = _brief_for_package(p["name"])
    cls = "pkg primary" if p["primary"] else "pkg"
    verdict = brief.get("verdict") or ("Primary package" if p["primary"] else "Scenario package")
    why = brief.get("why") or "Briefing pending — see Ensemble shred."
    norman = re.sub(r"\*+$", "", p["norman"]).strip()
    analysis = f"""
    <div class="pkg-analysis">
      <h4>Why this package</h4>
      <p class="pkg-why">{escape(why)}</p>
      <div class="pkg-gbu">
        <div class="gbu-good"><h5>The good</h5>{_ul(brief.get("good") or [])}</div>
        <div class="gbu-bad"><h5>The bad</h5>{_ul(brief.get("bad") or [])}</div>
        <div class="gbu-ugly"><h5>The ugly</h5>{_ul(brief.get("ugly") or [])}</div>
      </div>
      <div class="pkg-caveats">
        <h4>Caveats</h4>
        {_ul(brief.get("caveats") or [])}
      </div>
    </div>"""
    return f"""<article class="{cls}" data-reveal>
  <div class="pkg-head">
    <h3>{escape(p['name'])}</h3>
    <p class="pkg-verdict">{escape(verdict)}</p>
    <div class="metrics">{escape(p['scenario'])} · <strong>{escape(p['pos'])}% PoS</strong> · ROI {escape(p['roi'])} · Auth {escape(p['auth'])}</div>
  </div>
  <div class="pkg-body">
    <div class="pkg-cast">
      <h4>Cast</h4>
      <ul>
        <li>Sheila — {escape(p['sheila'])}</li>
        <li>James — {escape(p['james'])}</li>
        <li>Samantha — {escape(p['samantha'])}</li>
        <li>Melina — {escape(p['melina'])}</li>
        <li>Norman — {escape(norman)}</li>
      </ul>
    </div>
    {analysis}
  </div>
</article>"""


def render_ensemble(registry: dict) -> str:
    meta = ENSEMBLE
    md = (DOCSWAMP / meta["file"]).read_text(encoding="utf-8")
    packages = extract_packages(md)
    # Scenario order: keep shred order; group headers inside the grid via eyebrows
    pkg_html: list[str] = []
    last_scenario = None
    for p in packages:
        if p["scenario"] != last_scenario:
            last_scenario = p["scenario"]
            pkg_html.append(
                f'<header class="section-head" data-reveal style="margin:28px 0 8px">'
                f'<p class="eyebrow">Scenario</p>'
                f'<h2 style="font-size:1.8rem">{escape(last_scenario)}</h2>'
                f"</header>"
            )
        pkg_html.append(render_package_card(p))

    body = f"""
<header class="hero" data-reveal>
  <div class="hero-copy">
    <p class="eyebrow">{escape(meta['tag'])}</p>
    <h1>{escape(meta['hero'])}</h1>
    <p>{escape(meta['lede'])}</p>
    <div class="cta">
      <a class="btn" href="#packages">Packages</a>
      <a class="btn ghost" href="#why-b1">Why B1</a>
      <a class="btn ghost" href="index.html">Overview</a>
    </div>
  </div>
  <span class="avatar-wrap"><span class="avatar lg" style="display:grid;place-items:center;font-family:'Bebas Neue',sans-serif;font-size:2rem;letter-spacing:.06em">B1</span></span>
</header>
<section id="packages" data-reveal>
  <header class="section-head">
    <p class="eyebrow">Scenario grid</p>
    <h2>Recommended packages</h2>
    <p class="lede">Primary Balanced package B1 is marked with a heavier rule. Each card carries the why, the caveats, and the good / bad / ugly.</p>
  </header>
  <div class="pkg-grid">{''.join(pkg_html)}</div>
</section>
<section class="ens-stack" id="why-b1" data-reveal>
  <div class="ens-block">
    <h3>Investor narrative</h3>
    <p>WAR packages as a contained, concept-led marriage horror with Invisible Man–style upside: Sheila as an emotionally microscopic lead (Kirby / Foy / Negga band per sales feedback), James as an ambiguity engine (Abbott / O’Connor craft or Redmayne prestige), Melina as look-locked soft temptation, Samantha as the rational sister who almost explains it away, and Norman as the detective who cannot close the file. Attach LOIs in that order to convert existing investor interest into talent gravity — without forcing a dual Extremely High fee stack that would erase the low–mid budget advantage the deck sells.</p>
  </div>
  <div class="ens-two">
    <div class="ens-block">
      <h3>Chemistry matrix · B1</h3>
      <table class="chem-table">
        <thead><tr><th>Pair</th><th>Score</th><th>Note</th></tr></thead>
        <tbody>
          <tr><td>Kirby ↔ Abbott</td><td>9</td><td>Prestige restraint vs indie uncanny — marriage dread grammar</td></tr>
          <tr><td>Abbott ↔ Onieogou</td><td>8</td><td>Soft workplace gravity; chemistry read required</td></tr>
          <tr><td>Kirby ↔ Wilson</td><td>8</td><td>Sister foil: crown-steel vs clinical certainty</td></tr>
          <tr><td>Kirby ↔ Asomugha</td><td>8</td><td>Interrogation stillness; inconclusive file stays honest</td></tr>
          <tr><td>Foy ↔ O’Connor</td><td>9</td><td>B2 parallel prestige pair if Kirby declines</td></tr>
          <tr><td>Negga ↔ Redmayne</td><td>8</td><td>B3 awards-forward alternate</td></tr>
        </tbody>
      </table>
      <p style="margin-top:12px">Must-pair gate: B1 pairs ≥ 8 (met).</p>
    </div>
    <div class="ens-block">
      <h3>Aggregate risk</h3>
      <table class="risk-table">
        <thead><tr><th>Cluster</th><th>Reading</th><th>Mitigation</th></tr></thead>
        <tbody>
          <tr><td>Fee inflation</td><td>Moderate–High on A1</td><td>Prefer A3 / B1; backend for feelers</td></tr>
          <tr><td>Schedule / franchise</td><td>Moderate on Pugh / Comer / Isaac</td><td>Parallel LOI waves</td></tr>
          <tr><td>Tone clash</td><td>Low on B1</td><td>Keep James off comic-charm casting</td></tr>
          <tr><td>Solver Norman</td><td>Low if Asomugha / Hornsby</td><td>No crusading star who demands closure</td></tr>
          <tr><td>Spector gap</td><td>Moderate</td><td>Keep A-list feelers alive while closing B anchors</td></tr>
        </tbody>
      </table>
      <p style="margin-top:12px">Package Risk (B1): Low–Moderate.</p>
    </div>
  </div>
  <div class="ens-two">
    <div class="ens-block">
      <h3>LOI outreach order</h3>
      <ol class="loi-list">
        <li>Vanessa Kirby — Sheila</li>
        <li>Claire Foy — Sheila parallel</li>
        <li>Christopher Abbott — James</li>
        <li>Eddie Redmayne — James financing alt</li>
        <li>Nnamdi Asomugha — Norman (writer lock)</li>
        <li>Ruth Wilson — Samantha</li>
        <li>Greta Onieogou — Melina</li>
        <li>Feelers: Comer, O’Connor, Thompson, Pugh</li>
      </ol>
    </div>
    <div class="ens-block">
      <h3>Decline swaps</h3>
      <table class="risk-table">
        <thead><tr><th>If declines</th><th>Swap to</th></tr></thead>
        <tbody>
          <tr><td>Kirby</td><td>Foy → Negga → Comer → Reinsve</td></tr>
          <tr><td>Abbott</td><td>O’Connor → Redmayne → Rhodes</td></tr>
          <tr><td>Asomugha</td><td>Hornsby → Holland → Morgan</td></tr>
          <tr><td>Wilson</td><td>Coon → Condon</td></tr>
          <tr><td>Onieogou</td><td>Beetz → Clemons → Myha’la</td></tr>
        </tbody>
      </table>
    </div>
  </div>
  <div class="ens-block">
    <h3>Composite line</h3>
    <p>WAR Ensemble · Package PoS peak 84% (A1) / recommended 83% (B1) · Best median ROI 3.6x (B4) / recommended 3.5x (B1) · Package Risk Low–Moderate → RECOMMEND PACKAGE (P1 Balanced / B1).</p>
  </div>
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
  {avatar_html('assets/' + c['portrait'], 'tile', c['title'])}
</a>"""
        )
    cards.append(
        f"""<a class="home-card" href="ensemble.html" data-reveal>
  <div>
    <span class="n">06</span>
    <h2>ENSEMBLE</h2>
    <p>Package architecture</p>
  </div>
  <span class="avatar-wrap"><span class="avatar tile" style="display:grid;place-items:center;font-family:'Bebas Neue',sans-serif;font-size:1.4rem">B1</span></span>
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
  {avatar_html('assets/characters/char-sheila.png', 'lg', 'Sheila concept portrait')}
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
    gallery = load_gallery()
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
        path.write_text(render_actor_page(name, payload, en, registry, gallery), encoding="utf-8")
        written += 1

    print(f"wrote site to {OUT} with {written} actor detail pages; gallery keys={len(gallery)}")


if __name__ == "__main__":
    main()
