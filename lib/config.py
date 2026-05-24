"""Central configuration: disclosure text and optional API key loading."""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv not installed — env vars still work
    pass

APP_NAME = "Stock Market Analyst"
APP_TAGLINE = "Educational personal-research dashboard"

# Compliance: shown on every page. No buy/sell/hold language anywhere in the app.
DISCLOSURE = (
    "**Disclosure** — This tool is for educational and personal-research "
    "purposes only. It does not provide investment, financial, legal, or tax "
    "advice, and nothing here is a recommendation to buy, sell, or hold any "
    "security. Data may be delayed or inaccurate. Do your own research and "
    "consult a licensed professional before making any financial decision."
)


def get_key(name: str) -> str | None:
    """Return an API key from the environment, or None if unset/blank."""
    val = os.environ.get(name, "").strip()
    return val or None


def fred_key() -> str | None:
    return get_key("FRED_API_KEY")


def anthropic_key() -> str | None:
    return get_key("ANTHROPIC_API_KEY")
