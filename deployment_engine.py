"""
Deployment window engine for EXECUTE.
Only the selected ETF is shown as the main recommendation.
Other ETFs are available only as a compact comparison inside an expander.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

from config import ETF_META


@dataclass
class DeploymentWindow:
    etf: str
    role: str
    action: str
    suggested_window: str
    confidence: int
    reason: str
    guardrail: str


def _base_confidence(market_context, vix_val: float) -> int:
    if market_context.regime == "Risk-On":
        return 58
    if market_context.regime == "Neutral":
        return 66
    if market_context.regime in ["Defensive", "Risk-Off"]:
        return 74
    return 61


def _distance_to_target(state: dict) -> float:
    try:
        live = float(state.get("live_price", state.get("spot")))
        target = float(state.get("target"))
        return ((live - target) / target) * 100
    except Exception:
        return 999.0


def score_single_etf(etf: str, state: dict, market_context, vix_val: float) -> DeploymentWindow:
    meta = ETF_META[etf]
    distance = _distance_to_target(state)
    conf = _base_confidence(market_context, vix_val)
    window = f"{meta['primary_window']} · {meta['bahrain_window']}"

    if distance <= 0.20:
        action = "DEPLOY IF TARGET TRADES"
        conf = min(90, conf + 14)
        reason = "Price is very close to the target. A DAY limit is statistically reasonable."
    elif distance <= 0.75:
        action = "KEEP DAY LIMIT"
        conf = min(84, conf + 7)
        reason = "The target is close enough to keep the order active without chasing."
    else:
        action = "WAIT — DO NOT CHASE"
        conf = max(45, conf - 8)
        reason = "The ETF is still above the target. Wait for the market to come to the limit."

    if etf == "VNGA80" and market_context.regime in ["Defensive", "Risk-Off"]:
        window = "After US open · 16:30–18:00 Bahrain"
        reason += " Equity-heavy funds often give cleaner entries during the US overlap."
    elif etf == "VWCE" and market_context.regime == "Risk-On":
        window = "Reassess after US open · 16:30–18:30 Bahrain"
        reason += " Strong risk-on sessions reduce the odds of an attractive limit fill."
    elif etf == "V60A" and market_context.regime == "Neutral":
        window = "European morning · 10:00–12:00 CET"
        reason += " Balanced funds often provide cleaner pricing in the European morning."

    return DeploymentWindow(
        etf=etf,
        role=meta["role"],
        action=action,
        suggested_window=window,
        confidence=int(conf),
        reason=reason,
        guardrail="Use IBKR live bid/ask before execution. Do not convert an estimated window into a market order.",
    )


def score_deployment_windows(active_asset: str, state: dict, market_context, vix_val: float) -> List[DeploymentWindow]:
    rows: List[DeploymentWindow] = []
    for etf in ETF_META.keys():
        rows.append(score_single_etf(etf, state if etf == active_asset else state, market_context, vix_val))
    return rows


def windows_as_dicts(windows: List[DeploymentWindow]) -> List[Dict]:
    return [asdict(w) for w in windows]
