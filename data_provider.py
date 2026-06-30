from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from functools import lru_cache
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
    fetched_at: str


def _clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    needed = ["Open", "High", "Low", "Close", "Volume"]
    df = df[[c for c in needed if c in df.columns]].copy()
    for c in needed:
        if c not in df.columns:
            df[c] = np.nan
    df = df[needed].dropna(subset=["Open", "High", "Low", "Close"])
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def _demo_history(ticker: str, days: int = 1260) -> pd.DataFrame:
    """Deterministic fallback so the app still works offline. Clearly labelled as demo."""
    seed = abs(hash(ticker)) % (2**32)
    rng = np.random.default_rng(seed)
    end = pd.Timestamp.today().normalize()
    idx = pd.bdate_range(end=end, periods=days)
    base = 36 if "60" in ticker else 43 if "80" in ticker else 162 if "VWCE" in ticker else 100
    drift = 0.00018
    vol = 0.006 if base < 100 else 0.008
    rets = rng.normal(drift, vol, len(idx))
    close = base * np.exp(np.cumsum(rets))
    high = close * (1 + rng.uniform(0.001, 0.010, len(idx)))
    low = close * (1 - rng.uniform(0.001, 0.010, len(idx)))
    open_ = close * (1 + rng.normal(0, 0.002, len(idx)))
    volume = rng.integers(5000, 70000, len(idx))
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=idx)


@lru_cache(maxsize=64)
def fetch_history_cached(ticker: str, period: str = "5y", refresh_key: int = 0) -> PriceBundle:
    fetched = dt.datetime.now().strftime("%d %b %Y %H:%M")
    if yf is None:
        return PriceBundle(ticker, _demo_history(ticker), "demo/offline", fetched)
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False, threads=False)
        df = _clean_ohlcv(df)
        if len(df) < 120:
            raise ValueError("not enough rows")
        return PriceBundle(ticker, df, "live/yfinance", fetched)
    except Exception:
        return PriceBundle(ticker, _demo_history(ticker), "demo fallback", fetched)


def fetch_history(ticker: str, period: str = "5y", refresh_key: int = 0) -> PriceBundle:
    return fetch_history_cached(ticker, period, refresh_key)


def latest_quote(ticker: str, refresh_key: int = 0) -> Dict[str, float | str]:
    """Return the freshest available quote.

    The daily chart still uses 5-year OHLC data, but this function first tries
    yfinance fast_info so the dashboard price can update more often. If that
    fails, it falls back to the latest daily close.
    """
    fetched = dt.datetime.now().strftime("%d %b %Y %H:%M")
    if yf is not None:
        try:
            info = yf.Ticker(ticker).fast_info
            price = info.get("last_price") or info.get("lastPrice")
            prev = info.get("previous_close") or info.get("previousClose")
            if price is not None and prev is not None and float(prev) > 0:
                price_f = float(price)
                prev_f = float(prev)
                return {
                    "ticker": ticker,
                    "price": price_f,
                    "change_pct": ((price_f / prev_f) - 1) * 100,
                    "source": "live/yfinance quote",
                    "date": fetched,
                    "fetched_at": fetched,
                }
        except Exception:
            pass

    bundle = fetch_history(ticker, "6mo", refresh_key)
    df = bundle.history
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    close = float(last["Close"])
    prev_close = float(prev["Close"])
    change = ((close / prev_close) - 1) * 100 if prev_close else 0.0
    return {
        "ticker": ticker,
        "price": close,
        "change_pct": change,
        "source": bundle.source,
        "date": str(df.index[-1].date()),
        "fetched_at": bundle.fetched_at,
    }


def atr(df: pd.DataFrame, period: int = 14) -> float:
    data = df.copy()
    prev_close = data["Close"].shift(1)
    tr = pd.concat([
        data["High"] - data["Low"],
        (data["High"] - prev_close).abs(),
        (data["Low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    value = float(tr.rolling(period).mean().iloc[-1])
    if not np.isfinite(value) or value <= 0:
        value = float((data["High"] - data["Low"]).tail(period).mean())
    return value


def rsi(df: pd.DataFrame, period: int = 14) -> float:
    close = df["Close"].astype(float)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    value = float((100 - (100 / (1 + rs))).iloc[-1])
    return 50.0 if not np.isfinite(value) else value


def moving_trend(df: pd.DataFrame) -> str:
    close = df["Close"].astype(float)
    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]
    last = close.iloc[-1]
    if last > ma20 > ma50:
        return "Uptrend"
    if last < ma20 < ma50:
        return "Downtrend"
    return "Mixed"
