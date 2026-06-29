import streamlit as st
import pandas as pd
import numpy as np
import datetime
import yfinance as yf


@st.cache_data(ttl=30)
def fetch_bench(s):
    """
    Live-ish benchmark quote.

    Priority:
    1. yfinance fast_info last_price / previous_close
    2. intraday 1-minute fallback
    3. daily fallback

    Returns:
        (last_price, percent_change_from_previous_close)

    Note: Yahoo Finance can still be delayed. IBKR remains the final source
    for tradeable bid/ask prices.
    """
    try:
        ticker = yf.Ticker(s)

        try:
            info = ticker.fast_info
            last_price = float(info.get("last_price") or 0.0)
            previous_close = float(info.get("previous_close") or 0.0)

            if last_price > 0 and previous_close > 0:
                return last_price, ((last_price / previous_close) - 1) * 100
        except Exception:
            pass

        # Intraday fallback. This is useful during active market hours.
        try:
            df = yf.download(
                s,
                period="2d",
                interval="1m",
                progress=False,
                auto_adjust=False,
                prepost=False,
                threads=False,
            )

            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                close_series = df["Close"].dropna()
                if len(close_series) >= 2:
                    last_price = float(close_series.iloc[-1])

                    # Use first available close as fallback baseline if previous_close is unavailable.
                    baseline = float(close_series.iloc[0])
                    if baseline > 0:
                        return last_price, ((last_price / baseline) - 1) * 100
        except Exception:
            pass

        # Daily fallback.
        df = yf.download(
            s,
            period="7d",
            progress=False,
            auto_adjust=False,
            threads=False,
        )

        if df.empty or len(df) < 2:
            return 0.0, 0.0

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close_series = df["Close"].dropna()
        if len(close_series) < 2:
            return 0.0, 0.0

        close = float(close_series.iloc[-1])
        prev = float(close_series.iloc[-2])

        return close, ((close / prev) - 1) * 100

    except Exception:
        return 0.0, 0.0


