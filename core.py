import pandas as pd

from config import TICKERS
from helpers import (
    fetch_institutional_core,
    fetch_live_quote,
    compute_daily_trap_backtest,
    compute_multi_day_trap_backtest,
    compute_dip_statistics,
    suggest_deployment_ladder,
)


def status_word(vix):
    if vix >= 35:
        return "Stress"
    if vix >= 25:
        return "Elevated"
    return "Calm"

def confidence_word(score):
    if score >= 80:
        return "High"
    if score >= 60:
        return "Moderate"
    return "Low"

def decision_badge(decision):
    if decision == "STRATEGIC BUY":
        return "badge badge-buy"
    if decision == "PLACE DAY LIMIT":
        return "badge badge-buy"
    if decision == "MONITOR":
        return "badge badge-wait"
    return "badge badge-hold"

def decision_logic(vix, drawdown, gap):
    if vix > 35:
        return "HOLD CASH", "High stress", "Market stress is too high. Do not force execution."
    if drawdown < -12 and gap < 0.4:
        return "STRATEGIC BUY", "Deep discount", "Large drawdown and close target. The model becomes more aggressive."
    if gap > 1.5:
        return "MONITOR", "Too far from target", "The target is too far below the latest close. Wait."
    return "PLACE DAY LIMIT", "Target nearby", "Place a DAY limit order and let the market come to your price."

def compute_market_regime(vix_val, drawdown, z_score, dip_score):
    """Classify the current environment into a simple execution regime."""
    points = 0
    reasons = []

    if vix_val < 20:
        points += 30
        reasons.append("VIX below 20: normal stress")
    elif vix_val < 25:
        points += 22
        reasons.append("VIX between 20 and 25: mild caution")
    elif vix_val < 35:
        points += 10
        reasons.append("VIX above 25: elevated volatility")
    else:
        points += 0
        reasons.append("VIX above 35: stress regime")

    if drawdown > -5:
        points += 25
        reasons.append("ETF close to highs")
    elif drawdown > -12:
        points += 18
        reasons.append("ETF in pullback zone")
    elif drawdown > -20:
        points += 10
        reasons.append("ETF in correction zone")
    else:
        points += 5
        reasons.append("ETF in deep drawdown")

    if abs(z_score) < 1:
        points += 25
        reasons.append("Price near recent trend")
    elif z_score < -1:
        points += 18
        reasons.append("Price below trend: possible opportunity")
    else:
        points += 12
        reasons.append("Price stretched above trend")

    if dip_score >= 85:
        points += 20
        reasons.append("Rare intraday dip")
    elif dip_score >= 65:
        points += 14
        reasons.append("Meaningful intraday dip")
    else:
        points += 8
        reasons.append("Dip not historically rare")

    confidence = max(0, min(100, points))

    if vix_val >= 35:
        regime = "Panic"
    elif drawdown <= -12 or dip_score >= 90:
        regime = "Correction opportunity"
    elif vix_val >= 25:
        regime = "Elevated"
    elif drawdown <= -5 or dip_score >= 70:
        regime = "Pullback"
    else:
        regime = "Normal"

    return {"regime": regime, "confidence": confidence, "reasons": reasons}

def compute_opportunity_score_v2(state, vix_val):
    """Transparent 100-point score combining stress, dip rarity, drawdown, trend, and execution evidence."""
    dip_stats = state.get("dip_stats", {})
    dip_score = float(dip_stats.get("opportunity_score", 0))

    market_stress = 20 if vix_val < 20 else 15 if vix_val < 25 else 8 if vix_val < 35 else 2
    drawdown_score = max(0, min(20, abs(float(state.get("drawdown", 0))) * 2.0))
    rarity_score = max(0, min(20, dip_score * 0.20))

    z = float(state.get("z_score", 0))
    trend_score = 20 if -1.5 <= z <= 0.5 else 15 if z < -1.5 else 8

    fill = float(state.get("stats1", {}).get("fill_rate", 0))
    execution_score = max(0, min(20, 20 - abs(25 - fill) * 0.4))

    total = int(round(market_stress + drawdown_score + rarity_score + trend_score + execution_score))
    total = max(0, min(100, total))

    return {
        "total": total,
        "Market stress": market_stress,
        "Drawdown": drawdown_score,
        "Dip rarity": rarity_score,
        "Trend position": trend_score,
        "Execution evidence": execution_score,
    }

