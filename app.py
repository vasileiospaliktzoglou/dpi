from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from config import APP_TITLE, APP_VERSION, LOG_DIR, LOG_FILE
from styles import css
from engine import build_decisions, choose_primary
from charts import price_chart, comparison_chart, market_bar
from excel_memory import save_run

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="collapsed")
st.markdown(css(), unsafe_allow_html=True)

Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def money(x: float) -> str:
    return f"€{x:,.2f}"


def pct(x: float, signed: bool = False) -> str:
    return f"{x:+.2f}%" if signed else f"{x:.2f}%"


def bahrain_now() -> str:
    return (dt.datetime.utcnow() + dt.timedelta(hours=3)).strftime("%d %b %Y · %H:%M Bahrain")


def change_class(x: float) -> str:
    return "positive" if x >= 0 else "negative"



def component_theme() -> str:
    return """
    <style>
      :root {
        --panel:#152033; --panel2:#1A2740; --text:#E6EDF7; --text2:#D7E0EE;
        --muted:#9FB0C7; --line:rgba(159,176,199,.20); --good:#3DDC84;
        --warn:#F4B740; --bad:#F87171; --blue:#A6CCFF; --amber-bg:rgba(244,183,64,.16);
      }
      html, body { margin:0; padding:0; background:transparent; color:var(--text);
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Arial,sans-serif;
      }
      * { box-sizing:border-box; overflow-wrap:anywhere; }
      .card { background:rgba(21,32,51,.94); border:1px solid var(--line); border-radius:22px;
        padding:18px; box-shadow:0 18px 42px rgba(4,8,18,.20); overflow:hidden; min-width:0;
      }
      .cards, .timing-cards { display:grid; grid-template-columns:repeat(3,minmax(245px,1fr)); gap:14px; }
      .market-grid { display:grid; grid-template-columns:repeat(3,minmax(180px,1fr)); gap:12px; }
      .market-card { background:linear-gradient(180deg,rgba(26,39,64,.98),rgba(21,32,51,.94)); border:1px solid var(--line); border-radius:20px; padding:15px; min-width:0; }
      .market-top { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
      .market-name { font-weight:850; font-size:14px; line-height:1.15; }
      .ticker { color:var(--muted); font-size:11px; margin-top:3px; letter-spacing:.06em; }
      .market-price { font-size:clamp(20px,3vw,27px); font-weight:950; letter-spacing:-.04em; margin-top:10px; white-space:nowrap; }
      .market-move { font-size:13px; font-weight:900; white-space:nowrap; padding:4px 8px; border-radius:999px; background:rgba(159,176,199,.10); }
      .market-sub { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:11px; }
      .market-sub div { background:rgba(159,176,199,.08); border-radius:12px; padding:7px 8px; }
      .market-sub span { display:block; font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }
      .market-sub b { font-size:12px; }
      .timing-card { background:linear-gradient(180deg,rgba(26,39,64,.98),rgba(21,32,51,.94)); border:1px solid var(--line); border-radius:22px; padding:18px; box-shadow:0 18px 42px rgba(4,8,18,.20); overflow:hidden; min-width:0; }
      .timing-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; }
      .timing-score { font-size:28px; font-weight:950; color:var(--good); white-space:nowrap; letter-spacing:-.04em; }
      .timing-grid { display:grid; grid-template-columns:1fr; gap:8px; margin-top:14px; }
      .timing-grid div { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:9px 10px; border-radius:14px; background:rgba(159,176,199,.08); }
      .timing-grid span { color:var(--muted); font-size:12px; }
      .timing-grid b { color:var(--text); font-size:13px; text-align:right; }
      .row { display:flex; align-items:flex-start; justify-content:space-between; gap:14px; min-width:0; }
      .row > * { min-width:0; }
      .eyebrow { color:var(--blue); text-transform:uppercase; letter-spacing:.14em; font-size:11px;
        font-weight:850; margin-bottom:6px;
      }
      h3 { margin:0; font-size:clamp(16px,1.8vw,19px); letter-spacing:-.025em; color:var(--text); line-height:1.18; }
      .metric { font-size:clamp(22px,3.2vw,28px); font-weight:950; letter-spacing:-.045em;
        color:var(--text); white-space:nowrap;
      }
      .muted { color:var(--muted); font-size:13px; line-height:1.45; min-width:0; }
      .small { color:var(--muted); font-size:12px; }
      .divider { height:1px; background:var(--line); margin:14px 0; }
      .positive { color:var(--good); font-weight:800; white-space:nowrap; }
      .negative { color:var(--bad); font-weight:800; white-space:nowrap; }
      .status { display:inline-flex; align-items:center; border-radius:999px; padding:5px 9px; font-size:11px; font-weight:950; letter-spacing:.08em; text-transform:uppercase; white-space:nowrap; }
      .status-wait { color:var(--warn); background:var(--amber-bg); border:1px solid rgba(244,183,64,.30); }
      .status-ready { color:var(--good); background:rgba(61,220,132,.14); border:1px solid rgba(61,220,132,.30); }
      .status-monitor { color:var(--muted); background:rgba(159,176,199,.10); border:1px solid var(--line); }
      .stat-line { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:7px 0; }
      .stat-label { color:var(--muted); font-size:13px; }
      .stat-value { color:var(--text); font-weight:850; text-align:right; }
      @media (max-width:920px) { .cards, .timing-cards, .market-grid { grid-template-columns:1fr; } }
      @media (max-width:640px) { .card { border-radius:18px; padding:15px; } .metric { font-size:23px; } .market-card { border-radius:18px; padding:14px; } }
      @media (max-width:430px) { .row { gap:8px; } .metric { white-space:normal; text-align:right; } .market-price { font-size:23px; } }
    </style>
    """
