from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import datetime as dt

import pandas as pd

from config import ETFS, MARKET_TICKERS
from data_provider import fetch_history, latest_quote, atr, rsi, moving_trend


@dataclass
class ETFDecision:
    symbol: str
    name: str
    role: str
    ticker: str
    action: str
    action_plain: str
    live_price: float
    target_price: float
    gap_eur: float
    gap_pct: float
    atr: float
    rsi: float
    trend: str
    target_touch_1d: float
    target_touch_5d: float
    target_touch_1d_count: int
    target_touch_5d_count: int
    sample_1d: int
    sample_5d: int
    confidence_label: str
    confidence_score: int
    window: str
    reason: str
    guardrail: str
    history: pd.DataFrame
    data_source: str


@dataclass
class MarketSummary:
    regime: str
    score: int
    one_sentence: str
    plain_english: str
    drivers: List[str]
    rows: List[Dict]


def _target_touch_rates(df: pd.DataFrame, target_distance_atr: float, current_atr: float) -> tuple[float, float, int, int, int, int]:
    """Historical question: if we placed a limit x ATR below close, was that level touched later?"""
    close = df["Close"].astype(float).reset_index(drop=True)
    low = df["Low"].astype(float).reset_index(drop=True)
    # use a simple rolling ATR estimate so the logic is transparent
    daily_range = (df["High"].astype(float) - df["Low"].astype(float)).reset_index(drop=True)
    rolling_atr = daily_range.rolling(14).mean().bfill()
    one = []
    five = []
    for i in range(20, len(df) - 5):
        target = close.iloc[i] - target_distance_atr * rolling_atr.iloc[i]
        one.append(low.iloc[i + 1] <= target)
        five.append(low.iloc[i + 1:i + 6].min() <= target)
    n1 = len(one)
    n5 = len(five)
    c1 = int(sum(one))
    c5 = int(sum(five))
    r1 = c1 / n1 * 100 if n1 else 0.0
    r5 = c5 / n5 * 100 if n5 else 0.0
    return r1, r5, c1, c5, n1, n5


def build_market_summary() -> MarketSummary:
    rows = []
    for label, ticker in MARKET_TICKERS.items():
        q = latest_quote(ticker)
        rows.append({"label": label, "ticker": ticker, "price": q["price"], "change_pct": q["change_pct"], "source": q["source"]})

    equity = [r["change_pct"] for r in rows if r["label"] in {"Global stocks", "S&P 500", "Europe stocks"}]
    avg_equity = sum(equity) / len(equity) if equity else 0
    vix = next((r["price"] for r in rows if r["label"] == "Volatility"), 18)
    bond = next((r["change_pct"] for r in rows if r["label"] == "US bonds"), 0)

    score = 50 + avg_equity * 12 - max(0, vix - 18) * 1.5 + bond * 3
    score = int(max(0, min(100, round(score))))
    if score >= 70:
        regime = "Positive"
        one = "Markets are positive today, so limit orders may be harder to fill."
    elif score <= 40:
        regime = "Cautious"
        one = "Markets are cautious today, which can improve the chance of patient limit orders being reached."
    else:
        regime = "Neutral"
        one = "Markets are mixed today, so the best action is to follow the plan and avoid chasing."

    drivers = []
    if avg_equity > 0.3:
        drivers.append("Equities are broadly higher.")
    elif avg_equity < -0.3:
        drivers.append("Equities are broadly weaker.")
    else:
        drivers.append("Equities are not giving a strong directional signal.")
    drivers.append(f"Volatility is around {vix:.1f}, which is {'elevated' if vix > 22 else 'normal' if vix < 19 else 'moderate'}.")
    if abs(bond) > 0.2:
        drivers.append("Bond prices moved enough to matter for balanced ETFs.")

    plain = "The app uses this one market reading for all ETFs. It does not repeat separate market stories for each ETF."
    return MarketSummary(regime, score, one, plain, drivers, rows)


def analyse_etf(symbol: str, market: MarketSummary) -> ETFDecision:
    meta = ETFS[symbol]
    bundle = fetch_history(meta["ticker"], "1y")
    df = bundle.history.copy()
    live = float(df["Close"].iloc[-1])
    a = atr(df)
    current_rsi = rsi(df)
    trend = moving_trend(df)
    offset = float(meta["default_target_offset_atr"])
    target = max(0.01, live - offset * a)
    gap = live - target
    gap_pct = (gap / target * 100) if target else 0
    r1, r5, c1, c5, n1, n5 = _target_touch_rates(df, offset, a)

    if gap_pct <= 0.20 or current_rsi < 38:
        action = "Deploy planned limit"
        plain = "The ETF is close enough to the target zone to use the planned limit order."
    elif r5 >= 45:
        action = "Wait with limit"
        plain = "History suggests patience has a reasonable chance of working within a few trading days."
    else:
        action = "Monitor only"
        plain = "The price is too far from the target. Do not chase unless the daily plan changes."

    if market.regime == "Cautious":
        window = "Next European session; check after the first 30–90 minutes."
    elif market.regime == "Positive":
        window = "Wait for a pullback; avoid raising the limit during strong buying."
    else:
        window = "Standard window: European morning or after US open volatility."

    confidence_score = int(max(30, min(95, (r5 * 0.8) + (10 if trend != "Downtrend" else -5) + (8 if market.regime != "Positive" else -3))))
    if confidence_score >= 75:
        conf = "High"
    elif confidence_score >= 55:
        conf = "Moderate"
    else:
        conf = "Low"

    reason = f"Current price is €{gap:.2f} above the target ({gap_pct:.2f}%). In similar historical setups, the target was reached within five trading days {r5:.1f}% of the time."
    guardrail = "Confirm live bid/ask in IBKR before placing any order. This is a disciplined execution aid, not a prediction of tomorrow's close."

    return ETFDecision(symbol, meta["name"], meta["role"], meta["ticker"], action, plain, live, target, gap, gap_pct, a, current_rsi, trend, r1, r5, c1, c5, n1, n5, conf, confidence_score, window, reason, guardrail, df, bundle.source)


def build_decisions() -> tuple[MarketSummary, Dict[str, ETFDecision]]:
    market = build_market_summary()
    decisions = {symbol: analyse_etf(symbol, market) for symbol in ETFS.keys()}
    return market, decisions


def choose_primary(decisions: Dict[str, ETFDecision]) -> ETFDecision:
    priority = {"Deploy planned limit": 3, "Wait with limit": 2, "Monitor only": 1}
    return sorted(decisions.values(), key=lambda d: (priority.get(d.action, 0), -d.gap_pct, d.confidence_score), reverse=True)[0]