def compute_market_sentiment(market_rows, vix_val):
    """Rule-based daily sentiment score from benchmark direction and volatility."""
    score = 50
    reasons = []
    lookup = {r.get("Market"): float(r.get("Change") or 0.0) for r in market_rows}

    # Equity tone
    for key in ["S&P", "NASDAQ", "DAX"]:
        chg = lookup.get(key, 0.0)
        if chg > 0.25:
            score += 6
            reasons.append(f"{key} positive")
        elif chg < -0.25:
            score -= 6
            reasons.append(f"{key} negative")

    # Volatility
    if vix_val < 18:
        score += 10
        reasons.append("VIX calm")
    elif vix_val < 25:
        score += 2
        reasons.append("VIX normal")
    elif vix_val < 35:
        score -= 14
        reasons.append("VIX elevated")
    else:
        score -= 28
        reasons.append("VIX stress")

    # Safe havens and rates
    gold = lookup.get("Gold", 0.0)
    us10y = lookup.get("US10Y", 0.0)
    brent = lookup.get("Brent", 0.0)
    btc = lookup.get("BTC", 0.0)

    if gold > 0.6:
        score -= 5
        reasons.append("Gold bid: defensive tone")
    if us10y > 0.5:
        score -= 4
        reasons.append("Yields rising")
    elif us10y < -0.5:
        score += 3
        reasons.append("Yields easing")
    if brent > 1.5:
        score -= 3
        reasons.append("Oil up: inflation/geopolitical pressure")
    if btc > 1.0:
        score += 3
        reasons.append("BTC risk appetite positive")
    elif btc < -1.0:
        score -= 3
        reasons.append("BTC risk appetite weak")

    score = int(max(0, min(100, score)))
    if score >= 70:
        label = "Risk-On"
        effect = "Targets may not fill easily. Avoid chasing; keep the limit discipline."
        css = "sentiment-risk-on"
    elif score >= 45:
        label = "Neutral / Mixed"
        effect = "Standard DAY limit logic. Let the market come to your price."
        css = "sentiment-neutral"
    elif score >= 25:
        label = "Defensive"
        effect = "Limit orders are more likely to fill. Watch the dip ladder but avoid emotional overdeployment."
        css = "sentiment-defensive"
    else:
        label = "Risk-Off"
        effect = "Stress conditions. Confirm spreads and consider wider targets or planned reserve rules only."
        css = "sentiment-risk-off"

    return {"score": score, "label": label, "effect": effect, "reasons": reasons[:6], "css": css}

def calculate_state(asset_key, vix_val):
    latest_bar, df_clean = fetch_institutional_core(TICKERS[asset_key])
    if df_clean.empty or latest_bar is None:
        return None

    spot = float(latest_bar["Close"])
    atr = float(latest_bar["Atr"])
    z_score = float(latest_bar["Zscore"])
    drawdown = float(latest_bar["Drawdown"])
    latest_data_date = pd.to_datetime(latest_bar["Date"]).strftime("%d %b %Y")

    # Live-ish ETF quote for monitoring. The target remains based on completed daily candles.
    live_quote = fetch_live_quote(TICKERS[asset_key])
    live_price = float(live_quote.get("price") or spot)
    live_change_pct = float(live_quote.get("change_pct") or 0.0)

    base_m = 1.0 if vix_val < 20 else 1.3 if vix_val < 30 else 1.6
    if drawdown < -12:
        base_m -= 0.30
    elif drawdown < -5:
        base_m -= 0.15
    base_m = max(0.4, base_m)

    target = spot - base_m * atr
    gap_pct = ((spot / target) - 1) * 100

    stats1 = compute_daily_trap_backtest(df_clean, multiplier=base_m)
    stats5 = compute_multi_day_trap_backtest(df_clean, multiplier=base_m, horizon=5)

    setup_quality = max(5, min(99, int(100 - gap_pct * 12)))
    suitability = max(5, min(99, int(95 - abs(z_score) * 20)))
    if vix_val > 28:
        suitability = int(suitability * 0.7)

    decision, reason, detail = decision_logic(vix_val, drawdown, gap_pct)

    dip_stats = compute_dip_statistics(df_clean)
    deployment = suggest_deployment_ladder(dip_stats.get("current_dip_pct", 0.0), base_amount=20000)
    regime = compute_market_regime(vix_val, drawdown, z_score, dip_stats.get("opportunity_score", 0))

    temp_state = {
        "drawdown": drawdown,
        "z_score": z_score,
        "dip_stats": dip_stats,
        "stats1": stats1,
    }
    opportunity_v2 = compute_opportunity_score_v2(temp_state, vix_val)

    return {
        "df_clean": df_clean,
        "spot": spot,
        "live_price": live_price,
        "live_change_pct": live_change_pct,
        "live_source": live_quote.get("source", "unavailable"),
        "live_timestamp": live_quote.get("timestamp", ""),
        "live_is_liveish": bool(live_quote.get("is_liveish", False)),
        "atr": atr,
        "z_score": z_score,
        "drawdown": drawdown,
        "latest_data_date": latest_data_date,
        "base_m": base_m,
        "target": target,
        "gap_pct": gap_pct,
        "stats1": stats1,
        "stats5": stats5,
        "setup_quality": setup_quality,
        "suitability": suitability,
        "decision": decision,
        "reason": reason,
        "detail": detail,
        "dip_stats": dip_stats,
        "deployment": deployment,
        "regime": regime,
        "opportunity_v2": opportunity_v2,
    }
