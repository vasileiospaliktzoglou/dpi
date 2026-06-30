# PALI EXECUTE v7.2.5 — Timing Window Polish

This release keeps the v7.2.2 UI Polish foundation and applies focused improvements:

- Keeps the previous best layout and detailed charts.
- Fixes the raw HTML card rendering issue.
- Adds a **Best timing window** section for each ETF.
- Shows the historically strongest weekday and part of the month for V60A, VNGA80, and VWCE.
- Explains why the timing window matters in plain English.
- Keeps Excel memory hidden/internal.
- Maintains 5-year backtest statistics.
- Keeps automatic refresh.

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Smoke test:

```bash
python backtest_smoke.py
```


## v7.3 final cosmetic patch

- Page now starts with Today's markets.
- Removed the left sidebar navigation.
- Removed the duplicated Today's execution decision block.
- Replaced emoji status labels with professional badges.
- Market cards now show current value, today's move, 5-day move and 1-month move.
- Kept the detailed ETF charts and timing logic from the v7.2.5 base.
- Smoke test: `python backtest_smoke.py` passed in the build environment.

## v7.4 Decision Journal update

Added to the existing v7.3 design:

- Fair Value anchor for V60A, VNGA80, and VWCE.
- Expected Intraday Range based on historical intraday low/high behaviour versus previous close.
- Historical probability of getting a better price if you wait 1, 2, or 3 trading days.
- Execution Journal in the app UI, saved to `data/PALI_EXECUTE_MEMORY.xlsx` under `Execution_Journal`.
- Extended analytics table and Excel memory with fair value, expected range, and patience probabilities.

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Notes:

- Yahoo / yfinance data can be delayed, especially for European ETFs. Confirm live bid/ask in IBKR before placing orders.
- The probabilities are historical patience metrics, not forecasts.
- The journal is intended to improve the model over time by comparing real executions against later market prices.
