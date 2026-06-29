"""
EXECUTE v6.10 - Email Report Builder
"""
from __future__ import annotations

from datetime import datetime
from html import escape


def build_daily_intelligence_email(active_asset: str, state: dict, context, windows):
    now = datetime.now()
    active = next((w for w in windows if w.etf == active_asset), windows[0])
    subject = f"EXECUTE | Daily Intelligence | {now.strftime('%d %b %Y')} | {active_asset}"

    lines = []
    lines.append(subject)
    lines.append("=" * len(subject))
    lines.append("")
    lines.append("Good evening,\n")
    lines.append("Market summary")
    lines.append(f"- Regime: {context.regime} ({context.score}/100)")
    lines.append(f"- Explanation: {context.explanation}")
    lines.append("")
    lines.append("Key drivers")
    for d in context.drivers:
        lines.append(f"- {d}")
    lines.append("")
    lines.append("Tomorrow deployment plan")
    for w in windows:
        lines.append(f"- {w.etf}: {w.action} | {w.suggested_window} | confidence {w.confidence}/100")
        lines.append(f"  Reason: {w.reason}")
    lines.append("")
    lines.append("Active ETF instruction")
    lines.append(f"- ETF: {active_asset}")
    lines.append(f"- Action: {active.action}")
    lines.append(f"- Window: {active.suggested_window}")
    lines.append(f"- Guardrail: {active.guardrail}")
    lines.append("")
    lines.append("Principle: Evidence over emotion. Use the window only if price and spread support the plan.")
    text = "\n".join(lines)

    rows = "".join(
        f"<tr><td>{escape(w.etf)}</td><td>{escape(w.action)}</td><td>{escape(w.suggested_window)}</td><td>{w.confidence}/100</td><td>{escape(w.reason)}</td></tr>"
        for w in windows
    )
    drivers = "".join(f"<li>{escape(d)}</li>" for d in context.drivers)
    risks = "".join(f"<li>{escape(r)}</li>" for r in context.risks)
    html = f"""
    <html><body style="font-family:Arial, sans-serif;background:#f8fafc;color:#111827;padding:24px;">
      <div style="max-width:860px;margin:auto;background:white;border:1px solid #e5e7eb;border-radius:18px;padding:28px;">
      <h2 style="margin:0 0 8px 0;">EXECUTE Daily Intelligence</h2>
      <p>Good evening,</p>
      <div style="border:1px solid #e5e7eb;border-radius:14px;padding:16px;background:#f9fafb;">
        <b>Market regime:</b> {escape(context.regime)} ({context.score}/100)<br/>
        <b>Summary:</b> {escape(context.explanation)}
      </div>
      <h3>Key drivers</h3><ul>{drivers}</ul>
      <h3>Risks / guardrails</h3><ul>{risks}</ul>
      <h3>Tomorrow deployment plan</h3>
      <table cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;font-size:14px;">
        <tr style="background:#111827;color:white;"><th>ETF</th><th>Action</th><th>Window</th><th>Confidence</th><th>Reason</th></tr>
        {rows}
      </table>
      <h3>Active ETF instruction</h3>
      <p><b>{escape(active_asset)}</b>: {escape(active.action)} during <b>{escape(active.suggested_window)}</b>.</p>
      <p style="color:#6b7280;">Generated {now.strftime('%Y-%m-%d %H:%M Bahrain')} by EXECUTE v6.10.</p>
      </div>
    </body></html>
    """
    return {"subject": subject, "text": text, "html": html}
