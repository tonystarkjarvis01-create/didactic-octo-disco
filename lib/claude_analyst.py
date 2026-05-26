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
    "You are an educational equity-research assistant. Given metrics for a "
    "company, write a balanced, structured research summary that helps a reader "
    "form their OWN view. Cover both sides honestly.\n\n"
    "Use exactly these markdown sections:\n"
    "**Overview** — 1-2 sentences on what the company does and recent price action.\n"
    "**Reasons one might view it favorably** — bullet points grounded in the "
    "provided metrics (growth, margins, momentum, valuation, etc.).\n"
    "**Reasons for caution / risks** — bullet points on weaknesses, rich "
    "valuation, downtrends, or unknowns.\n"
    "**Valuation context** — how the multiples compare to typical ranges, neutrally.\n"
    "**What to watch** — concrete data points a researcher could track next.\n\n"
    "STRICT RULES: NEVER tell the reader to buy, sell, or hold. NEVER say "
    "whether it 'is a good investment' or give a verdict/score/rating. NEVER "
    "predict prices or give price targets. Present both sides; do not lean. "
    "This is educational context for the reader's own due diligence, not advice."
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
            model="claude-sonnet-4-6",
            max_tokens=1300,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            b.text for b in msg.content if getattr(b, "type", "") == "text"
        ).strip() or None
    except Exception:
        return None


def _offline_generate(ctx: dict) -> str:
    """Compose a balanced, structured summary directly from computed metrics."""
    sym = ctx.get("symbol", "the security")
    name = ctx.get("name", sym)
    price = ctx.get("price")
    chg = ctx.get("change_pct")
    tech = ctx.get("technical", {})
    fund = ctx.get("fundamental", {})
    extra = ctx.get("extra", {})

    favorable: list[str] = []
    caution: list[str] = []

    # Derive balanced bullet points from the supplied factors/metrics.
    for n, note in tech.get("factors", []):
        text = f"{n} ({note})" if note else n
        low = f"{n} {note}".lower()
        if any(k in low for k in ("above", "+")) and "below" not in low:
            favorable.append(text)
        elif any(k in low for k in ("below", "subdued", "-")):
            caution.append(text)
    for n, _ in fund.get("factors", []):
        favorable.append(n)
    margin = extra.get("profitMargins")
    if isinstance(margin, (int, float)) and margin < 0:
        caution.append(f"Negative profit margin ({margin*100:.1f}%)")
    pe = extra.get("trailingPE")
    if isinstance(pe, (int, float)) and pe > 35:
        caution.append(f"Elevated trailing P/E ({pe:.1f})")

    lines = [f"### Research summary — {name} ({sym})", ""]
    lines.append("**Overview**")
    move = ""
    if isinstance(chg, (int, float)):
        move = f", {'up' if chg >= 0 else 'down'} {abs(chg):.2f}% on the session"
    sector = extra.get("sector")
    biz = f"{name} operates in the {sector} sector. " if sector else ""
    lines.append(f"{biz}The last observed price is **{price:,.2f}**{move}." if price is not None else biz or "Limited data available.")

    lines.append("\n**Reasons one might view it favorably**")
    lines += [f"- {x}" for x in (favorable or ["Insufficient data to list factors."])]

    lines.append("\n**Reasons for caution / risks**")
    lines += [f"- {x}" for x in (caution or ["No specific risk flags surfaced from the available metrics."])]

    lines.append("\n**Valuation context**")
    if isinstance(pe, (int, float)):
        lines.append(
            f"Trailing P/E is {pe:.1f}; broad-market averages have historically "
            "sat in the high-teens to low-20s, so read this relative to the "
            "company's growth and sector — higher multiples imply higher growth "
            "expectations baked in."
        )
    else:
        lines.append("Valuation multiples were not available for this security.")

    lines.append("\n**What to watch**")
    lines.append(
        "- Upcoming earnings vs. expectations\n- Revenue/margin trend over the "
        "next few quarters\n- Whether price holds above or below its moving "
        "averages\n- Sector and macro conditions"
    )

    lines.append(
        "\n---\n*This is a balanced educational summary generated from public "
        "metrics. It is **not** a recommendation to buy, sell, or hold, not a "
        "verdict on whether to invest, and not a forecast. Do your own research.*"
    )
    return "\n".join(lines)


def _build_prompt(ctx: dict) -> str:
    return (
        "Write a balanced educational research summary for the company below, "
        "using the required section structure. Present both the favorable and "
        "the cautionary side. Do NOT give a verdict, rating, or buy/sell/hold "
        "advice, and do NOT predict prices.\n\n"
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