@st.cache_data(ttl=30)
def fetch_live_quote(s):
    """
    Live-ish quote for ETFs and benchmarks.

    Priority:
    1. yfinance fast_info last_price / previous_close
    2. latest 1-minute intraday bar
    3. latest daily close fallback

    Returns a dict so the UI can show source/freshness clearly.
    Yahoo Finance may still be delayed. IBKR is the final trading source.
    """
    now_utc = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    empty = {
        "price": 0.0,
        "previous_close": 0.0,
        "change_pct": 0.0,
        "source": "unavailable",
        "timestamp": now_utc,
        "is_liveish": False,
    }

    try:
        ticker = yf.Ticker(s)

        try:
            info = ticker.fast_info
            last_price = float(info.get("last_price") or 0.0)
            previous_close = float(info.get("previous_close") or 0.0)
            if last_price > 0 and previous_close > 0:
                return {
                    "price": last_price,
                    "previous_close": previous_close,
                    "change_pct": ((last_price / previous_close) - 1) * 100,
                    "source": "fast_info",
                    "timestamp": now_utc,
                    "is_liveish": True,
                }
        except Exception:
            pass

        try:
            df = yf.download(
                s,
                period="2d",
                interval="1m",
                progress=False,
                auto_adjust=False,
                prepost=False,
                threads=False,
            )
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                close_series = df["Close"].dropna()
                if len(close_series) >= 2:
                    last_price = float(close_series.iloc[-1])
                    # Prefer previous daily close if available; otherwise first intraday bar.
                    previous_close = float(close_series.iloc[0])
                    if previous_close > 0:
                        return {
                            "price": last_price,
                            "previous_close": previous_close,
                            "change_pct": ((last_price / previous_close) - 1) * 100,
                            "source": "1m_intraday",
                            "timestamp": now_utc,
                            "is_liveish": True,
                        }
        except Exception:
            pass

        try:
            df = yf.download(
                s,
                period="7d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                close_series = df["Close"].dropna()
                if len(close_series) >= 2:
                    last_price = float(close_series.iloc[-1])
                    previous_close = float(close_series.iloc[-2])
                    if previous_close > 0:
                        return {
                            "price": last_price,
                            "previous_close": previous_close,
                            "change_pct": ((last_price / previous_close) - 1) * 100,
                            "source": "daily_fallback",
                            "timestamp": now_utc,
                            "is_liveish": False,
                        }
        except Exception:
            pass

        return empty

    except Exception:
        return empty


@st.cache_data(ttl=300)
def fetch_institutional_core(s):
    try:
        df = yf.download(
            s,
            start=datetime.date.today() - datetime.timedelta(days=5 * 365),
            end=datetime.date.today() + datetime.timedelta(days=1),
            progress=False,
            auto_adjust=False,
            threads=False,
        )

        if df.empty:
            return None, pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        df.columns = [str(c).capitalize() for c in df.columns]

        df["Date"] = pd.to_datetime(df["Date"])
        df["Wkday"] = df["Date"].dt.weekday
        df["Mday"] = df["Date"].dt.day

        df["Atr"] = (df["High"] - df["Low"]).rolling(14).mean()
        df["Ema20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["Sma200"] = df["Close"].rolling(200).mean()
        df["Std20"] = df["Close"].rolling(20).std()
        df["Zscore"] = (df["Close"] - df["Ema20"]) / df["Std20"]
        df["High52"] = df["High"].rolling(252).max()
        df["Drawdown"] = ((df["Close"] / df["High52"]) - 1) * 100

        clean = df.dropna().sort_values("Date").reset_index(drop=True)

        if clean.empty:
            return None, pd.DataFrame()

        return clean.iloc[-1], clean

    except Exception:
        return None, pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_sparkline_data(s, period="1mo", interval="1d"):
    try:
        df = yf.download(
            s,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            prepost=False,
            threads=False,
        )

        if df.empty:
            return pd.DataFrame(columns=["Date", "Close"])

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        date_col = "Datetime" if "Datetime" in df.columns else "Date"
        df[date_col] = pd.to_datetime(df[date_col])

        if "Close" not in df.columns:
            return pd.DataFrame(columns=["Date", "Close"])

        return (
            df[[date_col, "Close"]]
            .rename(columns={date_col: "Date"})
            .dropna(subset=["Date", "Close"])
            .sort_values("Date")
            .reset_index(drop=True)
        )

    except Exception:
        return pd.DataFrame(columns=["Date", "Close"])


@st.cache_data(ttl=300)
def fetch_chart_data(s, period="1mo", interval="1d"):
    try:
        df = yf.download(
            s,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            prepost=False,
            threads=False,
        )

        if df.empty:
            return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        date_col = "Datetime" if "Datetime" in df.columns else "Date"
        df[date_col] = pd.to_datetime(df[date_col])

        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col not in df.columns:
                df[col] = np.nan

        df = df[[date_col, "Open", "High", "Low", "Close", "Volume"]].rename(
            columns={date_col: "Date"}
        )

        return (
            df.dropna(subset=["Date", "Close"])
            .sort_values("Date")
            .reset_index(drop=True)
        )

    except Exception:
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Volume"])


@st.cache_data(ttl=300)
def compute_daily_trap_backtest(df_clean, multiplier=1.0):
    sim_df = df_clean.copy().sort_values("Date").reset_index(drop=True)

    fills = 0
    attempts = 0
    savings = []
    missed_moves = []

    for i in range(20, len(sim_df) - 1):
        today = sim_df.iloc[i]
        tomorrow = sim_df.iloc[i + 1]

        close = float(today["Close"])
        atr = float(today["Atr"])

        if np.isnan(close) or np.isnan(atr) or atr <= 0:
            continue

        limit_price = close - multiplier * atr
        attempts += 1

        if float(tomorrow["Low"]) <= limit_price:
            fills += 1
            saving = ((float(tomorrow["Close"]) / limit_price) - 1) * 100
            savings.append(saving)
        else:
            missed_move = ((float(tomorrow["Close"]) / close) - 1) * 100
            missed_moves.append(missed_move)

    return {
        "attempts": attempts,
        "fills": fills,
        "fill_rate": (fills / attempts) * 100 if attempts else 0.0,
        "avg_saving": float(np.mean(savings)) if savings else 0.0,
        "median_saving": float(np.median(savings)) if savings else 0.0,
        "avg_missed_move": float(np.mean(missed_moves)) if missed_moves else 0.0,
    }


@st.cache_data(ttl=300)
def compute_multi_day_trap_backtest(df_clean, multiplier=1.0, horizon=5):
    sim_df = df_clean.copy().sort_values("Date").reset_index(drop=True)

    fills = 0
    attempts = 0
    savings = []
    days_to_fill = []

    for i in range(20, len(sim_df) - horizon):
        today = sim_df.iloc[i]

        close = float(today["Close"])
        atr = float(today["Atr"])

        if np.isnan(close) or np.isnan(atr) or atr <= 0:
            continue

        limit_price = close - multiplier * atr
        attempts += 1

        future = sim_df.iloc[i + 1 : i + 1 + horizon]
        hit = future[future["Low"] <= limit_price]

        if not hit.empty:
            fills += 1
            first_hit_index = hit.index[0]
            fill_day = sim_df.loc[first_hit_index]

            saving = ((float(fill_day["Close"]) / limit_price) - 1) * 100
            savings.append(saving)
            days_to_fill.append(first_hit_index - i)

    return {
        "attempts": attempts,
        "fills": fills,
        "fill_rate": (fills / attempts) * 100 if attempts else 0.0,
        "avg_saving": float(np.mean(savings)) if savings else 0.0,
        "median_saving": float(np.median(savings)) if savings else 0.0,
        "avg_days_to_fill": float(np.mean(days_to_fill)) if days_to_fill else 0.0,
    }


@st.cache_data(ttl=300)
def compute_tab3_matrices(df_clean):
    sim_df = df_clean.copy().sort_values("Date").reset_index(drop=True)

    records = []
    multipliers = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]

    for mult in multipliers:
        stats_1d = compute_daily_trap_backtest(sim_df, multiplier=mult)
        stats_5d = compute_multi_day_trap_backtest(sim_df, multiplier=mult, horizon=5)

        records.append(
            {
                "ATR Multiplier": mult,
                "Next-Day Fill Rate (%)": stats_1d["fill_rate"],
                "Five-Day Fill Rate (%)": stats_5d["fill_rate"],
                "Average Saving (%)": stats_1d["avg_saving"],
                "Median Saving (%)": stats_1d["median_saving"],
                "Average Missed Move (%)": stats_1d["avg_missed_move"],
            }
        )

    return pd.DataFrame(records).set_index("ATR Multiplier")


@st.cache_data(ttl=300)
def compute_backtest_metrics(df_clean, monthly_amount=20000):
    sim_df = df_clean.copy().sort_values("Date").reset_index(drop=True)
    sim_df["Ym"] = sim_df["Date"].dt.to_period("M")

    blind_units = 0.0
    timed_units = 0.0
    chart_records = []

    for ym, gp in sim_df.groupby("Ym"):
        gp = gp.reset_index(drop=True)

        if gp.empty:
            continue

        blind_price = float(gp["Close"].iloc[-1])
        blind_units += monthly_amount / blind_price

        window = gp[(gp["Mday"] >= 18) & (gp["Mday"] <= 22)].copy()

        if not window.empty:
            base_day = window.iloc[0]
            atr = float(base_day["Atr"])
            close = float(base_day["Close"])
            trap = close - atr

            hit = window[window["Low"] <= trap]

            if not hit.empty:
                timed_price = trap
            else:
                timed_price = float(window["Close"].iloc[-1])
        else:
            timed_price = blind_price

        timed_units += monthly_amount / timed_price

        latest_price = float(gp["Close"].iloc[-1])

        chart_records.append(
            {
                "Date": gp["Date"].iloc[-1],
                "Blind DCA": blind_units * latest_price,
                "Timed Strategy": timed_units * latest_price,
            }
        )

    if not chart_records:
        return 0.0, 0.0, 0.0, 0.0, pd.DataFrame()

    chart_data = pd.DataFrame(chart_records).set_index("Date")

    v_a = float(chart_data["Blind DCA"].iloc[-1])
    v_b = float(chart_data["Timed Strategy"].iloc[-1])
    alpha = v_b - v_a
    pct_edge = (alpha / v_a) * 100 if v_a else 0.0

    return v_a, v_b, alpha, pct_edge, chart_data


@st.cache_data(ttl=300)
def compute_dip_statistics(df_clean, thresholds=None, recovery_horizons=None):
    """
    ETF-specific dip probability engine.

    Measures intraday dips from the previous completed close:
        intraday_dip_pct = (today_low / previous_close - 1) * 100

    Returns:
        {
            current_dip_pct,
            opportunity_score,
            threshold_table,
            recovery_table,
            total_sessions,
        }
    """
    if thresholds is None:
        thresholds = [-1, -2, -3, -5, -10]

    if recovery_horizons is None:
        recovery_horizons = [5, 20, 60]

    try:
        df = df_clean.copy().sort_values("Date").reset_index(drop=True)

        required = {"Date", "Open", "High", "Low", "Close"}
        if df.empty or not required.issubset(df.columns):
            return {
                "current_dip_pct": 0.0,
                "opportunity_score": 0,
                "threshold_table": pd.DataFrame(),
                "recovery_table": pd.DataFrame(),
                "total_sessions": 0,
            }

        df["Prev_close"] = df["Close"].shift(1)
        df["Intraday_dip_pct"] = ((df["Low"] / df["Prev_close"]) - 1) * 100
        df["Close_return_pct"] = ((df["Close"] / df["Prev_close"]) - 1) * 100

        valid = df.dropna(subset=["Prev_close", "Intraday_dip_pct"]).copy()
        total = len(valid)

        if total == 0:
            return {
                "current_dip_pct": 0.0,
                "opportunity_score": 0,
                "threshold_table": pd.DataFrame(),
                "recovery_table": pd.DataFrame(),
                "total_sessions": 0,
            }

        current_dip = float(valid["Intraday_dip_pct"].iloc[-1])

        # Rarity percentile: how many historical days had a less severe dip than today?
        # Example: 98 means today's dip is more severe than 98% of historical sessions.
        opportunity_score = int(
            max(
                0,
                min(
                    100,
                    (valid["Intraday_dip_pct"] > current_dip).mean() * 100,
                ),
            )
        )

        threshold_records = []
        for th in thresholds:
            hits = valid[valid["Intraday_dip_pct"] <= th]
            freq = (len(hits) / total) * 100 if total else 0.0

            threshold_records.append(
                {
                    "Dip threshold": f"{th:.0f}%",
                    "Historical frequency (%)": freq,
                    "Historical sessions": int(len(hits)),
                    "Current trigger": bool(current_dip <= th),
                    "Average dip on triggered days (%)": float(hits["Intraday_dip_pct"].mean()) if len(hits) else 0.0,
                    "Median same-day close return (%)": float(hits["Close_return_pct"].median()) if len(hits) else 0.0,
                }
            )

        threshold_table = pd.DataFrame(threshold_records)

        recovery_records = []
        for th in thresholds:
            hit_indexes = valid.index[valid["Intraday_dip_pct"] <= th].tolist()

            for horizon in recovery_horizons:
                returns = []

                for idx in hit_indexes:
                    future_idx = idx + horizon
                    if future_idx < len(df):
                        entry_close = float(df.loc[idx, "Close"])
                        future_close = float(df.loc[future_idx, "Close"])
                        if entry_close > 0:
                            returns.append(((future_close / entry_close) - 1) * 100)

                recovery_records.append(
                    {
                        "Dip threshold": f"{th:.0f}%",
                        "Horizon": f"{horizon}D",
                        "Average forward return (%)": float(np.mean(returns)) if returns else 0.0,
                        "Median forward return (%)": float(np.median(returns)) if returns else 0.0,
                        "Positive outcome rate (%)": float((np.array(returns) > 0).mean() * 100) if returns else 0.0,
                        "Sample size": int(len(returns)),
                    }
                )

        recovery_table = pd.DataFrame(recovery_records)

        return {
            "current_dip_pct": current_dip,
            "opportunity_score": opportunity_score,
            "threshold_table": threshold_table,
            "recovery_table": recovery_table,
            "total_sessions": int(total),
        }

    except Exception:
        return {
            "current_dip_pct": 0.0,
            "opportunity_score": 0,
            "threshold_table": pd.DataFrame(),
            "recovery_table": pd.DataFrame(),
            "total_sessions": 0,
        }


def suggest_deployment_ladder(current_dip_pct, base_amount=20000):
    """
    Smart deployment ladder for accumulation.

    Base:
        planned monthly/tranche execution amount.

    Extra:
        -2% dip: +5k optional reserve
        -5% dip: +10k extra reserve
        -10% dip: +10k additional crisis reserve
    """
    extra = 0
    triggers = []

    if current_dip_pct <= -2:
        extra += 5000
        triggers.append("-2% dip: optional +EUR 5k")

    if current_dip_pct <= -5:
        extra += 10000
        triggers.append("-5% dip: add +EUR 10k")

    if current_dip_pct <= -10:
        extra += 10000
        triggers.append("-10% dip: add another +EUR 10k")

    total = base_amount + extra

    if not triggers:
        explanation = "No major dip trigger today. Use the standard planned order only."
    else:
        explanation = " | ".join(triggers)

    return {
        "base_amount": int(base_amount),
        "extra_amount": int(extra),
        "total_amount": int(total),
        "triggers": triggers,
        "explanation": explanation,
    }



@st.cache_data(ttl=3600)
def compute_calendar_timing(df_clean, multiplier=1.0):
    """
    ETF-specific calendar execution analytics.

    This replaces the old raw-close calendar test. It asks a directly useful
    execution question:

        On which calendar days was the ETF most likely to touch a limit order
        placed multiplier x ATR below the previous completed close?

    This is better aligned with PALI because the app is not trying to find the
    lowest raw close of the month; it is trying to estimate when a limit order
    is most likely to be touched.
    """
    try:
        df = df_clean.copy().sort_values("Date").reset_index(drop=True)
        required = {"Date", "Close", "Low", "Atr"}
        if df.empty or not required.issubset(df.columns):
            empty = pd.DataFrame()
            return {
                "day_table": empty,
                "weekday_table": empty,
                "week_table": empty,
                "summary": "Not enough data for calendar execution analytics.",
                "method": "touch_probability",
            }

        df["Date"] = pd.to_datetime(df["Date"])
        df["Prev_close"] = df["Close"].shift(1)
        df["Prev_atr"] = df["Atr"].shift(1)
        df["Trap_price"] = df["Prev_close"] - (multiplier * df["Prev_atr"])
        df["Touched_trap"] = df["Low"] <= df["Trap_price"]
        df["Touch_saving_pct"] = ((df["Prev_close"] / df["Trap_price"]) - 1) * 100
        df["Intraday_dip_pct"] = ((df["Low"] / df["Prev_close"]) - 1) * 100

        df["Mday"] = df["Date"].dt.day
        df["Weekday"] = df["Date"].dt.day_name()
        df["Month_week"] = ((df["Mday"] - 1) // 7 + 1).clip(1, 5)

        valid = df.dropna(subset=["Prev_close", "Prev_atr", "Trap_price", "Intraday_dip_pct"]).copy()
        valid = valid[valid["Prev_close"] > 0]
        if valid.empty:
            empty = pd.DataFrame()
            return {
                "day_table": empty,
                "weekday_table": empty,
                "week_table": empty,
                "summary": "Not enough valid sessions for calendar execution analytics.",
                "method": "touch_probability",
            }

        def summarize(group_cols, label_col=None):
            out = (
                valid.groupby(group_cols)
                .agg(
                    Touch_probability_pct=("Touched_trap", lambda x: float(x.mean() * 100)),
                    Median_intraday_dip_pct=("Intraday_dip_pct", "median"),
                    Average_intraday_dip_pct=("Intraday_dip_pct", "mean"),
                    Median_target_discount_pct=("Touch_saving_pct", "median"),
                    Sample_size=("Touched_trap", "count"),
                )
                .reset_index()
            )
            if label_col:
                out = out.rename(columns={group_cols: label_col})
            return out.sort_values(["Touch_probability_pct", "Sample_size"], ascending=[False, False]).reset_index(drop=True)

        day_table = summarize("Mday", "Day of month")

        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        weekday_table = summarize("Weekday")
        weekday_table["_order"] = weekday_table["Weekday"].apply(lambda x: weekday_order.index(x) if x in weekday_order else 99)
        weekday_table = weekday_table.sort_values(["Touch_probability_pct", "Sample_size"], ascending=[False, False]).drop(columns=["_order"]).reset_index(drop=True)

        week_table = summarize("Month_week", "Week of month")

        best_day = day_table.iloc[0]
        best_weekday = weekday_table.iloc[0] if not weekday_table.empty else None
        best_week = week_table.iloc[0]

        # Reliability flag: if the best result is not meaningfully above the average,
        # do not pretend there is a strong calendar edge.
        overall_touch = float(valid["Touched_trap"].mean() * 100)
        edge = float(best_day["Touch_probability_pct"] - overall_touch)
        if edge >= 8 and int(best_day["Sample_size"]) >= 20:
            reliability = "meaningful"
        elif edge >= 4 and int(best_day["Sample_size"]) >= 15:
            reliability = "modest"
        else:
            reliability = "weak"

        summary = (
            f"Best day-of-month by limit-touch probability: day {int(best_day['Day of month'])} "
            f"({best_day['Touch_probability_pct']:.1f}% touch rate vs overall {overall_touch:.1f}%). "
            f"Best week-of-month: week {int(best_week['Week of month'])} "
            f"({best_week['Touch_probability_pct']:.1f}%)."
        )
        if best_weekday is not None:
            summary += f" Best weekday: {best_weekday['Weekday']} ({best_weekday['Touch_probability_pct']:.1f}%)."
        summary += f" Calendar edge reliability: {reliability}."

        return {
            "day_table": day_table,
            "weekday_table": weekday_table,
            "week_table": week_table,
            "summary": summary,
            "method": "touch_probability",
            "overall_touch_probability_pct": overall_touch,
            "reliability": reliability,
        }

    except Exception:
        empty = pd.DataFrame()
        return {
            "day_table": empty,
            "weekday_table": empty,
            "week_table": empty,
            "summary": "Calendar execution analytics failed.",
            "method": "touch_probability",
        }


@st.cache_data(ttl=1800)
def fetch_intraday_low_distribution(s, period="60d", interval="30m"):
    """
    Recent intraday timing analytics.

    Yahoo intraday history is limited, so this is a recent-sample tool rather
    than a multi-year institutional tape study. It estimates when the day's low
    most often occurred in recent sessions.

    Timestamps are converted to Bahrain time when Yahoo provides timezone-aware
    timestamps. Otherwise the output is labelled as Yahoo timestamp.
    """
    try:
        df = yf.download(
            s,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            prepost=False,
            threads=False,
        )

        if df.empty:
            return pd.DataFrame(), "No recent intraday data available.", "unknown"

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        date_col = "Datetime" if "Datetime" in df.columns else "Date"
        df[date_col] = pd.to_datetime(df[date_col])

        timezone_label = "Yahoo timestamp"
        try:
            if getattr(df[date_col].dt, "tz", None) is not None:
                df[date_col] = df[date_col].dt.tz_convert("Asia/Bahrain")
                timezone_label = "Bahrain time"
        except Exception:
            timezone_label = "Yahoo timestamp"

        if "Low" not in df.columns:
            return pd.DataFrame(), "Intraday low column unavailable.", timezone_label

        df["Session_date"] = df[date_col].dt.date
        idx = df.groupby("Session_date")["Low"].idxmin()
        lows = df.loc[idx, [date_col, "Low"]].copy()
        lows["Hour"] = lows[date_col].dt.hour + lows[date_col].dt.minute / 60.0

        def bucket(hour):
            if 10 <= hour < 12:
                return "10:00-12:00"
            if 12 <= hour < 14:
                return "12:00-14:00"
            if 14 <= hour < 16:
                return "14:00-16:00"
            if 16 <= hour <= 18.75:
                return "16:00-18:45"
            return "Other"

        lows["Low window"] = lows["Hour"].apply(bucket)
        total = len(lows)
        table = lows.groupby("Low window").size().reset_index(name="Sessions")
        table["Frequency (%)"] = (table["Sessions"] / total) * 100 if total else 0
        order = ["10:00-12:00", "12:00-14:00", "14:00-16:00", "16:00-18:45", "Other"]
        table["_order"] = table["Low window"].apply(lambda x: order.index(x) if x in order else 99)
        table = table.sort_values("_order").drop(columns=["_order"]).reset_index(drop=True)

        if not table.empty:
            best = table.sort_values("Frequency (%)", ascending=False).iloc[0]
            summary = (
                f"In the recent intraday sample, the daily low most often occurred during "
                f"{best['Low window']} ({best['Frequency (%)']:.1f}% of sessions, {timezone_label})."
            )
        else:
            summary = "Not enough intraday sessions to identify a timing pattern."

        return table, summary, timezone_label

    except Exception:
        return pd.DataFrame(), "Intraday timing calculation failed.", "unknown"



@st.cache_data(ttl=300)
def compute_previous_execution_review(df_clean, multiplier=1.0):
    """
    Review yesterday's generated limit order using the next completed daily candle.

    If row t-1 generated a target for row t, this function checks whether row t's
    low touched the target, how close it came, and where the close finished.
    """
    try:
        df = df_clean.copy().sort_values("Date").reset_index(drop=True)
        required = {"Date", "Close", "Low", "Atr"}
        if df.empty or len(df) < 3 or not required.issubset(df.columns):
            return {
                "available": False,
                "summary": "Not enough completed daily data to review the previous target.",
            }

        signal = df.iloc[-2]
        outcome = df.iloc[-1]

        prev_close = float(signal["Close"])
        prev_atr = float(signal["Atr"])
        target = prev_close - (multiplier * prev_atr)
        day_low = float(outcome["Low"])
        day_close = float(outcome["Close"])
        filled = bool(day_low <= target)

        closest_distance_eur = day_low - target
        closest_distance_pct = (closest_distance_eur / target) * 100 if target else 0.0
        close_distance_eur = day_close - target
        close_distance_pct = (close_distance_eur / target) * 100 if target else 0.0
        saving_vs_close_pct = ((day_close / target) - 1) * 100 if filled and target else 0.0

        if filled:
            status = "Filled"
            summary = (
                f"Previous target was touched. The day low reached EUR {day_low:.2f} versus target EUR {target:.2f}."
            )
        elif closest_distance_pct <= 0.25:
            status = "Very close"
            summary = (
                f"Previous target was not filled but came very close: missed by EUR {closest_distance_eur:.2f} ({closest_distance_pct:.2f}%)."
            )
        elif closest_distance_pct <= 0.75:
            status = "Reasonable miss"
            summary = (
                f"Previous target was not filled. Closest miss was EUR {closest_distance_eur:.2f} ({closest_distance_pct:.2f}%)."
            )
        else:
            status = "Far miss"
            summary = (
                f"Previous target was not close. It missed by EUR {closest_distance_eur:.2f} ({closest_distance_pct:.2f}%)."
            )

        return {
            "available": True,
            "signal_date": pd.to_datetime(signal["Date"]).strftime("%Y-%m-%d"),
            "outcome_date": pd.to_datetime(outcome["Date"]).strftime("%Y-%m-%d"),
            "target": target,
            "signal_close": prev_close,
            "signal_atr": prev_atr,
            "day_low": day_low,
            "day_close": day_close,
            "filled": filled,
            "status": status,
            "closest_distance_eur": closest_distance_eur,
            "closest_distance_pct": closest_distance_pct,
            "close_distance_eur": close_distance_eur,
            "close_distance_pct": close_distance_pct,
            "saving_vs_close_pct": saving_vs_close_pct,
            "summary": summary,
        }
    except Exception:
        return {
            "available": False,
            "summary": "Previous target review failed.",
        }
