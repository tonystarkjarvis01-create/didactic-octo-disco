"""Local JSON persistence for a personal-research watch portfolio.

Stores positions in ``portfolio.json`` next to the project root. This is a
tracking tool only — no recommendations, targets, or trade suggestions.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

STORE = Path(__file__).resolve().parent.parent / "portfolio.json"


@dataclass
class Position:
    symbol: str
    shares: float
    cost_basis: float  # per-share


def load() -> list[Position]:
    if not STORE.exists():
        return []
    try:
        raw = json.loads(STORE.read_text())
        return [Position(**p) for p in raw]
    except Exception:
        return []


def save(positions: list[Position]) -> None:
    try:
        STORE.write_text(json.dumps([asdict(p) for p in positions], indent=2))
    except Exception:
        pass


def add(positions: list[Position], symbol: str, shares: float, cost: float) -> list[Position]:
    symbol = symbol.upper().strip()
    for p in positions:
        if p.symbol == symbol:
            # blend into a weighted average cost basis
            total = p.shares + shares
            if total > 0:
                p.cost_basis = (p.shares * p.cost_basis + shares * cost) / total
            p.shares = total
            save(positions)
            return positions
    positions.append(Position(symbol, shares, cost))
    save(positions)
    return positions


def remove(positions: list[Position], symbol: str) -> list[Position]:
    symbol = symbol.upper().strip()
    positions = [p for p in positions if p.symbol != symbol]
    save(positions)
    return positions
