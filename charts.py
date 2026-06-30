from __future__ import annotations
import plotly.graph_objects as go
import pandas as pd


def price_chart(df: pd.DataFrame, symbol: str, target: float):
    plot_df = df.tail(90).copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["Close"], mode="lines", name="Close"))
    fig.add_hline(y=target, line_dash="dash", annotation_text="Target", annotation_position="top left")
    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
        title=f"{symbol} price vs target",
        xaxis_title=None,
        yaxis_title="Price",
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def comparison_chart(decisions):
    symbols = list(decisions.keys())
    gaps = [decisions[s].gap_pct for s in symbols]
    fig = go.Figure(go.Bar(x=symbols, y=gaps, text=[f"{g:.2f}%" for g in gaps], textposition="auto"))
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=30, b=10),
        title="Distance from target",
        xaxis_title=None,
        yaxis_title="Above target (%)",
        template="plotly_dark",
    )
    return fig