def render_fragment(html: str, height: int) -> None:
    components.html(component_theme() + html, height=height, scrolling=False)


def topbar(fetched_at: str = "") -> None:
    subtitle = "ETF execution dashboard · V60A · VNGA80 · VWCE"
    stamp = f"<span class=\"live-dot\"></span> Live · updated {fetched_at or bahrain_now()} · auto-refresh 60s"
    st.markdown(
        f"""
        <div class="brandbar">
          <div>
            <div class="brand">{APP_TITLE}</div>
            <div class="sub">{subtitle}</div>
          </div>
          <div class="stamp">{stamp}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market(market) -> None:
    st.markdown("<div class='section-title first-section'>Today’s markets</div>", unsafe_allow_html=True)

    market_cards = []
    for r in market.rows:
        cls = change_class(float(r["change_pct"]))
        change_5d = float(r.get("change_5d_pct", 0.0))
        change_1m = float(r.get("change_1m_pct", 0.0))
        cls5 = change_class(change_5d)
        cls1m = change_class(change_1m)
        market_cards.append(
            f"""
            <div class="market-card">
              <div class="market-top">
                <div>
                  <div class="market-name">{r['label']}</div>
                  <div class="ticker">{r['ticker']}</div>
                </div>
                <div class="market-move {cls}">{pct(float(r['change_pct']), signed=True)}</div>
              </div>
              <div class="market-price">{r['price']:,.2f}</div>
              <div class="market-sub">
                <div><span>5 days</span><b class="{cls5}">{pct(change_5d, signed=True)}</b></div>
                <div><span>1 month</span><b class="{cls1m}">{pct(change_1m, signed=True)}</b></div>
              </div>
            </div>
            """
        )
    render_fragment("<div class='market-grid'>" + "".join(market_cards) + "</div>", height=360)

    driver_html = "".join(f"<div class='muted'>• {d}</div>" for d in market.drivers[:3])
    render_fragment(
        f"""
        <div class="card">
          <div class="eyebrow">Market insight</div>
          <h3>{market.regime} · {market.score}/100</h3>
          <p class="muted" style="color:var(--text2);font-size:15px;line-height:1.55;margin:0">{market.one_sentence}</p>
          <div class="divider"></div>
          {driver_html}
        </div>
        """,
        height=210,
    )
    st.plotly_chart(market_bar(market.rows), use_container_width=True, config={"displayModeBar": False})
def status_class(action: str) -> str:
    if action == "Ready to deploy":
        return "status-ready"
    if action == "Wait with limit":
        return "status-wait"
    return "status-monitor"


def render_etf_cards(decisions) -> None:
    blocks = []
    for d in decisions.values():
        cls = change_class(d.day_change_pct)
        blocks.append(
            f"""
            <div class="card">
              <div class="row">
                <div>
                  <div class="eyebrow">{d.symbol}</div>
                  <span class="status {status_class(d.action)}">{d.action}</span>
                </div>
                <div class="metric">{money(d.live_price)}</div>
              </div>
              <div class="muted" style="margin-top:10px"><span class="{cls}">{pct(d.day_change_pct, signed=True)}</span> today · target {money(d.target_price)}</div>
              <div class="divider"></div>
              <div class="stat-line"><span class="stat-label">Distance to target</span><span class="stat-value">{pct(d.gap_pct)}</span></div>
              <div class="stat-line"><span class="stat-label">Historical 5-day target touch</span><span class="stat-value">{d.target_touch_5d:.1f}%</span></div>
              <div class="stat-line"><span class="stat-label">Estimated saving</span><span class="stat-value">{money(d.estimated_saving_eur)}</span></div>
            </div>
            """
        )
    st.markdown("<div class='section-title'>ETF plan</div>", unsafe_allow_html=True)
    render_fragment("<div class='cards'>" + "".join(blocks) + "</div>", height=285)
def render_timing_plan(decisions) -> None:
    """Show the historical best weekday and month window for each ETF."""
    blocks = []
    for d in decisions.values():
        blocks.append(
            f"""
            <div class="timing-card">
              <div class="timing-head">
                <div>
                  <div class="eyebrow">{d.symbol}</div>
                  <h3>Best historical timing</h3>
                </div>
                <div class="timing-score">{d.timing_score:.0f}%</div>
              </div>
              <div class="timing-grid">
                <div><span>Best weekday</span><b>{d.best_weekday}</b></div>
                <div><span>Best month window</span><b>{d.best_month_window}</b></div>
              </div>
              <div class="divider"></div>
              <div class="muted">{d.timing_reason}</div>
            </div>
            """
        )
    st.markdown("<div class='section-title'>Best timing window</div>", unsafe_allow_html=True)
    st.caption("Based on the last five years: when did a limit target similar to today’s distance get reached within five trading days?")
    render_fragment("<div class='timing-cards'>" + "".join(blocks) + "</div>", height=310)

def select_etf(decisions) -> str:
    symbols = list(decisions.keys())
    current = st.session_state.get("selected_etf", symbols[0])
    if current not in symbols:
        current = symbols[0]

    st.markdown("<div class='section-title'>Detailed ETF view</div>", unsafe_allow_html=True)
    cols = st.columns(len(symbols))
    selected = current
    for col, sym in zip(cols, symbols):
        with col:
            d = decisions[sym]
            label = f"{sym} · {d.action}"
            if st.button(label, key=f"choose_{sym}", use_container_width=True):
                selected = sym
    st.session_state["selected_etf"] = selected
    return selected
def render_selected_etf(d) -> None:
    st.markdown(f"<div class='section-title'>{d.symbol} detailed view</div>", unsafe_allow_html=True)
    summary_cols = st.columns(4)
    items = [
        ("Current", money(d.live_price), pct(d.day_change_pct, signed=True)),
        ("Target", money(d.target_price), f"{money(d.gap_eur)} below"),
        ("Trend", d.trend, f"RSI {d.rsi:.0f}"),
        ("Review window", d.window, d.confidence_label),
    ]
    for col, (label, value, note) in zip(summary_cols, items):
        with col:
            st.markdown(f"<div class='card'><div class='eyebrow'>{label}</div><div class='metric'>{value}</div><div class='muted'>{note}</div></div>", unsafe_allow_html=True)

    view = st.radio("Chart range", ["1M", "3M", "6M", "1Y", "3Y"], index=2, horizontal=True)
    st.plotly_chart(price_chart(d.history, d.symbol, d.target_price, view), use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        f"""
        <div class="soft">
          <div class="eyebrow">What this means in simple English</div>
          <p class="plain">{d.reason}</p>
          <div class="divider"></div>
          <div class="muted">If you were planning to invest the model amount today, waiting for the target instead of buying now could save about <b>{money(d.estimated_saving_eur)}</b>. This is the financial-impact metric; it matters more than prediction accuracy.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Explain the historical target-touch number", expanded=False):
        st.write(
            f"For {d.symbol}, the app looked across the available 5-year daily history. It asked a simple question: "
            f"when the model placed a limit target a similar distance below price, how often did the market later fall enough to touch that target? "
            f"Next day: {d.target_touch_1d_count}/{d.sample_1d} cases ({d.target_touch_1d:.1f}%). "
            f"Within five trading days: {d.target_touch_5d_count}/{d.sample_5d} cases ({d.target_touch_5d:.1f}%). "
            "This is not a forecast; it is a historical patience score."
        )

    with st.expander("Best day and month-window logic", expanded=False):
        st.write(
            f"For {d.symbol}, the best weekday in the 5-year test was **{d.best_weekday}**. "
            f"The strongest part of the month was **{d.best_month_window}**. "
            f"This comes from checking when similar limit targets were reached within five trading days. "
            f"{d.timing_reason} This should guide when to check or place limits, not force a market order."
        )


def render_analytics(decisions) -> None:
    st.markdown("<div class='section-title'>Analytics</div>", unsafe_allow_html=True)
    st.plotly_chart(comparison_chart(decisions), use_container_width=True, config={"displayModeBar": False})
    table = pd.DataFrame([
        {
            "ETF": d.symbol,
            "Action": d.action,
            "Current": round(d.live_price, 2),
            "Target": round(d.target_price, 2),
            "Above target": f"{d.gap_pct:.2f}%",
            "Potential saving": round(d.estimated_saving_eur, 2),
            "5-day target touch": f"{d.target_touch_5d:.1f}% ({d.target_touch_5d_count}/{d.sample_5d})",
            "Best weekday": d.best_weekday,
            "Best month window": d.best_month_window,
            "Trend": d.trend,
            "Source": d.data_source,
        }
        for d in decisions.values()
    ])
    st.dataframe(table, use_container_width=True, hide_index=True)


@st.cache_data(ttl=60, show_spinner=False)
def load_system_cached(refresh_key: int):
    market, decisions = build_decisions(refresh_key)
    primary = choose_primary(decisions)
    return market, decisions, primary


def load_system(refresh_key: int):
    with st.spinner("Updating live market data and decisions..."):
        market, decisions, primary = load_system_cached(refresh_key)
        try:
            save_run(APP_VERSION, market, decisions, primary)
        except Exception:
            logging.exception("Internal Excel memory update failed")
        return market, decisions, primary


def install_auto_refresh(seconds: int = 60) -> None:
    components.html(
        f"""
        <script>
          setTimeout(function() {{ window.parent.location.reload(); }}, {seconds * 1000});
        </script>
        """,
        height=0,
    )


def main() -> None:
    if "refresh_key" not in st.session_state:
        st.session_state["refresh_key"] = 0

    install_auto_refresh(60)

    market, decisions, primary = load_system(st.session_state["refresh_key"])
    topbar(market.fetched_at)

    render_market(market)
    render_etf_cards(decisions)
    render_timing_plan(decisions)
    selected = select_etf(decisions)
    render_selected_etf(decisions[selected])

    with st.expander("Analytics table", expanded=False):
        render_analytics(decisions)


if __name__ == "__main__":
    main()
