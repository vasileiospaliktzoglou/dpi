import datetime

import streamlit as st

from config import TICKERS, BENCHMARKS, APP_TITLE, APP_VERSION
from styles import load_css
from helpers import fetch_live_quote
from core import calculate_state, compute_market_sentiment, status_word, confidence_word
from charts import render_chart
from ui import (
    render_market_sentiment,
    render_decision_confidence,
    render_execution_plan,
    render_live_execution_tracker,
    render_previous_target_validation,
    render_data_freshness,
    render_why_today,
    render_dip_engine,
    render_execution_playbook,
    render_etf_priority_board,
    render_model_health,
    render_market_intelligence,
    render_etf_matrix,
    render_learn_page,
    render_quant_lab,
    render_timing_analytics,
    render_journal_page,
    render_end_of_day_page,
    render_daily_intelligence_page,
)

st.set_page_config(page_title=f"{APP_TITLE} v{APP_VERSION}", layout="wide", initial_sidebar_state="expanded")
st.markdown(load_css(), unsafe_allow_html=True)


if "active_asset" not in st.session_state:
    st.session_state.active_asset = "V60A"
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "layout_mode" not in st.session_state:
    st.session_state.layout_mode = "Desktop"


def fmt_eur(value):
    try:
        return f"EUR {float(value):,.2f}"
    except Exception:
        return "EUR --"


def sentiment_plain_label(score):
    if score <= 24:
        return "Very cautious", "Markets are under broad selling pressure. Keep risk controlled."
    if score <= 44:
        return "Cautious", "Markets are weak but orderly. Limit orders may have a better chance of filling."
    if score <= 69:
        return "Mixed", "The market has no clear direction. Use the standard plan and avoid chasing."
    if score <= 84:
        return "Positive", "Buyers have the advantage. Your limit may be harder to reach."
    return "Very positive", "Strong buying across markets. Wait for your price rather than chasing."


def render_topbar():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    st.markdown(
        f"""
        <div class="app-topbar">
            <div>
                <div class="app-title">{APP_TITLE}</div>
                <div class="app-subtitle">Live execution intelligence for disciplined ETF deployment</div>
            </div>
            <div class="live-pill"><span class="live-dot"></span> Auto-refresh ready &nbsp; | &nbsp; {now.strftime('%d %b %Y, %H:%M Bahrain')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_strip(asset, state, sentiment, vix_val):
    confidence = confidence_word(state.get("suitability", 0))
    live_price = state.get("live_price", state.get("spot"))
    distance = live_price - state["target"]
    distance_pct = (distance / state["target"]) * 100 if state.get("target") else 0
    sent_label, sent_text = sentiment_plain_label(int(sentiment.get("score", 50)))

    cols = st.columns(5)
    with cols[0]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Target day limit</div>
            <div class="kpi-main green">{fmt_eur(state['target'])}</div>
            <div class="kpi-note">Tomorrow's execution reference after IBKR bid/ask check.</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Live ETF price</div>
            <div class="kpi-main blue">{fmt_eur(live_price)}</div>
            <div class="kpi-note">{asset} quote: {state.get('live_source','live-ish')}.</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        tone = "green" if distance_pct <= 0.25 else "amber" if distance_pct <= 0.75 else "red"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Distance to target</div>
            <div class="kpi-main {tone}">{distance_pct:.2f}%</div>
            <div class="kpi-note">{fmt_eur(distance)} above target. Lower is closer to fill.</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Next-day fill base rate</div>
            <div class="kpi-main">{state['stats1']['fill_rate']:.1f}%</div>
            <div class="kpi-note">Historical fill rate for similar ATR setup.</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[4]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Sentiment</div>
            <div class="kpi-main {'green' if sentiment.get('score',50)>=70 else 'amber' if sentiment.get('score',50)>=25 else 'red'}">{sent_label}</div>
            <div class="kpi-note">{sent_text} VIX {vix_val:.2f}.</div>
        </div>
        """, unsafe_allow_html=True)


