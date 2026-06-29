"""
PALI Execute v6.10 - Email Report Builder

Creates plain text / HTML daily intelligence emails. SMTP sending is intentionally
optional; the app can first download the email draft safely.
"""
from __future__ import annotations

import datetime as _dt
import html
from typing import List


def build_daily_intelligence_email(active_asset: str, state: dict, market_context, windows: List, row: dict | None = None):
    now = _dt.datetime.utcnow() + _dt.timedelta(hours=3)
    target = float(state.get("target", 0) or 0)
    live = float(state.get("live_price", state.get("spot", 0)) or 0)
    distance_pct = ((live - target) / target * 100) if target else 0
    subject = f"PALI EXECUTE | Daily Intelligence | {now.strftime('%d %b %Y')} | {active_asset}"

    top_window = next((w for w in windows if w.etf == active_asset), windows[0] if windows else None)
    lines = []
    lines.append(f"Good evening Vasileios,\n")
    lines.append(f"Market regime: {market_context.regime} ({market_context.score}/100)")
    lines.append(f"Active ETF: {active_asset}")
    lines.append(f"Target: EUR {target:.2f}")
    lines.append(f"Live/close proxy: EUR {live:.2f} ({distance_pct:+.2f}% vs target)")
    if top_window:
        lines.append(f"Best estimated deployment window: {top_window.suggested_window}")
        lines.append(f"Action: {top_window.action} | Confidence: {top_window.confidence}/100")
    lines.append("\nWhat is happening in the market:")
    lines.append(market_context.explanation)
    for d in market_context.drivers:
        lines.append(f"- {d}")
    lines.append("\nRisks / guardrails:")
    for r in market_context.risks:
        lines.append(f"- {r}")
    lines.append("\nETF deployment plan:")
    for w in windows:
        lines.append(f"- {w.etf}: {w.action}; window: {w.suggested_window}; confidence {w.confidence}/100. {w.reason}")
    lines.append("\nMain rule: do not chase. Deploy only when price enters the planned zone or when the DCA calendar requires it.")
    text = "\n".join(lines)

    rows_html = "".join(
        f"<tr><td>{html.escape(w.etf)}</td><td>{html.escape(w.action)}</td><td>{html.escape(w.suggested_window)}</td><td>{w.confidence}/100</td><td>{html.escape(w.reason)}</td></tr>"
        for w in windows
    )
    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#111827;">
      <h2>PALI EXECUTE Daily Intelligence</h2>
      <p>Good evening Vasileios,</p>
      <h3>Executive Summary</h3>
      <ul>
        <li><b>Market regime:</b> {html.escape(market_context.regime)} ({market_context.score}/100)</li>
        <li><b>Active ETF:</b> {html.escape(active_asset)}</li>
        <li><b>Target:</b> EUR {target:.2f}</li>
        <li><b>Live/close proxy:</b> EUR {live:.2f} ({distance_pct:+.2f}% vs target)</li>
      </ul>
      <h3>What is happening in the market</h3>
      <p>{html.escape(market_context.explanation)}</p>
      <ul>{''.join(f'<li>{html.escape(d)}</li>' for d in market_context.drivers)}</ul>
      <h3>ETF Deployment Plan</h3>
      <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
        <tr><th>ETF</th><th>Action</th><th>Best estimated window</th><th>Confidence</th><th>Reason</th></tr>
        {rows_html}
      </table>
      <h3>Guardrails</h3>
      <ul>{''.join(f'<li>{html.escape(r)}</li>' for r in market_context.risks)}</ul>
      <p><b>Main rule:</b> do not chase. Deploy only when price enters the planned zone or when the DCA calendar requires it.</p>
      <p style="color:#6b7280;">Generated {now.strftime('%Y-%m-%d %H:%M Bahrain')} by PALI Execute v6.10.</p>
    </body></html>
    """
    return {"subject": subject, "text": text, "html": html_body}
