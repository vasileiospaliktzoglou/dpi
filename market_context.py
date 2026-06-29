"""
PALI Execute v6.10 - Market Context Engine

Rule-based market explanation for daily investment intelligence.
This does not predict markets. It converts current benchmark moves into a concise,
transparent explanation and a next-session risk view.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class MarketContext:
    regime: str
    tone: str
    score: int
    explanation: str
    drivers: List[str]
    risks: List[str]
    tomorrow_bias: str


def _change_lookup(market_rows: List[dict]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for row in market_rows or []:
        try:
            out[str(row.get("Market"))] = float(row.get("Change") or 0.0)
        except Exception:
            out[str(row.get("Market"))] = 0.0
    return out


def classify_market_context(market_rows: List[dict], vix_val: float, sentiment: dict | None = None) -> MarketContext:
    """Return a human-readable market context from current benchmarks."""
    chg = _change_lookup(market_rows)
    score = int((sentiment or {}).get("score", 50))
    label = (sentiment or {}).get("label", "Neutral / Mixed")

    drivers: List[str] = []
    risks: List[str] = []

    sp = chg.get("S&P", 0.0)
    nas = chg.get("NASDAQ", 0.0)
    dax = chg.get("DAX", 0.0)
    eurusd = chg.get("EURUSD", 0.0)
    us10y = chg.get("US10Y", 0.0)
    gold = chg.get("Gold", 0.0)
    brent = chg.get("Brent", 0.0)
    btc = chg.get("BTC", 0.0)

    # Equity tone
    eq_avg = (sp + nas + dax) / 3.0
    if eq_avg > 0.35:
        drivers.append("Global equities are positive, so equity-heavy ETFs may stay above conservative limits.")
    elif eq_avg < -0.35:
        drivers.append("Global equities are weak, increasing the chance that limit orders are reached.")
    else:
        drivers.append("Equity markets are mixed/flat; standard DCA discipline is appropriate.")

    # Rates / bonds
    if us10y > 0.45:
        drivers.append("US yields are rising, which can pressure equity valuations and bond-sensitive balanced ETFs.")
        risks.append("Higher yields can create short-term weakness in V60A/V80A/VWCE.")
    elif us10y < -0.45:
        drivers.append("US yields are easing, which is supportive for balanced funds and global equities.")
    else:
        drivers.append("Bond-yield movement is not large enough to change the execution plan.")

    # Volatility
    if vix_val >= 25:
        risks.append("Volatility is elevated; use planned sizes only and confirm IBKR spreads before placing orders.")
    elif vix_val < 18:
        drivers.append("Volatility is calm; attractive limit fills may be less frequent unless equity markets pull back.")

    # Currency and defensive signals
    if abs(eurusd) > 0.35:
        direction = "stronger" if eurusd > 0 else "weaker"
        drivers.append(f"EUR/USD is moving {direction}, which matters for your USD-heavy global equity exposure and U03A.")
    if gold > 0.7:
        risks.append("Gold is bid, suggesting some defensive or geopolitical demand.")
    if brent > 1.2:
        risks.append("Oil is rising; watch inflation/geopolitical risk headlines.")
    if btc < -1.5:
        risks.append("Speculative liquidity is weak, which can spill into risk sentiment.")

    if score >= 70:
        regime = "Risk-On"
        tone = "Positive market tone, but less favorable for cheap limit fills."
        tomorrow_bias = "Be patient. Keep limits; do not chase stronger prices."
    elif score >= 45:
        regime = "Neutral"
        tone = "Balanced market tone. Use the standard execution plan."
        tomorrow_bias = "Use normal DCA rules and wait for target zones."
    elif score >= 25:
        regime = "Defensive"
        tone = "Weak but orderly tone. Limit orders have a better chance."
        tomorrow_bias = "Good environment for disciplined limits; avoid overdeploying unless dip ladder triggers."
    else:
        regime = "Risk-Off"
        tone = "Stress tone. Opportunities may appear, but execution risk is higher."
        tomorrow_bias = "Protect discipline. Wider limits and smaller size may be preferable."

    explanation = (
        f"Market regime is {regime}. {tone} "
        f"Current benchmark mix is classified as {label} with a score of {score}/100."
    )

    return MarketContext(
        regime=regime,
        tone=tone,
        score=score,
        explanation=explanation,
        drivers=drivers[:6],
        risks=risks[:5] or ["No major market-risk override detected from the current benchmark set."],
        tomorrow_bias=tomorrow_bias,
    )
