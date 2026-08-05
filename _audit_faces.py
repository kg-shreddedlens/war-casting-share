# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _build_site import CHARACTERS, DOCSWAMP, extract_shortlists, headshot_src, load_registry, slugify

reg = load_registry()
missing = []
ok = 0
names = set()
for c in CHARACTERS:
    md = (DOCSWAMP / c["file"]).read_text(encoding="utf-8")
    for _t, _code, rows in extract_shortlists(md):
        for row in rows:
            name = row.get("Actor", "").replace("*", "").strip()
            if not name or name.startswith("CD Match"):
                continue
            names.add(name)
for name in sorted(names):
    src = headshot_src(name, reg)
    if src:
        ok += 1
    else:
        missing.append(name)
print(f"shortlist actors={len(names)} with_face={ok} missing={len(missing)}")
for n in missing:
    print(" MISSING", n)
