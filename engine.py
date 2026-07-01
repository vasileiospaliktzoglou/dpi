from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from config import ETFS, MARKET_TICKERS
from data_provider import fetch_history, latest_quote, atr, rsi, moving_trend


@dataclass
class MarketSummary:
    regime: str
    score: int
    one_sentence: str
    plain: str
    drivers: List[str]
    rows: List[dict]
    fetched_at: str


@dataclass
class ETFDecision:
    symbol: str
    name: str
    role: str
    ticker: str
    action: str
    action_plain: str
    live_price: float
    previous_close: float
    day_change_pct: float
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
    best_weekday: str
    best_month_window: str
    timing_score: float
    timing_sample: int
    timing_reason: str
    reason: str
    guardrail: str
    history: pd.DataFrame
    data_source: str
    fetched_at: str
    estimated_saving_eur: float


def _target_touch_rates(df: pd.DataFrame, target_distance_atr: float) -> tuple[float, float, int, int, int, int]:
    """How often a limit x ATR below the close was reached later."""
    close = df["Close"].astype(float).reset_index(drop=True)
    low = df["Low"].astype(float).reset_index(drop=True)
    daily_range = (df["High"].astype(float) - df["Low"].astype(float)).reset_index(drop=True)
    rolling_atr = daily_range.rolling(14).mean().bfill()
    one, five = [], []
    for i in range(30, len(df) - 5):
        target = close.iloc[i] - target_distance_atr * rolling_atr.iloc[i]
        one.append(bool(low.iloc[i + 1] <= target))
        five.append(bool(low.iloc[i + 1:i + 6].min() <= target))
    n1, n5 = len(one), len(five)
    c1, c5 = int(sum(one)), int(sum(five))
    return (c1 / n1 * 100 if n1 else 0.0, c5 / n5 * 100 if n5 else 0.0, c1, c5, n1, n5)




def _month_bucket(day: int) -> str:
    if day <= 5:
        return "1st–5th"
    if day <= 10:
        return "6th–10th"
    if day <= 15:
        return "11th–15th"
    if day <= 20:
        return "16th–20th"
    if day <= 25:
        return "21st–25th"
    return "26th–month end"


def _rate_table(events: list[dict], key: str, min_sample: int = 20) -> list[tuple[str, float, int, int]]:
    table = []
    values = sorted({e[key] for e in events})
    for value in values:
        subset = [e for e in events if e[key] == value]
        n = len(subset)
        if n < min_sample:
            continue
        wins = sum(1 for e in subset if e["touch5"])
        rate = wins / n * 100 if n else 0.0
        table.append((value, rate, wins, n))
    return sorted(table, key=lambda x: (x[1], x[3]), reverse=True)


