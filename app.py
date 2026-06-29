import calendar
from datetime import date, datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf


APP_NAME = "DPI — Daily Portfolio Intelligence"
APP_VERSION = "v6 Pro"

ETFS = {
    "V60A": {
        "ticker": "V60A.AS",
        "name": "Vanguard LifeStrategy 60% Equity UCITS ETF",
        "role": "Core Defensive Growth",
        "default_allocation": 0.60,
    },
    "V80A": {
        "ticker": "V80A.AS",
        "name": "Vanguard LifeStrategy 80% Equity UCITS ETF",
        "role": "Core Growth",
        "default_allocation": 0.30,
    },
    "VWCE": {
        "ticker": "VWCE.DE",
        "name": "Vanguard FTSE All-World UCITS ETF",
        "role": "Global Equity Satellite",
        "default_allocation": 0.10,
    },
}

MARKET_INDICATORS = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "VIX": "^VIX",
    "EUR/USD": "EURUSD=X",
    "Gold": "GC=F",
    "Brent Oil": "BZ=F",
    "US 10Y Yield": "^TNX",
}


st.set_page_config(page_title=f"{APP_NAME} {APP_VERSION}", layout="wide")


st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1380px;
    }
    .hero {
        padding: 1.15rem 1.35rem;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(0,194,168,0.18), rgba(75,104,255,0.12));
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 2rem;
        letter-spacing: -0.03em;
    }
    .hero p {
        color: #B8C0CC;
        margin-top: 0.35rem;
        margin-bottom: 0;
    }
    .card {
        padding: 1rem;
        border-radius: 16px;
        background: #141A24;
        border: 1px solid rgba(255,255,255,0.07);
        box-shadow: 0 6px 26px rgba(0,0,0,0.18);
        min-height: 250px;
    }
    .card h2 {
        margin-top: 0.3rem;
        margin-bottom: 0.1rem;
    }
    .muted {
        color: #9AA4B2;
        font-size: 0.9rem;
    }
    .action-box {
        padding: 1rem;
        border-radius: 14px;
        background: rgba(0,194,168,0.10);
        border: 1px solid rgba(0,194,168,0.35);
        margin-top: 0.5rem;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 14px;
        background: rgba(255,193,7,0.10);
        border: 1px solid rgba(255,193,7,0.28);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=900, show_spinner=False)
def download_history(ticker: str, period: str = "1y") -> pd.DataFrame:
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

    required = {"Open", "High", "Low", "Close"}
    missing = required.difference(set(df.columns))
    if missing:
        raise ValueError(f"Missing columns for {ticker}: {missing}")

    return df.dropna(subset=["Open", "High", "Low", "Close"])


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def build_etf_signal(symbol: str, meta: dict, atr_multiplier: float, atr_period: int = 14) -> dict:
    df = download_history(meta["ticker"], period="1y").copy()
    df["ATR"] = calculate_atr(df, atr_period)
    df["RSI"] = rsi(df["Close"], 14)
    clean = df.dropna()

    latest = clean.iloc[-1]
    previous = clean.iloc[-2] if len(clean) > 1 else latest

    close = float(latest["Close"])
    prev_close = float(previous["Close"])
    low = float(latest["Low"])
    atr = float(latest["ATR"])
    rsi_value = float(latest["RSI"])
    target = close - (atr * atr_multiplier)

    high_60d = float(clean["Close"].tail(60).max())
    high_252d = float(clean["Close"].tail(252).max())
    ma_200 = float(clean["Close"].tail(200).mean()) if len(clean) >= 200 else np.nan

    return {
        "ETF": symbol,
        "Ticker": meta["ticker"],
        "Name": meta["name"],
        "Role": meta["role"],
        "Allocation": meta["default_allocation"],
        "Close": close,
        "DailyChangePct": ((close - prev_close) / prev_close) * 100 if prev_close else 0,
        "Low": low,
        "ATR": atr,
        "ATRTarget": target,
        "TargetDistancePct": ((close - target) / close) * 100,
        "RSI14": rsi_value,
        "Drawdown60D": ((close - high_60d) / high_60d) * 100 if high_60d else 0,
        "Drawdown1Y": ((close - high_252d) / high_252d) * 100 if high_252d else 0,
        "MA200": ma_200,
        "DistanceMA200Pct": ((close - ma_200) / ma_200) * 100 if ma_200 and not np.isnan(ma_200) else np.nan,
        "TrapTouchedToday": low <= target,
    }


def get_market_indicator(name: str, ticker: str) -> dict:
    try:
        df = download_history(ticker, period="10d")
        last = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2])
        return {
            "Indicator": name,
            "Ticker": ticker,
            "Value": last,
            "DailyChangePct": ((last - prev) / prev) * 100 if prev else 0,
            "Status": "OK",
        }
    except Exception as exc:
        return {
            "Indicator": name,
            "Ticker": ticker,
            "Value": np.nan,
            "DailyChangePct": np.nan,
            "Status": str(exc),
        }


