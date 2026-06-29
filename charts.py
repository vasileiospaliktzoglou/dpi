import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from config import TICKERS, TIMEFRAME_MAP
from helpers import fetch_chart_data


def _to_float(value, default=np.nan):
    try:
        return float(value)
    except Exception:
        return default


def _fmt(value):
    try:
        return f"EUR {float(value):.2f}"
    except Exception:
        return "EUR --"


def _clean(df):
    df = df.copy()
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["Date", "Close"]).sort_values("Date").reset_index(drop=True)


def _line_segments(df, reference):
    close = df["Close"]
    above = close.where(close >= reference)
    below = close.where(close < reference)
    return above, below


def _add_hline(fig, y, label, color, dash="dot", width=1.2):
    y = _to_float(y)
    if np.isnan(y):
        return
    fig.add_hline(
        y=y,
        row=1,
        col=1,
        line_color=color,
        line_dash=dash,
        line_width=width,
        opacity=0.95,
        annotation_text=label,
        annotation_position="right",
        annotation_font_color=color,
        annotation_font_size=11,
    )


def _chart_range(df, target=None, atr=None, reference=None):
    vals = []
    for col in ["Low", "High", "Close"]:
        if col in df.columns and not df[col].dropna().empty:
            vals.extend([df[col].min(), df[col].max()])
    for v in [target, reference]:
        v = _to_float(v)
        if not np.isnan(v):
            vals.append(v)
    vals = [float(v) for v in vals if not pd.isna(v)]
    if not vals:
        return None
    lo, hi = min(vals), max(vals)
    spread = max(hi - lo, 0.01)
    pad = spread * 0.32
    atr = _to_float(atr)
    if not np.isnan(atr) and atr > 0:
        pad = max(pad, atr * 0.40)
    return [lo - pad, hi + pad]


def _status_story(current, low, target, atr):
    distance = current - target
    distance_pct = distance / target * 100 if target else 0.0
    low_distance = low - target
    low_distance_pct = low_distance / target * 100 if target else 0.0
    atr_distance = distance / atr if atr and atr > 0 else np.nan

    if low <= target:
        status = "Target reached"
        meaning = "The ETF traded at or below your limit. If your DAY order was active, it should have filled or come very close depending on spread."
        progress = 100
        tone = "good"
    elif distance_pct <= 0.25:
        status = "Very close"
        meaning = "Only a small intraday move is needed. Keep the limit order; do not chase upward."
        progress = 82
        tone = "good"
    elif distance_pct <= 0.75:
        status = "Waiting"
        meaning = "The target is still possible today, but it needs a meaningful pullback."
        progress = 55
        tone = "wait"
    else:
        status = "Far from target"
        meaning = "The limit is not close. Treat this as monitor-only unless price weakens."
        progress = 25
        tone = "far"

    return {
        "status": status,
        "meaning": meaning,
        "distance": distance,
        "distance_pct": distance_pct,
        "low_distance": low_distance,
        "low_distance_pct": low_distance_pct,
        "atr_distance": atr_distance,
        "progress": progress,
        "tone": tone,
    }


