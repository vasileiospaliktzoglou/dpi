from __future__ import annotations

import datetime as dt
import logging
import time
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from config import APP_TITLE, APP_VERSION, LOG_DIR, LOG_FILE
from styles import css
from engine import build_decisions, choose_primary
from charts import price_chart, comparison_chart, market_bar
from excel_memory import save_run

AUTO_REFRESH_SECONDS = 60

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


def auto_refresh(seconds: int = AUTO_REFRESH_SECONDS) -> None:
    # Lightweight client-side refresh. No visible Refresh button and no dependency on streamlit-autorefresh.
    components.html(
        f"""
        <script>
          setTimeout(function() {{ window.parent.location.reload(); }}, {seconds * 1000});
        </script>
        """,
        height=0,
        width=0,
    )


def change_arrow(x: float) -> str:
    return "▲" if x >= 0 else "▼"


def trend_tone(x: float) -> str:
    return "normal" if abs(x) < 0.25 else "positive" if x > 0 else "negative"


def header(market) -> None:
    st.title(APP_TITLE)
    c1, c2 = st.columns([0.68, 0.32])
    with c1:
        st.caption("Evidence-based ETF execution system · V60A · VNGA80 · VWCE")
    with c2:
        st.caption(f"🟢 Auto-refresh every {AUTO_REFRESH_SECONDS}s · Updated {market.fetched_at or bahrain_now()}")


def render_today(primary, decisions, market) -> None:
    total_saving = sum(max(0, d.estimated_saving_eur) for d in decisions.values())
    closest = min(decisions.values(), key=lambda d: d.gap_pct)

    st.subheader("Today’s decision")
    st.info(primary.action_plain)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Action", primary.action, primary.symbol)
    k2.metric("Estimated saving", money(total_saving), "vs buying now")
    k3.metric("Closest ETF", closest.symbol, f"{pct(closest.gap_pct)} above target")
    k4.metric("Market mood", market.regime, f"{market.score}/100")

    with st.expander("Why this is the decision", expanded=True):
        st.write(market.one_sentence)
        st.write(
            "The app is optimizing execution price, not predicting the market. "
            "The main question is whether waiting for the limit targets is likely to save money compared with buying immediately."
        )


def render_markets(market) -> None:
    st.subheader("Today’s markets")
    st.write(market.one_sentence)

    table = pd.DataFrame(
        [
            {
                "Market": r["label"],
                "Ticker": r["ticker"],
                "Price": round(float(r["price"]), 4 if r["ticker"] == "EURUSD=X" else 2),
                "Today": f"{change_arrow(float(r['change_pct']))} {pct(float(r['change_pct']), signed=True)}",
                "Source": r.get("source", ""),
            }
            for r in market.rows
        ]
    )
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.plotly_chart(market_bar(market.rows), use_container_width=True, config={"displayModeBar": False})

    with st.expander("Market explanation", expanded=False):
        for d in market.drivers:
            st.write(f"• {d}")


