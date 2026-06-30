import datetime as dt
import socket
from typing import Dict, Iterable

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from config import FALLBACK_PRICES, TICKER_ALIASES


def _internet_available() -> bool:
    try:
        socket.setdefaulttimeout(1.0)
        socket.gethostbyname("query1.finance.yahoo.com")
        return True
    except Exception:
        return False


def _symbols_to_try(symbol: str) -> Iterable[str]:
    return [symbol]


def _normalise_download(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _fallback_history(symbol: str, years: int = 5) -> pd.DataFrame:
    """Deterministic fallback OHLC data when Yahoo is unavailable.

    This is not used for final trading decisions; it keeps the app alive and clearly
    labels data as fallback so the user can continue using the interface.
    """
    base = float(FALLBACK_PRICES.get(symbol, 100.0))
    days = min(365 * years, 900)
    end = pd.Timestamp(dt.date.today())
    dates = pd.bdate_range(end=end, periods=days)
    rng = np.random.default_rng(abs(hash(symbol)) % (2**32))
    # Conservative ETF-like random walk; V60A less volatile, VNGA80/VWCE more volatile.
    vol = 0.0035 if "V60A" in symbol else 0.0060
    drift = 0.00008
    rets = rng.normal(drift, vol, size=len(dates))
    prices = base * np.exp(np.cumsum(rets) - np.cumsum(rets)[-1])
    opens = prices * (1 + rng.normal(0, vol / 3, size=len(dates)))
    highs = np.maximum(opens, prices) * (1 + np.abs(rng.normal(vol / 2, vol / 4, size=len(dates))))
    lows = np.minimum(opens, prices) * (1 - np.abs(rng.normal(vol / 2, vol / 4, size=len(dates))))
    df = pd.DataFrame({"Date": dates, "Open": opens, "High": highs, "Low": lows, "Close": prices})
    return _add_indicators(df, source="fallback/offline")


def _add_indicators(df: pd.DataFrame, source: str) -> pd.DataFrame:
    df = df.reset_index(drop=True).copy()
    df["Date"] = pd.to_datetime(df["Date"])
    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Date", "Open", "High", "Low", "Close"]).sort_values("Date").reset_index(drop=True)
    df["Return %"] = df["Close"].pct_change() * 100
    df["Range %"] = ((df["High"] / df["Low"]) - 1) * 100
    df["Low from Prev Close %"] = ((df["Low"] / df["Close"].shift(1)) - 1) * 100
    df["Close from Prev Close %"] = ((df["Close"] / df["Close"].shift(1)) - 1) * 100
    df["ATR"] = (df["High"] - df["Low"]).rolling(14).mean()
    df["ATR %"] = (df["ATR"] / df["Close"]) * 100
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    df["High52"] = df["High"].rolling(252).max()
    df["Drawdown %"] = ((df["Close"] / df["High52"]) - 1) * 100
    df["Data Source"] = source
    return df.dropna().reset_index(drop=True)


@st.cache_data(ttl=60)
def fetch_live_quote(symbol: str) -> Dict[str, float]:
    """Live-ish quote from Yahoo daily data. Yahoo can be delayed for EU ETFs; confirm IBKR before trading."""
    if not _internet_available():
        price = float(FALLBACK_PRICES.get(symbol, 0.0))
        return {"price": price, "previous_close": price, "change_pct": 0.0, "bid": 0.0, "ask": 0.0, "source": "fallback/offline"}
    for sym in _symbols_to_try(symbol):
        try:
            df = yf.download(sym, period="7d", progress=False, auto_adjust=False, threads=False, timeout=5)
            df = _normalise_download(df)
            if not df.empty and "Close" in df.columns:
                closes = df["Close"].dropna()
                if len(closes) >= 2:
                    price = float(closes.iloc[-1])
                    previous_close = float(closes.iloc[-2])
                    change_pct = ((price / previous_close) - 1) * 100 if previous_close else 0.0
                    return {"price": price, "previous_close": previous_close, "change_pct": change_pct, "bid": 0.0, "ask": 0.0, "source": sym}
        except Exception:
            continue

    price = float(FALLBACK_PRICES.get(symbol, 0.0))
    return {"price": price, "previous_close": price, "change_pct": 0.0, "bid": 0.0, "ask": 0.0, "source": "fallback/offline"}


@st.cache_data(ttl=3600)
def fetch_history(symbol: str, years: int = 5) -> pd.DataFrame:
    if not _internet_available():
        return _fallback_history(symbol, years=years)
    start = dt.date.today() - dt.timedelta(days=365 * years + 30)
    end = dt.date.today() + dt.timedelta(days=1)
    for sym in _symbols_to_try(symbol):
        try:
            df = yf.download(sym, start=start, end=end, progress=False, auto_adjust=False, threads=False, timeout=5)
            df = _normalise_download(df)
            if df.empty:
                continue
            df = df.reset_index()
            if "Date" not in df.columns:
                continue
            out = _add_indicators(df, source=sym)
            if len(out) >= 120:
                return out
        except Exception:
            continue
    return _fallback_history(symbol, years=years)


def pct_price(base: float, pct_down: float) -> float:
    return float(base * (1 - pct_down / 100.0))


def percentile_safe(series: pd.Series, q: float, default: float) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 30:
        return default
    return float(np.percentile(s, q * 100))


def probability_lower_next_day(df: pd.DataFrame, today_change_pct: float, current_price: float, lookback_window: float = 0.35) -> Dict[str, float]:
    """Analog study: after similar daily declines/rises, how often did next session trade lower?"""
    if df.empty or len(df) < 120:
        return {"sample": 0, "prob_lower_next_day": 0.0, "median_next_low_pct": 0.0, "p25_next_low_pct": 0.0}

    d = df.copy().reset_index(drop=True)
    d["Next Low %"] = ((d["Low"].shift(-1) / d["Close"]) - 1) * 100
    mask = (d["Close from Prev Close %"] >= today_change_pct - lookback_window) & (d["Close from Prev Close %"] <= today_change_pct + lookback_window)
    sample = d.loc[mask, "Next Low %"].dropna()
    if len(sample) < 15:
        sample = d["Next Low %"].dropna()
    if sample.empty:
        return {"sample": 0, "prob_lower_next_day": 0.0, "median_next_low_pct": 0.0, "p25_next_low_pct": 0.0}
    return {
        "sample": int(len(sample)),
        "prob_lower_next_day": float((sample < 0).mean() * 100),
        "median_next_low_pct": float(sample.median()),
        "p25_next_low_pct": float(np.percentile(sample, 25)),
    }


def shares_for_amount(amount_eur: float, price: float) -> int:
    if not price or price <= 0:
        return 0
    return int(amount_eur // price)
