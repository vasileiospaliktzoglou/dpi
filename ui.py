from pathlib import Path
import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from config import TICKERS, MARKET_EXPLAINERS
from helpers import (
    fetch_live_quote,
    fetch_chart_data,
    compute_calendar_timing,
    fetch_intraday_low_distribution,
    compute_previous_execution_review,
    compute_tab3_matrices,
)
from core import (
    status_word,
    confidence_word,
    decision_badge,
    calculate_state,
)


def render_market_sentiment(sentiment):
    reason_text = " | ".join(sentiment.get("reasons", [])) or "No strong directional signals."
    score = int(sentiment.get("score", 50))
    raw_label = sentiment.get("label", "Mixed")

    if score <= 24:
        headline = "Markets are under pressure"
        plain = "Selling pressure is broad and investors are avoiding risk. This can create buying opportunities, but price swings and spreads may be larger than normal."
        action = "Be careful. Keep only planned orders active and confirm IBKR bid/ask before increasing exposure."
        bucket = "0-24: Risk-off = heavy selling pressure"
        confidence = "Cautious"
    elif score <= 44:
        headline = "Markets are cautious"
        plain = "Stocks are weak, but this is not panic. Investors are reducing risk in an orderly way."
        action = "Your limit order has a better chance of filling. Do not chase prices. Add extra cash only if the -5% or -10% ladder rule activates."
        bucket = "25-44: Defensive = weak but orderly market"
        confidence = "Medium"
    elif score <= 69:
        headline = "Markets are mixed"
        plain = "There is no strong message from the market today. Some signals are positive and some are negative."
        action = "Use the standard DAY limit plan and wait for the market to come to your price."
        bucket = "45-69: Mixed = no clear direction"
        confidence = "Medium"
    elif score <= 84:
        headline = "Markets are positive"
        plain = "Buyers have the advantage today. Risk appetite is healthy."
        action = "Your target may be harder to reach. Keep the order, but do not raise the limit just because the market is moving up."
        bucket = "70-84: Risk-on = buyers have the advantage"
        confidence = "Medium to high"
    else:
        headline = "Markets are strongly positive"
        plain = "Most risk assets are moving up together. The market is confident and buyers are in control."
        action = "Limit orders are less likely to fill. Avoid chasing; wait for the next daily recalculation if the market runs away."
        bucket = "85-100: Strong risk-on = broad upward momentum"
        confidence = "High"

    st.markdown(f"""
    <div class="{sentiment['css']}">
        <div class="dip-label">Daily market sentiment</div>
        <div class="sentiment-big">{headline}</div>
        <div class="insight-text">
            <b>Score:</b> {score}/100. {bucket}.<br>
            <b>Plain English:</b> {plain}<br>
            <b>Execution meaning:</b> {action}<br>
            <b>Confidence:</b> {confidence}. This is a market condition reading, not a market forecast.<br>
            <b>Drivers:</b> {reason_text}
        </div>
        <div class="score-scale plain-scale">
            <div><b>0-24</b><br>Heavy selling</div>
            <div><b>25-44</b><br>Cautious</div>
            <div><b>45-69</b><br>Mixed</div>
            <div><b>70-84</b><br>Positive</div>
            <div><b>85-100</b><br>Strong buying</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_execution_plan(asset, state):
    shares = int(20000 / state["target"])
    saving = (state["spot"] - state["target"]) * shares
    confidence = confidence_word(state["suitability"])
    badge = decision_badge(state["decision"])

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">Today's execution command</div>
            <div class="{badge}">{state['decision']}</div>
            <div class="hero-price">EUR {state['target']:.2f}</div>
            <div class="hero-text">
                Use this as tomorrow's <b>DAY limit</b> reference after confirming live IBKR bid/ask.
                It is an execution target, not a prediction of tomorrow's close.
            </div>
            <div class="kpi-grid">
                <div class="kpi-box"><div class="kpi-label">ETF</div><div class="kpi-value">{asset}</div></div>
                <div class="kpi-box"><div class="kpi-label">Live ETF</div><div class="kpi-value">EUR {state['live_price']:.2f}</div></div>
                <div class="kpi-box"><div class="kpi-label">Improvement</div><div class="kpi-value">{state['gap_pct']:.2f}%</div></div>
                <div class="kpi-box"><div class="kpi-label">Next-day fill</div><div class="kpi-value">{state['stats1']['fill_rate']:.1f}%</div></div>
                <div class="kpi-box"><div class="kpi-label">Confidence</div><div class="kpi-value">{confidence}</div></div>
                <div class="kpi-box"><div class="kpi-label">EUR 20k saving</div><div class="kpi-value">EUR {saving:.0f}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.code(f"BUY {asset} IBIS LMT {state['target']:.2f} DAY", language="bash")
    st.caption(
        f"ETF monitor quote: {state['live_source']} | change {state['live_change_pct']:.2f}% | "
        "Yahoo/yfinance can be delayed; use IBKR bid/ask for final execution."
    )

def render_why_today(state, vix_val):
    st.markdown("### Why today?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="factor-card">
            <div class="factor-head">1. Market stress</div>
            <div class="factor-body">VIX is around <b>{vix_val:.2f}</b>, classified as <b>{status_word(vix_val)}</b>. The app is not treating the market as panic.</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="factor-card">
            <div class="factor-head">2. Normal volatility</div>
            <div class="factor-body">ATR is <b>EUR {state['atr']:.2f}</b>. The target is <b>{state['base_m']:.2f} x ATR</b> below the latest completed close.</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="factor-card">
            <div class="factor-head">3. Historical base rate</div>
            <div class="factor-body">Similar setups filled <b>{state['stats1']['fill_rate']:.1f}%</b> next day and <b>{state['stats5']['fill_rate']:.1f}%</b> within five trading days.</div>
        </div>
        """, unsafe_allow_html=True)
    st.caption("Historical statistics describe past behaviour. They are not guarantees.")

