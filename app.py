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
        --warn:#F4B740; --bad:#F87171; --blue:#A6CCFF;
      }
      html, body { margin:0; padding:0; background:transparent; color:var(--text);
        font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Arial,sans-serif;
      }
      * { box-sizing:border-box; overflow-wrap:anywhere; }
      .card { background:rgba(21,32,51,.94); border:1px solid var(--line); border-radius:22px;
        padding:18px; box-shadow:0 18px 42px rgba(4,8,18,.20); overflow:hidden; min-width:0;
      }
      .cards { display:grid; grid-template-columns:repeat(3,minmax(245px,1fr)); gap:14px; }
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
      .market-row { display:grid; grid-template-columns:minmax(0,1fr) minmax(74px,auto) minmax(72px,auto);
        gap:12px; align-items:center; padding:10px 0; border-bottom:1px solid var(--line);
      }
      .market-row:last-child { border-bottom:none; }
      .stat-line { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:7px 0; }
      .stat-label { color:var(--muted); font-size:13px; }
      .stat-value { color:var(--text); font-weight:850; text-align:right; }
      @media (max-width:920px) { .cards { grid-template-columns:1fr; } }
      @media (max-width:640px) { .card { border-radius:18px; padding:15px; } .metric { font-size:23px; }
        .market-row { grid-template-columns:minmax(0,1fr) auto; } .market-row > div:nth-child(3) { grid-column:2; }
      }
      @media (max-width:430px) { .row { gap:8px; } .metric { white-space:normal; text-align:right; } }
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


def render_primary(primary, decisions) -> None:
    total_saving = sum(max(0, d.estimated_saving_eur) for d in decisions.values())
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-grid">
            <div>
              <div class="eyebrow">Today’s execution decision</div>
              <div class="decision">{primary.action}</div>
              <p class="plain">{primary.action_plain}</p>
              <div style="margin-top:12px">
                <span class="pill">Focus: <b>{primary.symbol}</b></span>
                <span class="pill">Evidence: <b>{primary.confidence_label}</b></span>
                <span class="pill">Data: <b>{primary.data_source}</b></span>
              </div>
            </div>
            <div class="hero-metrics">
              <div class="mini"><div class="mini-value">{money(primary.live_price)}</div><div class="mini-label">Current price</div></div>
              <div class="mini"><div class="mini-value">{money(primary.target_price)}</div><div class="mini-label">Limit target</div></div>
              <div class="mini"><div class="mini-value">{pct(primary.gap_pct)}</div><div class="mini-label">Above target</div></div>
              <div class="mini"><div class="mini-value">{money(total_saving)}</div><div class="mini-label">Potential saving vs buying now</div></div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market(market) -> None:
    rows_html = []
    for r in market.rows:
        cls = change_class(float(r["change_pct"]))
        rows_html.append(
            f"""
            <div class="market-row">
              <div><b>{r['label']}</b><div class="small">{r['ticker']}</div></div>
              <div>{r['price']:,.2f}</div>
              <div class="{cls}">{pct(float(r['change_pct']), signed=True)}</div>
            </div>
            """
        )
    driver_html = "".join(f"<div class='muted'>• {d}</div>" for d in market.drivers)
    st.markdown("<div class='section-title'>Today’s markets</div>", unsafe_allow_html=True)
    left, right = st.columns([1.05, 0.95])
    with left:
        render_fragment(
            f"""
            <div class="card">
              <div class="eyebrow">Market sentiment</div>
              <h3>{market.regime} · {market.score}/100</h3>
              <p class="muted" style="color:var(--text2);font-size:15px;line-height:1.55;margin:0">{market.one_sentence}</p>
              <div class="divider"></div>
              {driver_html}
            </div>
            """,
            height=238,
        )
    with right:
        render_fragment("<div class='card'>" + "".join(rows_html) + "</div>", height=238)
    st.plotly_chart(market_bar(market.rows), use_container_width=True, config={"displayModeBar": False})

def render_etf_cards(decisions) -> None:
    blocks = []
    for d in decisions.values():
        icon = "🟢" if d.action == "Ready to deploy" else "🟡" if d.action == "Wait with limit" else "⚪"
        cls = change_class(d.day_change_pct)
        blocks.append(
            f"""
            <div class="card">
              <div class="row">
                <div>
                  <div class="eyebrow">{d.symbol}</div>
                  <h3>{icon} {d.action}</h3>
                </div>
                <div class="metric">{money(d.live_price)}</div>
              </div>
              <div class="muted"><span class="{cls}">{pct(d.day_change_pct, signed=True)}</span> today · target {money(d.target_price)}</div>
              <div class="divider"></div>
              <div class="stat-line"><span class="stat-label">Distance to target</span><span class="stat-value">{pct(d.gap_pct)}</span></div>
              <div class="stat-line"><span class="stat-label">Reached within 5 days before</span><span class="stat-value">{d.target_touch_5d:.1f}%</span></div>
              <div class="stat-line"><span class="stat-label">Estimated saving</span><span class="stat-value">{money(d.estimated_saving_eur)}</span></div>
            </div>
            """
        )
    st.markdown("<div class='section-title'>ETF plan</div>", unsafe_allow_html=True)
    # Render the card grid as a proper HTML component so Streamlit never prints raw <div> markup.
    render_fragment("<div class='cards'>" + "".join(blocks) + "</div>", height=285)

def select_etf(decisions) -> str:
    symbols = list(decisions.keys())
    current = st.session_state.get("selected_etf", symbols[0])
    if current not in symbols:
        current = symbols[0]
    selected = st.radio(
        "Choose ETF",
        symbols,
        index=symbols.index(current),
        horizontal=True,
        help="Pick one ETF to inspect. The rest of the app stays focused on that ETF.",
    )
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

    with st.sidebar:
        page = st.radio("Navigation", ["Dashboard", "ETF Detail", "Analytics"], label_visibility="collapsed")
        st.caption("Updates automatically every 60 seconds. Excel memory runs silently in the background.")

    market, decisions, primary = load_system(st.session_state["refresh_key"])
    topbar(market.fetched_at)

    if page == "Dashboard":
        render_primary(primary, decisions)
        render_market(market)
        render_etf_cards(decisions)
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
