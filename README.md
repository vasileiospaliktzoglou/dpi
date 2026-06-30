# PALI EXECUTE v7.0 Clean Decision

Professional Streamlit redesign focused on clarity instead of more widgets.

## What changed

- One market summary for all ETFs.
- No XEON or U03A anywhere.
- No repeated chart story blocks.
- Mobile-first layout with large decision hierarchy.
- Easier ETF selector on the main page.
- Restored live ETF charts using yfinance, with offline fallback demo data.
- Internal Excel memory only: `data/PALI_EXECUTE_MEMORY.xlsx`.
- Fixed Excel memory type handling so floats do not trigger `len()` errors.
- Plain-English explanation of target-touch statistics.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Main pages

- Dashboard: what to do today.
- ETF Detail: one ETF at a time.
- Analytics: compact comparison and historical target-touch explanation.
- Memory: confirms the hidden Excel memory location.

## Important

This is an execution decision-support tool. It does not predict tomorrow's close and does not place orders.
Always confirm the live bid/ask in IBKR before acting.
