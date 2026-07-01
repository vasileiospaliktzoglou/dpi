from __future__ import annotations

import datetime as dt
import logging
import time
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

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


def change_class(x: float | None) -> str:
    try:
        return "positive" if float(x) >= 0 else "negative"
    except Exception:
        return "neutral"


def pct_or_na(x: float | None, signed: bool = True, max_abs: float = 50.0) -> str:
    """Format a percentage only when it is plausible and finite.

    This prevents misleading values caused by mixing a live quote with fallback
    demo history when Yahoo returns one source but not the other.
    """
    try:
        val = float(x)
    except Exception:
        return "n/a"
    if not pd.notna(val) or abs(val) > max_abs:
        return "n/a"
    return pct(val, signed=signed)


def plain_number(x: float | None, default: float = 0.0) -> float:
    """Return a safe numeric value for UI calculations."""
    try:
        val = float(x)
    except Exception:
        return default
    return val if pd.notna(val) else default


def find_market_row(market, tickers: tuple[str, ...]):
    """Return the first market row matching one of the provided tickers."""
    wanted = {t.upper() for t in tickers}
    for row in getattr(market, "rows", []):
        if str(row.get("ticker", "")).upper() in wanted:
            return row
    return None


def market_move(row) -> float:
    return plain_number(row.get("change_pct")) if row else 0.0


def classify_market_mood(market) -> tuple[str, str]:
    """Classify today's market mood using the live market rows already in the app."""
    world = market_move(find_market_row(market, ("URTH", "ACWI", "VT")))
    sp500 = market_move(find_market_row(market, ("SPY", "^GSPC", "VOO")))
    europe = market_move(find_market_row(market, ("VGK", "FEZ", "^STOXX")))
    vix = market_move(find_market_row(market, ("^VIX", "VIX")))
    bonds = market_move(find_market_row(market, ("IEF", "TLT", "AGG")))

    risk_score = 0
    risk_score += 1 if world > 0 else -1 if world < 0 else 0
    risk_score += 1 if sp500 > 0 else -1 if sp500 < 0 else 0
    risk_score += 1 if europe > 0 else -1 if europe < 0 else 0
    risk_score += 1 if vix < 0 else -1 if vix > 0 else 0
    risk_score += 1 if bonds >= 0 else 0

    if risk_score >= 3:
        return "Positive", "Risk appetite improved today. Stronger equity markets and/or lower volatility usually make limit orders slightly less likely to fill immediately."
    if risk_score <= -2:
        return "Defensive", "Markets were more cautious today. Softer equities or higher volatility can improve the chance that lower limit targets are reached."
    return "Mixed", "Markets were mixed today. The evidence does not strongly favour chasing prices or cancelling existing limits."


def build_daily_brief(market, decisions, primary) -> dict:
    """Create a concise daily brief: what happened, did we miss anything, and action."""
    mood, meaning = classify_market_mood(market)
    rows = getattr(market, "rows", [])
    movers = []
    for row in rows[:6]:
        label = row.get("label", row.get("ticker", "Market"))
        change = plain_number(row.get("change_pct"))
        if abs(change) >= 0.01:
            direction = "rose" if change >= 0 else "fell"
            movers.append(f"{label} {direction} {pct(abs(change))}")

    above_target = []
    total_gap_value = 0.0
    total_expected_saving = 0.0
    for d in decisions.values():
        gap_pct = plain_number(getattr(d, "gap_pct", 0.0))
        gap_eur = plain_number(getattr(d, "gap_eur", 0.0))
        saving = plain_number(getattr(d, "estimated_saving_eur", 0.0))
        total_expected_saving += max(saving, 0.0)
        if gap_pct > 0:
            above_target.append(f"{d.symbol} is {pct(gap_pct)} above target")
            total_gap_value += max(saving, 0.0)
        elif gap_eur <= 0:
            above_target.append(f"{d.symbol} is at or below target")

    if total_gap_value > 0:
        missed = (
            f"No clear execution was missed. The targets were still below the live prices. "
            f"Buying immediately instead of waiting for the model targets would cost about {money(total_gap_value)} more across the model deployment amounts."
        )
    else:
        missed = "At least one target appears to be reached or very close. Review the selected ETF and confirm final bid/ask in your broker."

    primary_symbol = getattr(primary, "symbol", next(iter(decisions.keys()), "selected ETF"))
    primary_action = getattr(primary, "action", "Wait with limit")

    action = (
        f"Maintain the current plan for {primary_symbol}: {primary_action.lower()}. "
        "Do not chase unless the target, spread, and broker quote confirm a better entry."
    )

    return {
        "mood": mood,
        "meaning": meaning,
        "movers": movers[:4],
        "missed": missed,
        "action": action,
        "total_expected_saving": total_expected_saving,
        "above_target": above_target[:3],
    }


