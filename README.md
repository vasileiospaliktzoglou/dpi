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


## v7.3.1 Final Responsive Patch
- Smart auto-refresh: 15 seconds during the broad market window, 5 minutes outside.
- Internal memory saves only when quote values change.
- Responsive CSS only: same design, better wrapping on tablet/mobile.
- Plotly charts remain full-width on phone screens.
- PWA metadata added for install-to-home-screen support where Streamlit hosting allows it.


## v7.3.3 final mobile/PWA fix
- Card sections now render directly in Streamlit instead of fixed-height iframes, fixing mobile card wrapping/cropping.
- Market and ETF cards keep the same visual design but flow to 2 columns on tablet and 1 column on phone.
- Charts remain full width on phone.
- PWA metadata is served from `/app/static/` with Streamlit static serving enabled. Browser install support still depends on the hosting platform and HTTPS.
