# -*- coding: utf-8 -*-
"""Supplement galleries via DuckDuckGo image search (name-verified URLs)."""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def name_tokens(name: str) -> list[str]:
    return [p.lower() for p in re.findall(r"[A-Za-z]+", name) if len(p) > 1]


def url_ok(url: str, title: str, name: str) -> bool:
    blob = (url + " " + title).lower()
    if any(x in blob for x in ("svg", "logo", "sprite", "icon", "churchill", "marlborough")):
        return False
    if not re.search(r"\.(jpe?g|png|webp)(\?|$)", url, re.I):
        return False
    tokens = name_tokens(name)
    if len(tokens) < 2:
        return tokens[0] in blob if tokens else False
    return tokens[0] in blob and tokens[-1] in blob


def ddg_images(query: str, max_n: int = 40) -> list[tuple[str, str]]:
    # landing page for vqd
    land = "https://duckduckgo.com/?" + urllib.parse.urlencode({"q": query, "iax": "images", "ia": "images"})
    req = urllib.request.Request(land, headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    m = re.search(r"vqd=['\"]([^'\"]+)['\"]", html) or re.search(r"vqd=([\d-]+)", html)
    if not m:
        # alternate pattern
        m = re.search(r"vqd:\\\"([^\\\"]+)\\\"", html)
    if not m:
        print("no vqd", query)
        return []
    vqd = m.group(1)
    out: list[tuple[str, str]] = []
    next_url = "https://duckduckgo.com/i.js?" + urllib.parse.urlencode(
        {"l": "us-en", "o": "json", "q": query, "vqd": vqd, "f": ",,,", "p": "1"}
    )
    while next_url and len(out) < max_n:
        req = urllib.request.Request(
            next_url,
            headers={"User-Agent": UA, "Referer": "https://duckduckgo.com/", "Accept": "application/json"},
        )
        try:
            raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
            data = json.loads(raw)
        except Exception as e:
            print("ddg fail", e)
            break
        for r in data.get("results") or []:
            img = r.get("image") or ""
            title = r.get("title") or ""
            if img:
                out.append((img, title))
            if len(out) >= max_n:
                break
        nxt = data.get("next")
        if not nxt:
            break
        next_url = "https://duckduckgo.com/" + nxt if nxt.startswith("i.js") else None
        time.sleep(0.8)
    return out


if __name__ == "__main__":
    name = "Winston Duke"
    results = ddg_images(f"{name} actor", 50)
    print("raw", len(results))
    kept = [(u, t) for u, t in results if url_ok(u, t, name)]
    print("kept", len(kept))
    for u, t in kept[:30]:
        print(t[:50], "->", u[:120])