def is_market_window_bahrain(now: dt.datetime | None = None) -> bool:
    """Broad trading-data window covering Europe + US sessions in Bahrain time.

    Yahoo quote timestamps are not exact, so this deliberately uses a practical
    window rather than exchange-specific seconds. Outside this window the app
    refreshes more slowly to reduce unnecessary calls.
    """
    now = now or (dt.datetime.utcnow() + dt.timedelta(hours=3))
    if now.weekday() >= 5:
        return False
    minutes = now.hour * 60 + now.minute
    return (10 * 60) <= minutes <= (24 * 60 - 5)


def refresh_interval_seconds() -> int:
    """Refresh market quotes on a 15-minute cadence during trading hours.

    PALI EXECUTE is an ETF deployment decision-support tool, not a
    second-by-second trading terminal. A 15-minute cadence aligns better with
    Yahoo/yfinance data behaviour, reduces unnecessary reruns, and is more
    stable on mobile/PWA. Outside the broad Europe + US trading window, refresh
    hourly because prices rarely change meaningfully.
    """
    return 900 if is_market_window_bahrain() else 3600


def quote_signature(market, decisions) -> tuple:
    """Small signature used to detect whether prices changed materially."""
    market_sig = tuple((r.get('ticker'), round(float(r.get('price', 0.0)), 4), round(float(r.get('change_pct', 0.0)), 4)) for r in market.rows)
    etf_sig = tuple((sym, round(float(d.live_price), 4), round(float(d.day_change_pct), 4)) for sym, d in decisions.items())
    return market_sig + etf_sig


