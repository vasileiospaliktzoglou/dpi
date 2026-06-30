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
