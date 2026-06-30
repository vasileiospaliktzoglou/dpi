# PALI Execute v8.1 — Tested Decision Engine

Streamlit decision-support app for V60A, VNGA80 and VWCE.

## What is included
- Daily BUY / WAIT / STRONG BUY / EXCEPTIONAL BUY signal.
- Suggested limit price based on historical ETF behaviour.
- Expected daily movement and next-day probability context.
- ETF priority board.
- Price ladder.
- Journal-ready snapshot.
- Robust fallback mode if Yahoo data is temporarily unavailable.

## Important
Yahoo Finance data for European ETFs may be delayed. Always confirm the final bid/ask in IBKR before placing orders.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud
Use `app.py` as the main file.

## Test status
- Python syntax checked: PASS
- Decision engine import/test for V60A, VNGA80, VWCE: PASS
- Streamlit server boot test: PASS
- Offline fallback test: PASS

The app loads even if Yahoo is temporarily unreachable. In that case it clearly warns that fallback/offline data is being used.