def render_etf_plan(decisions) -> None:
    st.subheader("ETF plan")
    rows = []
    for d in decisions.values():
        rows.append(
            {
                "ETF": d.symbol,
                "Action": d.action,
                "Current": money(d.live_price),
                "Target": money(d.target_price),
                "Distance": pct(d.gap_pct),
                "5-day target touch": f"{d.target_touch_5d:.1f}%",
                "Estimated saving": money(d.estimated_saving_eur),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    cols = st.columns(len(decisions))
    for col, d in zip(cols, decisions.values()):
        with col:
            with st.container(border=True):
                st.markdown(f"**{d.symbol}**")
                st.metric("Current", money(d.live_price), pct(d.day_change_pct, signed=True))
                st.metric("Target", money(d.target_price), f"{pct(d.gap_pct)} away")
                st.metric("Saving if target hits", money(d.estimated_saving_eur))
                st.caption(d.action)


def select_etf(decisions) -> str:
    symbols = list(decisions.keys())
    current = st.session_state.get("selected_etf", symbols[0])
    if current not in symbols:
        current = symbols[0]
    selected = st.radio("ETF", symbols, index=symbols.index(current), horizontal=True, label_visibility="collapsed")
    st.session_state["selected_etf"] = selected
    return selected


def render_selected_etf(d) -> None:
    st.subheader(f"{d.symbol} detail")
    st.caption(d.name)

    a, b, c, e = st.columns(4)
    a.metric("Current price", money(d.live_price), pct(d.day_change_pct, signed=True))
    b.metric("Limit target", money(d.target_price), f"{money(d.gap_eur)} lower")
    c.metric("Expected saving", money(d.estimated_saving_eur))
    e.metric("Historical patience", f"{d.target_touch_5d:.1f}%", "5 trading days")

    view = st.radio("Chart range", ["1M", "3M", "6M", "1Y", "3Y"], index=2, horizontal=True)
    st.plotly_chart(price_chart(d.history, d.symbol, d.target_price, view), use_container_width=True, config={"displayModeBar": False})

    with st.container(border=True):
        st.markdown("**Simple meaning**")
        st.write(d.reason)
        st.write(
            f"If your planned order is executed at the target instead of buying now, the estimated saving is about **{money(d.estimated_saving_eur)}**. "
            "This money-saved measure is more important than a prediction success rate."
        )

    with st.expander("What does 5-day target touch mean?", expanded=False):
        st.write(
            f"The app checked the available 5-year daily history for {d.symbol}. It asks: "
            "when a similar limit target was placed below the market price, how often did the ETF later fall enough to touch that target?"
        )
        st.write(f"Next day: {d.target_touch_1d_count}/{d.sample_1d} cases ({d.target_touch_1d:.1f}%).")
        st.write(f"Within five trading days: {d.target_touch_5d_count}/{d.sample_5d} cases ({d.target_touch_5d:.1f}%).")
        st.warning("This is historical evidence, not a forecast or guarantee.")


def render_analytics(decisions) -> None:
    st.subheader("Analytics")
    st.plotly_chart(comparison_chart(decisions), use_container_width=True, config={"displayModeBar": False})
    table = pd.DataFrame(
        [
            {
                "ETF": d.symbol,
                "Action": d.action,
                "Current": round(d.live_price, 2),
                "Target": round(d.target_price, 2),
                "Distance from target": f"{d.gap_pct:.2f}%",
                "Estimated saving": round(d.estimated_saving_eur, 2),
                "5-day target touch": f"{d.target_touch_5d:.1f}% ({d.target_touch_5d_count}/{d.sample_5d})",
                "Trend": d.trend,
                "Data source": d.data_source,
            }
            for d in decisions.values()
        ]
    )
    st.dataframe(table, use_container_width=True, hide_index=True)


@st.cache_data(ttl=AUTO_REFRESH_SECONDS, show_spinner=False)
def load_system_cached(refresh_bucket: int):
    market, decisions = build_decisions(refresh_bucket)
    primary = choose_primary(decisions)
    return market, decisions, primary


def load_system(refresh_bucket: int):
    market, decisions, primary = load_system_cached(refresh_bucket)
    try:
        save_run(APP_VERSION, market, decisions, primary)
    except Exception:
        logging.exception("Internal Excel memory update failed")
    return market, decisions, primary


def main() -> None:
    auto_refresh(AUTO_REFRESH_SECONDS)
    refresh_bucket = int(time.time() // AUTO_REFRESH_SECONDS)
    market, decisions, primary = load_system(refresh_bucket)
    header(market)

    tab_today, tab_etf, tab_analytics = st.tabs(["Today", "ETF detail", "Analytics"])

    with tab_today:
        render_today(primary, decisions, market)
        render_markets(market)
        render_etf_plan(decisions)

    with tab_etf:
        selected = select_etf(decisions)
        render_selected_etf(decisions[selected])

    with tab_analytics:
        render_analytics(decisions)


if __name__ == "__main__":
    main()
