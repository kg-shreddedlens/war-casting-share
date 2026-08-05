# WAR Casting Share (GitHub Pages)

High-Contrast Editorial HTML casting shreds for WAR, AES-encrypted with [staticrypt](https://github.com/robinmoisson/staticrypt).

## Local rebuild

```bash
python _build_site.py
python _protect.py
```

Password is stored in `PASSWORD.txt` (gitignored). Share it out-of-band with customers.

## Deploy (after `gh` is on the shreddedlens account)

```bash
# from casting-share/
gh auth status   # confirm shreddedlens account is active
gh repo create war-casting-share --public --source=. --remote=origin --push
gh pages deploy dist --branch gh-pages
```

Site URL will be:
`https://<github-username>.github.io/war-casting-share/`

Customers open that URL and enter the access password.
