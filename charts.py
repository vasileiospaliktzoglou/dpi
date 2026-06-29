import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from config import TICKERS
from helpers import fetch_chart_data


def _safe_float(value, default=np.nan):
    try:
        return float(value)
    except Exception:
        return default


def _clean_numeric(df):
    df = df.copy().sort_values("Date").reset_index(drop=True)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["Date", "Close"]).reset_index(drop=True)


def _target_status(current, session_low, target, atr=None):
    distance = current - target
    distance_pct = (distance / target) * 100 if target else 0.0
    low_distance = session_low - target
    low_distance_pct = (low_distance / target) * 100 if target else 0.0
    atr_distance = distance / atr if atr and atr > 0 else np.nan

    if session_low <= target:
        return {
            "status": "Target reached",
            "tone": "filled",
            "plain": "The ETF has already traded at or below your limit level today. If your DAY order was live, it should have filled or come very close depending on spread and exchange execution.",
            "distance": distance,
            "distance_pct": distance_pct,
            "low_distance": low_distance,
            "low_distance_pct": low_distance_pct,
            "atr_distance": atr_distance,
        }
    if distance_pct <= 0.25:
        return {
            "status": "Very close",
            "tone": "close",
            "plain": "The target is close. A normal small pullback could still reach your limit price today.",
            "distance": distance,
            "distance_pct": distance_pct,
            "low_distance": low_distance,
            "low_distance_pct": low_distance_pct,
            "atr_distance": atr_distance,
        }
    if distance_pct <= 0.75:
        return {
            "status": "Waiting",
            "tone": "wait",
            "plain": "The target is still possible today, but it needs a meaningful intraday pullback. Do not chase the price upward.",
            "distance": distance,
            "distance_pct": distance_pct,
            "low_distance": low_distance,
            "low_distance_pct": low_distance_pct,
            "atr_distance": atr_distance,
        }
    return {
        "status": "Far from target",
        "tone": "far",
        "plain": "The target is not close yet. Treat this as monitor-only unless the ETF moves lower or the model recalculates after the close.",
        "distance": distance,
        "distance_pct": distance_pct,
        "low_distance": low_distance,
        "low_distance_pct": low_distance_pct,
        "atr_distance": atr_distance,
    }


def _line(fig, y, label, dash="dot", width=1.0, color="#64748b"):
    y = _safe_float(y)
    if np.isnan(y):
        return
    fig.add_hline(
        y=y,
        line_dash=dash,
        line_width=width,
        line_color=color,
        opacity=0.92,
        annotation_text=label,
        annotation_position="right",
        annotation_font_size=10,
        annotation_font_color=color,
    )


def _professional_y_range(df, target=None, atr=None):
    lows = []
    highs = []
    if "Low" in df.columns:
        lows.append(_safe_float(df["Low"].min()))
    if "High" in df.columns:
        highs.append(_safe_float(df["High"].max()))
    lows.append(_safe_float(df["Close"].min()))
    highs.append(_safe_float(df["Close"].max()))
    if target is not None:
        lows.append(_safe_float(target))
        highs.append(_safe_float(target))

    low = np.nanmin(lows)
    high = np.nanmax(highs)
    if np.isnan(low) or np.isnan(high) or low == high:
        return None

    pad = (high - low) * 0.20
    if atr and atr > 0:
        pad = max(pad, atr * 0.60)
    else:
        pad = max(pad, high * 0.002)
    return [low - pad, high + pad]


def plot_chart(df, asset, timeframe, target=None, atr=None):
    """Clean professional chart for execution decisions.

    Design goal: one story, not chart clutter.
    Visible layers: price, EMA20, current price, previous close, target.
    Removed: session marker arrows, dominant volume bars, oversized target rectangle.
    """
    df = _clean_numeric(df)
    fig = go.Figure()
    if df.empty:
        return fig

    use_candle = timeframe in ["1D", "5D"] and {"Open", "High", "Low", "Close"}.issubset(df.columns)

    if use_candle:
        fig.add_trace(
            go.Candlestick(
                x=df["Date"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name=asset,
                increasing_line_color="#059669",
                increasing_fillcolor="rgba(5,150,105,0.55)",
                decreasing_line_color="#dc2626",
                decreasing_fillcolor="rgba(220,38,38,0.45)",
                increasing_line_width=1.2,
                decreasing_line_width=1.2,
                showlegend=False,
                hoverinfo="x+y",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                mode="lines",
                name="Price",
                line=dict(width=2.6, color="#2563eb"),
                hovertemplate="%{x}<br>Close: EUR %{y:.2f}<extra></extra>",
            )
        )

    # Moving average kept subtle, not dominant.
    if len(df) >= 20:
        ema20 = df["Close"].ewm(span=20, adjust=False).mean()
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=ema20,
                mode="lines",
                name="EMA20",
                line=dict(width=1.3, color="#f59e0b"),
                hovertemplate="%{x}<br>EMA20: EUR %{y:.2f}<extra></extra>",
            )
        )

    latest = _safe_float(df["Close"].iloc[-1])
    previous_close = _safe_float(df["Close"].iloc[-2]) if len(df) >= 2 else np.nan
    session_low = _safe_float(df["Low"].min()) if "Low" in df.columns else _safe_float(df["Close"].min())
    session_high = _safe_float(df["High"].max()) if "High" in df.columns else _safe_float(df["Close"].max())

    target_val = _safe_float(target)
    if not np.isnan(target_val):
        band = max((atr or 0) * 0.04, target_val * 0.00025)
        fig.add_hrect(
            y0=target_val - band,
            y1=target_val + band,
            fillcolor="rgba(16,185,129,0.08)",
            line_width=0,
            layer="below",
        )
        _line(fig, target_val, "Target", dash="dash", width=1.8, color="#059669")

    _line(fig, latest, "Current", dash="solid", width=1.2, color="#1d4ed8")
    if not np.isnan(previous_close):
        _line(fig, previous_close, "Prev close", dash="dot", width=0.9, color="#94a3b8")

    # Dynamic y-axis: zoom around the price/action zone so candles are readable.
    y_range = _professional_y_range(df, target=target_val, atr=atr)

    height = 340 if st.session_state.get("layout_mode") == "Mobile" else 520
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=24, b=8),
        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        dragmode=False,
        font=dict(size=11, color="#334155"),
    )
    fig.update_xaxes(
        showgrid=False,
        rangeslider=dict(visible=False),
        title=None,
        showline=True,
        linewidth=1,
        linecolor="#e5e7eb",
        tickfont=dict(size=10),
    )
    fig.update_yaxes(
        range=y_range,
        showgrid=True,
        gridcolor="#eef2f7",
        zeroline=False,
        title=None,
        tickprefix="EUR ",
        showline=True,
        linewidth=1,
        linecolor="#e5e7eb",
        tickfont=dict(size=10),
    )
    return fig