def render_command_center(asset, state):
    shares = int(20000 / state["target"]) if state.get("target") else 0
    saving = (state.get("live_price", state["spot"]) - state["target"]) * shares
    confidence = confidence_word(state.get("suitability", 0))
    live_price = state.get("live_price", state.get("spot"))

    st.markdown(
        f"""
        <div class="command-card">
            <div class="command-grid">
                <div class="command-left">
                    <div class="command-label">Today's execution command</div>
                    <div class="command-action">{state['decision']}</div>
                    <div class="command-price">{fmt_eur(state['target'])}</div>
                    <div class="command-text">
                        Use this as tomorrow's DAY limit reference after confirming live IBKR bid/ask.
                        This is an execution target, not a prediction of tomorrow's close.
                    </div>
                    <div class="code-strip">BUY {asset} IBIS LMT {state['target']:.2f} DAY</div>
                    <div class="small-muted" style="margin-top:8px;">
                        ETF monitor quote: {state.get('live_source','live-ish')} | change {state.get('live_change_pct',0):.2f}% | Yahoo/yfinance can be delayed.
                    </div>
                </div>
                <div>
                    <div class="mini-grid">
                        <div class="mini-cell"><div class="mini-label">ETF</div><div class="mini-value">{asset}</div></div>
                        <div class="mini-cell"><div class="mini-label">Live ETF</div><div class="mini-value">{fmt_eur(live_price)}</div></div>
                        <div class="mini-cell"><div class="mini-label">Improvement</div><div class="mini-value">{state['gap_pct']:.2f}%</div></div>
                        <div class="mini-cell"><div class="mini-label">Next-day fill</div><div class="mini-value">{state['stats1']['fill_rate']:.1f}%</div></div>
                        <div class="mini-cell"><div class="mini-label">Confidence</div><div class="mini-value">{confidence}</div></div>
                        <div class="mini-cell"><div class="mini-label">EUR 20k saving</div><div class="mini-value">EUR {saving:.0f}</div></div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_etf_decision_cards(active_asset, active_state, vix_val):
    """Compact ETF cards used as the single plan overview on the dashboard."""
    cards = []
    for ticker in TICKERS.keys():
        try:
            state_i = active_state if ticker == active_asset else calculate_state(ticker, vix_val)
            if state_i is None:
                continue
            live = float(state_i.get("live_price", state_i.get("spot", 0)) or 0)
            target = float(state_i.get("target", 0) or 0)
            distance = ((live - target) / target * 100) if target else 0
            fill = float(state_i.get("stats1", {}).get("fill_rate", 0) or 0)
            action = state_i.get("decision", "WAIT")
            tone = "buy" if "BUY" in action.upper() else "watch" if distance <= 0.75 else "wait"
            cards.append((ticker, state_i, live, target, distance, fill, action, tone))
        except Exception:
            continue

    cols = st.columns(max(1, len(cards)))
    for col, (ticker, state_i, live, target, distance, fill, action, tone) in zip(cols, cards):
        with col:
            active = " active" if ticker == active_asset else ""
            st.markdown(f"""
            <div class="pro-etf-card {tone}{active}">
                <div class="pro-etf-top">
                    <div>
                        <div class="pro-etf-label">{ticker}</div>
                        <div class="pro-etf-role">Core deployment candidate</div>
                    </div>
                    <div class="pro-badge {tone}">{action}</div>
                </div>
                <div class="pro-etf-price">{fmt_eur(target)}</div>
                <div class="pro-etf-sub">Target limit reference</div>
                <div class="pro-meter"><div style="width:{min(100,max(5,100-distance*18)):.0f}%"></div></div>
                <div class="pro-etf-grid">
                    <div><span>Live</span><b>{fmt_eur(live)}</b></div>
                    <div><span>Gap</span><b>{distance:.2f}%</b></div>
                    <div><span>Fill</span><b>{fill:.1f}%</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_dashboard(asset, state, sentiment, vix_val, market_rows):
    """v6.10.4 consolidated dashboard: one decision, one plan, less duplication."""
    render_topbar()
    live_price = float(state.get("live_price", state.get("spot", 0)) or 0)
    target = float(state.get("target", 0) or 0)
    distance_pct = ((live_price - target) / target * 100) if target else 0
    sent_label, sent_text = sentiment_plain_label(int(sentiment.get("score", 50)))
    confidence = confidence_word(state.get("suitability", 0))
    next_fill = float(state.get("stats1", {}).get("fill_rate", 0) or 0)
    status_tone = "green" if distance_pct <= 0.25 else "amber" if distance_pct <= 0.75 else "red"

    st.markdown(f"""
    <div class="pro-hero">
        <div class="pro-hero-left">
            <div class="pro-kicker">Today’s decision</div>
            <div class="pro-title">{state['decision']}</div>
            <div class="pro-subtitle">Use the target as a DAY limit reference after checking the live IBKR bid/ask. The dashboard only shows the current decision; the explanation lives in Daily Intelligence.</div>
            <div class="pro-command">BUY {asset} IBIS LMT {target:.2f} DAY</div>
        </div>
        <div class="pro-hero-right">
            <div class="pro-target-label">Target limit</div>
            <div class="pro-target">{fmt_eur(target)}</div>
            <div class="pro-status {status_tone}">{distance_pct:.2f}% from target</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"<div class='pro-stat'><span>Live price</span><b>{fmt_eur(live_price)}</b><em>{state.get('live_source','live-ish')}</em></div>", unsafe_allow_html=True)
    with k2:
        st.markdown(f"<div class='pro-stat'><span>Market regime</span><b>{sent_label}</b><em>{sent_text}</em></div>", unsafe_allow_html=True)
    with k3:
        st.markdown(f"<div class='pro-stat'><span>Next-day fill</span><b>{next_fill:.1f}%</b><em>Similar historical setups</em></div>", unsafe_allow_html=True)
    with k4:
        st.markdown(f"<div class='pro-stat'><span>Model confidence</span><b>{confidence}</b><em>Suitability score {state.get('suitability',0)}/100</em></div>", unsafe_allow_html=True)

    st.markdown("<div class='pro-section'><div><b>ETF deployment board</b><span> One card per ETF. No repeated commentary.</span></div></div>", unsafe_allow_html=True)
    render_etf_decision_cards(asset, state, vix_val)

    left, right = st.columns([1.55, 1])
    with left:
        st.markdown("<div class='pro-section'><div><b>Price vs target</b><span> The only chart needed on the dashboard.</span></div></div>", unsafe_allow_html=True)
        st.markdown("<div class='pro-chart-shell'>", unsafe_allow_html=True)
        render_chart(asset, target, atr=state.get("atr"))
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='pro-section'><div><b>Next action</b><span> Operational checklist.</span></div></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="pro-plan-card">
            <div class="pro-plan-step"><b>1</b><span>Check IBKR live bid/ask for {asset}</span></div>
            <div class="pro-plan-step"><b>2</b><span>Use {fmt_eur(target)} only if spread is normal</span></div>
            <div class="pro-plan-step"><b>3</b><span>Do not chase if price stays above target</span></div>
            <div class="pro-plan-step"><b>4</b><span>Review Daily Intelligence after Xetra close</span></div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("Diagnostics and explanation", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            render_market_sentiment(sentiment)
        with c2:
            render_decision_confidence(state, vix_val)
        with c3:
            render_live_execution_tracker(asset, state)
        e1, e2 = st.columns(2)
        with e1:
            render_why_today(state, vix_val)
        with e2:
            render_data_freshness(state)


# ---------------- SIDEBAR ----------------
st.sidebar.title(APP_TITLE)
st.sidebar.caption(f"v{APP_VERSION} professional command center")
layout_mode = st.sidebar.radio("Layout", ["Desktop", "Mobile"], key="layout_mode", horizontal=True)

now_bahrain = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
st.sidebar.caption(now_bahrain.strftime("%d %b %Y | %H:%M Bahrain"))

st.sidebar.markdown("### Market Watch")
vix_val = 15.0
market_rows = []

for name, symbol in BENCHMARKS.items():
    q = fetch_live_quote(symbol)
    val = float(q.get("price") or 0.0)
    chg = float(q.get("change_pct") or 0.0)
    if symbol == "^VIX" and val > 0:
        vix_val = val

    color = "#10b981" if chg >= 0 else "#ef4444"
    arrow = "+" if chg >= 0 else ""
    display_val = f"{val:.4f}" if name == "EURUSD" else f"{val:,.2f}"

    st.sidebar.markdown(
        f"""
        <div class="market-row"><b>{name}</b><span>{display_val} <span style="color:{color};font-weight:800;">{arrow}{chg:.2f}%</span></span></div>
        """,
        unsafe_allow_html=True,
    )
    market_rows.append({"Market": name, "Value": display_val, "Change": chg})

sentiment = compute_market_sentiment(market_rows, vix_val)
st.sidebar.caption("Market Watch + ETF monitor use live-ish Yahoo quotes with 30s cache. Execution target uses completed daily candles. Confirm IBKR live bid/ask before trading.")


# ---------------- MAIN CONTROLS ----------------
active_asset = st.radio("ETF", list(TICKERS.keys()), key="active_asset", horizontal=True)
page = st.radio("Workspace", ["Dashboard", "Daily Intelligence", "EOD Plan", "Journal", "Research Lab"], key="page", horizontal=True)


# ---------------- DATA ----------------
state = calculate_state(active_asset, vix_val)
if state is None:
    st.error("Data pipeline timeout.")
    st.stop()

df_clean = state["df_clean"]


# ---------------- ROUTING ----------------
if page == "Dashboard":
    render_dashboard(active_asset, state, sentiment, vix_val, market_rows)

elif page == "Daily Intelligence":
    render_topbar()
    render_daily_intelligence_page(active_asset, state, sentiment, vix_val, market_rows)

elif page == "EOD Plan":
    render_topbar()
    render_end_of_day_page(active_asset, state, sentiment, vix_val, market_rows)

elif page == "Journal":
    render_topbar()
    render_journal_page(active_asset, state, vix_val)

elif page == "Research Lab":
    render_topbar()
    st.markdown("<div class='page-intro'><b>Research Lab</b><br/>Advanced diagnostics are grouped here so the dashboard remains clean.</div>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["Market", "ETF Matrix", "Quant", "Timing"])
    with tab1:
        render_market_sentiment(sentiment)
        render_market_intelligence(market_rows)
        render_etf_priority_board(vix_val)
    with tab2:
        render_etf_matrix(vix_val)
    with tab3:
        render_quant_lab(state, df_clean)
    with tab4:
        render_timing_analytics(active_asset, state)