def _timing_edges(df: pd.DataFrame, target_distance_atr: float) -> tuple[str, str, float, int, str]:
    """Find simple historical timing patterns for deployment planning.

    This does not forecast exact prices. It asks: on which weekdays and month windows
    did a target x ATR below the close get touched within the next five trading days?
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        work = df.copy()
        work.index = pd.to_datetime(work.index, errors="coerce")
    else:
        work = df.copy()
    work = work.dropna(subset=["Close", "Low", "High"])
    close = work["Close"].astype(float).reset_index(drop=True)
    low = work["Low"].astype(float).reset_index(drop=True)
    daily_range = (work["High"].astype(float) - work["Low"].astype(float)).reset_index(drop=True)
    rolling_atr = daily_range.rolling(14).mean().bfill()
    dates = pd.Series(work.index).reset_index(drop=True)
    events = []
    for i in range(30, len(work) - 5):
        date = dates.iloc[i]
        if pd.isna(date):
            continue
        target = close.iloc[i] - target_distance_atr * rolling_atr.iloc[i]
        touch5 = bool(low.iloc[i + 1:i + 6].min() <= target)
        events.append({
            "weekday": date.day_name(),
            "bucket": _month_bucket(int(date.day)),
            "touch5": touch5,
        })
    weekday_table = _rate_table(events, "weekday", min_sample=30)
    bucket_table = _rate_table(events, "bucket", min_sample=30)
    best_weekday = weekday_table[0][0] if weekday_table else "No clear weekday edge"
    best_bucket = bucket_table[0][0] if bucket_table else "No clear month-window edge"
    best_rate = weekday_table[0][1] if weekday_table else 0.0
    best_n = weekday_table[0][3] if weekday_table else 0
    if weekday_table and bucket_table:
        reason = (
            f"Historically, {best_weekday}s had the strongest five-day target-touch rate "
            f"({weekday_table[0][2]}/{weekday_table[0][3]} cases). The strongest month window was "
            f"{best_bucket} ({bucket_table[0][2]}/{bucket_table[0][3]} cases)."
        )
    else:
        reason = "There is not enough stable history to claim a strong weekday or month-window edge."
    return best_weekday, best_bucket, best_rate, best_n, reason


def build_market_summary(refresh_key: int = 0) -> MarketSummary:
    rows = []
    fetched = ""
    for label, ticker in MARKET_TICKERS.items():
        q = latest_quote(ticker, refresh_key)
        fetched = q.get("fetched_at", fetched) or fetched
        change_5d = None
        change_1m = None
        try:
            bundle = fetch_history(ticker, "3mo", refresh_key)
            hist = bundle.history
            closes = hist["Close"].astype(float).dropna()
            # Do not compare a live Yahoo quote with synthetic/demo history.
            # That produced impossible values such as +327% for SPY.
            compatible_sources = not ("demo" in str(bundle.source).lower() and "live" in str(q.get("source", "")).lower())
            if compatible_sources and len(closes) > 6 and closes.iloc[-6] != 0:
                value_5d = (q["price"] / float(closes.iloc[-6]) - 1) * 100
                change_5d = value_5d if abs(value_5d) <= 50 else None
            if compatible_sources and len(closes) > 22 and closes.iloc[-22] != 0:
                value_1m = (q["price"] / float(closes.iloc[-22]) - 1) * 100
                change_1m = value_1m if abs(value_1m) <= 50 else None
        except Exception:
            change_5d = None
            change_1m = None
        rows.append({
            "label": "MSCI World" if label == "Global stocks" else label,
            "ticker": ticker,
            "price": q["price"],
            "change_pct": q["change_pct"],
            "change_5d_pct": change_5d,
            "change_1m_pct": change_1m,
            "source": q["source"],
            "date": q["date"],
        })

    equity = [r["change_pct"] for r in rows if r["label"] in {"MSCI World", "S&P 500", "Europe stocks"}]
    avg_equity = sum(equity) / len(equity) if equity else 0.0
    vix_price = next((r["price"] for r in rows if r["label"] == "Volatility"), 18.0)
    vix_change = next((r["change_pct"] for r in rows if r["label"] == "Volatility"), 0.0)
    bonds = next((r["change_pct"] for r in rows if r["label"] == "US bonds"), 0.0)

    score = 50 + avg_equity * 11 - max(0, vix_price - 18) * 1.4 - max(0, vix_change) * 0.35 + bonds * 2.5
    score = int(max(0, min(100, round(score))))
    if score >= 70:
        regime = "Positive"
        one = "Markets are firm today, so patient limit orders may need more time."
    elif score <= 40:
        regime = "Cautious"
        one = "Markets are weaker or more defensive, which can improve the chance of lower limit prices being reached."
    else:
        regime = "Neutral"
        one = "Markets are mixed, so the plan is to avoid chasing and let the limit orders work."

    drivers = []
    drivers.append(f"Global equity tone: {'positive' if avg_equity > 0.3 else 'weak' if avg_equity < -0.3 else 'mixed'}.")
    drivers.append(f"Volatility level: {vix_price:.1f}, {'elevated' if vix_price > 22 else 'normal' if vix_price < 19 else 'moderate'}.")
    if abs(bonds) > 0.15:
        drivers.append("Bond movement matters today for balanced ETFs such as V60A and VNGA80.")
    drivers.append("One market view is used for all ETFs; individual cards only show ETF-specific differences.")
    plain = "This is a daily execution reading, not a market forecast."
    return MarketSummary(regime, score, one, plain, drivers, rows, fetched)


def analyse_etf(symbol: str, market: MarketSummary, refresh_key: int = 0) -> ETFDecision:
    meta = ETFS[symbol]
    bundle = fetch_history(meta["ticker"], "5y", refresh_key)
    df = bundle.history.copy()
    previous = float(df["Close"].iloc[-2]) if len(df) > 1 else float(df["Close"].iloc[-1])
    quote = latest_quote(meta["ticker"], refresh_key)
    live = float(quote.get("price", df["Close"].iloc[-1]))
    day_change_pct = float(quote.get("change_pct", ((live / previous) - 1) * 100 if previous else 0.0))
    fetched_at = str(quote.get("fetched_at") or bundle.fetched_at)
    data_source = str(quote.get("source") or bundle.source)
    current_atr = atr(df)
    current_rsi = rsi(df)
    trend = moving_trend(df)
    offset = float(meta["default_target_offset_atr"])
    target = max(0.01, live - offset * current_atr)
    gap = live - target
    gap_pct = (gap / target * 100) if target else 0.0
    r1, r5, c1, c5, n1, n5 = _target_touch_rates(df, offset)
    best_weekday, best_month_window, timing_score, timing_sample, timing_reason = _timing_edges(df, offset)

    planned = float(meta.get("planned_amount_eur", 10000))
    estimated_saving = planned * max(gap_pct, 0) / 100.0

    if gap_pct <= 0.20 or current_rsi < 38:
        action = "Ready to deploy"
        plain = "The ETF is close to its preferred buying zone. Use the planned limit order, not a market order."
    elif r5 >= 45:
        action = "Wait with limit"
        plain = "The target is not reached yet, but history suggests patience often works within a few trading days."
    else:
        action = "Monitor only"
        plain = "The ETF is still far from the preferred entry zone. Keep watching; do not chase the price."

    if market.regime == "Cautious":
        window = "Next European session"
    elif market.regime == "Positive":
        window = "After a pullback"
    else:
        window = "European morning or US open"

    confidence_score = int(max(30, min(95, (r5 * 0.75) + (12 if trend != "Downtrend" else -5) + (8 if market.regime == "Cautious" else 0))))
    confidence_label = "High" if confidence_score >= 75 else "Moderate" if confidence_score >= 55 else "Low"

    reason = (
        f"{symbol} is €{gap:.2f} above the current limit target ({gap_pct:.2f}%). "
        f"Across the 5-year test window, a similar target was touched within five trading days in {c5} of {n5} cases ({r5:.1f}%)."
    )
    guardrail = "Check the live bid/ask in IBKR before placing an order. The chart and statistics help execution discipline; they do not guarantee tomorrow's price."

    return ETFDecision(
        symbol, meta["name"], meta["role"], meta["ticker"], action, plain, live, previous,
        day_change_pct, target, gap, gap_pct, current_atr, current_rsi, trend,
        r1, r5, c1, c5, n1, n5, confidence_label, confidence_score, window,
        best_weekday, best_month_window, timing_score, timing_sample, timing_reason,
        reason, guardrail, df, data_source, fetched_at, estimated_saving,
    )


def build_decisions(refresh_key: int = 0) -> tuple[MarketSummary, Dict[str, ETFDecision]]:
    market = build_market_summary(refresh_key)
    decisions = {symbol: analyse_etf(symbol, market, refresh_key) for symbol in ETFS.keys()}
    return market, decisions


def choose_primary(decisions: Dict[str, ETFDecision]) -> ETFDecision:
    priority = {"Ready to deploy": 3, "Wait with limit": 2, "Monitor only": 1}
    return sorted(decisions.values(), key=lambda d: (priority.get(d.action, 0), d.confidence_score, -d.gap_pct), reverse=True)[0]
