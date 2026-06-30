import numpy as np
import pandas as pd

from config import TICKERS, BASE_AMOUNTS
from helpers import fetch_history, fetch_live_quote, pct_price, percentile_safe, probability_lower_next_day, shares_for_amount


def status_word(vix: float) -> str:
    if vix >= 35:
        return "Stress"
    if vix >= 25:
        return "Elevated"
    if vix >= 20:
        return "Caution"
    return "Calm"


def compute_market_sentiment(market_rows, vix_val):
    score = 50
    reasons = []
    changes = {r["Market"]: r.get("Change", 0) for r in market_rows}
    if changes.get("S&P 500", 0) > 0:
        score += 10; reasons.append("S&P positive")
    else:
        score -= 8; reasons.append("S&P weak")
    if changes.get("NASDAQ", 0) > 0:
        score += 10; reasons.append("NASDAQ positive")
    else:
        score -= 8; reasons.append("NASDAQ weak")
    if vix_val < 20:
        score += 10; reasons.append("VIX calm")
    elif vix_val >= 25:
        score -= 15; reasons.append("VIX elevated")
    score = max(0, min(100, score))
    if score >= 70:
        label = "Risk-on"
    elif score >= 45:
        label = "Rotation / mixed"
    else:
        label = "Risk-off"
    return {"score": score, "label": label, "reasons": reasons}


def calculate_decision(asset: str):
    symbol = TICKERS[asset]
    df = fetch_history(symbol)
    live = fetch_live_quote(symbol)
    if df.empty:
        return None

    last_completed = df.iloc[-1]
    prev_close = float(last_completed["Close"])
    live_price = live["price"] or prev_close
    change_from_prev = ((live_price / prev_close) - 1) * 100 if prev_close else 0.0

    abs_ret = df["Return %"].abs()
    low_from_prev_abs = -df["Low from Prev Close %"]  # positive value = dip depth
    p50_dip = percentile_safe(low_from_prev_abs, 0.50, 0.45)
    p70_dip = percentile_safe(low_from_prev_abs, 0.70, 0.70)
    p85_dip = percentile_safe(low_from_prev_abs, 0.85, 1.05)
    p95_dip = percentile_safe(low_from_prev_abs, 0.95, 1.65)
    typical_abs = percentile_safe(abs_ret, 0.50, 0.35)
    large_abs = percentile_safe(abs_ret, 0.85, 1.0)

    normal_price = pct_price(prev_close, p50_dip)
    good_price = pct_price(prev_close, p70_dip)
    strong_price = pct_price(prev_close, p85_dip)
    exceptional_price = pct_price(prev_close, p95_dip)

    if live_price <= exceptional_price:
        decision = "EXCEPTIONAL BUY"
        confidence = "High"
        suggested_limit = live.get("ask") or live_price
        action = "Buy now / do not over-optimize cents"
    elif live_price <= strong_price:
        decision = "STRONG BUY"
        confidence = "High"
        suggested_limit = live.get("ask") or live_price
        action = "Use live IBKR bid/ask; execute planned amount"
    elif live_price <= good_price:
        decision = "BUY"
        confidence = "Moderate"
        suggested_limit = live.get("ask") or live_price
        action = "Good DCA window"
    elif live_price <= normal_price:
        decision = "LIMIT BUY"
        confidence = "Moderate"
        suggested_limit = good_price
        action = "Place limit near Good Buy price"
    else:
        decision = "WAIT"
        confidence = "Low"
        suggested_limit = good_price
        action = "Do not chase; wait for statistically better price"

    analog = probability_lower_next_day(df, change_from_prev, live_price)
    base_amount = BASE_AMOUNTS.get(asset, 0)
    shares = shares_for_amount(base_amount, suggested_limit) if base_amount else 0

    return {
        "asset": asset,
        "symbol": symbol,
        "df": df,
        "latest_data_date": str(pd.to_datetime(last_completed["Date"]).date()),
        "data_source": str(last_completed.get("Data Source", live.get("source", "unknown"))),
        "prev_close": prev_close,
        "live_price": float(live_price),
        "bid": float(live.get("bid") or 0.0),
        "ask": float(live.get("ask") or 0.0),
        "change_from_prev": float(change_from_prev),
        "decision": decision,
        "confidence": confidence,
        "action": action,
        "suggested_limit": float(suggested_limit),
        "base_amount": int(base_amount),
        "suggested_shares": int(shares),
        "levels": {
            "Normal watch": normal_price,
            "Good buy": good_price,
            "Strong buy": strong_price,
            "Exceptional": exceptional_price,
        },
        "stats": {
            "median_abs_return_pct": float(typical_abs),
            "large_abs_return_pct": float(large_abs),
            "median_dip_pct": float(p50_dip),
            "good_dip_pct": float(p70_dip),
            "strong_dip_pct": float(p85_dip),
            "exceptional_dip_pct": float(p95_dip),
            **analog,
        },
        "distance_to_levels": {
            k: ((live_price / v) - 1) * 100 if v else 0.0 for k, v in {
                "Good buy": good_price,
                "Strong buy": strong_price,
                "Exceptional": exceptional_price,
            }.items()
        },
    }


def calculate_all_states():
    return {asset: calculate_decision(asset) for asset in TICKERS}
