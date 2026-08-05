# -*- coding: utf-8 -*-
"""Expand priority scorecards in WAR character shreds with full Rubric V1 Section 1 tables."""
from __future__ import annotations

import re
from pathlib import Path

DOCSWAMP = Path(__file__).resolve().parents[1]

SECTION1 = [
    ("Character Alignment", 22, "Does the actor align with physical, emotional, tonal, and regional traits?"),
    ("On-Screen Presence", 17, "Charisma, magnetism, and visual command on screen"),
    ("Chemistry Potential", 11, "Fit with romantic lead or ensemble? Prior co-star rapport?"),
    ("Commercial Viability", 22, "Fanbase, genre appeal, box office/streaming record"),
    ("Strategic Value", 11, "Awards potential, PR value, funding leverage"),
    ("Artistic Contribution", 11, "Will they elevate the role through interpretation or improvisation?"),
    ("Availability & Cost Fit", 6, "Affordability, scheduling fit, and representation access"),
]

# Curated 0–10 scores: Alignment, Presence, Chemistry, Commercial, Strategic, Artistic, Cost Fit
SCORES: dict[str, dict[str, tuple[int, int, int, int, int, int, int]]] = {
    "Sheila": {
        "Vanessa Kirby": (9, 9, 8, 9, 9, 8, 6),
        "Claire Foy": (9, 8, 8, 9, 9, 8, 6),
        "Ruth Negga": (10, 8, 8, 7, 8, 9, 8),
        "Renate Reinsve": (9, 8, 8, 6, 6, 10, 7),
        "Florence Pugh": (9, 10, 8, 10, 9, 9, 4),
        "Jodie Comer": (9, 9, 8, 8, 8, 9, 5),
        "Nicole Beharie": (8, 7, 8, 5, 5, 8, 9),
    },
    "James": {
        "Eddie Redmayne": (8, 8, 8, 8, 8, 8, 5),
        "Christopher Abbott": (9, 9, 9, 7, 7, 9, 7),
        "Josh O'Connor": (9, 8, 9, 7, 7, 9, 7),
        "Oscar Isaac": (9, 10, 8, 9, 9, 9, 4),
        "Jake Gyllenhaal": (8, 10, 8, 10, 9, 8, 3),
        "Trevante Rhodes": (8, 8, 8, 6, 6, 8, 8),
        "Aldis Hodge": (8, 8, 7, 6, 6, 7, 9),
        "John David Washington": (8, 8, 7, 9, 8, 8, 5),
    },
    "Samantha": {
        "Ruth Wilson": (9, 9, 8, 8, 8, 9, 7),
        "Carrie Coon": (9, 8, 8, 7, 7, 9, 8),
        "Rebecca Ferguson": (8, 9, 7, 8, 8, 8, 5),
        "Sian Clifford": (8, 7, 8, 5, 5, 8, 9),
    },
    "Melina": {
        "Tessa Thompson": (9, 9, 9, 8, 8, 9, 6),
        "Greta Onieogou": (9, 8, 8, 5, 5, 8, 9),
        "Zazie Beetz": (8, 9, 8, 7, 7, 8, 7),
        "Myha'la": (8, 8, 8, 6, 6, 8, 8),
        "Zoe Kravitz": (8, 9, 8, 9, 8, 8, 4),
    },
    "Norman": {
        "Nnamdi Asomugha": (10, 9, 7, 5, 6, 8, 9),
        "Russell Hornsby": (9, 8, 7, 6, 6, 8, 8),
        "Mahershala Ali": (9, 10, 7, 10, 10, 10, 3),
        "André Holland": (9, 8, 7, 6, 6, 9, 8),
        "Rob Morgan": (8, 8, 6, 5, 5, 8, 9),
    },
}

FILES = {
    "Sheila": "SLS Casting Shred - WAR - Character - Sheila Collier - 2026-08-05.md",
    "James": "SLS Casting Shred - WAR - Character - James Collier - 2026-08-05.md",
    "Samantha": "SLS Casting Shred - WAR - Character - Samantha - 2026-08-05.md",
    "Melina": "SLS Casting Shred - WAR - Character - Melina - 2026-08-05.md",
    "Norman": "SLS Casting Shred - WAR - Character - Detective Norman - 2026-08-05.md",
}


def table_for(scores: tuple[int, ...]) -> str:
    rows = [
        "| Category | Weight | Score (0–10) | Weighted Score | Comments |",
        "| --- | --- | --- | --- | --- |",
    ]
    total = 0.0
    for (label, weight, prompt), val in zip(SECTION1, scores):
        w = round(val * weight / 10, 1)
        total += w
        rows.append(f"| {label} | {weight} | **{val}** | {w:g} | {prompt} |")
    rows.append(f"| **Total Weighted Score** |  |  | **{int(round(total))}/100** |  |")
    return "\n".join(rows)


def expand_file(role_key: str) -> None:
    path = DOCSWAMP / FILES[role_key]
    text = path.read_text(encoding="utf-8")
    score_map = SCORES[role_key]

    def repl(m: re.Match) -> str:
        name = m.group(1).strip()
        header = m.group(0).split("\n\n")[0]
        rest = m.group(2).strip() if m.group(2) else ""
        note_lines = []
        for line in rest.splitlines():
            if re.match(r"^Alignment\s+\d+", line):
                after = re.sub(r"^Alignment\s+\d+.*?Cost Fit\s+\d+\.?\s*", "", line).strip()
                if after:
                    note_lines.append(after)
                continue
            if line.startswith("|"):
                continue
            note_lines.append(line)
        note = "\n".join(note_lines).strip()
        scores = score_map.get(name)
        if not scores:
            return m.group(0)
        block = f"{header}\n\n{table_for(scores)}\n"
        if note:
            block += f"\n{note}\n"
        return block

    pattern = re.compile(
        r"^### (.+?) \| Creative: .+? → \*\*.+?\*\*\s*(?:\n\n([\s\S]*?))?(?=\n### |\n## |\Z)",
        re.M,
    )
    new_text, n = pattern.subn(repl, text)
    path.write_text(new_text, encoding="utf-8")
    print(f"{path.name}: expanded {n} scorecards")


def main() -> None:
    for key in FILES:
        expand_file(key)


if __name__ == "__main__":
    main()
