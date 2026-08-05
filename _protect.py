# -*- coding: utf-8 -*-
"""Password-protect the casting share site for GitHub Pages.

Uses:
1) Soft session gate (gate.html -> index) for UX
2) staticrypt encryption of HTML payloads so source is not readable without password

Share PASSWORD.txt out-of-band with customers. Do not commit it.
"""
from __future__ import annotations

import hashlib
import secrets
import shutil
import string
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DIST = ROOT / "dist"
PW_FILE = ROOT / "PASSWORD.txt"


def gen_password(n: int = 14) -> str:
    alphabet = string.ascii_letters + string.digits
    # avoid ambiguous chars
    alphabet = alphabet.replace("O", "").replace("0", "").replace("l", "").replace("1", "").replace("I", "")
    return "".join(secrets.choice(alphabet) for _ in range(n))


def restore_actors_dir(dist: Path) -> None:
    """Move flattened actor detail pages back into dist/actors/."""
    role_slugs = ("sheila", "james", "samantha", "melina", "norman")
    actors_dir = dist / "actors"
    actors_dir.mkdir(parents=True, exist_ok=True)
    moved = 0
    for path in list(dist.glob("*.html")):
        name = path.name
        if any(name.startswith(f"{slug}-") for slug in role_slugs):
            path.replace(actors_dir / name)
            moved += 1
    print(f"restored {moved} actor pages under actors/")


def patch_always_remember(dist: Path) -> None:
    """Force permanent remember-me on successful unlock (no checkbox required)."""
    old = (
        'const password = document.getElementById("staticrypt-password").value,\n'
        '                    isRememberChecked = document.getElementById("staticrypt-remember").checked;'
    )
    new = (
        'const password = document.getElementById("staticrypt-password").value,\n'
        "                    isRememberChecked = true; // always remember across pages on this device"
    )
    hide = (
        "if (isRememberEnabled) {\n"
        '                        document.getElementById("staticrypt-remember-label").classList.remove("hidden");\n'
        "                    }"
    )
    paths = list(dist.rglob("*.html"))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise SystemExit(f"remember patch target missing in {path}")
        text = text.replace(old, new)
        text = text.replace(hide, "/* remember-me always on; checkbox hidden */")
        path.write_text(text, encoding="utf-8")
    print(f"patched always-remember on {len(paths)} files")


def main() -> None:
    if not SITE.exists():
        raise SystemExit("Run _build_site.py first")

    if PW_FILE.exists():
        password = PW_FILE.read_text(encoding="utf-8").strip()
    else:
        password = gen_password()
        PW_FILE.write_text(password + "\n", encoding="utf-8")
        print(f"generated password -> {PW_FILE}")

    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()

    # Inject hash into soft gate (used if someone opens gate.html before staticrypt wrap)
    gate = SITE / "gate.html"
    text = gate.read_text(encoding="utf-8")
    text = text.replace('"__HASH_PLACEHOLDER__"', f'"{digest}"')
    gate.write_text(text, encoding="utf-8")

    # Auth helper: protect content pages; gate stays as entry after encrypt of whole set
    # staticrypt encrypts each HTML file into a password prompt page.
    DIST.mkdir(parents=True, exist_ok=True)

    html_files = sorted(SITE.rglob("*.html"))
    # Use paths relative to SITE so staticrypt preserves actors/ structure under DIST
    rel_files = [str(p.relative_to(SITE)) for p in html_files]
    cmd = [
        "npx",
        "--yes",
        "staticrypt@3",
        *rel_files,
        "-d",
        str(DIST),
        "-p",
        password,
        "--short",
        # 0 = remember with no expiration (localStorage unlocks every page forever)
        "--remember",
        "0",
        "--template-title",
        "SLS WAR Casting",
        "--template-instructions",
        "Enter the access password from your Shredded Lens contact. You will only need this once on this device.",
        "--template-button",
        "ENTER",
        "--template-color-primary",
        "#0a0a0a",
        "--template-color-secondary",
        "#fafafa",
        "--template-error",
        "Incorrect password.",
    ]
    print("running staticrypt on", len(html_files), "files...")
    r = subprocess.run(cmd, cwd=str(SITE), shell=True)
    if r.returncode != 0:
        raise SystemExit(r.returncode)

    # Always persist unlock — do not require the "Remember me" checkbox.
    patch_always_remember(DIST)

    # staticrypt flattens paths; restore actors/ so relative links work
    restore_actors_dir(DIST)

    # Copy static assets (portraits, headshots) beside encrypted HTML
    src_assets = SITE / "assets"
    if src_assets.exists():
        dst_assets = DIST / "assets"
        if dst_assets.exists():
            shutil.rmtree(dst_assets)
        shutil.copytree(src_assets, dst_assets)
        print(f"copied assets -> {dst_assets}")

    # Copy a note
    (DIST / "README.md").write_text(
        "# WAR Casting (password protected)\n\n"
        "Open `index.html` (or the Pages URL). Enter the shared access password.\n"
        "One unlock is remembered forever on that browser/device via localStorage.\n"
        "Content is AES-encrypted in the browser via staticrypt.\n",
        encoding="utf-8",
    )
    print(f"protected site -> {DIST}")
    print("PASSWORD (also in PASSWORD.txt):", password)


if __name__ == "__main__":
    main()
