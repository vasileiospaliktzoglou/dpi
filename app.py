from __future__ import annotations

import datetime as dt
from typing import Iterable

import pandas as pd
import streamlit as st

from config import APP_TITLE, APP_VERSION, TICKERS, BENCHMARKS, ORDER_SIZE_EUR, ETF_META
from styles import load_css
from helpers import fetch_live_quote, compute_calendar_timing
from core import calculate_state, compute_market_sentiment
from market_context import classify_market_context
from deployment_engine import score_single_etf, DeploymentWindow
from email_report import build_daily_intelligence_email
from excel_store import save_daily_intelligence, workbook_status, WORKBOOK_PATH
from charts import render_chart

st.set_page_config(page_title=f"{APP_TITLE} {APP_VERSION}", layout="wide", initial_sidebar_state="expanded")
st.markdown(load_css(), unsafe_allow_html=True)

PAGES = ["Today", "Backtest", "Memory"]


def money(value) -> str:
    try:
        return f"€{float(value):,.2f}"
    except Exception:
        return "€--"


def pct(value) -> str:
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "--%"


def now_label() -> str:
    return (dt.datetime.utcnow() + dt.timedelta(hours=3)).strftime("%d %b %Y · %H:%M Bahrain")


def badge_class(action: str) -> str:
    a = (action or "").lower()
    if "deploy" in a:
        return "buy"
    if "keep" in a:
        return "watch"
    return "wait"


def sidebar() -> str:
    st.sidebar.markdown("### EXECUTE")
    page = st.sidebar.radio("Section", PAGES, label_visibility="collapsed")
    st.sidebar.markdown("---")
    st.sidebar.caption("Focused on V60A, VNGA80 and VWCE only.")
    st.sidebar.caption("Excel memory is internal and used to improve future recommendations.")
    return page


def etf_picker() -> str:
    """Mobile-friendly ETF picker shown in the main page, not hidden in the sidebar."""
    options = list(TICKERS.keys())
    if "active_etf" not in st.session_state:
        st.session_state["active_etf"] = options[0]
    st.markdown("<div class='picker-label'>Choose ETF focus</div>", unsafe_allow_html=True)
    try:
        selected = st.segmented_control(
            "Choose ETF focus",
            options,
            selection_mode="single",
            default=st.session_state["active_etf"],
            label_visibility="collapsed",
        )
    except Exception:
        selected = st.radio(
            "Choose ETF focus",
            options,
            index=options.index(st.session_state["active_etf"]),
            horizontal=True,
            label_visibility="collapsed",
        )
    active = selected or st.session_state["active_etf"]
    st.session_state["active_etf"] = active
    meta = ETF_META[active]
    st.caption(f"{meta['name']} · {meta['role']}")
    return active


