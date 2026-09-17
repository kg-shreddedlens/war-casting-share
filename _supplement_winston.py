# -*- coding: utf-8 -*-
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "ShreddedLensCastingBot/1.2"
ROOT = Path(__file__).resolve().parent
folder = ROOT / "site" / "assets" / "galleries" / "winston-duke"
local_path = ROOT / "gallery_local.json"
local = json.loads(local_path.read_text(encoding="utf-8"))
kept = list(local.get("Winston Duke") or [])
print("have", len(kept))


def api(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())


queries = [
    "Mbaku Gage Skidmore",
    "Winston Duke TIFF",
    "Winston Duke premiere",
    "Winston Duke Comic-Con",
    "Winston Duke Us movie",
]
titles = []
for q in queries:
    data = api(
        "https://commons.wikimedia.org/w/api.php?"
        + urllib.parse.urlencode(
            {
                "action": "query",
                "list": "search",
                "srsearch": q,
                "srnamespace": 6,
                "srlimit": 20,
                "format": "json",
            }
        )
    )
    for h in data.get("query", {}).get("search", []):
        t = h["title"]
        tl = t.lower()
        if "winston" in tl and "duke" in tl and t not in titles:
            titles.append(t)
    time.sleep(1)
print("extra titles", titles)

seen = {Path(p).name.lower() for p in kept}
for p in folder.glob("*"):
    seen.add(p.name.lower())

urls = []
if titles:
    data = api(
        "https://commons.wikimedia.org/w/api.php?"
        + urllib.parse.urlencode(
            {
                "action": "query",
                "titles": "|".join(titles),
                "prop": "imageinfo",
                "iiprop": "url|mime",
                "iiurlwidth": 500,
                "format": "json",
            }
        )
    )
    for p in data.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        src = (ii.get("thumburl") or ii.get("url") or "").split("?")[0]
        if src:
            urls.append(src)

for tag in ["WinstonDuke", "Winston Duke"]:
    feed = "https://www.flickr.com/services/feeds/photos_public.gne?" + urllib.parse.urlencode(
        {"tags": tag, "format": "json", "nojsoncallback": 1}
    )
    try:
        req = urllib.request.Request(feed, headers={"User-Agent": UA})
        data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore"))
        for item in data.get("items") or []:
            media = item.get("media", {}).get("m", "")
            big = re.sub(r"_[mst]\.jpg", "_b.jpg", media)
            title = item.get("title", "")
            blob = (title + " " + big).lower()
            if "winston" in blob and "duke" in blob and big:
                urls.append(big)
                print("flickr", title[:50])
    except Exception as e:
        print("flickr fail", e)
    time.sleep(1)

print("candidate urls", len(urls))
for u in urls:
    if len(kept) >= 25:
        break
    key = Path(urllib.parse.urlparse(u).path).name.lower()
    if key in seen:
        continue
    seen.add(key)
    dest = folder / f"{len(kept):02d}.jpg"
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=40).read()
        if len(data) < 2500:
            continue
        dest.write_bytes(data)
        kept.append(f"assets/galleries/winston-duke/{dest.name}")
        print("ok", len(kept), dest.name)
        time.sleep(1.2)
    except Exception as e:
        print("fail", e)
        time.sleep(2)

# If still short: download alternate resolutions of existing commons originals as last resort? skip.
# Use Wikipedia page images from other language wikis via media-list
for wiki in ["en", "fr", "de", "es", "it"]:
    if len(kept) >= 25:
        break
    try:
        url = f"https://{wiki}.wikipedia.org/api/rest_v1/page/media-list/Winston_Duke"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        for item in data.get("items") or []:
            if len(kept) >= 25:
                break
            if item.get("type") and item.get("type") != "image":
                continue
            src = item.get("src") or ""
            if not src and item.get("srcset"):
                src = sorted(item["srcset"], key=lambda x: x.get("scale", 1), reverse=True)[0].get("src") or ""
            if src.startswith("//"):
                src = "https:" + src
            src = re.sub(r"/\d+px-", "/500px-", src.split("?")[0])
            title = (item.get("title") or "") + " " + src
            if "winston" not in title.lower() or "duke" not in title.lower():
                continue
            if "svg" in src.lower():
                continue
            key = Path(urllib.parse.urlparse(src).path).name.lower()
            if key in seen:
                continue
            seen.add(key)
            dest = folder / f"{len(kept):02d}.jpg"
            req = urllib.request.Request(src, headers={"User-Agent": UA})
            blob = urllib.request.urlopen(req, timeout=40).read()
            if len(blob) < 2500:
                continue
            dest.write_bytes(blob)
            kept.append(f"assets/galleries/winston-duke/{dest.name}")
            print("wiki", wiki, len(kept), dest.name)
            time.sleep(1.0)
    except Exception as e:
        print("wiki fail", wiki, e)
    time.sleep(0.8)

local["Winston Duke"] = kept
local_path.write_text(json.dumps(local, indent=2), encoding="utf-8")
print("FINAL", len(kept))
