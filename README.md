# PALI EXECUTE v7.2.4 HTML Card Fix

Based on v7.2.2 UI Polish. This patch keeps the same visual direction and fixes the raw HTML card/market-row issue by rendering those sections inside safe Streamlit HTML components.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Validation

`python backtest_smoke.py` passes.

## Changes

- Preserved the v7.2.2 layout and charts.
- Fixed raw `<div class="market-row">` / `<div class="card">` text appearing in the app.
- Kept automatic refresh.
- Kept hidden Excel memory.
- Kept V60A, VNGA80, VWCE only.

# PALI EXECUTE v7.2.2 UI Polish

Streamlit version based on v7.2, with focused UI fixes only.

## Changes
- Preserved the v7.2 layout and detailed charts.
- Added automatic 60-second refresh.
- Removed the manual refresh button.
- Improved mobile spacing and card wrapping.
- Changed the palette to softer navy/slate tones instead of harsh black/white contrast.
- Kept ETF scope to V60A, VNGA80, and VWCE only.
- Kept Excel memory hidden/internal.
- Added live quote attempt via yfinance `fast_info`; charts still use 5-year OHLC history.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

The internal memory workbook is created automatically at:

`data/PALI_EXECUTE_MEMORY.xlsx`