def topbar(active_etf: str) -> None:
    meta = ETF_META[active_etf]
    st.markdown(
        f"""
        <div class="topbar">
          <div>
            <div class="logo">{APP_TITLE}</div>
            <div class="subtitle">{meta['name']} · {meta['role']}</div>
          </div>
          <div class="pill"><span class="dot"></span>{APP_VERSION} · {now_label()}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_market_rows() -> tuple[list[dict], float]:
    rows: list[dict] = []
    vix_value = 18.0
    for label, ticker in BENCHMARKS.items():
        quote = fetch_live_quote(ticker)
        if label == "VIX":
            try:
                vix_value = float(quote.get("price", vix_value))
            except Exception:
                pass
        rows.append({"Market": label, "Price": quote.get("price", 0.0), "Change": quote.get("change_pct", 0.0), "Source": quote.get("source", "market data")})
    return rows, vix_value


def prepare_run(active_etf: str) -> dict:
    market_rows, vix_value = load_market_rows()
    sentiment = compute_market_sentiment(market_rows, vix_value)
    context = classify_market_context(market_rows, vix_value, sentiment)

    # Calculate each ETF once so the plan table is meaningful and not duplicated from the active ETF.
    etf_states = {}
    windows = []
    for etf in TICKERS.keys():
        etf_state = calculate_state(etf, vix_value)
        if etf_state:
            etf_states[etf] = etf_state
            windows.append(score_single_etf(etf, etf_state, context, vix_value))

    if active_etf not in etf_states:
        st.error("Could not calculate ETF state. Check the market-data connection and ticker symbols.")
        st.stop()

    state = etf_states[active_etf]
    active_window = next(w for w in windows if w.etf == active_etf)
    email = build_daily_intelligence_email(active_etf, state, context, windows)
    try:
        save_daily_intelligence(active_etf, state, context, windows, email)
    except Exception as exc:
        st.warning(f"Internal memory could not be updated: {exc}")
    return {"market_rows": market_rows, "vix": vix_value, "state": state, "etf_states": etf_states, "sentiment": sentiment, "context": context, "windows": windows, "active_window": active_window, "email": email}


def decision_panel(active_etf: str, state: dict, context, w: DeploymentWindow) -> None:
    live = float(state.get("live_price", state.get("spot", 0)) or 0)
    target = float(state.get("target", 0) or 0)
    gap = ((live - target) / target * 100) if target else 0
    shares = int(ORDER_SIZE_EUR / target) if target else 0
    saving = max(0, live - target) * shares
    tone = badge_class(w.action)

    st.markdown(
        f"""
        <div class="hero">
          <div class="card">
            <div class="eyebrow">Single ETF decision</div>
            <div class="decision">{w.action}</div>
            <div class="price">{money(target)}</div>
            <p class="copy">Target limit for <b>{active_etf}</b>. The app now focuses on the selected ETF first; other ETFs are only shown in a compact comparison.</p>
            <div class="code">BUY {active_etf} · LIMIT {target:.2f} · DAY</div>
            <p class="muted">Live reference: {money(live)} · target gap {pct(gap)} · estimated saving vs market entry {money(saving)}</p>
          </div>
          <div class="card">
            <div class="eyebrow">Best estimated deployment window</div>
            <div class="title">{w.suggested_window}</div>
            <span class="badge {tone}">{w.confidence}/100 confidence</span>
            <div class="meter"><div style="width:{max(8,min(100,w.confidence))}%"></div></div>
            <p class="copy">{w.reason}</p>
            <div class="callout">{w.guardrail}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_grid(state: dict, context, w: DeploymentWindow) -> None:
    stats1 = state.get("stats1", {})
    stats5 = state.get("stats5", {})
    items = [
        ("Market mood", f"{context.regime}", f"{context.score}/100 · {context.tone}"),
        ("Chance target is touched tomorrow", pct(stats1.get("fill_rate", 0)), "Based on similar historical limit targets"),
        ("Chance target is touched within 5 days", pct(stats5.get("fill_rate", 0)), "Shows the value of patience before chasing"),
    ]
    html = ''.join([f"<div class='mini-card'><div class='metric-label'>{a}</div><div class='metric-value'>{b}</div><div class='muted'>{c}</div></div>" for a,b,c in items])
    st.markdown(f"<div class='grid3'>{html}</div>", unsafe_allow_html=True)


def market_story(context, market_rows: list[dict]) -> None:
    rows_html = "".join(
        f"<div class='row'><b>{r['Market']}</b><span>{pct(r.get('Change',0))}</span></div>" for r in market_rows[:6]
    )
    drivers = "".join(f"<div class='row'><b>{d}</b></div>" for d in context.drivers[:4]) or "<div class='row'><b>No major driver detected.</b></div>"
    st.markdown(
        f"""
        <div class="grid2">
          <div class="card">
            <div class="eyebrow">Market explanation</div>
            <div class="section">What is happening?</div>
            <p class="copy">{context.explanation}</p>
            <div class="callout">Tomorrow bias: {context.tomorrow_bias}</div>
          </div>
          <div class="card">
            <div class="eyebrow">Inputs used today</div>
            <div class="section">Market tape</div>
            <div class="list">{rows_html}</div>
          </div>
        </div>
        <div class="card">
          <div class="eyebrow">Drivers</div>
          <div class="list">{drivers}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compact_comparison(active_etf: str, windows: Iterable[DeploymentWindow]) -> None:
    st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)
    st.markdown("### Deployment plan")
    st.caption("One simple plan for all tracked ETFs. The selected ETF is shown first; the others stay compact.")
    rows = []
    for w in windows:
        rows.append({
            "ETF": w.etf,
            "Role": w.role,
            "Action": w.action.replace("—", "-"),
            "Best estimated window": w.suggested_window,
            "Confidence": f"{w.confidence}/100",
        })
    df = pd.DataFrame(rows)
    df["_sort"] = df["ETF"].apply(lambda x: 0 if x == active_etf else 1)
    df = df.sort_values(["_sort", "ETF"]).drop(columns=["_sort"])
    st.dataframe(df, use_container_width=True, hide_index=True)



def live_chart_card(active_etf: str, state: dict) -> None:
    st.markdown("### Live chart")
    st.caption("Selected ETF only. No repeated ETF commentary below the chart.")
    render_chart(active_etf, target=state.get("target"), atr=state.get("atr"))


def simple_backtest_explanation(stats1: dict, stats5: dict) -> None:
    fills1 = int(stats1.get("fills", 0) or 0)
    attempts1 = int(stats1.get("attempts", 0) or 0)
    fills5 = int(stats5.get("fills", 0) or 0)
    attempts5 = int(stats5.get("attempts", 0) or 0)
    st.markdown(
        f"""
        <div class="card">
          <div class="eyebrow">Plain English backtest meaning</div>
          <div class="section">What do these numbers mean?</div>
          <p class="copy"><b>Next-day target touch</b> means: in the historical test, the same type of limit order reached its price on the next trading day <b>{fills1}</b> times out of <b>{attempts1}</b> valid tests.</p>
          <p class="copy"><b>Five-day target touch</b> means: if the same limit was kept open for up to five trading days, it reached the target <b>{fills5}</b> times out of <b>{attempts5}</b> valid tests.</p>
          <div class="callout">Simple interpretation: a low next-day number does not mean the plan is bad. It means the target is selective. The five-day number shows whether patience improves the chance of execution.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def today_page(active_etf: str, data: dict) -> None:
    topbar(active_etf)
    market_story(data["context"], data["market_rows"])
    compact_comparison(active_etf, data["windows"])
    decision_panel(active_etf, data["state"], data["context"], data["active_window"])
    status_grid(data["state"], data["context"], data["active_window"])
    live_chart_card(active_etf, data["state"])
    with st.expander("Email draft", expanded=False):
        st.text_area("Subject", data["email"]["subject"], height=70)
        st.text_area("Body", data["email"]["text"], height=300)


def backtest_page(active_etf: str, data: dict) -> None:
    topbar(active_etf)
    state = data["state"]
    stats1 = state.get("stats1", {})
    stats5 = state.get("stats5", {})
    st.markdown(
        f"""
        <div class="card">
          <div class="eyebrow">Backtest summary</div>
          <div class="section">Limit-touch evidence for {active_etf}</div>
          <p class="copy">This test checks whether a disciplined limit price would have been reached in past market conditions. It is a reality check for the execution rule, not a promise that the future will behave the same way.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    items = [
        ("Next-day target touch", pct(stats1.get("fill_rate", 0)), f"{int(stats1.get('fills',0))}/{int(stats1.get('attempts',0))} tests"),
        ("Five-day target touch", pct(stats5.get("fill_rate", 0)), f"{int(stats5.get('fills',0))}/{int(stats5.get('attempts',0))} tests"),
        ("Average price advantage", pct(stats1.get("avg_saving", 0)), "when next-day target was touched"),
    ]
    html = ''.join([f"<div class='mini-card'><div class='metric-label'>{a}</div><div class='metric-value'>{b}</div><div class='muted'>{c}</div></div>" for a,b,c in items])
    st.markdown(f"<div class='grid3'>{html}</div>", unsafe_allow_html=True)
    simple_backtest_explanation(stats1, stats5)

    try:
        cal = compute_calendar_timing(state["df_clean"], multiplier=float(state.get("base_m", 1.0)))
        st.markdown(f"<div class='card'><div class='eyebrow'>Calendar timing</div><p class='copy'>{cal.get('summary','')}</p></div>", unsafe_allow_html=True)
        tabs = st.tabs(["Weekday", "Week of month", "Day of month"])
        tables = [cal.get("weekday_table"), cal.get("week_table"), cal.get("day_table")]
        for tab, df in zip(tabs, tables):
            with tab:
                if isinstance(df, pd.DataFrame) and not df.empty:
                    st.dataframe(df.head(10), use_container_width=True, hide_index=True)
                else:
                    st.info("Not enough data for this table.")
    except Exception as exc:
        st.info(f"Calendar backtest unavailable: {exc}")


def memory_page(active_etf: str) -> None:
    topbar(active_etf)
    status = workbook_status()
    st.markdown(
        f"""
        <div class="card">
          <div class="eyebrow">Internal memory</div>
          <div class="section">Excel file is the app memory, not a user-facing download</div>
          <p class="copy">Path: <b>{status['path']}</b><br>Exists: <b>{status['exists']}</b> · Size: <b>{status['size_kb']} KB</b></p>
          <div class="callout">The workbook stores recommendations, market context, feature inputs and learning outcomes for future validation.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if WORKBOOK_PATH.exists():
        tabs = st.tabs(["Recommendations", "Daily Intelligence", "Feature Store", "Learning"])
        for tab, sheet in zip(tabs, ["Recommendations", "Daily_Intelligence", "Feature_Store", "Learning"]):
            with tab:
                try:
                    df = pd.read_excel(WORKBOOK_PATH, sheet_name=sheet)
                    st.dataframe(df.tail(50), use_container_width=True, hide_index=True)
                except Exception as exc:
                    st.info(f"No readable {sheet} sheet yet: {exc}")


def main() -> None:
    page = sidebar()
    active_etf = etf_picker()
    data = prepare_run(active_etf)
    if page == "Today":
        today_page(active_etf, data)
    elif page == "Backtest":
        backtest_page(active_etf, data)
    else:
        memory_page(active_etf)


if __name__ == "__main__":
    main()