def should_save_memory(market, decisions) -> bool:
    """Persist only when fresh quotes changed, avoiding duplicate Excel writes on refresh reruns."""
    sig = quote_signature(market, decisions)
    previous = st.session_state.get('_last_quote_signature')
    st.session_state['_last_quote_signature'] = sig
    return sig != previous

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
      @media (max-width:920px) { .cards, .timing-cards, .market-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
      @media (max-width:760px) { .cards, .timing-cards, .market-grid { grid-template-columns:1fr; } .stat-line { align-items:flex-start; } .stat-label { max-width:62%; } .stat-value { max-width:38%; } }
      @media (max-width:640px) { .card { border-radius:18px; padding:15px; width:100%; } .metric { font-size:23px; } .market-card { border-radius:18px; padding:14px; } .row .metric { max-width:48%; } }
      @media (max-width:430px) { .row { gap:8px; } .metric { white-space:normal; text-align:right; } .market-price { font-size:23px; } }
    </style>
    """
def render_fragment(html: str, height: int | None = None) -> None:
    """Render card HTML safely without fixed-height iframes.

    Streamlit Markdown can sometimes treat long nested HTML fragments as text
    when the fragment is malformed upstream or when mobile wrapping creates an
    unusual parse boundary. st.html renders the fragment as HTML directly and
    avoids raw <div> blocks appearing on the page. The height argument is kept
    for backward compatibility and intentionally ignored.
    """
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def topbar(fetched_at: str = "", interval_seconds: int = 60) -> None:
    subtitle = "ETF execution dashboard · V60A · VNGA80 · VWCE"
    # Keep the header clean: show only the latest available data timestamp.
    # The refresh cadence is handled silently in the background.
    stamp = f"<span class=\"live-dot\"></span> Updated {fetched_at or bahrain_now()}"
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
        change_5d = r.get("change_5d_pct")
        change_1m = r.get("change_1m_pct")
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
                <div><span>5 days</span><b class="{cls5}">{pct_or_na(change_5d, signed=True)}</b></div>
                <div><span>1 month</span><b class="{cls1m}">{pct_or_na(change_1m, signed=True)}</b></div>
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


def render_daily_brief(market, decisions, primary) -> None:
    """Render the 'what happened today' card below Today's Markets."""
    brief = build_daily_brief(market, decisions, primary)
    movers_html = "".join(f"<div class='muted'>• {m}</div>" for m in brief["movers"])
    target_html = "".join(f"<div class='muted'>• {x}</div>" for x in brief["above_target"])

    render_fragment(
        f"""
        <div class="card">
          <div class="eyebrow">AI daily brief</div>
          <h3>What happened today: {brief['mood']}</h3>
          <p class="muted" style="color:var(--text2);font-size:15px;line-height:1.55;margin:8px 0 0">{brief['meaning']}</p>
          <div class="divider"></div>
          <div class="row" style="align-items:flex-start">
            <div>
              <div class="eyebrow">Market moves</div>
              {movers_html or "<div class='muted'>• Market moves were small or unavailable.</div>"}
            </div>
            <div>
              <div class="eyebrow">ETF targets</div>
              {target_html or "<div class='muted'>• Targets are very close or data is unavailable.</div>"}
            </div>
          </div>
          <div class="divider"></div>
          <div class="muted" style="color:var(--text2);font-size:15px;line-height:1.55"><b>Did we miss today?</b> {brief['missed']}</div>
          <div class="muted" style="margin-top:8px;color:var(--text2);font-size:15px;line-height:1.55"><b>Next action:</b> {brief['action']}</div>
        </div>
        """,
        height=330,
    )


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


@st.cache_data(ttl=900, show_spinner=False)
def load_system_cached(refresh_key: int):
    market, decisions = build_decisions(refresh_key)
    primary = choose_primary(decisions)
    return market, decisions, primary


def load_system(refresh_key: int):
    with st.spinner("Updating live market data and decisions..."):
        market, decisions, primary = load_system_cached(refresh_key)
        try:
            if should_save_memory(market, decisions):
                save_run(APP_VERSION, market, decisions, primary)
        except Exception:
            logging.exception("Internal Excel memory update failed")
        return market, decisions, primary


def install_auto_refresh(seconds: int = 900) -> None:
    """Trigger a Streamlit rerun without forcing a browser page reload.

    This is smoother on mobile/PWA than window.location.reload(). The script
    still reruns, because that is how Streamlit updates data, but the browser
    tab itself is not hard-refreshed.
    """
    st_autorefresh(interval=seconds * 1000, key="pali_market_refresh")


def install_pwa_metadata() -> None:
    # Streamlit serves ./static when [server] enableStaticServing=true.
    # We inject metadata into the parent document so Android/iOS can offer
    # Add to Home Screen without changing the visual design.
    components.html(
        """
        <script>
          const d = window.parent.document;
          function upsertLink(rel, href, extra) {
            let l = d.querySelector('link[rel="' + rel + '"]');
            if (!l) { l = d.createElement('link'); l.rel = rel; d.head.appendChild(l); }
            l.href = href;
            if (extra) { Object.keys(extra).forEach(k => l.setAttribute(k, extra[k])); }
          }
          function upsertMeta(name, content) {
            let m = d.querySelector('meta[name="' + name + '"]');
            if (!m) { m = d.createElement('meta'); m.name = name; d.head.appendChild(m); }
            m.content = content;
          }
          const base = window.parent.location.origin + '/app/static/';
          upsertLink('manifest', base + 'manifest.webmanifest');
          upsertLink('apple-touch-icon', base + 'icon-192.png');
          upsertMeta('theme-color', '#0D1424');
          upsertMeta('apple-mobile-web-app-capable', 'yes');
          upsertMeta('apple-mobile-web-app-status-bar-style', 'black-translucent');
          upsertMeta('apple-mobile-web-app-title', 'PALI EXECUTE');
          upsertMeta('mobile-web-app-capable', 'yes');
          upsertMeta('application-name', 'PALI EXECUTE');
          // Service worker support in Streamlit is host-dependent; metadata works
          // for Add to Home Screen where the browser permits it.
          if ('serviceWorker' in window.parent.navigator) {
            window.parent.navigator.serviceWorker.register(base + 'service-worker.js', {scope: '/app/static/'})
              .catch(function(){ });
          }
        </script>
        """,
        height=0,
    )


def main() -> None:
    if "refresh_key" not in st.session_state:
        st.session_state["refresh_key"] = 0

    interval = refresh_interval_seconds()
    install_pwa_metadata()
    install_auto_refresh(interval)

    market, decisions, primary = load_system(st.session_state["refresh_key"])
    topbar(market.fetched_at, interval)

    render_market(market)
    render_daily_brief(market, decisions, primary)
    render_etf_cards(decisions)
    render_timing_plan(decisions)
    selected = select_etf(decisions)
    render_selected_etf(decisions[selected])

    with st.expander("Analytics table", expanded=False):
        render_analytics(decisions)


if __name__ == "__main__":
    main()
