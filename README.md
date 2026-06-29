# EXECUTE v6.10.6 Mobile Pro

Professional single-ETF deployment dashboard for V60A, VNGA80 and VWCE.

## What changed

- Mobile-first professional UI.
- One selected ETF is the main focus.
- Other ETFs are hidden in a compact comparison expander.
- Removed repeated Daily Intelligence / Deployment Plan blocks.
- Removed cash ETF references from the app universe.
- Internal Excel memory remains hidden in `data/PALI_EXECUTE_DATA.xlsx`.
- Backtest page added for 1-day and 5-day limit-touch evidence.
- Cleaner code structure with fewer repeated UI components.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Pages

1. **Today** — one ETF decision, best estimated deployment window, market explanation.
2. **Backtest** — historical limit-touch evidence for the selected ETF.
3. **Memory** — internal Excel memory status and recent stored records.

## Important note

The app estimates probability-based deployment windows. It does not predict exact prices or guarantee fills. Always confirm live bid/ask in IBKR before execution.
