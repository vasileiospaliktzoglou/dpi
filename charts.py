from __future__ import annotations
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def _range(df: pd.DataFrame, view: str) -> pd.DataFrame:
    if view == "1M":
        return df.tail(22)
    if view == "3M":
        return df.tail(66)
    if view == "6M":
        return df.tail(132)
    if view == "1Y":
        return df.tail(252)
    return df.tail(756)


def price_chart(df: pd.DataFrame, symbol: str, target: float, view: str = "6M"):
    plot_df = _range(df, view).copy()
    plot_df["MA20"] = plot_df["Close"].rolling(20).mean()
    plot_df["MA50"] = plot_df["Close"].rolling(50).mean()
    recent_range = (plot_df["High"] - plot_df["Low"]).tail(14).mean()
    zone_low = target - recent_range * 0.25
    zone_high = target + recent_range * 0.25

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.78, 0.22])
    fig.add_trace(
        go.Candlestick(
            x=plot_df.index,
            open=plot_df["Open"],
            high=plot_df["High"],
            low=plot_df["Low"],
            close=plot_df["Close"],
            name="Price",
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["MA20"], mode="lines", name="20-day avg", line=dict(width=1.4, color="#60a5fa")), row=1, col=1)
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["MA50"], mode="lines", name="50-day avg", line=dict(width=1.2, color="#a78bfa")), row=1, col=1)
    fig.add_hrect(y0=zone_low, y1=zone_high, fillcolor="#22c55e", opacity=0.10, line_width=0, row=1, col=1)
    fig.add_hline(y=target, line_dash="dash", line_color="#22c55e", annotation_text="Limit target", annotation_position="bottom right", row=1, col=1)
    fig.add_trace(go.Bar(x=plot_df.index, y=plot_df["Volume"], name="Volume", marker_color="rgba(148,163,184,.36)"), row=2, col=1)

    fig.update_layout(
        height=520,
        margin=dict(l=4, r=4, t=30, b=8),
        title=f"{symbol} chart · {view}",
        hovermode="x unified",
        autosize=True,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False,
        font=dict(family="Inter, Segoe UI, Arial", size=12),
    )
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,.13)", row=1, col=1)
    fig.update_yaxes(showgrid=False, title=None, row=2, col=1)
    fig.update_xaxes(showgrid=False, automargin=True)
    return fig


def market_bar(rows):
    labels = [r["label"] for r in rows]
    changes = [float(r["change_pct"]) for r in rows]
    colors = ["#22c55e" if x >= 0 else "#ef4444" for x in changes]
    fig = go.Figure(go.Bar(x=changes, y=labels, orientation="h", text=[f"{x:+.2f}%" for x in changes], textposition="auto", marker_color=colors))
    fig.update_layout(
        height=300,
        margin=dict(l=8, r=8, t=22, b=8),
        title="Today’s market moves",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Daily move",
        yaxis_title=None,
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,.13)")
    return fig


def comparison_chart(decisions):
    symbols = list(decisions.keys())
    gaps = [decisions[s].gap_pct for s in symbols]
    savings = [decisions[s].estimated_saving_eur for s in symbols]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=symbols, y=gaps, name="Above target (%)", text=[f"{g:.2f}%" for g in gaps], textposition="auto"))
    fig.add_trace(go.Scatter(x=symbols, y=[s / 100 for s in savings], name="Estimated saving / €100", mode="lines+markers", yaxis="y2"))
    fig.update_layout(
        height=320,
        margin=dict(l=8, r=8, t=30, b=8),
        title="Distance from target and execution value",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="Above target (%)"),
        yaxis2=dict(title="Saving per €100", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