def classify_vix(vix: float | None) -> str:
    if vix is None or np.isnan(vix):
        return "Unknown"
    if vix < 18:
        return "Calm / Risk-on"
    if vix < 25:
        return "Normal / Watch"
    if vix < 35:
        return "Elevated Risk"
    return "Panic / Opportunity"


def build_market_sentiment(rows: list[dict]) -> dict:
    vix_row = next((r for r in rows if r["Indicator"] == "VIX"), None)
    vix = None if vix_row is None or pd.isna(vix_row["Value"]) else float(vix_row["Value"])
    regime = classify_vix(vix)

    equities = [
        r for r in rows
        if r["Indicator"] in ["S&P 500", "Nasdaq"] and not pd.isna(r["DailyChangePct"])
    ]

    if not equities:
        label = "Neutral"
    else:
        avg = sum(r["DailyChangePct"] for r in equities) / len(equities)
        if vix is not None and vix >= 35:
            label = "Fear / Potential Opportunity"
        elif avg > 0.50 and (vix is None or vix < 25):
            label = "Constructive"
        elif avg < -0.80:
            label = "Risk-off"
        else:
            label = "Neutral"

    return {"label": label, "regime": regime, "vix": vix, "rows": rows}


def month_end_status(fallback_day: int) -> dict:
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    days_left = max(0, last_day - today.day)
    fallback = today.day >= fallback_day
    return {
        "fallback": fallback,
        "days_left": days_left,
        "message": (
            "Fallback window active: if ATR trap has not filled, prepare the month-end buy."
            if fallback
            else "ATR trap window active: use daily adaptive limit orders."
        ),
    }


def opportunity_score(signal: dict, market: dict) -> tuple[int, str, list[str]]:
    score = 0
    reasons = []

    drawdown = abs(signal["Drawdown1Y"])
    if drawdown >= 20:
        score += 35
        reasons.append("major 1-year drawdown")
    elif drawdown >= 12:
        score += 27
        reasons.append("meaningful 1-year drawdown")
    elif drawdown >= 6:
        score += 18
        reasons.append("moderate pullback")
    else:
        score += 7
        reasons.append("limited discount from highs")

    vix = market.get("vix")
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

    rsi_value = signal.get("RSI14")
    if rsi_value < 35:
        score += 15
        reasons.append("RSI cooldown")
    elif rsi_value < 45:
        score += 8
        reasons.append("mild RSI cooldown")
    elif rsi_value > 70:
        score -= 10
        reasons.append("RSI extended")

    if signal["TargetDistancePct"] >= 1:
        score += 8
        reasons.append("meaningful ATR target distance")
    else:
        score += 4
        reasons.append("tight ATR target distance")

    score = max(0, min(100, int(score)))

    if score >= 80:
        label = "Exceptional opportunity"
    elif score >= 60:
        label = "Good opportunity"
    elif score >= 40:
        label = "Normal opportunity"
    else:
        label = "Low urgency"

    return score, label, reasons


def build_daily_brief(signals: list[dict], market: dict, status: dict, monthly_allocation: int, opp: tuple) -> str:
    score, label, reasons = opp

    lines = [
        "📊 DPI Daily Investment Brief",
        datetime.now().strftime("%d %b %Y, %H:%M"),
        "",
        f"Market sentiment: {market['label']}",
        f"Market regime: {market['regime']}",
        f"Execution status: {status['message']}",
        f"Days until month-end: {status['days_left']}",
        "",
        f"Opportunity score: {score}/100 — {label}",
        "Drivers: " + "; ".join(reasons),
        "",
        "ETF ATR targets:",
    ]

    for s in signals:
        touched = "yes" if s["TrapTouchedToday"] else "no"
        lines.append(
            f"- {s['ETF']}: close €{s['Close']:.2f}, target €{s['ATRTarget']:.2f}, "
            f"distance {s['TargetDistancePct']:.2f}%, RSI {s['RSI14']:.1f}, trap touched today: {touched}"
        )

    lines.extend([
        "",
        f"Monthly allocation reference: €{monthly_allocation:,.0f}",
        "Action: place DAY limit at the ATR target. If not filled by month-end, execute the planned monthly buy.",
    ])

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
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=55, b=20), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