def render_decision_confidence(state, vix_val):
    score = state["opportunity_v2"]
    regime = state["regime"]
    total = int(score.get("total", 0))
    deployment = state["deployment"]

    if total >= 80:
        score_meaning = "Strong setup: the model sees above-average conditions for disciplined execution."
    elif total >= 60:
        score_meaning = "Good/average setup: place the planned limit, but do not increase allocation unless dip rules trigger."
    elif total >= 40:
        score_meaning = "Weak setup: monitor, but the evidence is not strong enough to chase or overdeploy."
    else:
        score_meaning = "Poor setup: wait for a better entry or a new daily candle."

    st.markdown("### Decision confidence")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="regime-card">
            <div class="dip-label">Market regime</div>
            <div class="regime-big">{regime['regime']}</div>
            <div class="meaning-text"><b>Meaning:</b> This tells you whether the execution model should behave normally, cautiously, or defensively.</div>
            <div class="small-muted">Regime confidence {regime['confidence']}/100 | VIX {vix_val:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="dip-score">
            <div class="dip-label">Opportunity Score 2.0</div>
            <div class="dip-score-big">{total}/100</div>
            <div class="meaning-text"><b>Meaning:</b> {score_meaning}</div>
            <div class="small-muted">Combines stress, drawdown, dip rarity, trend and execution evidence.</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="deployment-card">
            <div class="dip-label">Cash deployment</div>
            <div class="deployment-big">EUR {deployment['total_amount']:,}</div>
            <div class="meaning-text"><b>Meaning:</b> This is the suggested amount for today's conditions under your ladder rules.</div>
            <div class="small-muted">Base EUR {deployment['base_amount']:,} + Extra EUR {deployment['extra_amount']:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("Why this score?"):
        breakdown = pd.DataFrame([
            {"Factor": k, "Score": round(v, 1), "Meaning": _score_factor_meaning(k)}
            for k, v in score.items() if k != "total"
        ])
        st.dataframe(breakdown, use_container_width=True, hide_index=True)
        st.write("Regime evidence:")
        for reason in regime.get("reasons", []):
            st.write(f"- {reason}")


def _score_factor_meaning(name):
    meanings = {
        "Market stress": "Higher score means volatility conditions support normal execution.",
        "Drawdown": "Higher score means the ETF is further below recent highs.",
        "Dip rarity": "Higher score means today's move is unusual for this ETF.",
        "Trend position": "Higher score means price is not stretched above its recent trend.",
        "Execution evidence": "Higher score means historical fill odds are near the preferred range.",
    }
    return meanings.get(name, "Contribution to the overall execution confidence.")

def render_live_execution_tracker(active_asset, state):
    st.markdown("### Live execution tracker")
    chart_df = fetch_chart_data(TICKERS[active_asset], period="1d", interval="5m")
    if chart_df.empty:
        st.info("No intraday data available yet. Use IBKR live bid/ask for execution.")
        return

    live_quote = fetch_live_quote(TICKERS[active_asset])
    current = float(live_quote.get("price") or chart_df["Close"].iloc[-1])
    low = float(chart_df["Low"].min()) if "Low" in chart_df.columns else current
    open_price = float(chart_df["Open"].iloc[0]) if "Open" in chart_df.columns and len(chart_df) else current
    target = float(state["target"])
    distance = current - target
    distance_pct = (distance / target) * 100 if target else 0.0
    low_distance = low - target
    low_distance_pct = (low_distance / target) * 100 if target else 0.0
    atr_value = float(state.get("atr") or 0.0)
    atr_distance = distance / atr_value if atr_value > 0 else np.nan
    reached = low <= target

    # Progress: 0 = far from target, 100 = touched/reached.
    start_gap = max(abs(open_price - target), abs(state.get("atr", 0)) * 1.5, 0.01)
    progress = 100 if reached else int(max(0, min(99, (1 - max(0, low_distance) / start_gap) * 100)))
    if reached:
        status = "Target reached"
        status_class = "deployment-card"
        fill_class = "progress-fill-good"
    elif distance_pct <= 0.25:
        status = "Very close"
        status_class = "warning-card"
        fill_class = "progress-fill-warn"
    elif distance_pct <= 0.75:
        status = "Waiting"
        status_class = "live-card"
        fill_class = "progress-fill"
    else:
        status = "Far"
        status_class = "warning-card"
        fill_class = "progress-fill"

    st.markdown(f"""
    <div class="dynamic-strip">
        <div class="dip-label">Target proximity radar</div>
        <div class="progress-bg"><div class="{fill_class}" style="width:{progress}%"></div></div>
        <div class="insight-text"><b>{status}</b> | distance to target EUR {distance:.2f} ({distance_pct:.2f}%). Today's low missed by EUR {low_distance:.2f} ({low_distance_pct:.2f}%). Current distance is {atr_distance:.2f}x ATR.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="live-card"><div class="dip-label">Current</div><div class="live-big">EUR {current:.2f}</div><div class="small-muted">{live_quote.get('source', 'Yahoo')} | 30s cache</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="live-card"><div class="dip-label">Today's low</div><div class="live-big">EUR {low:.2f}</div><div class="small-muted">Closest miss: EUR {low_distance:.2f}</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="live-card"><div class="dip-label">Target</div><div class="live-big">EUR {target:.2f}</div><div class="small-muted">{state['base_m']:.2f} x ATR below close</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="{status_class}"><div class="dip-label">Status</div><div class="deployment-big">{status}</div><div class="small-muted">Confirm actual fill in IBKR.</div></div>""", unsafe_allow_html=True)

def render_data_freshness(state):
    st.markdown("### Data freshness")
    live_status = "Live-ish" if state.get("live_is_liveish") else "Fallback / delayed"
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="live-card">
            <div class="dip-label">ETF live monitor</div>
            <div class="live-big">{live_status}</div>
            <div class="small-muted">Source: {state.get('live_source', 'unknown')} | refreshed by cache every ~30s</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="live-card">
            <div class="dip-label">Target engine</div>
            <div class="live-big">Daily candle</div>
            <div class="small-muted">Target based on completed daily close: {state.get('latest_data_date', '')}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="warning-card">
            <div class="dip-label">Final execution</div>
            <div class="deployment-big">IBKR</div>
            <div class="small-muted">Use IBKR live bid/ask before placing or adjusting orders.</div>
        </div>
        """, unsafe_allow_html=True)

def render_etf_priority_board(vix_val):
    st.markdown("### ETF priority board")
    cards = []
    for name in TICKERS.keys():
        s = calculate_state(name, vix_val)
        if s is not None:
            cards.append((name, s))
    cards = sorted(cards, key=lambda x: x[1]["opportunity_v2"]["total"], reverse=True)

    cols = st.columns(len(cards) if cards else 1)
    for idx, (name, s) in enumerate(cards):
        with cols[idx]:
            st.markdown(f"""
            <div class="priority-card">
                <div class="dip-label">{name}</div>
                <div class="priority-score">{s['opportunity_v2']['total']}/100</div>
                <div class="insight-text">
                    Signal: <b>{s['decision']}</b><br>
                    Target: <b>EUR {s['target']:.2f}</b><br>
                    Dip score: <b>{s['dip_stats']['opportunity_score']}/100</b><br>
                    Deploy: <b>EUR {s['deployment']['total_amount']:,}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_timing_analytics(active_asset, state):
    st.markdown("### Timing analytics")
    st.write(
        "This page now measures calendar timing by **limit-order touch probability**, not raw close price. "
        "That makes it ETF-specific and directly aligned with the execution model."
    )

    calendar = compute_calendar_timing(state["df_clean"], multiplier=state.get("base_m", 1.0))
    st.markdown("#### Calendar execution window")
    st.write(calendar.get("summary", "No summary available."))
    st.caption(
        "Method: probability that the ETF touched a limit order placed at the previous close minus the current ATR multiplier. "
        "If reliability is weak, treat the calendar signal as educational, not actionable."
    )

    fmt = {
        "Touch_probability_pct": "{:.1f}%",
        "Median_intraday_dip_pct": "{:.2f}%",
        "Average_intraday_dip_pct": "{:.2f}%",
        "Median_target_discount_pct": "{:.2f}%",
    }

    c1, c2, c3 = st.columns(3)
    with c1:
        day_table = calendar.get("day_table", pd.DataFrame()).head(10)
        st.write("Day-of-month candidates")
        if not day_table.empty:
            st.dataframe(day_table.style.format(fmt), use_container_width=True, hide_index=True)
    with c2:
        weekday_table = calendar.get("weekday_table", pd.DataFrame())
        st.write("Weekday evidence")
        if not weekday_table.empty:
            st.dataframe(weekday_table.style.format(fmt), use_container_width=True, hide_index=True)
    with c3:
        week_table = calendar.get("week_table", pd.DataFrame())
        st.write("Week-of-month evidence")
        if not week_table.empty:
            st.dataframe(week_table.style.format(fmt), use_container_width=True, hide_index=True)

    st.markdown("#### Intraday low timing")
    intraday_table, intraday_summary, tz_label = fetch_intraday_low_distribution(TICKERS[active_asset])
    st.write(intraday_summary)
    st.caption(f"Timestamp basis: {tz_label}. Yahoo intraday history is limited; use this as a recent-sample guide, not a multi-year tape study.")
    if not intraday_table.empty:
        st.dataframe(intraday_table.style.format({"Frequency (%)": "{:.1f}%"}), use_container_width=True, hide_index=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=intraday_table["Low window"], y=intraday_table["Frequency (%)"], name="Frequency"))
        fig.update_layout(height=320, margin=dict(l=6, r=6, t=6, b=6), yaxis=dict(title="% of sessions", ticksuffix="%"), xaxis=dict(title=f"Window ({tz_label})"), paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def render_previous_target_validation(state):
    st.markdown("### Yesterday's target validation")
    review = compute_previous_execution_review(state["df_clean"], multiplier=state.get("base_m", 1.0))
    if not review.get("available"):
        st.info(review.get("summary", "No previous review available."))
        return

    filled = review.get("filled", False)
    card = "deployment-card" if filled else "warning-card"
    status = review.get("status", "Unknown")
    st.markdown(f"""
    <div class="{card}">
        <div class="dip-label">Previous recommendation review</div>
        <div class="deployment-big">{status}</div>
        <div class="insight-text">
            Signal date: <b>{review['signal_date']}</b> | Outcome date: <b>{review['outcome_date']}</b><br>
            Target: <b>EUR {review['target']:.2f}</b> | Day low: <b>EUR {review['day_low']:.2f}</b> | Close: <b>EUR {review['day_close']:.2f}</b><br>
            Closest miss: <b>EUR {review['closest_distance_eur']:.2f}</b> ({review['closest_distance_pct']:.2f}%). Close distance: <b>EUR {review['close_distance_eur']:.2f}</b> ({review['close_distance_pct']:.2f}%).
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(review.get("summary", ""))

def render_journal_page(active_asset, state, vix_val):
    st.markdown("### Daily Execution Journal")
    st.write("Track each target, whether it filled, and how close the market came by the close. This is how PALI learns whether its targets are too aggressive or too loose.")

    render_previous_target_validation(state)

    from pathlib import Path
    journal_path = Path("pali_execution_journal.csv")
    chart_df = fetch_chart_data(TICKERS[active_asset], period="1d", interval="5m")
    live_quote = fetch_live_quote(TICKERS[active_asset])
    current = float(live_quote.get("price") or state.get("live_price") or state["spot"])
    day_low = float(chart_df["Low"].min()) if not chart_df.empty and "Low" in chart_df.columns else np.nan
    day_close_proxy = float(chart_df["Close"].iloc[-1]) if not chart_df.empty and "Close" in chart_df.columns else current
    target = float(state["target"])
    filled_today = bool(day_low <= target) if not np.isnan(day_low) else False
    closest_miss = (day_low - target) if not np.isnan(day_low) else np.nan
    close_distance = day_close_proxy - target

    row = {
        "timestamp_bahrain": (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
        "engine_version": "v5.8",
        "etf": active_asset,
        "target": round(target, 4),
        "completed_close_basis": round(float(state["spot"]), 4),
        "live_or_last_price": round(current, 4),
        "day_low": round(day_low, 4) if not np.isnan(day_low) else "",
        "day_close_proxy": round(day_close_proxy, 4),
        "filled_intraday": filled_today,
        "closest_miss_eur": round(closest_miss, 4) if not np.isnan(closest_miss) else "",
        "close_distance_eur": round(close_distance, 4),
        "decision": state["decision"],
        "opportunity_score": state["opportunity_v2"]["total"],
        "dip_score": state["dip_stats"]["opportunity_score"],
        "suggested_deployment": state["deployment"]["total_amount"],
        "market_regime": state["regime"]["regime"],
        "vix": round(float(vix_val), 2),
        "actual_fill_price": "",
        "notes": "",
    }

    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("Log today's target snapshot"):
            new_df = pd.DataFrame([row])
            if journal_path.exists():
                old = pd.read_csv(journal_path)
                out = pd.concat([old, new_df], ignore_index=True)
            else:
                out = new_df
            out.to_csv(journal_path, index=False)
            st.success("Snapshot logged to pali_execution_journal.csv")
    with c2:
        st.caption("For persistent cloud storage, connect this CSV logic to Google Sheets later. Streamlit local storage may reset after redeploy.")

    st.markdown("#### Today's snapshot preview")
    st.dataframe(pd.DataFrame([row]), use_container_width=True, hide_index=True)

    if journal_path.exists():
        journal = pd.read_csv(journal_path)
        st.markdown("#### Recent journal entries")
        st.dataframe(journal.tail(50), use_container_width=True, hide_index=True)
        csv = journal.to_csv(index=False).encode("utf-8")
        st.download_button("Download journal CSV", csv, "pali_execution_journal.csv", "text/csv")

        if len(journal) >= 3:
            st.markdown("#### Model calibration")
            filled_rate = journal["filled_intraday"].astype(str).str.lower().isin(["true", "1", "yes"]).mean() * 100
            miss_numeric = pd.to_numeric(journal.get("closest_miss_eur", pd.Series(dtype=float)), errors="coerce")
            avg_miss = miss_numeric[miss_numeric > 0].mean()
            c1, c2, c3 = st.columns(3)
            c1.metric("Logged fill rate", f"{filled_rate:.1f}%")
            c2.metric("Average positive miss", f"EUR {avg_miss:.2f}" if pd.notna(avg_miss) else "n/a")
            c3.metric("Records", f"{len(journal)}")
    else:
        st.info("No saved journal entries yet.")

def render_execution_playbook(state):
    st.markdown("### Execution playbook")
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown("""
        <div class="playbook-step">
            <div class="step-number">Step 1</div>
            <div class="step-title">After EU close</div>
            <div class="step-body">Use the latest completed candle to calculate tomorrow's target. Do not base tomorrow's target on an unfinished intraday candle.</div>
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown("""
        <div class="playbook-step">
            <div class="step-number">Step 2</div>
            <div class="step-title">EU open check</div>
            <div class="step-body">At the European open, confirm bid/ask, VIX regime, and whether the ETF is trading normally. If conditions are calm, place the DAY limit.</div>
        </div>
        """, unsafe_allow_html=True)
    with p3:
        st.markdown(f"""
        <div class="playbook-step">
            <div class="step-number">Step 3</div>
            <div class="step-title">If a deeper dip appears</div>
            <div class="step-body">If the ETF drops beyond its historical dip thresholds, use the ladder: base amount plus reserve deployment. Current suggested deployment is <b>EUR {state['deployment']['total_amount']:,}</b>.</div>
        </div>
        """, unsafe_allow_html=True)

def render_dip_engine(state):
    dip_stats = state["dip_stats"]
    deployment = state["deployment"]

    current_dip = dip_stats.get("current_dip_pct", 0.0)
    opportunity_score = dip_stats.get("opportunity_score", 0)
    total_sessions = dip_stats.get("total_sessions", 0)

    st.markdown("### Dynamic Dip Engine")
    st.caption("This section answers: if the ETF falls much more than expected, is the move normal noise or a historically rare opportunity?")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="dip-score">
            <div class="dip-label">Current intraday dip</div>
            <div class="dip-score-big">{current_dip:.2f}%</div>
            <div class="small-muted">Previous close to today's low.</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="dip-score">
            <div class="dip-label">Opportunity score</div>
            <div class="dip-score-big">{opportunity_score}/100</div>
            <div class="small-muted">Higher means the dip is rarer for this ETF.</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="deployment-card">
            <div class="dip-label">Suggested deployment</div>
            <div class="deployment-big">EUR {deployment['total_amount']:,}</div>
            <div class="small-muted">Base EUR {deployment['base_amount']:,} + Extra EUR {deployment['extra_amount']:,}</div>
        </div>
        """, unsafe_allow_html=True)

    if deployment["extra_amount"] > 0:
        st.markdown(f"""
        <div class="warning-card"><b>Dip trigger active:</b> {deployment['explanation']}</div>
        """, unsafe_allow_html=True)
    else:
        st.caption(deployment["explanation"])

    st.write(f"Historical sample: **{total_sessions:,} trading sessions**.")

    threshold_table = dip_stats.get("threshold_table", pd.DataFrame())
    recovery_table = dip_stats.get("recovery_table", pd.DataFrame())

    t1, t2 = st.tabs(["Dip probabilities", "Recovery after dips"])
    with t1:
        if not threshold_table.empty:
            st.dataframe(threshold_table.style.format({
                "Historical frequency (%)": "{:.2f}%",
                "Average dip on triggered days (%)": "{:.2f}%",
                "Median same-day close return (%)": "{:.2f}%",
            }), use_container_width=True)
        else:
            st.info("Not enough data to compute dip probabilities.")
    with t2:
        if not recovery_table.empty:
            st.dataframe(recovery_table.style.format({
                "Average forward return (%)": "{:.2f}%",
                "Median forward return (%)": "{:.2f}%",
                "Positive outcome rate (%)": "{:.1f}%",
            }), use_container_width=True)
        else:
            st.info("Not enough data to compute recovery statistics.")

def render_etf_matrix(vix_val):
    rows = []
    for name in TICKERS.keys():
        state = calculate_state(name, vix_val)
        if state is None:
            continue
        rows.append({
            "ETF": name,
            "Now": f"EUR {state['spot']:.2f}",
            "Target": f"EUR {state['target']:.2f}",
            "Gap": f"{state['gap_pct']:.2f}%",
            "Dip Score": state["dip_stats"]["opportunity_score"],
            "Deploy": f"EUR {state['deployment']['total_amount']:,}",
            "Signal": state["decision"],
        })
    if rows:
        st.dataframe(pd.DataFrame(rows).set_index("ETF"), use_container_width=True, height=180)

def render_market_intelligence(market_rows):
    st.markdown("### Market Intelligence")
    st.write("Raw numbers are not enough. This page explains what each market signal means for ETF execution.")

    cols = st.columns(3)
    for i, row in enumerate(market_rows):
        with cols[i % 3]:
            chg = float(row["Change"])
            direction = "higher" if chg >= 0 else "lower"
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">{row['Market']}</div>
                <div class="insight-big">{row['Value']}</div>
                <div class="insight-text"><b>{chg:.2f}% {direction}</b><br>{MARKET_EXPLAINERS.get(row['Market'], 'Market context indicator.')}</div>
            </div>
            """, unsafe_allow_html=True)

def render_learn_page(active_asset, state, vix_val):
    st.markdown("### Learn the Decision")
    st.write("This page turns today's recommendation into a short lesson. The numbers below use the current selected ETF.")

    with st.expander("Lesson 1 - What is PALI estimating?", expanded=True):
        st.write(
            f"PALI estimates a **next-day intraday buy zone** for {active_asset}. It starts from the latest completed close of "
            f"**EUR {state['spot']:.2f}** and positions the limit order below that close using recent volatility. "
            "It is not trying to predict tomorrow's closing price."
        )
    with st.expander("Lesson 2 - Why use ATR?"):
        st.write(
            f"ATR is the recent average daily trading range. For {active_asset}, ATR is **EUR {state['atr']:.2f}**. "
            f"The current target uses **{state['base_m']:.2f} x ATR**, meaning the model waits for a normal pullback rather than chasing the market."
        )
    with st.expander("Lesson 3 - Why not always buy immediately?"):
        st.write(
            f"Buying immediately around **EUR {state['spot']:.2f}** guarantees execution. Waiting at **EUR {state['target']:.2f}** may improve price, "
            f"but historically similar next-day setups filled only **{state['stats1']['fill_rate']:.1f}%** of the time. This is the trade-off: certainty versus price improvement."
        )
    with st.expander("Lesson 4 - What is a meaningful dip for this ETF?"):
        st.write(
            f"A fixed -5% rule is too crude. V60A, VNGA80, and VWCE have different risk profiles. PALI therefore calculates dip rarity separately for each ETF. "
            f"The current opportunity score is **{state['dip_stats']['opportunity_score']}/100** for {active_asset}."
        )
    with st.expander("Lesson 5 - When should I monitor and place the order?"):
        st.write(
            "Use the app after the European close to calculate the next target. During the next session, monitor after the first noisy minutes of the open and again during the US-Europe overlap. "
            "If VIX remains in the same regime, keep the target. If VIX jumps into elevated or stress territory before placing the order, recalculate and become more patient."
        )
    with st.expander("Lesson 6 - What could go wrong?"):
        st.write(
            "A strong rally may leave your order unfilled. A sudden news shock may make historical conditions less relevant. ETF bid/ask spreads may widen. "
            "That is why PALI is a decision-support system, not an autopilot."
        )

def render_quant_lab(state, df_clean):
    st.markdown("### Quant Lab")
    st.write("Research view: use this page to understand the trade-off between fill probability, expected discount, dip rarity, and reserve deployment.")

    render_dip_engine(state)

    st.markdown("### Execution style comparison")
    matrix_df = compute_tab3_matrices(df_clean)

    def style_snapshot(label, multiplier, note):
        nearest = min(matrix_df.index, key=lambda x: abs(float(x) - multiplier))
        row = matrix_df.loc[nearest]
        fill = float(row["Next-Day Fill Rate (%)"])
        saving = float(row["Average Saving (%)"])
        bar = max(3, min(100, fill))
        st.markdown(f"""
        <div class="style-card">
            <div class="style-title">{label}</div>
            <div class="small-muted">ATR multiplier: {nearest:.1f}</div>
            <div class="bar-bg"><div class="bar-fill" style="width:{bar:.0f}%"></div></div>
            <div class="insight-text">Fill probability: <b>{fill:.1f}%</b><br>Average saving: <b>{saving:.2f}%</b><br>{note}</div>
        </div>
        """, unsafe_allow_html=True)

    s1, s2, s3 = st.columns(3)
    with s1:
        style_snapshot("Aggressive", 0.6, "Higher chance of filling, smaller discount.")
    with s2:
        style_snapshot("Balanced", 1.0, "Default execution style for normal markets.")
    with s3:
        style_snapshot("Patient", 1.6, "Lower chance of filling, larger expected discount.")

    st.markdown("### Full ATR table")
    st.dataframe(matrix_df.style.format({
        "Next-Day Fill Rate (%)": "{:.1f}%",
        "Five-Day Fill Rate (%)": "{:.1f}%",
        "Average Saving (%)": "{:.2f}%",
        "Median Saving (%)": "{:.2f}%",
        "Average Missed Move (%)": "{:.2f}%",
    }), use_container_width=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=matrix_df.index, y=matrix_df["Next-Day Fill Rate (%)"], mode="lines+markers", name="Next-day fill"))
    fig.add_trace(go.Scatter(x=matrix_df.index, y=matrix_df["Five-Day Fill Rate (%)"], mode="lines+markers", name="5-day fill"))
    fig.add_trace(go.Scatter(x=matrix_df.index, y=matrix_df["Average Saving (%)"], mode="lines+markers", name="Average saving"))
    fig.update_layout(height=420, margin=dict(l=6, r=6, t=6, b=6), hovermode="x unified", xaxis=dict(title="ATR multiplier"), yaxis=dict(title="Percent", ticksuffix="%"), paper_bgcolor="white", plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def render_model_health(state, market_rows):
    st.markdown("### Model health")
    feed_ok = any(float(r.get("Value", "0").replace(",", "") if isinstance(r.get("Value"), str) else r.get("Value", 0)) > 0 for r in market_rows)
    live_ok = bool(state.get("live_is_liveish", False))
    sample = len(state.get("df_clean", pd.DataFrame()))
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="{'deployment-card' if feed_ok else 'warning-card'}"><div class="dip-label">Market feed</div><div class="deployment-big">{'Healthy' if feed_ok else 'Check'}</div><div class="small-muted">Yahoo/yfinance quotes.</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="{'deployment-card' if live_ok else 'warning-card'}"><div class="dip-label">ETF monitor</div><div class="deployment-big">{'Live-ish' if live_ok else 'Fallback'}</div><div class="small-muted">Source: {state.get('live_source', 'unknown')}</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="live-card"><div class="dip-label">Backtest sample</div><div class="live-big">{sample:,}</div><div class="small-muted">Completed daily rows.</div></div>""", unsafe_allow_html=True)
