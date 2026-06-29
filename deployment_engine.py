"""
EXECUTE v6.10 - Deployment Window Engine

Scores next-session deployment windows for growth ETFs using transparent rules.
It recommends windows, not exact predictions.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List


ETF_PROFILES = {
    "V60A": {
        "role": "Core balanced 60/40 accumulator",
        "best_window": "10:00-12:00 CET / 11:00-13:00 Bahrain",
        "secondary_window": "16:30-18:00 Bahrain",
        "sensitivity": "Medium equity and bond sensitivity",
    },
    "VNGA80": {
        "role": "Core growth 80/20 accumulator",
        "best_window": "16:30-18:00 Bahrain",
        "secondary_window": "10:00-12:00 CET / 11:00-13:00 Bahrain",
        "sensitivity": "High equity sensitivity",
    },
    "VWCE": {
        "role": "Global equity accumulator",
        "best_window": "16:30-18:30 Bahrain",
        "secondary_window": "Friday afternoon if event risk is low",
        "sensitivity": "Very high global equity and USD exposure",
    },
}


@dataclass
class DeploymentWindow:
    etf: str
    role: str
    action: str
    suggested_window: str
    confidence: int
    reason: str
    guardrail: str


def _base_confidence(etf: str, market_context, vix_val: float) -> int:
    if market_context.regime == "Risk-On":
        return 58
    if market_context.regime == "Neutral":
        return 68
    if market_context.regime == "Defensive":
        return 76
    return 61


def score_deployment_windows(active_asset: str, state: dict, market_context, vix_val: float) -> List[DeploymentWindow]:
    """Return deployment guidance for all tracked growth ETFs."""
    rows: List[DeploymentWindow] = []
    active_target_distance = 999.0
    try:
        live = float(state.get("live_price", state.get("spot")))
        target = float(state.get("target"))
        active_target_distance = ((live - target) / target) * 100
    except Exception:
        pass

    for etf, profile in ETF_PROFILES.items():
        conf = _base_confidence(etf, market_context, vix_val)
        suggested = profile["best_window"]
        action = "Wait for target zone"
        guardrail = "Confirm live bid/ask spread before placing the order. Do not chase a green candle."
        reason = f"{profile['sensitivity']}; {market_context.tomorrow_bias}"

        if etf == active_asset:
            if active_target_distance <= 0.20:
                action = "Deploy if target trades"
                conf = min(90, conf + 12)
                reason = "Active ETF is very close to the limit target; execution probability is elevated."
            elif active_target_distance <= 0.75:
                action = "Keep DAY limit"
                conf = min(84, conf + 6)
                reason = "Active ETF is close enough that disciplined limit execution is still realistic."
            else:
                action = "Do not chase"
                conf = max(50, conf - 7)
                reason = "Price remains far from the target; buying at market would weaken execution quality."

        if etf == "VNGA80" and market_context.regime in ["Defensive", "Risk-Off"]:
            suggested = "After US open: 16:30-18:00 Bahrain"
            reason = "Equity-heavy ETF; defensive sessions often create better post-US-open entry windows."
        elif etf == "V60A" and market_context.regime == "Neutral":
            suggested = "European morning: 10:00-12:00 CET"
            reason = "Balanced ETF; European morning pullbacks are usually cleaner than chasing later strength."
        elif etf == "VWCE" and market_context.regime == "Risk-On":
            suggested = "Wait for a pullback; reassess after US open"
            reason = "Global equity ETF; strong risk-on days reduce the odds of attractive limit fills."

        rows.append(DeploymentWindow(etf, profile["role"], action, suggested, int(conf), reason, guardrail))
    return rows


def windows_as_dicts(windows: List[DeploymentWindow]) -> List[Dict]:
    return [asdict(w) for w in windows]
