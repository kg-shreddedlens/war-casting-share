from pathlib import Path
import re

t = Path("site/actors/sheila-florence-pugh.html").read_text(encoding="utf-8")
m = re.search(r"Image board · (\d+)", t)
print("board", m.group(0) if m else None)
print("still-grid", "still-grid" in t)
print("score_before_gallery", t.find('id="scorecard"') < t.find("Image board"))
print("why-lane", "why-lane" in t)
print("Cost efficiency", "Cost efficiency" in t)
print("max-width scorecard", "max-width:680px" in t)