def render_chart(asset, target=None, atr=None, *args, **kwargs):
    timeframe_map = {
        "1D": ("1d", "5m"),
        "5D": ("5d", "15m"),
        "1M": ("1mo", "1d"),
        "6M": ("6mo", "1d"),
        "1Y": ("1y", "1d"),
        "5Y": ("5y", "1wk"),
    }

    timeframe_key = f"chart_timeframe_{asset}"
    if timeframe_key not in st.session_state:
        st.session_state[timeframe_key] = "1D"

    tf = st.radio(
        "Timeframe",
        list(timeframe_map.keys()),
        horizontal=True,
        key=timeframe_key,
        label_visibility="collapsed",
    )

    period, interval = timeframe_map[tf]
    chart_df = fetch_chart_data(TICKERS[asset], period=period, interval=interval)

    if chart_df.empty:
        st.warning("No chart data available for this timeframe.")
        return

    try:
        fig = plot_chart(chart_df, asset, tf, target=target, atr=atr)
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False, "scrollZoom": False, "responsive": True},
        )
    except Exception as exc:
        st.warning("Advanced chart failed, showing a simple fallback chart.")
        fallback = chart_df[["Date", "Close"]].dropna().set_index("Date")
        st.line_chart(fallback, use_container_width=True)
        st.caption(f"Chart fallback reason: {type(exc).__name__}")

    chart_df = _clean_numeric(chart_df)
    if chart_df.empty:
        return

    latest = _safe_float(chart_df["Close"].iloc[-1])
    first = _safe_float(chart_df["Close"].iloc[0])
    open_price = _safe_float(chart_df["Open"].iloc[0]) if "Open" in chart_df.columns else np.nan
    high_price = _safe_float(chart_df["High"].max()) if "High" in chart_df.columns else np.nan
    low_price = _safe_float(chart_df["Low"].min()) if "Low" in chart_df.columns else np.nan
    period_change = ((latest / first) - 1) * 100 if first and not np.isnan(first) else 0.0

    target_val = _safe_float(target, latest)
    status = _target_status(latest, low_price, target_val, atr)

    # Cleaner compact summary cards.
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Open", f"EUR {open_price:.2f}" if not np.isnan(open_price) else "n/a")
    c2.metric("High", f"EUR {high_price:.2f}" if not np.isnan(high_price) else "n/a")
    c3.metric("Low", f"EUR {low_price:.2f}" if not np.isnan(low_price) else "n/a")
    c4.metric("Latest", f"EUR {latest:.2f}" if not np.isnan(latest) else "n/a")
    c5.metric(f"{tf} move", f"{period_change:.2f}%")

    progress = 0.0
    if not np.isnan(target_val) and not np.isnan(latest) and latest > target_val:
        # 0% = far; 100% = target touched. Use 1.5% as practical maximum distance for progress scaling.
        progress = max(0, min(100, 100 - (status["distance_pct"] / 1.5) * 100))
    elif low_price <= target_val:
        progress = 100.0

    atr_text = "n/a" if np.isnan(status["atr_distance"]) else f"{status['atr_distance']:.2f}x ATR"
    low_text = "already touched" if status["low_distance"] <= 0 else f"EUR {status['low_distance']:.2f} away"

    st.markdown(
        f"""
        <div class="chart-story-card">
            <div class="chart-story-title">Chart meaning: {status['status']}</div>
            <div class="chart-progress-bg"><div class="chart-progress-fill" style="width:{progress:.0f}%"></div></div>
            <div class="chart-story-text">
                {status['plain']}<br>
                <b>Distance from latest price to target:</b> EUR {status['distance']:.2f} ({status['distance_pct']:.2f}%).<br>
                <b>Today’s low vs target:</b> {low_text}.<br>
                <b>ATR distance:</b> {atr_text}. This tells you whether the target needs a normal move or an unusually large move.
            </div>
            <div class="small-muted">Chart intentionally shows only the decision layers: price, EMA20, current price, previous close and target. Final execution must be confirmed in IBKR.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
