from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from config import APP_TITLE, APP_VERSION, ETFS, LOG_DIR, LOG_FILE
from styles import css
from engine import build_decisions, choose_primary
from charts import price_chart, comparison_chart
from excel_memory import save_run

st.set_page_config(page_title=f"{APP_TITLE} {APP_VERSION}", layout="wide", initial_sidebar_state="collapsed")
st.markdown(css(), unsafe_allow_html=True)

Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def money(x: float) -> str:
    return f"€{x:,.2f}"


def pct(x: float) -> str:
    return f"{x:.2f}%"


def bahrain_now() -> str:
    return (dt.datetime.utcnow() + dt.timedelta(hours=3)).strftime("%d %b %Y · %H:%M Bahrain")


def topbar() -> None:
    st.markdown(
        f"""
        <div class="topbar">
          <div>
            <div class="brand">{APP_TITLE}</div>
            <div class="subtitle">One decision dashboard for V60A, VNGA80 and VWCE.</div>
          </div>
          <div class="version">{APP_VERSION} · {bahrain_now()}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_primary(primary) -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-grid">
            <div>
              <div class="eyebrow">Today's decision</div>
              <div class="decision">{primary.action}</div>
              <p class="plain">{primary.action_plain}</p>
              <div style="margin-top:12px">
                <span class="status">Focus ETF <b>{primary.symbol}</b></span>
                <span class="status">Confidence <b>{primary.confidence_label}</b></span>
              </div>
            </div>
            <div class="hero-metrics">
              <div class="mini"><div class="mini-value">{money(primary.target_price)}</div><div class="mini-label">Preferred limit target</div></div>
              <div class="mini"><div class="mini-value">{pct(primary.gap_pct)}</div><div class="mini-label">Current price above target</div></div>
              <div class="mini"><div class="mini-value">{primary.trend}</div><div class="mini-label">Current trend</div></div>
              <div class="mini"><div class="mini-value">{primary.window}</div><div class="mini-label">Best checking window</div></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market(market) -> None:
    drivers = "".join(f"<div class='listrow'><span>{d}</span></div>" for d in market.drivers)
    rows = "".join(
        f"<div class='listrow'><b>{r['label']}</b><span>{r['change_pct']:.2f}%</span></div>"
        for r in market.rows
    )
    st.markdown(
        f"""
        <div class="grid2">
          <div class="card">
            <div class="eyebrow">Market summary</div>
            <h3>{market.regime} market · {market.score}/100</h3>
            <p class="plain">{market.one_sentence}</p>
            <div class="divider"></div>
            {drivers}
          </div>
          <div class="card">
            <div class="eyebrow">Market inputs</div>
            {rows}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def select_etf(decisions):
    symbols = list(decisions.keys())
    if "selected_etf" not in st.session_state or st.session_state["selected_etf"] not in symbols:
        st.session_state["selected_etf"] = symbols[0]
    tabs = st.tabs(symbols)
    selected = st.session_state["selected_etf"]
    for symbol, tab in zip(symbols, tabs):
        with tab:
            d = decisions[symbol]
            if st.button(f"Inspect {symbol}", key=f"inspect_{symbol}", use_container_width=True):
                st.session_state["selected_etf"] = symbol
                selected = symbol
            st.caption(f"{d.action} · target {money(d.target_price)} · current {money(d.live_price)}")
    return st.session_state.get("selected_etf", selected)


def render_etf_summary(decisions) -> None:
    blocks = []
    for d in decisions.values():
        action_color = "🟢" if d.action.startswith("Deploy") else "🟡" if d.action.startswith("Wait") else "⚪"
        blocks.append(
            f"""
            <div class="card">
              <div class="action-row">
                <div><div class="eyebrow">{d.symbol}</div><h3>{action_color} {d.action}</h3></div>
                <div class="metric">{money(d.target_price)}</div>
              </div>
              <div class="muted">Current {money(d.live_price)} · {pct(d.gap_pct)} above target</div>
              <div class="divider"></div>
              <div class="muted">{d.action_plain}</div>
            </div>
            """
        )
    st.markdown("<div class='cards'>" + "".join(blocks) + "</div>", unsafe_allow_html=True)


def render_selected_etf(d) -> None:
    st.markdown(f"<div class='section-title'>{d.symbol} detail</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='card'><div class='eyebrow'>Current price</div><div class='metric'>{money(d.live_price)}</div><div class='muted'>{d.data_source}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><div class='eyebrow'>Limit target</div><div class='metric'>{money(d.target_price)}</div><div class='muted'>{money(d.gap_eur)} below current price</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><div class='eyebrow'>Checking window</div><div class='metric' style='font-size:19px'>{d.window}</div><div class='muted'>Use this as a practical checking window.</div></div>", unsafe_allow_html=True)

    st.plotly_chart(price_chart(d.history, d.symbol, d.target_price), use_container_width=True)

    st.markdown(
        f"""
        <div class="soft">
          <div class="eyebrow">Plain-English reading</div>
          <p class="plain">{d.reason}</p>
          <div class="divider"></div>
          <div class="muted">{d.guardrail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("What do the historical target-touch numbers mean?", expanded=False):
        st.write(
            f"For {d.symbol}, this asks: in similar past situations, how often did the ETF fall enough to touch the planned limit price? "
            f"It happened the next trading day in {d.target_touch_1d_count} out of {d.sample_1d} cases. "
            f"It happened within five trading days in {d.target_touch_5d_count} out of {d.sample_5d} cases. "
            "This is a patience indicator, not a forecast."
        )


def render_analytics(decisions) -> None:
    st.markdown("<div class='section-title'>Analytics</div>", unsafe_allow_html=True)
    st.plotly_chart(comparison_chart(decisions), use_container_width=True)
    table = pd.DataFrame(
        [
            {
                "ETF": d.symbol,
                "Action": d.action,
                "Current": round(d.live_price, 2),
                "Target": round(d.target_price, 2),
                "Above target": f"{d.gap_pct:.2f}%",
                "Reached next day in history": f"{d.target_touch_1d_count}/{d.sample_1d}",
                "Reached within 5 days in history": f"{d.target_touch_5d_count}/{d.sample_5d}",
                "Confidence": d.confidence_label,
            }
            for d in decisions.values()
        ]
    )
    st.dataframe(table, use_container_width=True, hide_index=True)


def load_system():
    with st.spinner("Updating market data and decisions..."):
        market, decisions = build_decisions()
        primary = choose_primary(decisions)
        try:
            save_run(APP_VERSION, market, decisions, primary)
        except Exception:
            logging.exception("Internal Excel memory update failed")
            # No debug path is shown in the production UI. Details go to logs/app.log.
        return market, decisions, primary


def main() -> None:
    topbar()
    page = st.sidebar.radio("Navigation", ["Dashboard", "ETF Detail", "Analytics"], label_visibility="collapsed")
    market, decisions, primary = load_system()

    if page == "Dashboard":
        render_primary(primary)
        render_market(market)
        st.markdown("<div class='section-title'>ETF plan</div>", unsafe_allow_html=True)
        render_etf_summary(decisions)
        selected = select_etf(decisions)
        render_selected_etf(decisions[selected])
    elif page == "ETF Detail":
        selected = select_etf(decisions)
        render_selected_etf(decisions[selected])
    else:
        render_market(market)
        render_analytics(decisions)


if __name__ == "__main__":
    main()
