from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None


@dataclass
class PriceBundle:
    ticker: str
    history: pd.DataFrame
    source: str


def _demo_history(ticker: str, days: int = 260) -> pd.DataFrame:
    """Deterministic fallback so the app still works offline."""
    seed = abs(hash(ticker)) % (2**32)
    rng = np.random.default_rng(seed)
    end = pd.Timestamp.today().normalize()
    idx = pd.bdate_range(end=end, periods=days)
    base = 36 if "60" in ticker else 43 if "80" in ticker else 162
    drift = 0.00015
    vol = 0.006 if base < 100 else 0.008
    rets = rng.normal(drift, vol, len(idx))
    close = base * np.exp(np.cumsum(rets))
    high = close * (1 + rng.uniform(0.001, 0.008, len(idx)))
    low = close * (1 - rng.uniform(0.001, 0.008, len(idx)))
    open_ = close * (1 + rng.normal(0, 0.002, len(idx)))
    volume = rng.integers(5000, 50000, len(idx))
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=idx)


def fetch_history(ticker: str, period: str = "1y") -> PriceBundle:
    if yf is None:
        return PriceBundle(ticker, _demo_history(ticker), "demo data")
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        needed = ["Open", "High", "Low", "Close", "Volume"]
        df = df[[c for c in needed if c in df.columns]].dropna()
        if len(df) < 40:
            raise ValueError("not enough rows")
        return PriceBundle(ticker, df, "live/yfinance")
    except Exception:
        return PriceBundle(ticker, _demo_history(ticker), "demo fallback")


def latest_quote(ticker: str) -> Dict[str, float | str]:
    bundle = fetch_history(ticker, "3mo")
    df = bundle.history
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    close = float(last["Close"])
    prev_close = float(prev["Close"])
    change = ((close / prev_close) - 1) * 100 if prev_close else 0.0
    return {"ticker": ticker, "price": close, "change_pct": change, "source": bundle.source, "date": str(df.index[-1].date())}


def atr(df: pd.DataFrame, window: int = 14) -> float:
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    close = df["Close"].astype(float)
    prev_close = close.shift(1)
    tr = pd.concat([(high-low).abs(), (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    value = tr.rolling(window).mean().iloc[-1]
    return float(value) if math.isfinite(float(value)) else float(tr.tail(window).mean())


def rsi(df: pd.DataFrame, window: int = 14) -> float:
    close = df["Close"].astype(float)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    val = 100 - (100 / (1 + rs.iloc[-1]))
    if not math.isfinite(float(val)):
        return 50.0
    return float(val)


def moving_trend(df: pd.DataFrame) -> str:
    close = df["Close"].astype(float)
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1]
    if close.iloc[-1] > ma20 > ma60:
        return "Uptrend"
    if close.iloc[-1] < ma20 < ma60:
        return "Downtrend"
    return "Mixed"
