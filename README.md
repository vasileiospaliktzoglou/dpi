# PALI EXECUTE v6.10.7 Mobile Chart Fix

Fixes included:
- Internal Excel memory `float has no len()` error fixed.
- ETF selection moved into the main screen with a mobile-friendly selector.
- Live ETF chart restored on the Today page.
- Mobile layout improved.
- Backtest labels rewritten in simple English: "target touch" instead of unclear "fill rate".
- Only V60A, VNGA80 and VWCE are included. XEON/U03A remain removed.

Run:
```bash
pip install -r requirements.txt
streamlit run app.py
```
