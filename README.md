# PALI EXECUTE v6.10.8 Simplified Pro

This release removes repeated ETF commentary and keeps the app focused on one clear workflow:

1. One market summary for all tracked ETFs.
2. One deployment plan table for V60A, VNGA80 and VWCE.
3. One selected ETF decision card.
4. One live chart for the selected ETF.
5. Internal Excel memory only; no user-facing Excel download.

Fixes:
- Removed the duplicated chart story block.
- Reduced repeated market/ETF explanations.
- Fixed the internal Excel memory write path with safer cell sanitisation.
- Reworded backtest metrics into simple English.
- Keeps XEON and U03A excluded.

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```
