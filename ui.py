import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import TICKERS
from core import calculate_decision, calculate_all_states


def card_class(decision: str) -> str:
    if "BUY" in decision and "WAIT" not in decision:
        return "buy-card"
    if decision == "LIMIT BUY":
        return "wait-card"
    if decision == "WAIT":
        return "neutral-card"
    return "metric-card"


def render_market_sentiment(sentiment):
    st.markdown("### Market regime")
    c1, c2 = st.columns([0.7, 2.0])
    with c1:
        st.markdown(f"""
        <div class="neutral-card">
            <div class="label">Regime</div>
            <div class="big">{sentiment['label']}</div>
            <div class="small-muted">Score {sentiment['score']}/100</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='section-note'>{' · '.join(sentiment.get('reasons', []))}</div>", unsafe_allow_html=True)


def render_decision_engine(state):
    st.markdown("### Today's execution decision")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="{card_class(state['decision'])}">
            <div class="label">Signal</div>
            <div class="big">{state['decision']}</div>
            <div class="small-muted">Confidence: {state['confidence']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Live / latest price</div>
            <div class="big">€{state['live_price']:.3f}</div>
            <div class="small-muted">Move vs last close: {state['change_from_prev']:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="buy-card">
            <div class="label">Suggested limit</div>
            <div class="big">€{state['suggested_limit']:.3f}</div>
            <div class="small-muted">Confirm IBKR bid/ask before trading.</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        amount = state.get('base_amount', 0)
        shares = state.get('suggested_shares', 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Planned order</div>
            <div class="big">€{amount:,.0f}</div>
            <div class="small-muted">Approx. {shares:,} shares at suggested limit.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<div class='section-note'><b>Action:</b> {state['action']}</div>", unsafe_allow_html=True)


def render_price_ladder(state):
    st.markdown("### Price ladder")
    levels = pd.DataFrame(
        [{"Zone": k, "Price": v, "Distance from live (%)": ((state['live_price'] / v) - 1) * 100 if v else 0.0} for k, v in state["levels"].items()]
    )
    st.dataframe(levels.style.format({"Price": "€{:.3f}", "Distance from live (%)": "{:.2f}%"}), use_container_width=True, hide_index=True)


def render_probability_box(state):
    st.markdown("### Probability context")
    s = state["stats"]
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("Typical daily move", f"±{s['median_abs_return_pct']:.2f}%", "Median absolute daily close move."),
        ("Large daily move", f"±{s['large_abs_return_pct']:.2f}%", "85th percentile absolute move."),
        ("Lower next day", f"{s['prob_lower_next_day']:.0f}%", f"Analog sample: {s['sample']} sessions."),
        ("Median next-day low", f"{s['median_next_low_pct']:.2f}%", "Typical next-session intraday low after similar days."),
    ]
    for col, (label, value, note) in zip([c1, c2, c3, c4], metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">{label}</div>
                <div class="big">{value}</div>
                <div class="small-muted">{note}</div>
            </div>
            """, unsafe_allow_html=True)


def render_etf_priority_board():
    st.markdown("### ETF priority board")
    states = [s for s in calculate_all_states().values() if s]
    if not states:
        st.warning("No ETF data loaded.")
        return
    rank = {"EXCEPTIONAL BUY": 5, "STRONG BUY": 4, "BUY": 3, "LIMIT BUY": 2, "WAIT": 1}
    states = sorted(states, key=lambda s: (rank.get(s["decision"], 0), -s["distance_to_levels"].get("Good buy", 0)), reverse=True)
    cols = st.columns(len(states))
    for col, s in zip(cols, states):
        with col:
            st.markdown(f"""
            <div class="{card_class(s['decision'])}">
                <div class="label">{s['asset']}</div>
                <div class="big">{s['decision']}</div>
                <div class="small-muted">Live €{s['live_price']:.3f}<br>Limit €{s['suggested_limit']:.3f}</div>
            </div>
            """, unsafe_allow_html=True)


def render_chart(state):
    df = state["df"].tail(180).copy()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=state["asset"]))
    fig.add_hline(y=state["levels"]["Good buy"], line_dash="dot", annotation_text="Good buy", annotation_position="bottom right")
    fig.add_hline(y=state["levels"]["Strong buy"], line_dash="dash", annotation_text="Strong buy", annotation_position="bottom right")
    fig.add_hline(y=state["suggested_limit"], line_dash="solid", annotation_text="Suggested limit", annotation_position="top right")
    fig.update_layout(height=480, margin=dict(l=5, r=5, t=20, b=5), xaxis_rangeslider_visible=False, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_market_watch(market_rows):
    st.markdown("### Market watch")
    df = pd.DataFrame(market_rows)
    if not df.empty:
        st.dataframe(df.style.format({"Change": "{:.2f}%"}), use_container_width=True, hide_index=True)


def render_quant_lab(state):
    st.markdown("### Quant Lab: expected +/- and limit logic")
    st.write("This page converts historical daily behaviour into practical limit-order zones for your monthly DCA.")
    render_probability_box(state)
    render_price_ladder(state)

    df = state["df"].copy()
    thresholds = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00]
    rows = []
    for th in thresholds:
        touches = (-df["Low from Prev Close %"] >= th).mean() * 100
        closes_down = (df["Close from Prev Close %"] <= -th).mean() * 100
        rows.append({"Dip threshold": f"-{th:.2f}%", "Touched intraday (%)": touches, "Closed beyond threshold (%)": closes_down})
    tdf = pd.DataFrame(rows)
    st.dataframe(tdf.style.format({"Touched intraday (%)": "{:.1f}%", "Closed beyond threshold (%)": "{:.1f}%"}), use_container_width=True, hide_index=True)


def render_journal_page(state):
    st.markdown("### Journal-ready snapshot")
    row = {
        "timestamp_bahrain": (dt.datetime.utcnow() + dt.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
        "asset": state["asset"],
        "decision": state["decision"],
        "live_price": round(state["live_price"], 4),
        "suggested_limit": round(state["suggested_limit"], 4),
        "planned_amount": state["base_amount"],
        "approx_shares": state["suggested_shares"],
        "confidence": state["confidence"],
    }
    st.dataframe(pd.DataFrame([row]), use_container_width=True, hide_index=True)
    st.caption("Copy this row into your trading journal after execution.")
