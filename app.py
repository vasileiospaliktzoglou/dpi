import datetime as dt

import streamlit as st

from config import APP_TITLE, APP_VERSION, TICKERS, BENCHMARKS
from core import calculate_decision, compute_market_sentiment, status_word
from helpers import fetch_live_quote
from styles import load_css
from ui import (
    render_market_sentiment,
    render_decision_engine,
    render_price_ladder,
    render_probability_box,
    render_etf_priority_board,
    render_chart,
    render_market_watch,
    render_quant_lab,
    render_journal_page,
)

st.set_page_config(page_title=f"{APP_TITLE} v{APP_VERSION}", layout="wide", initial_sidebar_state="expanded")
st.markdown(load_css(), unsafe_allow_html=True)

if "active_asset" not in st.session_state:
    st.session_state.active_asset = "VNGA80"
if "page" not in st.session_state:
    st.session_state.page = "Decision Engine"

st.sidebar.title(APP_TITLE)
st.sidebar.caption(f"v{APP_VERSION}")
now_bahrain = dt.datetime.utcnow() + dt.timedelta(hours=3)
st.sidebar.caption(now_bahrain.strftime("%d %b %Y | %H:%M Bahrain"))

st.sidebar.markdown("### Market Watch")
market_rows = []
vix_val = 15.0
for name, symbol in BENCHMARKS.items():
    q = fetch_live_quote(symbol)
    val = float(q.get("price") or 0.0)
    chg = float(q.get("change_pct") or 0.0)
    if symbol == "^VIX" and val > 0:
        vix_val = val
    color = "#10b981" if chg >= 0 else "#ef4444"
    sign = "+" if chg >= 0 else ""
    display_val = f"{val:.4f}" if name == "EURUSD" else f"{val:,.2f}"
    st.sidebar.markdown(
        f"<div class='market-row'><b>{name}</b><span>{display_val} <span style='color:{color};font-weight:800;'>{sign}{chg:.2f}%</span></span></div>",
        unsafe_allow_html=True,
    )
    market_rows.append({"Market": name, "Value": display_val, "Change": chg})

st.sidebar.caption("Yahoo data may be delayed. Use IBKR bid/ask for final orders.")

st.markdown(f"### {APP_TITLE}")
active_asset = st.radio("ETF", list(TICKERS.keys()), key="active_asset", horizontal=True)
page = st.radio("Page", ["Decision Engine", "Dashboard", "Market", "Quant Lab", "Journal"], key="page", horizontal=True)

state = calculate_decision(active_asset)
if state is None:
    st.error("Data pipeline timeout or ticker unavailable.")
    st.stop()

sentiment = compute_market_sentiment(market_rows, vix_val)

if "fallback" in str(state.get("data_source", "")):
    st.warning("Market data source is offline fallback. Use this UI only for structure/testing; confirm live prices in IBKR before trading.")

if page == "Decision Engine":
    st.markdown(
        f"#### {active_asset} | {state['decision']} | Suggested limit EUR {state['suggested_limit']:.3f} | Market {status_word(vix_val)} | Data {state['latest_data_date']} · Source {state.get('data_source', 'unknown')}"
    )
    render_market_sentiment(sentiment)
    render_decision_engine(state)
    render_etf_priority_board()
    render_price_ladder(state)
    render_probability_box(state)

elif page == "Dashboard":
    render_decision_engine(state)
    render_chart(state)
    render_price_ladder(state)

elif page == "Market":
    render_market_sentiment(sentiment)
    render_market_watch(market_rows)
    render_etf_priority_board()

elif page == "Quant Lab":
    render_quant_lab(state)
    render_chart(state)

elif page == "Journal":
    render_journal_page(state)
