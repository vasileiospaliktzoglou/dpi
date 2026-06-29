import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
            "plain": "The ETF has traded at or below your limit level today. If your DAY order was live, it should have filled or come very close depending on spread and exchange execution.",
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


def _line(fig, y, label, row=1, dash="dot", width=1.0, color="#64748b"):
    y = _safe_float(y)
    if np.isnan(y):
        return
    fig.add_hline(
        y=y,
        row=row,
        col=1,
        line_dash=dash,
        line_width=width,
        line_color=color,
        opacity=0.9,
        annotation_text=label,
        annotation_position="right",
        annotation_font_size=10,
        annotation_font_color=color,
    )


def _professional_y_range(df, target=None, atr=None, baseline=None):
    values = []
    for col in ["Low", "High", "Close"]:
        if col in df.columns:
            values += [_safe_float(df[col].min()), _safe_float(df[col].max())]
    for v in [target, baseline]:
        if v is not None and not np.isnan(_safe_float(v)):
            values.append(_safe_float(v))
    values = [v for v in values if not np.isnan(v)]
    if not values:
        return None
    low = min(values)
    high = max(values)
    if low == high:
        pad = max(high * 0.002, 0.05)
    else:
        pad = (high - low) * 0.28
    if atr and atr > 0:
        pad = max(pad, atr * 0.45)
    return [low - pad, high + pad]


def _green_red_line_traces(df, baseline, asset):
    """Google-style line: green above reference, red below reference."""
    close = df["Close"]
    above = close.where(close >= baseline)
    below = close.where(close < baseline)
    traces = []
    traces.append(
        go.Scatter(
            x=df["Date"], y=above, mode="lines", name="Above reference",
            line=dict(width=3.0, color="#047857", shape="spline", smoothing=0.7),
            connectgaps=False,
            hovertemplate="%{x}<br>Price: EUR %{y:.2f}<extra></extra>",
        )
    )
    traces.append(
        go.Scatter(
            x=df["Date"], y=below, mode="lines", name="Below reference",
            line=dict(width=3.0, color="#dc2626", shape="spline", smoothing=0.7),
            connectgaps=False,
            hovertemplate="%{x}<br>Price: EUR %{y:.2f}<extra></extra>",
        )
    )
    return traces


