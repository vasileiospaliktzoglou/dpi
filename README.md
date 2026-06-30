# PALI EXECUTE v7.1 Professional UX

A cleaner decision-first Streamlit app for V60A, VNGA80 and VWCE.

## What changed in v7.1

- Removed the visible internal Excel-memory debug message.
- Hid the unnecessary Streamlit white header/top strip.
- Removed repeated market explanations across ETF cards.
- Kept one global market summary for all ETFs.
- Improved ETF selection with a clearer inspect flow.
- Restored ETF live charts with target line.
- Added a mobile-first layout with stacked cards.
- Made historical target-touch wording simpler.
- Made Excel memory more defensive: if the workbook is corrupted, it is backed up and recreated.

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

This file is not shown in the UI. It is used as the app's internal learning/memory layer.
