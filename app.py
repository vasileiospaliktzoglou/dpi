import calendar
from datetime import date, datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf


APP_VERSION = "DPI v1.0"

ETFS = {
    "V60A": {
        "ticker": "V60A.AS",
        "role": "Core Defensive Growth",
    },
    "V80A": {
        "ticker": "V80A.AS",
        "role": "Core Growth",
    },
    "VWCE": {
        "ticker": "VWCE.DE",
        "role": "Global Equity Satellite",
    },
}

MARKET = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "VIX": "^VIX",
    "EUR/USD": "EURUSD=X",
    "Gold": "GC=F",
    "Brent Oil": "BZ=F",
    "US 10Y Yield": "^TNX",
}


st.set_page_config(page_title=APP_VERSION, layout="wide")


st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1.2rem;
        max-width: 1350px;
    }
    .hero {
        padding: 1.2rem 1.4rem;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(0,194,168,0.18), rgba(51,102,255,0.12));
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 2rem;
    }
    .hero p {
        color: #B8C0CC;
        margin-top: 0.35rem;
    }
    .card {
        padding: 1rem;
        border-radius: 16px;
        background: #141A24;
        border: 1px solid rgba(255,255,255,0.08);
        min-height: 245px;
    }
    .action-box {
        padding: 1rem;
        border-radius: 14px;
        background: rgba(0,194,168,0.10);
        border: 1px solid rgba(0,194,168,0.35);
    }
    .muted {
        color: #9AA4B2;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=900)
def get_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    df = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if df is None or df.empty:
        raise ValueError(f"No data returned for {ticker}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df.dropna(subset=["Open", "High", "Low", "Close"])


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def get_etf_signal(symbol: str, meta: dict, multiplier: float) -> dict:
    df = get_history(meta["ticker"])
    df["ATR"] = calculate_atr(df, 14)
    clean = df.dropna()

    latest = clean.iloc[-1]
    previous = clean.iloc[-2] if len(clean) > 1 else latest

    close = float(latest["Close"])
    prev_close = float(previous["Close"])
    low = float(latest["Low"])
    atr = float(latest["ATR"])
    target = close - (atr * multiplier)

    high_60d = float(clean["Close"].tail(60).max())
    high_252d = float(clean["Close"].tail(252).max())

    return {
        "ETF": symbol,
        "Ticker": meta["ticker"],
        "Role": meta["role"],
        "Close": close,
        "Daily %": ((close - prev_close) / prev_close) * 100 if prev_close else 0,
        "Low": low,
        "ATR": atr,
        "Target": target,
        "Target Distance %": ((close - target) / close) * 100,
        "60D DD %": ((close - high_60d) / high_60d) * 100 if high_60d else 0,
        "1Y DD %": ((close - high_252d) / high_252d) * 100 if high_252d else 0,
        "Trap touched today": low <= target,
    }


def get_market_row(name: str, ticker: str) -> dict:
    try:
        df = get_history(ticker, period="10d")
        last = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2])
        return {
            "Indicator": name,
            "Ticker": ticker,
            "Value": last,
            "Daily %": ((last - prev) / prev) * 100 if prev else 0,
            "Status": "OK",
        }
    except Exception as exc:
        return {
            "Indicator": name,
            "Ticker": ticker,
            "Value": np.nan,
            "Daily %": np.nan,
            "Status": str(exc),
        }


def classify_regime(vix: float | None) -> str:
    if vix is None or np.isnan(vix):
        return "Unknown"
    if vix < 18:
        return "Calm / Risk-on"
    if vix < 25:
        return "Normal / Watch"
    if vix < 35:
        return "Elevated Risk"
    return "Panic / Opportunity"


def market_sentiment(rows: list[dict]) -> tuple[str, str, float | None]:
    vix_rows = [r for r in rows if r["Indicator"] == "VIX"]
    vix = vix_rows[0]["Value"] if vix_rows else np.nan
    regime = classify_regime(vix)

    equity_rows = [r for r in rows if r["Indicator"] in ["S&P 500", "Nasdaq"] and not np.isnan(r["Daily %"])]
    if not equity_rows:
        label = "Neutral"
    else:
        avg = sum(r["Daily %"] for r in equity_rows) / len(equity_rows)
        if not np.isnan(vix) and vix >= 35:
            label = "Fear / Potential Opportunity"
        elif avg > 0.5 and (np.isnan(vix) or vix < 25):
            label = "Constructive"
        elif avg < -0.8:
            label = "Risk-off"
        else:
            label = "Neutral"

    return label, regime, None if np.isnan(vix) else float(vix)


