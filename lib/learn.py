"""Investing-focused learning content: glossary + 'how to read it' notes.

Pitched at someone who understands general finance (revenue, profit, debt,
risk vs. return) but is new to *investing* — reading tickers, charts, and
valuation metrics. So we explain the investing/chart-reading layer plainly
and skip the basic-money definitions.

Each glossary entry is (what_it_tells_you, how_to_read_it). Keep everything
descriptive — never advice, never "you should".
"""
from __future__ import annotations

# term -> (what it tells you, how to read it / what's high vs low and why)
GLOSSARY: dict[str, tuple[str, str]] = {
    "P/E ratio (price-to-earnings)": (
        "How many dollars investors currently pay for each dollar of the "
        "company's annual earnings.",
        "Roughly: high-teens to low-20s is typical for the broad market. A high "
        "P/E means the market expects strong future growth (and you're paying up "
        "for it); a low P/E can mean modest expectations *or* a company the market "
        "is worried about. Always compare within the same sector — tech usually "
        "runs higher than utilities.",
    ),
    "P/B ratio (price-to-book)": (
        "Price relative to the company's net asset (book) value.",
        "Below ~1 means you're paying less than stated book value (common for "
        "banks/asset-heavy firms); high P/B is normal for asset-light businesses "
        "like software, where value is in brand/IP not buildings.",
    ),
    "EPS (earnings per share)": (
        "Profit attributed to each share.",
        "Rising EPS over time is the engine behind long-run returns. Watch the "
        "*trend* and whether growth is real or just from share buybacks.",
    ),
    "Dividend yield": (
        "Annual dividend as a % of the share price.",
        "A 2–4% yield is common for mature payers. A very high yield (8%+) is a "
        "flag, not a gift — it often means the price has fallen because the market "
        "doubts the dividend is sustainable.",
    ),
    "Market cap": (
        "Total value of all shares (price × shares outstanding) — the company's size.",
        "Large-cap (>$10B) tends to be steadier; small-cap (<$2B) more volatile "
        "with more room to grow or fail. Size shapes how risky the position is.",
    ),
    "Debt-to-equity": (
        "How much the company is financed by debt vs. shareholder equity.",
        "Higher = more leverage = more risk if earnings dip or rates rise. 'Healthy' "
        "varies wildly by sector — utilities carry lots of debt by design; software "
        "carries almost none.",
    ),
    "Free cash flow (FCF)": (
        "Cash left after running the business and funding capital spending.",
        "Positive and growing FCF means the company funds itself, dividends, and "
        "buybacks without borrowing. Profit can be accounting; cash is harder to fake.",
    ),
    "Beta": (
        "How much the stock moves relative to the overall market.",
        "Beta 1.0 ≈ moves with the market. >1 = more volatile (amplifies up and "
        "down moves); <1 = steadier than the market. It's a volatility gauge, not "
        "a quality gauge.",
    ),
    "RSI (Relative Strength Index)": (
        "A 0–100 momentum gauge of how fast/far price has moved recently.",
        "Above ~70 is often called 'overbought' (price ran up fast); below ~30 "
        "'oversold'. These describe momentum, not a verdict — strong stocks can "
        "stay 'overbought' for a long time.",
    ),
    "MACD": (
        "Compares a short vs. longer moving average to show momentum shifts.",
        "When the MACD line crosses above its signal line, short-term momentum is "
        "turning up; below, turning down. Read it as a momentum description, "
        "confirmed alongside price and volume — not a standalone trigger.",
    ),
    "Moving average (MA/SMA)": (
        "The average closing price over the last N periods, smoothed into a line.",
        "Price above its 50/200-day average is generally read as an uptrend; below, "
        "a downtrend. The 50-day crossing the 200-day is widely watched as a "
        "trend-change marker.",
    ),
    "Candlestick": (
        "Each candle shows open, high, low, and close for one period.",
        "Body = open-to-close (green/up, red/down); the thin wicks = the high/low "
        "extremes. Long wicks show rejection of a price level; a long body shows "
        "strong directional conviction that period.",
    ),
    "Expense ratio": (
        "The annual % an ETF/fund charges on your invested amount.",
        "It compounds *against* you every year. 0.03% vs 0.75% sounds tiny, but on "
        "$10,000 over 30 years at 7% growth that gap costs you thousands — lower-cost "
        "funds keep more of the return in your pocket.",
    ),
    "Volatility": (
        "How much a price swings around, usually annualized as a %.",
        "Higher volatility = wider swings = more risk *and* more potential range. "
        "It measures bumpiness, not direction.",
    ),
    "Diversification": (
        "Spreading holdings across companies, sectors, and regions.",
        "The point is that not everything falls together. Heavy concentration in one "
        "stock/sector/country raises the chance one bad event hits your whole "
        "portfolio at once.",
    ),
    "Ticker & exchange suffix": (
        "A ticker is a stock's short code; a suffix tells which exchange it trades on.",
        "US tickers have no suffix (AAPL). Other exchanges add one: Australia "
        "'.AX' (BHP.AX), London '.L' (BP.L), Tokyo '.T'. Same company can list in "
        "several places, priced in that market's local currency.",
    ),
}


def glossary_markdown() -> str:
    """Render the whole glossary as markdown for the Learn page."""
    out = []
    for term, (what, how) in GLOSSARY.items():
        out.append(f"**{term}**  \n*What it tells you:* {what}  \n*How to read it:* {how}")
    return "\n\n".join(out)


def term(name: str) -> str:
    """Return a compact markdown explainer for one term, for use in explain()."""
    if name not in GLOSSARY:
        return ""
    what, how = GLOSSARY[name]
    return f"**What it tells you:** {what}\n\n**How to read it:** {how}"
