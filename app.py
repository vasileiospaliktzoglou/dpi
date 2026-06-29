import datetime

import streamlit as st

from config import TICKERS, BENCHMARKS, APP_TITLE, APP_VERSION
from styles import load_css
from helpers import fetch_live_quote
from core import calculate_state, compute_market_sentiment, status_word
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
)


st.set_page_config(page_title=f"{APP_TITLE} v{APP_VERSION}", layout="wide", initial_sidebar_state="expanded")
st.markdown(load_css(), unsafe_allow_html=True)


if "active_asset" not in st.session_state:
    st.session_state.active_asset = "V60A"
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "layout_mode" not in st.session_state:
    st.session_state.layout_mode = "Desktop"


# ---------------- SIDEBAR ----------------
st.sidebar.title(APP_TITLE)
st.sidebar.caption(f"v{APP_VERSION} modular | dynamic dashboard | journal-ready")
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
st.markdown(f"### {APP_TITLE}")
active_asset = st.radio("ETF", list(TICKERS.keys()), key="active_asset", horizontal=True)
page = st.radio("Page", ["Dashboard", "Market Intelligence", "Learn", "Quant Lab", "Timing", "Journal"], key="page", horizontal=True)


# ---------------- DATA ----------------
state = calculate_state(active_asset, vix_val)
if state is None:
    st.error("Data pipeline timeout.")
    st.stop()

df_clean = state["df_clean"]


# ---------------- ROUTING ----------------
if page == "Dashboard":
    st.markdown(
        f"### {active_asset} | {state['decision']} | Target EUR {state['target']:.2f} | "
        f"Market {status_word(vix_val)} | Data {state['latest_data_date']}"
    )

    # v6.6 layout principle:
    # The chart is isolated as the main reading surface.
    # All execution cards, explanations and sentiment panels sit in their own sections below it.
    if layout_mode == "Mobile":
        st.markdown('<div class="chart-zone-title">Main execution chart</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-zone-subtitle">Read the price action first. The action cards are below the chart.</div>', unsafe_allow_html=True)
        with st.container(border=True):
            render_chart(active_asset, state["target"], atr=state.get("atr"))

        st.markdown('<div class="dashboard-section-title">Execution command</div>', unsafe_allow_html=True)
        render_execution_plan(active_asset, state)
        render_live_execution_tracker(active_asset, state)

        st.markdown('<div class="dashboard-section-title">Market context</div>', unsafe_allow_html=True)
        render_market_sentiment(sentiment)
        render_decision_confidence(state, vix_val)

        with st.container(border=True):
            render_previous_target_validation(state)
        with st.container(border=True):
            render_data_freshness(state)
        with st.container(border=True):
            render_why_today(state, vix_val)
        with st.container(border=True):
            render_dip_engine(state)
        with st.container(border=True):
            render_execution_playbook(state)
        with st.container(border=True):
            render_etf_priority_board(vix_val)
        with st.container(border=True):
            render_model_health(state, market_rows)
    else:
        st.markdown('<div class="chart-zone-title">Main execution chart</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-zone-subtitle">The chart is deliberately separated from the cards so it remains readable. Use it first to judge price action, distance to target and todays movement.</div>', unsafe_allow_html=True)
        chart_left, chart_center, chart_right = st.columns([0.10, 1.80, 0.10])
        with chart_center:
            with st.container(border=True):
                render_chart(active_asset, state["target"], atr=state.get("atr"))

        st.markdown('<div class="major-section-separator"></div>', unsafe_allow_html=True)
        st.markdown('<div class="dashboard-section-title">Execution command center</div>', unsafe_allow_html=True)
        command_col, tracker_col = st.columns([1.0, 1.0])
        with command_col:
            render_execution_plan(active_asset, state)
        with tracker_col:
            render_live_execution_tracker(active_asset, state)

        st.markdown('<div class="dashboard-section-title">Market context and confidence</div>', unsafe_allow_html=True)
        sentiment_col, confidence_col = st.columns([1.0, 1.0])
        with sentiment_col:
            render_market_sentiment(sentiment)
        with confidence_col:
            render_decision_confidence(state, vix_val)

        st.markdown('<div class="dashboard-section-title">Review and explanation</div>', unsafe_allow_html=True)
        review_col, why_col = st.columns([1.0, 1.0])
        with review_col:
            with st.container(border=True):
                render_previous_target_validation(state)
            with st.container(border=True):
                render_data_freshness(state)
        with why_col:
            with st.container(border=True):
                render_why_today(state, vix_val)

        st.markdown('<div class="dashboard-section-title">Deployment and monitoring</div>', unsafe_allow_html=True)
        dip_col, playbook_col = st.columns([1.0, 1.0])
        with dip_col:
            with st.container(border=True):
                render_dip_engine(state)
        with playbook_col:
            with st.container(border=True):
                render_execution_playbook(state)

        priority_col, health_col = st.columns([1.0, 1.0])
        with priority_col:
            with st.container(border=True):
                render_etf_priority_board(vix_val)
        with health_col:
            with st.container(border=True):
                render_model_health(state, market_rows)

elif page == "Market Intelligence":
    render_market_sentiment(sentiment)
    render_market_intelligence(market_rows)
    render_etf_priority_board(vix_val)
    st.markdown("### ETF Watch")
    render_etf_matrix(vix_val)

elif page == "Learn":
    render_learn_page(active_asset, state, vix_val)

elif page == "Quant Lab":
    render_quant_lab(state, df_clean)

elif page == "Timing":
    render_timing_analytics(active_asset, state)

elif page == "Journal":
    render_journal_page(active_asset, state, vix_val)
