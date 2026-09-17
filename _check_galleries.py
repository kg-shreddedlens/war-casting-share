# -*- coding: utf-8 -*-
import json
from pathlib import Path

root = Path(__file__).resolve().parent
d = json.loads((root / "gallery_local.json").read_text(encoding="utf-8"))
for name in ["Florence Pugh", "Jodie Comer", "Vanessa Kirby"]:
    paths = d.get(name) or []
    exist = 0
    missing = []
    for p in paths:
        if p.startswith("http"):
            exist += 1
            continue
        fp = root / "site" / p
        dp = root / "dist" / p
        if fp.exists() or dp.exists():
            exist += 1
        else:
            missing.append(p)
    print(f"{name}: json={len(paths)} on_disk={exist} missing={len(missing)}")
    if missing[:3]:
        print("  eg", missing[:3])
    slug = name.lower().replace(" ", "-").replace("'", "").replace("é", "e")
    for base in [root / "site" / "assets" / "galleries" / slug, root / "dist" / "assets" / "galleries" / slug]:
        if base.exists():
            print(f"  dir {base.name}: {len(list(base.glob('*')))} files")
