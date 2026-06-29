# EXECUTE v6.10.4 UX Consolidation

Professional UI/UX cleanup release.

## What changed

- Dashboard rebuilt as a clean decision screen.
- One source of truth: Dashboard = today’s command, Daily Intelligence = explanation, Journal/Research Lab = history and diagnostics.
- Removed duplicate explanation blocks from the main flow.
- Added professional ETF deployment cards for V60A, VNGA80 and VWCE only.
- Grouped advanced pages into Research Lab tabs.
- Daily Intelligence now uses a cleaner story → deployment plan layout.
- Excel remains internal app memory at `data/PALI_EXECUTE_DATA.xlsx`.
- No Excel download button.
- No XEON/U03A.
- No personal name in report text.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

This version is still a local Streamlit application. Market data uses the existing live-ish quote pipeline and should be confirmed against IBKR before executing orders.
