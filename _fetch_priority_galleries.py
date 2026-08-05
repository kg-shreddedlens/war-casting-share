# -*- coding: utf-8 -*-
import json, time, urllib.request, urllib.parse, re
from pathlib import Path

UA = "SLSCastingBot/1.0"
SKIP = re.compile(r"(logo|icon|flag|signature|svg|commons-logo)", re.I)
OUT = Path(__file__).with_name("gallery_cache.json")
cache = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
priority = [
    "Florence Pugh", "Saoirse Ronan", "Jodie Comer", "Emma Stone", "Vanessa Kirby",
    "Claire Foy", "Ruth Negga", "Renate Reinsve", "Nicole Beharie", "Eddie Redmayne",
    "Christopher Abbott", "Josh O'Connor", "Oscar Isaac", "Jake Gyllenhaal",
    "Trevante Rhodes", "Aldis Hodge", "Ruth Wilson", "Carrie Coon", "Rebecca Ferguson",
    "Sian Clifford", "Tessa Thompson", "Greta Onieogou", "Zazie Beetz", "Myha'la",
    "Zoe Kravitz", "Nnamdi Asomugha", "Russell Hornsby", "Mahershala Ali",
    "André Holland", "Rob Morgan", "Morfydd Clark", "Georgina Campbell",
    "Keira Knightley", "Anya Taylor-Joy", "Jessie Buckley", "Winston Duke",
]


def rest_media(title: str) -> list[str]:
    slug = title.replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/media-list/{urllib.parse.quote(slug)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    urls = []
    for item in data.get("items") or []:
        if item.get("type") and item.get("type") != "image":
            continue
        if SKIP.search(item.get("title") or ""):
            continue
        src = item.get("src") or ""
        if not src and item.get("srcset"):
            src = sorted(item["srcset"], key=lambda x: x.get("scale", 1), reverse=True)[0].get("src") or ""
        if src.startswith("//"):
            src = "https:" + src
        src = re.sub(r"/\d+px-", "/800px-", src)
        if not src or SKIP.search(src) or ".svg" in src.lower():
            continue
        if src not in urls:
            urls.append(src)
        if len(urls) >= 10:
            break
    return urls


for i, name in enumerate(priority, 1):
    if len(cache.get(name) or []) >= 4:
        print("skip", name, len(cache[name]))
        continue
    try:
        urls = rest_media(name)
        if len(urls) < 3 and "é" in name:
            urls = rest_media(name.replace("é", "e")) or urls
        cache[name] = urls
        print(i, name, len(urls))
        OUT.write_text(json.dumps(cache, indent=2), encoding="utf-8")
        time.sleep(1.0)
    except Exception as e:
        print(i, name, "FAIL", e)
        time.sleep(2)
print("priority done", sum(1 for n in priority if len(cache.get(n) or []) >= 3))
