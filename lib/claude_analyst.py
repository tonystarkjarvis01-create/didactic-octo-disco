"""AI analyst with a no-API-key-required provider chain.

Resolution order:
  1. Local Ollama, if a server is reachable on localhost:11434.
  2. Anthropic API, if ANTHROPIC_API_KEY is set (optional).
  3. Built-in offline generator that writes a neutral analysis directly from
     the already-computed metrics. Always works — no key, no network.

All output is descriptive/educational and must never contain buy/sell/hold
language; the system prompt and offline templates enforce this.
"""
from __future__ import annotations

import json
import urllib.request

from lib.config import anthropic_key

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

_SYSTEM = (
    "You are an educational market-research assistant. Write neutral, factual "
    "analysis of the provided metrics. NEVER recommend buying, selling, or "
    "holding. NEVER predict prices or give price targets. Avoid advice language "
    "entirely. Frame everything as context for the reader's own research."
)


def active_provider() -> str:
    """Resolve and name the provider that would be used right now."""
    if _ollama_available():
        return "ollama (local)"
    if anthropic_key():
        return "anthropic"
    return "offline (built-in)"


def _ollama_available() -> bool:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=0.6) as r:
            return r.status == 200
    except Exception:
        return False


def _ollama_generate(prompt: str) -> str | None:
    try:
        body = json.dumps(
            {
                "model": OLLAMA_MODEL,
                "prompt": f"{_SYSTEM}\n\n{prompt}",
                "stream": False,
            }
        ).encode()
        req = urllib.request.Request(
            OLLAMA_URL, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            return data.get("response", "").strip() or None
    except Exception:
        return None


def _anthropic_generate(prompt: str) -> str | None:
    key = anthropic_key()
    if not key:
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=700,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            b.text for b in msg.content if getattr(b, "type", "") == "text"
        ).strip() or None
    except Exception:
        return None


def _offline_generate(ctx: dict) -> str:
    """Compose a neutral narrative directly from computed metrics."""
    sym = ctx.get("symbol", "the security")
    name = ctx.get("name", sym)
    price = ctx.get("price")
    chg = ctx.get("change_pct")
    tech = ctx.get("technical", {})
    fund = ctx.get("fundamental", {})

    lines = [f"### Research notes — {name} ({sym})", ""]
    if price is not None:
        move = ""
        if isinstance(chg, (int, float)):
            move = f", {'up' if chg >= 0 else 'down'} {abs(chg):.2f}% on the session"
        lines.append(f"The last observed price is **{price:,.2f}**{move}.")

    if tech:
        lines.append(
            f"\n**Technical context** — composite reading {tech.get('score','—')}/100 "
            f"({tech.get('label','').lower()}). "
            + "; ".join(f"{n}: {note}" for n, note in tech.get("factors", []) if note) + "."
        )
    if fund:
        lines.append(
            f"\n**Fundamental context** — composite reading {fund.get('score','—')}/100 "
            f"({fund.get('label','').lower()}). "
            + "; ".join(f"{n}" for n, _ in fund.get("factors", [])) + "."
        )

    lines.append(
        "\nThese observations summarize publicly available metrics for "
        "educational and personal-research purposes. They are not a "
        "recommendation to buy, sell, or hold, and they are not a forecast. "
        "Verify all figures independently before drawing conclusions."
    )
    return "\n".join(lines)


def _build_prompt(ctx: dict) -> str:
    return (
        "Write a short (3-4 paragraph) neutral research note for the following "
        "metrics. Do not give advice or predictions.\n\n"
        + json.dumps(ctx, default=str, indent=2)
    )


def analyze(ctx: dict) -> tuple[str, str]:
    """Return (analysis_text, provider_used)."""
    prompt = _build_prompt(ctx)

    if _ollama_available():
        out = _ollama_generate(prompt)
        if out:
            return out, "ollama (local)"

    if anthropic_key():
        out = _anthropic_generate(prompt)
        if out:
            return out, "anthropic"

    return _offline_generate(ctx), "offline (built-in)"
