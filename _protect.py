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

    html_files = sorted(SITE.glob("*.html"))
    # Encrypt everything except we want a single entry: encrypt all content pages;
    # use staticrypt on all and set index as encrypted landing.
    cmd = [
        "npx",
        "--yes",
        "staticrypt@3",
        *[str(p) for p in html_files],
        "-d",
        str(DIST),
        "-p",
        password,
        "--short",
        "--remember",
        "7",
        "--template-title",
        "SLS WAR Casting",
        "--template-instructions",
        "Enter the access password from your Shredded Lens contact.",
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
    r = subprocess.run(cmd, cwd=str(ROOT), shell=True)
    if r.returncode != 0:
        raise SystemExit(r.returncode)

    # Copy a note
    (DIST / "README.md").write_text(
        "# WAR Casting (password protected)\n\n"
        "Open `index.html` (or the Pages URL). Enter the shared access password.\n"
        "Content is AES-encrypted in the browser via staticrypt.\n",
        encoding="utf-8",
    )
    print(f"protected site -> {DIST}")
    print("PASSWORD (also in PASSWORD.txt):", password)


if __name__ == "__main__":
    main()