def render_order_cards(signals: list[dict]):
    cols = st.columns(len(signals))
    for col, s in zip(cols, signals):
        touched = "✅ Yes" if s["TrapTouchedToday"] else "⏳ No"
        with col:
            st.markdown(
                f"""
                <div class="card">
                    <h3>{s['ETF']}</h3>
                    <p class="muted">{s['Role']}</p>
                    <h2>€{s['ATRTarget']:.2f}</h2>
                    <p>Tomorrow's ATR limit</p>
                    <hr>
                    <p><b>Close:</b> €{s['Close']:.2f}</p>
                    <p><b>ATR:</b> €{s['ATR']:.2f}</p>
                    <p><b>RSI:</b> {s['RSI14']:.1f}</p>
                    <p><b>Distance:</b> {s['TargetDistancePct']:.2f}%</p>
                    <p><b>Trap touched today:</b> {touched}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


st.markdown(
    f"""
    <div class="hero">
        <h1>📊 {APP_NAME}</h1>
        <p>{APP_VERSION}: ATR trap execution, daily market brief, opportunity scoring, and clean ETF command center.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("Control Panel")

    atr_multiplier = st.selectbox(
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

    st.caption("Stable pre-v7 build. No sliders. No fragile multi-page routing.")


signals = []
for symbol, meta in ETFS.items():
    try:
        signals.append(build_etf_signal(symbol, meta, float(atr_multiplier)))
    except Exception as exc:
        st.error(f"Could not load {symbol} ({meta['ticker']}): {exc}")

market_rows = [get_market_indicator(name, ticker) for name, ticker in MARKET_INDICATORS.items()]
market = build_market_sentiment(market_rows)
status = month_end_status(int(fallback_day))

main_signal = next((s for s in signals if s["ETF"] == "V60A"), signals[0] if signals else None)
opp = opportunity_score(main_signal, market) if main_signal else (0, "Unknown", ["No ETF data available"])

tab1, tab2, tab3, tab4 = st.tabs([
    "📌 Daily Brief",
    "🎯 ATR Orders",
    "🌍 Market Sentiment",
    "📈 Opportunity",
])

with tab1:
    st.subheader("Executive Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Market Sentiment", market["label"])
    c2.metric("Market Regime", market["regime"])
    c3.metric("ATR Multiplier", f"{atr_multiplier:.2f}x")
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

    st.subheader("Daily Investment Brief")
    st.code(build_daily_brief(signals, market, status, int(monthly_allocation), opp))

with tab2:
    st.subheader("Tomorrow's ATR Limit Orders")
    if signals:
        render_order_cards(signals)

        st.subheader("ETF Command Center")
        df = pd.DataFrame(signals)
        display_cols = [
            "ETF", "Ticker", "Role", "Close", "DailyChangePct", "Low", "ATR",
            "ATRTarget", "TargetDistancePct", "RSI14", "Drawdown60D",
            "Drawdown1Y", "DistanceMA200Pct", "TrapTouchedToday"
        ]
        display = df[display_cols].copy()
        for col in [
            "Close", "DailyChangePct", "Low", "ATR", "ATRTarget", "TargetDistancePct",
            "RSI14", "Drawdown60D", "Drawdown1Y", "DistanceMA200Pct"
        ]:
            display[col] = display[col].map(lambda x: round(x, 3) if not pd.isna(x) else None)

        display = display.rename(columns={
            "DailyChangePct": "Daily %",
            "ATRTarget": "ATR Target",
            "TargetDistancePct": "Target Distance %",
            "RSI14": "RSI 14",
            "Drawdown60D": "60D DD %",
            "Drawdown1Y": "1Y DD %",
            "DistanceMA200Pct": "Distance 200DMA %",
            "TrapTouchedToday": "Trap touched?",
        })
        st.dataframe(display, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Daily Market Sentiment")
    mdf = pd.DataFrame(market["rows"])
    for col in ["Value", "DailyChangePct"]:
        mdf[col] = mdf[col].map(lambda x: round(x, 3) if not pd.isna(x) else None)
    mdf = mdf.rename(columns={"DailyChangePct": "Daily %"})
    st.dataframe(mdf, use_container_width=True, hide_index=True)

    st.markdown(
        """
        ### Institutional read
        The sentiment page does not predict tomorrow. It gives context for execution:
        whether markets are calm, normal, elevated-risk, or panic-like.
        """
    )

with tab4:
    st.subheader("Opportunity Meter")
    score, label, reasons = opp
    col1, col2 = st.columns([1, 2])
    with col1:
        render_gauge(score, label)
    with col2:
        st.markdown("### Why this score?")
        for r in reasons:
            st.write(f"• {r}")

        if score >= 80:
            st.success("Exceptional environment. Review whether opportunity reserve should be used.")
        elif score >= 60:
            st.info("Good environment. Standard DCA plus modest extra allocation may be considered.")
        elif score >= 40:
            st.warning("Normal environment. Use standard DCA discipline.")
        else:
            st.info("Low urgency. Let the ATR trap work; avoid chasing.")
