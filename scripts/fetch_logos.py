"""Download company logos into assets/logos/ from multiple fallback sources.

Run locally:  python scripts/fetch_logos.py
Missing logos simply fall back to ticker initials in the app, so this is
entirely optional.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.logos import LOGO_DIR, TICKER_DOMAINS  # noqa: E402


def sources(ticker: str, domain: str) -> list[str]:
    slug = domain.split(".")[0]
    return [
        f"https://logo.clearbit.com/{domain}",
        f"https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/{slug}.svg",
        f"https://www.google.com/s2/favicons?sz=128&domain={domain}",
    ]


def fetch_one(ticker: str, domain: str) -> bool:
    out = LOGO_DIR / f"{ticker}.png"
    if out.exists():
        return True
    for url in sources(ticker, domain):
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200 and r.content and len(r.content) > 200:
                out.write_bytes(r.content)
                print(f"  ✓ {ticker} <- {url}")
                return True
        except Exception:
            continue
    print(f"  ✗ {ticker} (no source succeeded — will use initials)")
    return False


def main() -> None:
    LOGO_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for ticker, domain in TICKER_DOMAINS.items():
        if fetch_one(ticker, domain):
            ok += 1
    print(f"\nDone: {ok}/{len(TICKER_DOMAINS)} logos available in {LOGO_DIR}")


if __name__ == "__main__":
    main()
