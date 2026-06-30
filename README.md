# PALI EXECUTE v7.2 Mobile Dynamic

Decision-first Streamlit app for V60A, VNGA80 and VWCE.

## What changed in v7.2

- Reworked mobile layout so cards stack cleanly and text does not overflow.
- Removed visible version/debug text from the main interface.
- Made data dynamic with a refresh button and 15-minute cache.
- Uses 5-year price history for ETF decision statistics when live data is available.
- Replaced simplistic line chart with candlestick chart, 20/50-day averages, target line, buy zone and volume.
- Replaced confusing market-input block with Today’s Markets: real price + daily % move.
- Added chart range selector: 1M, 3M, 6M, 1Y, 3Y.
- Keeps Excel memory internal and silent.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Internal memory

The app writes internally to:

```text
data/PALI_EXECUTE_MEMORY.xlsx
```

It is not shown in the UI. Errors go to `logs/app.log`.
