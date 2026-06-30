from __future__ import annotations

import datetime as dt
import streamlit as st
import pandas as pd

from config import APP_TITLE, APP_VERSION, ETFS
from styles import css
from engine import build_decisions, choose_primary
from charts import price_chart, comparison_chart
from excel_memory import save_run, status as memory_status

st.set_page_config(page_title=f"{APP_TITLE} {APP_VERSION}", layout="wide", initial_sidebar_state="collapsed")
st.markdown(css(), unsafe_allow_html=True)


def money(x: float) -> str:
    return f"€{x:,.2f}"


def pct(x: float) -> str:
    return f"{x:.2f}%"


def topbar():
    now = (dt.datetime.utcnow() + dt.timedelta(hours=3)).strftime("%d %b %Y · %H:%M Bahrain")
    st.markdown(f"""
    <div class="top">
      <div><div class="brand">{APP_TITLE}</div><div class="sub">Clean decision dashboard for V60A, VNGA80 and VWCE.</div></div>
      <div class="version">{APP_VERSION} · {now}</div>
    </div>
    """, unsafe_allow_html=True)


def select_etf(symbols):
    st.markdown("<div class='seg-note'>Choose one ETF to inspect. The app keeps one market summary for all ETFs to avoid duplication.</div>", unsafe_allow_html=True)
    default = symbols[0]
    if "selected_etf" not in st.session_state:
        st.session_state["selected_etf"] = default
    try:
        selected = st.segmented_control("ETF", symbols, default=st.session_state["selected_etf"], label_visibility="collapsed")
    except Exception:
        selected = st.radio("ETF", symbols, index=symbols.index(st.session_state["selected_etf"]), horizontal=True, label_visibility="collapsed")
    st.session_state["selected_etf"] = selected or default
    return st.session_state["selected_etf"]


def render_market(market):
    driver_html = "".join(f"<div class='listrow'><span>{d}</span></div>" for d in market.drivers)
    rows_html = "".join(
        f"<div class='listrow'><b>{r['label']}</b><span>{r['change_pct']:.2f}%</span></div>" for r in market.rows
    )
    st.markdown(f"""
    <div class="grid2">
      <div class="card">
        <div class="eyebrow">One market summary</div>
        <h3>{market.regime} market · {market.score}/100</h3>
        <p class="plain">{market.one_sentence}</p>
        <p class="muted">{market.plain_english}</p>
        {driver_html}
      </div>
      <div class="card">
        <div class="eyebrow">Market inputs</div>
        {rows_html}
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_primary(primary):
    st.markdown(f"""
    <div class="hero">
      <div class="eyebrow">Today's decision</div>
      <div class="decision">{primary.action}</div>
      <p class="plain">{primary.action_plain}</p>
      <span class="pill">Focus ETF: <b>{primary.symbol}</b></span>
      <span class="pill">Target: <b>{money(primary.target_price)}</b></span>
      <span class="pill">Confidence: <b>{primary.confidence_label}</b></span>
      <p class="muted" style="margin-top:12px">{primary.guardrail}</p>
    </div>
    """, unsafe_allow_html=True)


def render_etf_cards(decisions):
    blocks = []
    for d in decisions.values():
        blocks.append(f"""
        <div class="card">
          <div class="eyebrow">{d.symbol}</div>
          <h3>{d.action}</h3>
          <div class="metric">{money(d.target_price)}</div>
          <div class="muted">Current: {money(d.live_price)} · {pct(d.gap_pct)} above target</div>
          <div style="margin-top:10px"><span class="pill">{d.confidence_label}</span><span class="pill">{d.trend}</span></div>
        </div>
        """)
    st.markdown("<div class='cards'>" + "".join(blocks) + "</div>", unsafe_allow_html=True)


def render_selected_etf(d):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='card'><div class='eyebrow'>Current price</div><div class='metric'>{money(d.live_price)}</div><div class='muted'>{d.data_source}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><div class='eyebrow'>Target price</div><div class='metric'>{money(d.target_price)}</div><div class='muted'>{pct(d.gap_pct)} below current price</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><div class='eyebrow'>Best window</div><div class='metric' style='font-size:20px'>{d.window}</div><div class='muted'>Plain-English estimate, not a forecast.</div></div>", unsafe_allow_html=True)

    st.plotly_chart(price_chart(d.history, d.symbol, d.target_price), use_container_width=True)

    with st.expander("What do the historical target-touch numbers mean?", expanded=False):
        st.write(
            f"For {d.symbol}, the app looked at similar historical days and asked a simple question: "
            f"if we placed a limit order around today's target distance, did the ETF fall enough to touch that price? "
            f"It happened the next day in {d.target_touch_1d_count} out of {d.sample_1d} cases ({d.target_touch_1d:.1f}%). "
            f"Within five trading days, it happened in {d.target_touch_5d_count} out of {d.sample_5d} cases ({d.target_touch_5d:.1f}%). "
            "This is not a guarantee; it is a patience indicator."
        )
    st.info(d.reason)


def render_analytics(decisions):
    st.plotly_chart(comparison_chart(decisions), use_container_width=True)
    table = pd.DataFrame([{
        "ETF": d.symbol,
        "Action": d.action,
        "Current": round(d.live_price, 2),
        "Target": round(d.target_price, 2),
        "Above target": f"{d.gap_pct:.2f}%",
        "Target touched next day historically": f"{d.target_touch_1d:.1f}%",
        "Target touched within 5 days historically": f"{d.target_touch_5d:.1f}%",
        "Confidence": d.confidence_label,
    } for d in decisions.values()])
    st.dataframe(table, use_container_width=True, hide_index=True)


def main():
    topbar()
    page = st.sidebar.radio("Navigate", ["Dashboard", "ETF Detail", "Analytics", "Memory"], label_visibility="collapsed")

    with st.spinner("Updating prices, market context and internal memory..."):
        market, decisions = build_decisions()
        primary = choose_primary(decisions)
        try:
            save_run(APP_VERSION, market, decisions, primary)
            memory_error = None
        except Exception as exc:
            memory_error = str(exc)

    if memory_error:
        st.error(f"Internal memory was not updated: {memory_error}")

    if page == "Dashboard":
        render_primary(primary)
        render_market(market)
        render_etf_cards(decisions)
        st.markdown("### Selected ETF")
        selected = select_etf(list(decisions.keys()))
        render_selected_etf(decisions[selected])
    elif page == "ETF Detail":
        selected = select_etf(list(decisions.keys()))
        render_selected_etf(decisions[selected])
    elif page == "Analytics":
        render_market(market)
        render_analytics(decisions)
    else:
        st.markdown("### Internal memory")
        st.success(memory_status())
        st.write("The Excel workbook is kept as internal app memory. It is not shown as a download button because the app uses it for future learning and validation.")
        st.code("data/PALI_EXECUTE_MEMORY.xlsx")


if __name__ == "__main__":
    main()