def month_status(fallback_day: int) -> dict:
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    days_left = max(0, last_day - today.day)
    fallback = today.day >= fallback_day
    msg = (
        "Fallback window active: if ATR trap has not filled, prepare the month-end buy."
        if fallback
        else "ATR trap window active: use the next daily adaptive limit order."
    )
    return {"fallback": fallback, "days_left": days_left, "message": msg}


def opportunity(signal: dict, vix: float | None) -> tuple[int, str, list[str]]:
    score = 0
    reasons = []

    dd = abs(signal["1Y DD %"])
    if dd >= 20:
        score += 35
        reasons.append("major 1-year drawdown")
    elif dd >= 12:
        score += 27
        reasons.append("meaningful 1-year drawdown")
    elif dd >= 6:
        score += 18
        reasons.append("moderate pullback")
    else:
        score += 7
        reasons.append("limited discount from highs")

    if vix is not None:
        if vix >= 35:
            score += 35
            reasons.append("panic-level volatility")
        elif vix >= 25:
            score += 25
            reasons.append("elevated volatility")
        elif vix >= 18:
            score += 15
            reasons.append("normal volatility")
        else:
            score += 6
            reasons.append("calm volatility")

    distance = signal["Target Distance %"]
    if distance >= 2:
        score += 15
        reasons.append("wide ATR target distance")
    elif distance >= 1:
        score += 10
        reasons.append("normal ATR target distance")
    else:
        score += 5
        reasons.append("tight ATR target distance")

    score = max(0, min(100, int(score)))

    if score >= 80:
        label = "Exceptional"
    elif score >= 60:
        label = "Good"
    elif score >= 40:
        label = "Normal"
    else:
        label = "Low urgency"

    return score, label, reasons


def daily_brief(signals: list[dict], sentiment: str, regime: str, status: dict, monthly: int, opp: tuple) -> str:
    score, label, reasons = opp

    lines = [
        "📊 DPI Daily Investment Brief",
        datetime.now().strftime("%d %b %Y, %H:%M"),
        "",
        f"Market sentiment: {sentiment}",
        f"Market regime: {regime}",
        f"Execution status: {status['message']}",
        f"Days until month-end: {status['days_left']}",
        "",
        f"Opportunity score: {score}/100 — {label}",
        "Reason: " + "; ".join(reasons),
        "",
        "ETF ATR targets:",
    ]

    for s in signals:
        touched = "yes" if s["Trap touched today"] else "no"
        lines.append(
            f"- {s['ETF']}: close €{s['Close']:.2f}, target €{s['Target']:.2f}, "
            f"distance {s['Target Distance %']:.2f}%, trap touched today: {touched}"
        )

    lines += [
        "",
        f"Monthly allocation reference: €{monthly:,.0f}",
        "Action: place DAY limit at the ATR target. If not filled by month-end, execute the planned monthly buy.",
    ]

    return "\n".join(lines)


def render_gauge(score: int, label: str):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": label},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"thickness": 0.25},
                "steps": [
                    {"range": [0, 40], "color": "rgba(255,255,255,0.08)"},
                    {"range": [40, 60], "color": "rgba(255,255,255,0.14)"},
                    {"range": [60, 80], "color": "rgba(255,255,255,0.20)"},
                    {"range": [80, 100], "color": "rgba(255,255,255,0.28)"},
                ],
            },
        )
    )
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