def _render_chart_story(current, low, target, atr, story):
    atr_txt = "n/a" if np.isnan(story["atr_distance"]) else f"{story['atr_distance']:.2f}x ATR"
    fill_class = "chart-progress-fill-good" if story["tone"] == "good" else "chart-progress-fill-warn" if story["tone"] == "wait" else "chart-progress-fill"
    st.markdown(
        f"""
        <div class="chart-story-card pro-story">
            <div class="chart-story-title">Chart story: {story['status']}</div>
            <div class="chart-progress-bg"><div class="{fill_class}" style="width:{story['progress']}%"></div></div>
            <div class="chart-story-grid">
                <div><b>Current</b><br>{_fmt(current)}</div>
                <div><b>Today low</b><br>{_fmt(low)}</div>
                <div><b>Target</b><br>{_fmt(target)}</div>
                <div><b>Distance</b><br>EUR {story['distance']:.2f} ({story['distance_pct']:.2f}%)</div>
                <div><b>Low missed by</b><br>EUR {story['low_distance']:.2f} ({story['low_distance_pct']:.2f}%)</div>
                <div><b>ATR distance</b><br>{atr_txt}</div>
            </div>
            <div class="chart-story-text">{story['meaning']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plot_meaningful_chart(df, asset, timeframe, target=None, atr=None):
    df = _clean(df)
    if df.empty:
        return go.Figure()

    has_volume = "Volume" in df.columns and df["Volume"].fillna(0).sum() > 0
    fig = make_subplots(
        rows=2 if has_volume else 1,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=[0.84, 0.16] if has_volume else [1.0],
    )

    current = _to_float(df["Close"].iloc[-1])
    reference = _to_float(df["Open"].iloc[0]) if "Open" in df.columns else _to_float(df["Close"].iloc[0])
    target = _to_float(target)
    low = _to_float(df["Low"].min()) if "Low" in df.columns else _to_float(df["Close"].min())

    above, below = _line_segments(df, reference)
    fig.add_trace(go.Scatter(x=df["Date"], y=above, mode="lines", name="Above reference", line=dict(color="#059669", width=3.0, shape="spline", smoothing=0.65), connectgaps=False, hovertemplate="%{x}<br>Price: EUR %{y:.2f}<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=below, mode="lines", name="Below reference", line=dict(color="#dc2626", width=3.0, shape="spline", smoothing=0.65), connectgaps=False, hovertemplate="%{x}<br>Price: EUR %{y:.2f}<extra></extra>"), row=1, col=1)

    if len(df) >= 20:
        ema = df["Close"].ewm(span=20, adjust=False).mean()
        fig.add_trace(go.Scatter(x=df["Date"], y=ema, mode="lines", name="EMA20", line=dict(color="rgba(37,99,235,.45)", width=1.2), hovertemplate="%{x}<br>EMA20: EUR %{y:.2f}<extra></extra>"), row=1, col=1)

    _add_hline(fig, reference, "Reference", "#94a3b8", "dot", 1.0)
    _add_hline(fig, current, "Current", "#2563eb", "solid", 1.25)
    if not np.isnan(target):
        _add_hline(fig, target, "DAY limit", "#059669", "dash", 1.8)

    fig.add_trace(go.Scatter(x=[df["Date"].iloc[-1]], y=[current], mode="markers+text", marker=dict(size=10, color="#2563eb", line=dict(color="white", width=1.5)), text=[f"{current:.2f}"], textposition="middle right", textfont=dict(size=12, color="#2563eb"), name="Current", showlegend=False, hovertemplate="Current: EUR %{y:.2f}<extra></extra>"), row=1, col=1)

    if has_volume:
        vol = df["Volume"].fillna(0)
        fig.add_trace(go.Bar(x=df["Date"], y=vol, name="Volume", marker=dict(color="rgba(148,163,184,.35)"), hovertemplate="%{x}<br>Volume: %{y:,.0f}<extra></extra>"), row=2, col=1)
        fig.update_yaxes(visible=False, row=2, col=1)

    yrange = _chart_range(df, target=target, atr=atr, reference=reference)
    fig.update_layout(
        height=540,
        margin=dict(l=8, r=52, t=16, b=8),
        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="x unified",
        showlegend=False,
        font=dict(family="Inter, Arial, sans-serif", size=12, color="#334155"),
        xaxis=dict(showgrid=False, zeroline=False, rangeslider=dict(visible=False)),
        yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.22)", zeroline=False, tickprefix="EUR ", side="right", range=yrange),
    )
    if has_volume:
        fig.update_xaxes(showgrid=False, row=2, col=1)
        fig.update_yaxes(showgrid=False, row=2, col=1)

    return fig


def render_chart(asset, target, atr=None, *args, **kwargs):
    if asset not in TICKERS:
        st.warning("Unknown asset selected.")
        return

    timeframe_key = f"chart_timeframe_{asset}"
    if timeframe_key not in st.session_state:
        st.session_state[timeframe_key] = "1D"

    # A compact tab-like selector above the central chart.
    tf = st.radio(
        "Timeframe",
        list(TIMEFRAME_MAP.keys()),
        key=timeframe_key,
        horizontal=True,
        label_visibility="collapsed",
    )

    period, interval = TIMEFRAME_MAP.get(tf, ("1d", "5m"))
    df = fetch_chart_data(TICKERS[asset], period=period, interval=interval)
    df = _clean(df)
    if df.empty:
        st.info("No chart data available yet. Confirm price in IBKR.")
        return

    fig = plot_meaningful_chart(df, asset, tf, target=target, atr=atr)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    current = _to_float(df["Close"].iloc[-1])
    low = _to_float(df["Low"].min()) if "Low" in df.columns else current
    story = _status_story(current, low, _to_float(target), _to_float(atr))
    _render_chart_story(current, low, _to_float(target), _to_float(atr), story)