def plot_chart(df, asset, timeframe, target=None, atr=None):
    """Meaning-first execution chart.

    v6.8 design:
    - Google Finance style price line for 1D/5D: green above previous close, red below.
    - Thin volume strip below the price, not dominating the chart.
    - Only the decision lines remain: reference/previous close, current, target.
    - Candlestick clutter removed from default dashboard view.
    """
    df = _clean_numeric(df)
    if df.empty:
        return go.Figure()

    has_volume = "Volume" in df.columns and df["Volume"].fillna(0).sum() > 0
    if has_volume:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.035,
            row_heights=[0.82, 0.18],
        )
    else:
        fig = make_subplots(rows=1, cols=1)

    latest = _safe_float(df["Close"].iloc[-1])
    first = _safe_float(df["Close"].iloc[0])
    # For intraday, previous close reference is approximated by first available price.
    # For longer timeframes, this still gives a clean visual reference for the displayed period.
    reference = first
    target_val = _safe_float(target)
    session_low = _safe_float(df["Low"].min()) if "Low" in df.columns else _safe_float(df["Close"].min())
    session_high = _safe_float(df["High"].max()) if "High" in df.columns else _safe_float(df["Close"].max())

    # Main price line, visually similar to Google Finance.
    if timeframe in ["1D", "5D"]:
        for trace in _green_red_line_traces(df, reference, asset):
            fig.add_trace(trace, row=1, col=1)
    else:
        line_color = "#047857" if latest >= reference else "#dc2626"
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                mode="lines",
                name="Price",
                line=dict(width=2.8, color=line_color, shape="spline", smoothing=0.6),
                hovertemplate="%{x}<br>Price: EUR %{y:.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    # EMA is kept very subtle, to avoid competing with price.
    if len(df) >= 20:
        ema20 = df["Close"].ewm(span=20, adjust=False).mean()
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=ema20,
                mode="lines",
                name="EMA20",
                line=dict(width=1.15, color="rgba(37,99,235,0.45)"),
                hovertemplate="%{x}<br>EMA20: EUR %{y:.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    # Reference lines that matter for execution.
    _line(fig, reference, "Reference", row=1, dash="dot", width=1.1, color="#64748b")
    _line(fig, latest, "Current", row=1, dash="solid", width=1.15, color="#0f172a")
    if not np.isnan(target_val):
        _line(fig, target_val, "Limit target", row=1, dash="dash", width=1.8, color="#059669")

    # Highlight latest price with a clear endpoint marker.
    fig.add_trace(
        go.Scatter(
            x=[df["Date"].iloc[-1]],
            y=[latest],
            mode="markers+text",
            marker=dict(size=9, color="#0f172a", line=dict(width=1, color="white")),
            text=[f"EUR {latest:.2f}"],
            textposition="middle right",
            textfont=dict(size=11, color="#0f172a"),
            showlegend=False,
            hovertemplate="Latest: EUR %{y:.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Low marker only if it is relevant to the target story; otherwise don't clutter.
    if not np.isnan(target_val) and session_low - target_val <= max(target_val * 0.004, (atr or 0) * 0.8):
        low_idx = df["Low"].idxmin() if "Low" in df.columns else df["Close"].idxmin()
        low_x = df.loc[low_idx, "Date"]
        fig.add_trace(
            go.Scatter(
                x=[low_x],
                y=[session_low],
                mode="markers",
                marker=dict(symbol="triangle-down", size=9, color="#f59e0b"),
                name="Today's low",
                showlegend=False,
                hovertemplate="Low: EUR %{y:.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    # Volume strip: present but intentionally quiet, like Google Finance.
    if has_volume:
        fig.add_trace(
            go.Bar(
                x=df["Date"],
                y=df["Volume"].fillna(0),
                marker=dict(color="rgba(100,116,139,0.35)"),
                name="Volume",
                hovertemplate="%{x}<br>Volume: %{y:,.0f}<extra></extra>",
                showlegend=False,
            ),
            row=2,
            col=1,
        )
        fig.update_yaxes(visible=False, row=2, col=1)

    y_range = _professional_y_range(df, target=target_val, atr=atr, baseline=reference)
    height = 360 if st.session_state.get("layout_mode") == "Mobile" else 560

    period_change = ((latest / reference) - 1) * 100 if reference else 0
    title_text = f"{asset} {timeframe} | EUR {latest:.2f} | {period_change:+.2f}%"

    fig.update_layout(
        title=dict(text=title_text, font=dict(size=16, color="#0f172a"), x=0.01, y=0.98),
        height=height,
        margin=dict(l=8, r=68, t=46, b=8),
        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="x unified",
        showlegend=False,
        dragmode=False,
        font=dict(size=11, color="#334155"),
    )
    fig.update_xaxes(
        showgrid=False,
        rangeslider=dict(visible=False),
        title=None,
        showline=False,
        tickfont=dict(size=10, color="#64748b"),
    )
    fig.update_yaxes(
        range=y_range,
        showgrid=True,
        gridcolor="#eef2f7",
        zeroline=False,
        title=None,
        tickprefix="EUR ",
        showline=False,
        tickfont=dict(size=10, color="#64748b"),
        row=1,
        col=1,
    )
    return fig


def render_chart(asset, target=None, atr=None, *args, **kwargs):
    timeframe_map = {
        "1D": ("1d", "5m"),
        "5D": ("5d", "15m"),
        "1M": ("1mo", "1d"),
        "6M": ("6mo", "1d"),
        "YTD": ("ytd", "1d"),
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
    high_price = _safe_float(chart_df["High"].max()) if "High" in chart_df.columns else np.nan
    low_price = _safe_float(chart_df["Low"].min()) if "Low" in chart_df.columns else np.nan
    period_change = ((latest / first) - 1) * 100 if first and not np.isnan(first) else 0.0

    # Keep the chart explanation compact. The app-level summary explains market context once.
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest", f"EUR {latest:.2f}" if not np.isnan(latest) else "n/a")
    c2.metric("Low", f"EUR {low_price:.2f}" if not np.isnan(low_price) else "n/a")
    c3.metric("High", f"EUR {high_price:.2f}" if not np.isnan(high_price) else "n/a")
    c4.metric(f"{tf} move", f"{period_change:.2f}%")

    st.caption("Chart guide: dashed green line = limit target; dark line = current price; dotted line = starting price for this view. Confirm final bid/ask in IBKR before execution.")