st.markdown(
    f"""
    <div class="hero">
        <h1>📊 {APP_VERSION}</h1>
        <p>Daily ETF decision-support: ATR targets, market sentiment, opportunity scoring, and month-end discipline.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("Control Panel")

    multiplier = st.selectbox(
        "ATR multiplier",
        options=[0.80, 0.90, 1.00, 1.10, 1.15, 1.20, 1.30, 1.50],
        index=4,
    )

    monthly_allocation = st.number_input(
        "Monthly allocation (€)",
        min_value=1000,
        max_value=100000,
        value=20000,
        step=1000,
    )

    fallback_day = st.selectbox(
        "Month-end fallback day",
        options=[25, 26, 27, 28, 29, 30, 31],
        index=3,
    )

    st.caption("No sliders are used in this version to avoid Streamlit Cloud frontend loading issues.")


signals = []
for symbol, meta in ETFS.items():
    try:
        signals.append(get_etf_signal(symbol, meta, float(multiplier)))
    except Exception as exc:
        st.error(f"Could not load {symbol} ({meta['ticker']}): {exc}")

market_rows = [get_market_row(name, ticker) for name, ticker in MARKET.items()]
sentiment, regime, vix = market_sentiment(market_rows)
status = month_status(int(fallback_day))

main_signal = next((s for s in signals if s["ETF"] == "V60A"), signals[0] if signals else None)
opp = opportunity(main_signal, vix) if main_signal else (0, "Unknown", ["No ETF data available"])

tab1, tab2, tab3, tab4 = st.tabs(["📌 Daily Brief", "🎯 ATR Orders", "🌍 Market", "📈 Opportunity"])

with tab1:
    st.subheader("Executive Summary")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sentiment", sentiment)
    c2.metric("Regime", regime)
    c3.metric("ATR Multiplier", f"{multiplier:.2f}x")
    c4.metric("Monthly Allocation", f"€{monthly_allocation:,.0f}")

    st.markdown(
        f"""
        <div class="action-box">
            <b>Execution status:</b> {status['message']}<br>
            <span class="muted">Days until month-end: {status['days_left']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Daily Brief")
    st.code(daily_brief(signals, sentiment, regime, status, int(monthly_allocation), opp))

with tab2:
    st.subheader("Tomorrow's ATR Limit Orders")

    if signals:
        cols = st.columns(len(signals))
        for col, s in zip(cols, signals):
            with col:
                touched = "✅ Yes" if s["Trap touched today"] else "⏳ No"
                st.markdown(
                    f"""
                    <div class="card">
                        <h3>{s['ETF']}</h3>
                        <p class="muted">{s['Role']}</p>
                        <h2>€{s['Target']:.2f}</h2>
                        <p>Tomorrow's ATR limit</p>
                        <hr>
                        <p><b>Close:</b> €{s['Close']:.2f}</p>
                        <p><b>ATR:</b> €{s['ATR']:.2f}</p>
                        <p><b>Distance:</b> {s['Target Distance %']:.2f}%</p>
                        <p><b>Trap touched today:</b> {touched}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.subheader("ETF Command Center")
        df = pd.DataFrame(signals)
        display_cols = [
            "ETF", "Ticker", "Role", "Close", "Daily %", "Low", "ATR",
            "Target", "Target Distance %", "60D DD %", "1Y DD %", "Trap touched today"
        ]
        display = df[display_cols].copy()
        for col in ["Close", "Daily %", "Low", "ATR", "Target", "Target Distance %", "60D DD %", "1Y DD %"]:
            display[col] = display[col].map(lambda x: round(x, 3))
        st.dataframe(display, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Market Sentiment Inputs")
    mdf = pd.DataFrame(market_rows)
    for col in ["Value", "Daily %"]:
        mdf[col] = mdf[col].map(lambda x: round(x, 3) if not pd.isna(x) else None)
    st.dataframe(mdf, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Opportunity Meter")
    score, label, reasons = opp
    c1, c2 = st.columns([1, 2])
    with c1:
        render_gauge(score, label)
    with c2:
        st.markdown("### Why this score?")
        for r in reasons:
            st.write(f"• {r}")

        if score >= 80:
            st.success("Exceptional environment. Review whether opportunity reserve should be used.")
        elif score >= 60:
            st.info("Good environment. Standard DCA plus modest extra may be considered.")
        elif score >= 40:
            st.warning("Normal environment. Use standard DCA discipline.")
        else:
            st.info("Low urgency. Let the ATR trap work; avoid chasing.")
